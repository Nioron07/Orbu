<template>
  <v-menu offset-y :close-on-content-click="false" width="360">
    <template v-slot:activator="{ props }">
      <v-btn
        v-bind="props"
        :class="['client-switcher-btn', { 'client-switcher-btn--connected': clientsStore.isConnected, 'client-switcher-btn--connecting': clientsStore.isConnecting }]"
        variant="tonal"
        size="large"
        :loading="clientsStore.isConnecting"
      >
        <v-icon start>
          {{ clientsStore.isConnecting ? 'mdi-loading' : clientsStore.isConnected ? 'mdi-check-circle' : 'mdi-alert-circle-outline' }}
        </v-icon>
        <span class="client-switcher-btn__text">
          {{ clientsStore.isConnecting ? 'Connecting...' : clientsStore.activeClient?.name || 'No Connection' }}
        </span>
        <v-icon end>mdi-chevron-down</v-icon>
      </v-btn>
    </template>

    <v-card class="client-switcher-menu">
      <v-card-title class="d-flex align-center justify-space-between px-4 py-3">
        <span class="text-subtitle-1 font-weight-semibold">Switch Client</span>
      </v-card-title>

      <v-divider></v-divider>

      <div v-if="loading" class="pa-4">
        <LoadingState type="skeleton" :skeleton-count="3" size="small" />
      </div>

      <v-list v-else-if="clients.length > 0" density="compact" class="py-2">
        <v-list-item
          v-for="client in clients"
          :key="client.id"
          :active="clientsStore.activeClient?.id === client.id"
          :disabled="connecting === client.id"
          @click="handleClientSelect(client)"
          class="client-item"
        >
          <template v-slot:prepend>
            <v-avatar :color="getClientColor(client)" size="32">
              <v-icon size="18">
                {{ clientsStore.activeClient?.id === client.id ? 'mdi-check' : 'mdi-domain' }}
              </v-icon>
            </v-avatar>
          </template>

          <v-list-item-title class="font-weight-medium">
            {{ client.name }}
          </v-list-item-title>

          <v-list-item-subtitle class="text-caption">
            {{ client.tenant }}
          </v-list-item-subtitle>

          <template v-slot:append>
            <v-progress-circular
              v-if="connecting === client.id"
              indeterminate
              size="20"
              width="2"
              color="primary"
            ></v-progress-circular>
            <v-chip
              v-else-if="clientsStore.activeClient?.id === client.id"
              color="success"
              size="x-small"
              variant="flat"
            >
              Connected
            </v-chip>
          </template>
        </v-list-item>
      </v-list>

      <div v-else class="pa-6">
        <EmptyState
          icon="mdi-domain-off"
          title="No Clients"
          description="Add a client to get started"
          size="small"
          action-text="Add Client"
          action-icon="mdi-plus"
          @action="goToClients"
        />
      </div>

      <v-divider v-if="clients.length > 0"></v-divider>

      <v-card-actions v-if="clients.length > 0" class="px-4 py-3">
        <v-btn
          variant="text"
          color="primary"
          block
          @click="goToClients"
        >
          <v-icon start>mdi-cog</v-icon>
          Manage Clients
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-menu>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useClientsStore } from '@/stores/clients';
import type { Client } from '@/services/clientApi';
import LoadingState from './LoadingState.vue';
import EmptyState from './EmptyState.vue';

const router = useRouter();
const clientsStore = useClientsStore();

const connecting = ref<string | null>(null);

// Use active clients from the store
const clients = computed(() => clientsStore.activeClients);
const loading = computed(() => clientsStore.isLoading);

async function loadClients() {
  // Load clients into the store if not already loaded
  if (clientsStore.clients.length === 0) {
    await clientsStore.loadClients();
  }
}

async function handleClientSelect(client: Client) {
  if (clientsStore.activeClient?.id === client.id) {
    return; // Already connected
  }

  if (!client.id) return;

  connecting.value = client.id;
  try {
    await clientsStore.connectToClient(client.id);
  } catch (error) {
    console.error('Failed to connect to client:', error);
  } finally {
    connecting.value = null;
  }
}

function getClientColor(client: Client): string {
  if (clientsStore.activeClient?.id === client.id) {
    return 'success';
  }
  return 'primary';
}

function goToClients() {
  router.push('/clients');
}

onMounted(() => {
  loadClients();
});
</script>

<style scoped lang="scss">
.client-switcher-btn {
  min-width: 200px;
  transition: all 0.2s ease;

  &--connected {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%);

    &:hover {
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(6, 182, 212, 0.25) 100%);
    }
  }

  &--connecting {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);

    &:hover {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.25) 100%);
    }
  }
}

.client-switcher-btn__text {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin: 0 0.5rem;
}

.client-switcher-menu {
  max-height: 500px;
  overflow-y: auto;
}

.client-item {
  margin: 0 0.5rem;
  border-radius: 8px;
  transition: all 0.2s ease;

  &:hover {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
  }

  &.v-list-item--active {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.12) 100%);

    .v-theme--dark & {
      background: linear-gradient(135deg, rgba(129, 140, 248, 0.15) 0%, rgba(167, 139, 250, 0.15) 100%);
    }
  }
}
</style>
