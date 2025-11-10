/**
 * Pinia store for managing multiple Acumatica clients
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { clientApi, type Client } from '@/services/clientApi';
import { useSettingsStore } from '@/stores/settings';

export const useClientsStore = defineStore('clients', () => {
  // State
  const clients = ref<Client[]>([]);
  const activeClientId = ref<string | null>(null);
  const activeClient = ref<Client | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Connection state
  const isConnected = ref(false);
  const isConnecting = ref(false);
  const connectionInfo = ref<any>(null);

  // Computed
  const activeClients = computed(() =>
    clients.value.filter(c => c.is_active !== false)
  );

  const connectedClientName = computed(() =>
    activeClient.value?.name || ''
  );

  const hasClients = computed(() =>
    clients.value.length > 0
  );

  // Actions

  /**
   * Load all clients from the server
   */
  async function loadClients(params?: { active?: boolean; search?: string }) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await clientApi.listClients(params);
      if (response.success) {
        clients.value = response.clients;
        return { success: true };
      } else {
        throw new Error(response.error || 'Failed to load clients');
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to load clients';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Create a new client configuration
   */
  async function createClient(client: Client) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await clientApi.createClient(client);
      if (response.success) {
        // Add to local list
        clients.value.push(response.client);
        return { success: true, client: response.client };
      } else {
        throw new Error(response.error || 'Failed to create client');
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to create client';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Update a client configuration
   */
  async function updateClient(clientId: string, updates: Partial<Client>) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await clientApi.updateClient(clientId, updates);
      if (response.success) {
        // Update local list
        const index = clients.value.findIndex(c => c.id === clientId);
        if (index !== -1) {
          clients.value[index] = response.client;
        }
        // Update active client if it's the one being updated
        if (activeClientId.value === clientId) {
          activeClient.value = response.client;
        }
        return { success: true, client: response.client };
      } else {
        throw new Error(response.error || 'Failed to update client');
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to update client';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Delete a client configuration
   */
  async function deleteClient(clientId: string) {
    isLoading.value = true;
    error.value = null;

    try {
      await clientApi.deleteClient(clientId);

      // Remove from local list
      clients.value = clients.value.filter(c => c.id !== clientId);

      // Clear active client if it was deleted
      if (activeClientId.value === clientId) {
        activeClientId.value = null;
        activeClient.value = null;
        isConnected.value = false;
        connectionInfo.value = null;
      }

      // Handle auto-connect settings if this client was set as default or last connected
      const settingsStore = useSettingsStore();
      if (settingsStore.defaultClientId === clientId || settingsStore.lastConnectedClientId === clientId) {
        // Reset to manual mode to avoid connection errors
        settingsStore.resetToManual();
      }

      return { success: true };
    } catch (err: any) {
      error.value = err.message || 'Failed to delete client';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Test connection to a client
   */
  async function testClient(clientId: string) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await clientApi.testClient(clientId);
      if (response.success) {
        return {
          success: true,
          message: response.message,
          sessionInfo: response.session_info
        };
      } else {
        throw new Error(response.error || 'Connection test failed');
      }
    } catch (err: any) {
      error.value = err.message || 'Connection test failed';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Rebuild/refresh a client connection (invalidate cache)
   */
  async function rebuildClient(clientId: string) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await clientApi.rebuildClient(clientId);
      if (response.success) {
        // If this was the active client and it reconnected, update state
        if (response.was_connected && activeClientId.value === clientId) {
          // Reload clients to get updated metadata
          await loadClients();
        }
        return {
          success: true,
          message: response.message,
          was_connected: response.was_connected
        };
      } else {
        throw new Error(response.error || 'Client rebuild failed');
      }
    } catch (err: any) {
      error.value = err.message || 'Client rebuild failed';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Connect to a client (establish session)
   */
  async function connectToClient(clientId: string) {
    isConnecting.value = true;
    error.value = null;

    try {
      const response = await clientApi.connectToClient(clientId);
      if (response.success) {
        // Update state
        activeClientId.value = clientId;
        activeClient.value = clients.value.find(c => c.id === clientId) || null;
        isConnected.value = true;
        connectionInfo.value = response.connection_info;

        // Update last connected timestamp locally
        if (activeClient.value) {
          activeClient.value.last_connected_at = new Date().toISOString();
        }

        // Save as last connected client in settings
        const settingsStore = useSettingsStore();
        settingsStore.setLastConnectedClientId(clientId);

        return {
          success: true,
          message: response.message,
          connectionInfo: response.connection_info
        };
      } else {
        throw new Error(response.error || 'Connection failed');
      }
    } catch (err: any) {
      error.value = err.message || 'Connection failed';
      isConnected.value = false;
      activeClientId.value = null;
      activeClient.value = null;
      connectionInfo.value = null;
      return { success: false, error: error.value };
    } finally {
      isConnecting.value = false;
    }
  }

  /**
   * Disconnect from the current client
   */
  async function disconnectFromClient() {
    if (!activeClientId.value) return { success: true };

    try {
      await clientApi.disconnectFromClient(activeClientId.value);
    } catch (err) {
      console.error('Disconnect error:', err);
    } finally {
      isConnected.value = false;
      activeClientId.value = null;
      activeClient.value = null;
      connectionInfo.value = null;
    }

    return { success: true };
  }

  /**
   * Get a client by ID from the local list
   */
  function getClientById(clientId: string): Client | undefined {
    return clients.value.find(c => c.id === clientId);
  }

  /**
   * Clear any errors
   */
  function clearError() {
    error.value = null;
  }

  /**
   * Set the active client (for UI purposes, doesn't connect)
   */
  function setActiveClient(clientId: string | null) {
    activeClientId.value = clientId;
    activeClient.value = clientId ? getClientById(clientId) || null : null;
  }

  /**
   * Activate a client to make it available for connections
   */
  async function activateClient(clientId: string) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await clientApi.activateClient(clientId);
      if (response.success) {
        // Update local list
        const index = clients.value.findIndex(c => c.id === clientId);
        if (index !== -1) {
          clients.value[index] = response.client;
        }
        return { success: true, client: response.client };
      } else {
        throw new Error(response.error || 'Failed to activate client');
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to activate client';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Deactivate a client and disconnect if connected
   */
  async function deactivateClient(clientId: string) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await clientApi.deactivateClient(clientId);
      if (response.success) {
        // Update local list
        const index = clients.value.findIndex(c => c.id === clientId);
        if (index !== -1) {
          clients.value[index] = response.client;
        }

        // If this was the connected client, update connection state
        if (activeClientId.value === clientId) {
          isConnected.value = false;
          activeClientId.value = null;
          activeClient.value = null;
          connectionInfo.value = null;
        }

        return { success: true, client: response.client, wasConnected: response.was_connected };
      } else {
        throw new Error(response.error || 'Failed to deactivate client');
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to deactivate client';
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  }

  return {
    // State
    clients,
    activeClientId,
    activeClient,
    isLoading,
    error,
    isConnected,
    isConnecting,
    connectionInfo,

    // Computed
    activeClients,
    connectedClientName,
    hasClients,

    // Actions
    loadClients,
    createClient,
    updateClient,
    deleteClient,
    testClient,
    rebuildClient,
    connectToClient,
    disconnectFromClient,
    activateClient,
    deactivateClient,
    getClientById,
    clearError,
    setActiveClient,
  };
});