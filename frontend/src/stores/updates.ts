/**
 * Updates Store
 * Manages update checking and deployment state
 */

import { defineStore } from 'pinia'
import { updateApi, type UpdateCheckResponse } from '@/services/updateApi'

// Local storage keys
const DISMISSED_VERSION_KEY = 'orbu_dismissed_update_version'
const LAST_CHECK_KEY = 'orbu_last_update_check'

// Check interval (1 hour in milliseconds)
const CHECK_INTERVAL = 60 * 60 * 1000

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
     */
    async deploy(): Promise<boolean> {
      if (!this.canAutoUpdate) {
        this.error = 'Auto-update is not available on this platform'
        return false
      }

      if (this.isDeploying) return false

      this.isDeploying = true
      this.error = null

      try {
        const response = await updateApi.triggerDeploy()

        if (response.success) {
          // Show success message and wait for restart
          // The page will automatically reload when the service restarts
          return true
        } else {
          this.error = response.error || 'Deployment failed'
          return false
        }
      } catch (error: any) {
        this.error = error.response?.data?.error || error.message || 'Deployment failed'
        console.error('Deploy failed:', error)
        return false
      } finally {
        this.isDeploying = false
      }
    },

    /**
     * Clear all state
     */
    reset() {
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
      localStorage.removeItem(DISMISSED_VERSION_KEY)
      localStorage.removeItem(LAST_CHECK_KEY)
    },
  },
})
