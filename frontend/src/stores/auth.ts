/**
 * Authentication Store
 * Manages user authentication state and tokens
 */

import { defineStore } from 'pinia'
import { authApi, type User, type UserSettings, type AppConfig } from '@/services/authApi'
import { clientApi } from '@/services/clientApi'

// Token storage keys
const ACCESS_TOKEN_KEY = 'orbu_access_token'
const REFRESH_TOKEN_KEY = 'orbu_refresh_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY) || null,
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || null,
    isInitialized: false,
    isLoading: false,
    // App configuration (org name, etc.)
    appConfig: null as AppConfig | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken && !!state.user,
    isAdmin: (state) => state.user?.is_admin ?? false,
    userName: (state) => state.user?.name ?? '',
    userEmail: (state) => state.user?.email ?? '',
    userSettings: (state) => state.user?.settings ?? {},
    orgName: (state) => state.appConfig?.orgName ?? 'Orbu',
  },

  actions: {
    /**
     * Initialize auth state on app start
     */
    async initialize() {
      if (this.isInitialized) return

      // Mark as initializing to prevent re-entry
      this.isLoading = true

      try {
        // Fetch app config (org name, etc.) - doesn't require auth
        // Do this in the background, don't block initialization
        this.fetchAppConfig()

        if (this.accessToken) {
          // Set token on API services
          authApi.setAuthToken(this.accessToken)
          this.setupAxiosInterceptor()

          try {
            // Verify token and get user info
            const response = await authApi.getCurrentUser()
            this.user = response.user
          } catch (error: any) {
            // Token invalid, try to refresh
            if (this.refreshToken) {
              try {
                await this.refresh()
              } catch {
                // Refresh failed, clear tokens silently (don't redirect here)
                this.clearTokens()
              }
            } else {
              this.clearTokens()
            }
          }
        }
      } finally {
        this.isInitialized = true
        this.isLoading = false
      }
    },

    /**
     * Fetch app config in the background
     */
    async fetchAppConfig() {
      try {
        const configResponse = await authApi.getAppConfig()
        this.appConfig = configResponse.config
      } catch (error) {
        // Silently fail - org name will use default
        console.warn('Failed to fetch app config:', error)
      }
    },

    /**
     * Clear tokens without triggering side effects
     */
    clearTokens() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      authApi.setAuthToken(null)
    },

    /**
     * Login with email and password
     */
    async login(email: string, password: string) {
      this.isLoading = true
      try {
        const response = await authApi.login(email, password)

        this.accessToken = response.access_token
        this.refreshToken = response.refresh_token
        this.user = response.user

        // Store tokens
        localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token)
        localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token)

        // Set token on API services
        authApi.setAuthToken(response.access_token)
        this.setupAxiosInterceptor()

        return response
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Register a new account
     */
    async register(name: string, email: string, password: string) {
      this.isLoading = true
      try {
        return await authApi.register({ name, email, password })
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Logout and clear tokens
     */
    logout() {
      // Clear state
      this.user = null
      this.accessToken = null
      this.refreshToken = null

      // Clear storage
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)

      // Clear auth header
      authApi.setAuthToken(null)
    },

    /**
     * Refresh access token
     */
    async refresh() {
      if (!this.refreshToken) {
        throw new Error('No refresh token')
      }

      try {
        const response = await authApi.refreshToken(this.refreshToken)
        this.accessToken = response.access_token

        // Store new access token
        localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token)

        // Set token on API services
        authApi.setAuthToken(response.access_token)

        // Refresh user info
        const userResponse = await authApi.getCurrentUser()
        this.user = userResponse.user

        return response
      } catch (error) {
        // Refresh failed, logout
        this.logout()
        throw error
      }
    },

    /**
     * Update user settings on the server
     */
    async updateSettings(settings: Partial<UserSettings>) {
      if (!this.user) return

      try {
        const response = await authApi.updateUserSettings(settings)
        // Update local user settings
        if (this.user) {
          this.user.settings = response.settings
        }
        return response.settings
      } catch (error) {
        console.error('Failed to update settings:', error)
        throw error
      }
    },

    /**
     * Setup axios interceptor to handle 401 errors and auto-refresh
     */
    setupAxiosInterceptor() {
      // This would ideally be done on the axios instance in clientApi
      // For now, we handle 401 errors in the router guard
    },
  },
})
