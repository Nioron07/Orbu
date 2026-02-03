/**
 * Updates Store
 * Manages update checking and deployment state
 */

import { defineStore } from 'pinia'
import { updateApi, type UpdateCheckResponse, type BuildStatusResponse } from '@/services/updateApi'

// Local storage keys
const DISMISSED_VERSION_KEY = 'orbu_dismissed_update_version'
const LAST_CHECK_KEY = 'orbu_last_update_check'

// Check interval (1 hour in milliseconds)
const CHECK_INTERVAL = 60 * 60 * 1000

// Build polling interval (5 seconds)
const BUILD_POLL_INTERVAL = 5000

export const useUpdateStore = defineStore('updates', {
  state: () => ({
    currentVersion: '0.0.0',
    latestVersion: null as string | null,
    updateAvailable: false,
    releaseUrl: null as string | null,
    releaseNotes: '',
    platform: 'unknown',
    canAutoUpdate: false,
    isDismissed: false,
    isChecking: false,
    isDeploying: false,
    lastCheckTime: null as number | null,
    error: null as string | null,
    // Cloud Build state
    buildId: null as string | null,
    buildStatus: null as BuildStatusResponse['status'] | null,
    buildStep: null as string | null,
    buildLogsUrl: null as string | null,
    pollIntervalId: null as number | null,
    showUpdateDialog: false,
  }),

  getters: {
    shouldShowBanner: (state) => {
      return state.updateAvailable && !state.isDismissed
    },
  },

  actions: {
    /**
     * Initialize the store and load persisted state
     */
    async initialize() {
      // Load dismissed version from localStorage
      const dismissedVersion = localStorage.getItem(DISMISSED_VERSION_KEY)
      const lastCheck = localStorage.getItem(LAST_CHECK_KEY)

      if (lastCheck) {
        this.lastCheckTime = parseInt(lastCheck, 10)
      }

      // Get current version info
      try {
        const versionInfo = await updateApi.getCurrentVersion()
        this.currentVersion = versionInfo.version
        this.platform = versionInfo.platform
        this.canAutoUpdate = versionInfo.can_auto_update
      } catch (error) {
        console.error('Failed to get current version:', error)
      }

      // Check if we should auto-check (once per hour)
      if (this.shouldAutoCheck()) {
        await this.checkForUpdates()
      }

      // Restore dismissed state for current latest version
      if (dismissedVersion && dismissedVersion === this.latestVersion) {
        this.isDismissed = true
      }
    },

    /**
     * Determine if we should auto-check for updates
     */
    shouldAutoCheck(): boolean {
      if (!this.lastCheckTime) return true
      const timeSinceLastCheck = Date.now() - this.lastCheckTime
      return timeSinceLastCheck > CHECK_INTERVAL
    },

    /**
     * Check for updates from GitHub
     */
    async checkForUpdates(): Promise<UpdateCheckResponse | null> {
      if (this.isChecking) return null

      this.isChecking = true
      this.error = null

      try {
        const response = await updateApi.checkForUpdates()

        if (response.success) {
          this.currentVersion = response.current_version
          this.latestVersion = response.latest_version
          this.updateAvailable = response.update_available
          this.releaseUrl = response.release_url
          this.releaseNotes = response.release_notes
          this.platform = response.platform
          this.canAutoUpdate = response.can_auto_update

          // Update last check time
          this.lastCheckTime = Date.now()
          localStorage.setItem(LAST_CHECK_KEY, this.lastCheckTime.toString())

          // Check if this version was previously dismissed
          const dismissedVersion = localStorage.getItem(DISMISSED_VERSION_KEY)
          if (dismissedVersion && dismissedVersion !== this.latestVersion) {
            // New version available, clear dismissed state
            this.isDismissed = false
            localStorage.removeItem(DISMISSED_VERSION_KEY)
          }
        } else {
          this.error = response.error || 'Failed to check for updates'
        }

        return response
      } catch (error: any) {
        this.error = error.response?.data?.error || error.message || 'Failed to check for updates'
        console.error('Update check failed:', error)
        return null
      } finally {
        this.isChecking = false
      }
    },

    /**
     * Dismiss the update notification for the current version
     */
    dismiss() {
      this.isDismissed = true
      if (this.latestVersion) {
        localStorage.setItem(DISMISSED_VERSION_KEY, this.latestVersion)
      }
    },

    /**
     * Trigger deployment update (GCP only)
     * Starts Cloud Build and begins polling for status
     * @param machineType Cloud Build machine type
     */
    async deploy(machineType: string = 'E2_HIGHCPU_8'): Promise<boolean> {
      if (!this.canAutoUpdate) {
        this.error = 'Auto-update is not available on this platform'
        return false
      }

      if (this.isDeploying) return false

      this.isDeploying = true
      this.error = null
      this.buildId = null
      this.buildStatus = null
      this.buildStep = 'Starting build...'
      this.buildLogsUrl = null

      try {
        const response = await updateApi.triggerDeploy(machineType)

        if (response.success && response.build_id) {
          this.buildId = response.build_id
          this.buildLogsUrl = response.logs_url || null
          this.buildStep = response.message || 'Build started...'
          // Start polling for build status
          this.startPolling()
          return true
        } else {
          this.error = response.error || 'Failed to start build'
          this.isDeploying = false
          return false
        }
      } catch (error: any) {
        this.error = error.response?.data?.error || error.message || 'Deployment failed'
        console.error('Deploy failed:', error)
        this.isDeploying = false
        return false
      }
    },

    /**
     * Start polling for build status
     */
    startPolling() {
      // Clear any existing interval
      this.stopPolling()

      this.pollIntervalId = window.setInterval(async () => {
        await this.checkBuildStatus()
      }, BUILD_POLL_INTERVAL)
    },

    /**
     * Stop polling for build status
     */
    stopPolling() {
      if (this.pollIntervalId) {
        clearInterval(this.pollIntervalId)
        this.pollIntervalId = null
      }
    },

    /**
     * Check the current build status
     */
    async checkBuildStatus(): Promise<void> {
      if (!this.buildId) return

      try {
        const status = await updateApi.getBuildStatus(this.buildId)

        if (status.success) {
          this.buildStatus = status.status
          this.buildStep = status.step
          this.buildLogsUrl = status.logs_url

          // Check if build is complete (success or failure)
          const terminalStates = ['SUCCESS', 'FAILURE', 'CANCELLED', 'TIMEOUT', 'DEPLOY_FAILED']
          if (terminalStates.includes(status.status)) {
            this.stopPolling()
            this.isDeploying = false

            if (status.status === 'SUCCESS') {
              this.buildStep = 'Build complete! Please reload the page in a few minutes to use the new version.'
            } else {
              // Build failed
              this.error = `Build ${status.status.toLowerCase()}: ${status.step}`
            }
          }
        } else {
          this.error = status.error || 'Failed to check build status'
        }
      } catch (error: any) {
        console.error('Failed to check build status:', error)
        // Don't stop polling on transient errors
      }
    },

    /**
     * Clear all state
     */
    reset() {
      this.stopPolling()
      this.currentVersion = '0.0.0'
      this.latestVersion = null
      this.updateAvailable = false
      this.releaseUrl = null
      this.releaseNotes = ''
      this.platform = 'unknown'
      this.canAutoUpdate = false
      this.isDismissed = false
      this.isChecking = false
      this.isDeploying = false
      this.lastCheckTime = null
      this.error = null
      this.buildId = null
      this.buildStatus = null
      this.buildStep = null
      this.buildLogsUrl = null
      localStorage.removeItem(DISMISSED_VERSION_KEY)
      localStorage.removeItem(LAST_CHECK_KEY)
    },
  },
})
