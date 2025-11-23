/**
 * Endpoints Store
 * Manages deployed endpoint state and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clientApi } from '@/services/clientApi'
import type { Endpoint, EndpointExecution, CreateEndpointRequest, DeployServiceRequest } from '@/services/clientApi'

export const useEndpointsStore = defineStore('endpoints', () => {
  // State
  const endpoints = ref<Endpoint[]>([])
  const selectedEndpoint = ref<Endpoint | null>(null)
  const endpointLogs = ref<EndpointExecution[]>([])
  const isLoading = ref(false)
  const isDeploying = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const endpointsByClient = computed(() => {
    return (clientId: string) => {
      return endpoints.value.filter(ep => ep.client_id === clientId)
    }
  })

  const activeEndpoints = computed(() => {
    return endpoints.value.filter(ep => ep.is_active)
  })

  const inactiveEndpoints = computed(() => {
    return endpoints.value.filter(ep => !ep.is_active)
  })

  const endpointsByService = computed(() => {
    return (serviceName: string) => {
      return endpoints.value.filter(ep => ep.service_name === serviceName)
    }
  })

  // Actions

  /**
   * Load all endpoints for a client
   */
  async function loadEndpoints(clientId: string, filters?: { is_active?: boolean; service_name?: string; method_name?: string }) {
    isLoading.value = true
    error.value = null

    try {
      const response = await clientApi.listEndpoints(clientId, filters)
      if (response.success) {
        endpoints.value = response.endpoints
        return { success: true, endpoints: response.endpoints }
      } else {
        error.value = response.error || 'Failed to load endpoints'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to load endpoints'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a single endpoint
   */
  async function createEndpoint(clientId: string, data: CreateEndpointRequest) {
    isDeploying.value = true
    error.value = null

    try {
      const response = await clientApi.createEndpoint(clientId, data)
      if (response.success) {
        endpoints.value.push(response.endpoint)
        return { success: true, endpoint: response.endpoint }
      } else {
        error.value = response.error || 'Failed to create endpoint'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to create endpoint'
      return { success: false, error: error.value }
    } finally {
      isDeploying.value = false
    }
  }

  /**
   * Deploy all methods of a service as endpoints
   */
  async function deployService(clientId: string, data: DeployServiceRequest) {
    isDeploying.value = true
    error.value = null

    try {
      const response = await clientApi.deployService(clientId, data)
      if (response.success) {
        // Reload endpoints for this client
        await loadEndpoints(clientId)
        return {
          success: true,
          created: response.created,
          skipped: response.skipped,
          errors: response.errors,
          summary: response.summary
        }
      } else {
        error.value = response.error || 'Failed to deploy service'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to deploy service'
      return { success: false, error: error.value }
    } finally {
      isDeploying.value = false
    }
  }

  /**
   * Get endpoint details
   */
  async function getEndpoint(endpointId: string) {
    isLoading.value = true
    error.value = null

    try {
      const response = await clientApi.getEndpoint(endpointId)
      if (response.success) {
        selectedEndpoint.value = response.endpoint
        return { success: true, endpoint: response.endpoint }
      } else {
        error.value = response.error || 'Failed to get endpoint'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to get endpoint'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update an endpoint
   */
  async function updateEndpoint(endpointId: string, updates: Partial<Endpoint>) {
    error.value = null

    try {
      const response = await clientApi.updateEndpoint(endpointId, updates)
      if (response.success) {
        const index = endpoints.value.findIndex(ep => ep.id === endpointId)
        if (index !== -1) {
          endpoints.value[index] = response.endpoint
        }
        if (selectedEndpoint.value?.id === endpointId) {
          selectedEndpoint.value = response.endpoint
        }
        return { success: true, endpoint: response.endpoint }
      } else {
        error.value = response.error || 'Failed to update endpoint'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to update endpoint'
      return { success: false, error: error.value }
    }
  }

  /**
   * Delete an endpoint
   */
  async function deleteEndpoint(endpointId: string) {
    error.value = null

    try {
      const response = await clientApi.deleteEndpoint(endpointId)
      if (response.success) {
        endpoints.value = endpoints.value.filter(ep => ep.id !== endpointId)
        if (selectedEndpoint.value?.id === endpointId) {
          selectedEndpoint.value = null
        }
        return { success: true }
      } else {
        error.value = response.error || 'Failed to delete endpoint'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete endpoint'
      return { success: false, error: error.value }
    }
  }

  /**
   * Activate an endpoint
   */
  async function activateEndpoint(endpointId: string) {
    error.value = null

    try {
      const response = await clientApi.activateEndpoint(endpointId)
      if (response.success) {
        const index = endpoints.value.findIndex(ep => ep.id === endpointId)
        if (index !== -1) {
          endpoints.value[index] = response.endpoint
        }
        return { success: true }
      } else {
        error.value = response.error || 'Failed to activate endpoint'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to activate endpoint'
      return { success: false, error: error.value }
    }
  }

  /**
   * Deactivate an endpoint
   */
  async function deactivateEndpoint(endpointId: string) {
    error.value = null

    try {
      const response = await clientApi.deactivateEndpoint(endpointId)
      if (response.success) {
        const index = endpoints.value.findIndex(ep => ep.id === endpointId)
        if (index !== -1) {
          endpoints.value[index] = response.endpoint
        }
        return { success: true }
      } else {
        error.value = response.error || 'Failed to deactivate endpoint'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to deactivate endpoint'
      return { success: false, error: error.value }
    }
  }

  /**
   * Get execution logs for an endpoint with filtering
   */
  async function loadEndpointLogs(
    endpointId: string,
    options: {
      limit?: number;
      offset?: number;
      status?: number;
      search?: string;
      since?: string;
      until?: string;
    } = {}
  ) {
    isLoading.value = true
    error.value = null

    try {
      const response = await clientApi.getEndpointLogs(endpointId, options)
      if (response.success) {
        endpointLogs.value = response.logs
        return {
          success: true,
          logs: response.logs,
          total: response.total,
          count: response.count,
          offset: response.offset
        }
      } else {
        error.value = response.error || 'Failed to load logs'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to load logs'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Test an endpoint
   */
  async function testEndpoint(endpointId: string, requestBody: any = {}) {
    error.value = null

    try {
      const response = await clientApi.testEndpoint(endpointId, requestBody)
      return response
    } catch (err: any) {
      error.value = err.message || 'Failed to test endpoint'
      return { success: false, error: error.value }
    }
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset store
   */
  function $reset() {
    endpoints.value = []
    selectedEndpoint.value = null
    endpointLogs.value = []
    isLoading.value = false
    isDeploying.value = false
    error.value = null
  }

  return {
    // State
    endpoints,
    selectedEndpoint,
    endpointLogs,
    isLoading,
    isDeploying,
    error,

    // Getters
    endpointsByClient,
    activeEndpoints,
    inactiveEndpoints,
    endpointsByService,

    // Actions
    loadEndpoints,
    createEndpoint,
    deployService,
    getEndpoint,
    updateEndpoint,
    deleteEndpoint,
    activateEndpoint,
    deactivateEndpoint,
    loadEndpointLogs,
    testEndpoint,
    clearError,
    $reset
  }
})
