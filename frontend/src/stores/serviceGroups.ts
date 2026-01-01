/**
 * Service Groups Store
 * Manages service group state and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { clientApi } from '@/services/clientApi'
import type { ServiceGroup, CreateServiceGroupRequest } from '@/services/clientApi'

export const useServiceGroupsStore = defineStore('serviceGroups', () => {
  // State
  const serviceGroups = ref<ServiceGroup[]>([])
  const selectedServiceGroup = ref<ServiceGroup | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const activeServiceGroups = computed(() =>
    serviceGroups.value.filter(sg => sg.is_active)
  )

  const hasServiceGroups = computed(() => serviceGroups.value.length > 0)

  // Actions
  async function loadServiceGroups(clientId: string, filters?: { is_active?: boolean }) {
    isLoading.value = true
    error.value = null

    try {
      const response = await clientApi.listServiceGroups(clientId, filters)
      if (response.success) {
        serviceGroups.value = response.service_groups
        return { success: true, serviceGroups: response.service_groups }
      } else {
        error.value = response.error || 'Failed to load service groups'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to load service groups'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function createServiceGroup(clientId: string, data: CreateServiceGroupRequest) {
    isLoading.value = true
    error.value = null

    try {
      const response = await clientApi.createServiceGroup(clientId, data)
      if (response.success) {
        serviceGroups.value.unshift(response.service_group)
        return { success: true, serviceGroup: response.service_group }
      } else {
        error.value = response.error || 'Failed to create service group'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to create service group'
      return { success: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  async function updateServiceGroup(clientId: string, serviceGroupId: string, updates: Partial<ServiceGroup>) {
    error.value = null

    try {
      const response = await clientApi.updateServiceGroup(clientId, serviceGroupId, updates)
      if (response.success) {
        const index = serviceGroups.value.findIndex(sg => sg.id === serviceGroupId)
        if (index !== -1) {
          serviceGroups.value[index] = response.service_group
        }
        if (selectedServiceGroup.value?.id === serviceGroupId) {
          selectedServiceGroup.value = response.service_group
        }
        return { success: true, serviceGroup: response.service_group }
      } else {
        error.value = response.error || 'Failed to update service group'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to update service group'
      return { success: false, error: error.value }
    }
  }

  async function deleteServiceGroup(clientId: string, serviceGroupId: string) {
    error.value = null

    try {
      const response = await clientApi.deleteServiceGroup(clientId, serviceGroupId)
      if (response.success) {
        serviceGroups.value = serviceGroups.value.filter(sg => sg.id !== serviceGroupId)
        if (selectedServiceGroup.value?.id === serviceGroupId) {
          selectedServiceGroup.value = serviceGroups.value[0] ?? null
        }
        return { success: true, message: response.message }
      } else {
        error.value = response.error || 'Failed to delete service group'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete service group'
      return { success: false, error: error.value }
    }
  }

  async function activateServiceGroup(clientId: string, serviceGroupId: string) {
    error.value = null

    try {
      const response = await clientApi.activateServiceGroup(clientId, serviceGroupId)
      if (response.success) {
        const index = serviceGroups.value.findIndex(sg => sg.id === serviceGroupId)
        if (index !== -1) {
          serviceGroups.value[index] = response.service_group
        }
        return { success: true, serviceGroup: response.service_group }
      } else {
        error.value = response.error || 'Failed to activate service group'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to activate service group'
      return { success: false, error: error.value }
    }
  }

  async function deactivateServiceGroup(clientId: string, serviceGroupId: string) {
    error.value = null

    try {
      const response = await clientApi.deactivateServiceGroup(clientId, serviceGroupId)
      if (response.success) {
        const index = serviceGroups.value.findIndex(sg => sg.id === serviceGroupId)
        if (index !== -1) {
          serviceGroups.value[index] = response.service_group
        }
        return { success: true, serviceGroup: response.service_group }
      } else {
        error.value = response.error || 'Failed to deactivate service group'
        return { success: false, error: error.value }
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to deactivate service group'
      return { success: false, error: error.value }
    }
  }

  function setSelectedServiceGroup(serviceGroup: ServiceGroup | null) {
    selectedServiceGroup.value = serviceGroup
  }

  function getServiceGroupById(serviceGroupId: string) {
    return serviceGroups.value.find(sg => sg.id === serviceGroupId) || null
  }

  async function getDeployedMethods(clientId: string, serviceGroupId: string) {
    try {
      const response = await clientApi.getDeployedMethods(clientId, serviceGroupId)
      if (response.success) {
        return { success: true, deployed_methods: response.deployed_methods }
      } else {
        return { success: false, error: response.error || 'Failed to get deployed methods' }
      }
    } catch (err: any) {
      return { success: false, error: err.message || 'Failed to get deployed methods' }
    }
  }

  function clearError() {
    error.value = null
  }

  function $reset() {
    serviceGroups.value = []
    selectedServiceGroup.value = null
    isLoading.value = false
    error.value = null
  }

  return {
    // State
    serviceGroups,
    selectedServiceGroup,
    isLoading,
    error,

    // Getters
    activeServiceGroups,
    hasServiceGroups,

    // Actions
    loadServiceGroups,
    createServiceGroup,
    updateServiceGroup,
    deleteServiceGroup,
    activateServiceGroup,
    deactivateServiceGroup,
    setSelectedServiceGroup,
    getServiceGroupById,
    getDeployedMethods,
    clearError,
    $reset
  }
})
