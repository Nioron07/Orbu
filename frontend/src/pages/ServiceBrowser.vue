<template>
  <v-container fluid class="pa-6">
    <!-- Page Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h5 font-weight-bold">Service Browser</h1>
        <p class="text-caption text-medium-emphasis mb-0">
          Explore Acumatica REST API services and methods
        </p>
      </div>
    </div>

    <!-- Connection Required Alert -->
    <v-alert
      v-if="!clientsStore.isConnected"
      type="warning"
      variant="tonal"
      class="mb-4"
    >
      <div class="d-flex justify-space-between align-center">
        <span>Please connect to an Acumatica client first to browse services.</span>
        <v-btn
          color="warning"
          variant="text"
          @click="router.push('/clients')"
        >
          Go to Clients
        </v-btn>
      </div>
    </v-alert>

    <!-- Error Alert -->
    <v-alert
      v-if="error"
      type="error"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="error = null"
    >
      {{ error }}
    </v-alert>

    <!-- Filters Toolbar -->
    <div v-if="clientsStore.isConnected" class="d-flex gap-3 mb-4 align-center">
      <v-text-field
        v-model="searchQuery"
        prepend-inner-icon="mdi-magnify"
        placeholder="Search services..."
        density="compact"
        hide-details
        variant="outlined"
        clearable
        class="flex-grow-1"
        style="max-width: 600px"
      />

      <v-spacer />

      <v-chip size="small" variant="text" class="text-medium-emphasis">
        <v-icon start size="small">mdi-api</v-icon>
        {{ filteredServices.length }} {{ filteredServices.length === 1 ? 'service' : 'services' }}
      </v-chip>
    </div>

    <!-- Services Data Table -->
    <v-card v-if="clientsStore.isConnected" class="glass-card" elevation="0">
      <v-data-table
        :headers="tableHeaders"
        :items="filteredServices"
        :loading="loading"
        :items-per-page="25"
        density="comfortable"
        hover
        @click:row="handleRowClick"
      >
        <!-- Name Column -->
        <template v-slot:item.name="{ item }">
          <div class="d-flex align-center">
            <v-icon
              color="primary"
              size="small"
              class="mr-2"
            >
              mdi-api
            </v-icon>
            <span class="font-weight-medium">{{ item.name }}</span>
          </div>
        </template>

        <!-- Method Count Column -->
        <template v-slot:item.method_count="{ item }">
          <v-chip size="small" variant="tonal" color="info">
            {{ item.method_count }} {{ item.method_count === 1 ? 'method' : 'methods' }}
          </v-chip>
        </template>

        <!-- Loading State -->
        <template v-slot:loading>
          <v-skeleton-loader type="table-row@10" />
        </template>

        <!-- Empty State -->
        <template v-slot:no-data>
          <div class="text-center py-12">
            <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-api-off</v-icon>
            <h3 class="text-h6">No Services Found</h3>
            <p class="text-body-2 text-medium-emphasis mt-2">
              {{ searchQuery ? `No services match "${searchQuery}"` : 'No services available' }}
            </p>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Service Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="1600px" scrollable>
      <!-- Loading State -->
      <v-card v-if="!selectedServiceDetails">
        <v-card-title class="px-6 py-4">
          <v-skeleton-loader type="heading" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-6">
          <v-skeleton-loader type="table" />
        </v-card-text>
      </v-card>

      <!-- Loaded Content -->
      <v-card v-else>
        <v-card-title class="d-flex align-center justify-space-between px-6 py-4">
          <div class="text-h5 font-weight-bold">{{ selectedServiceDetails.name }}</div>
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="detailsDialog = false"
          />
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-6">
          <!-- Methods Table -->
          <div class="mb-4">
            <div class="d-flex align-center justify-end mb-3">
              <v-text-field
                v-model="methodSearch"
                prepend-inner-icon="mdi-magnify"
                placeholder="Search methods..."
                density="compact"
                variant="outlined"
                hide-details
                clearable
                style="max-width: 300px"
              />
            </div>

            <v-data-table
              :headers="methodHeaders"
              :items="filteredMethods"
              :items-per-page="15"
              density="compact"
              class="elevation-0"
            >
              <!-- Method Name -->
              <template v-slot:item.name="{ item }">
                <code class="method-name">{{ item.name }}</code>
              </template>

              <!-- Signature -->
              <template v-slot:item.signature="{ item }">
                <code v-if="item.signature" class="signature-code">{{ item.signature }}</code>
                <span v-else class="text-medium-emphasis">—</span>
              </template>
            </v-data-table>
          </div>
        </v-card-text>

        <v-divider />

        <v-card-actions class="px-6 py-4">
          <v-spacer />
          <v-btn
            variant="text"
            @click="detailsDialog = false"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useClientsStore } from '@/stores/clients';
import { clientApi } from '@/services/clientApi';
import type { ServiceInfo, ServiceDetails } from '@/services/clientApi';

const router = useRouter();
const clientsStore = useClientsStore();

// State
const allServices = ref<ServiceInfo[]>([]);
const selectedServiceDetails = ref<ServiceDetails | null>(null);
const searchQuery = ref('');
const methodSearch = ref('');
const loading = ref(false);
const error = ref<string | null>(null);
const detailsDialog = ref(false);

// Table headers
const tableHeaders = [
  {
    title: 'Service Name',
    key: 'name',
    sortable: true,
  },
  {
    title: 'Methods',
    key: 'method_count',
    sortable: true,
    width: '150px',
  },
];

const methodHeaders = [
  { title: 'Method Name', key: 'name', sortable: true, width: '40%' },
  { title: 'Signature', key: 'signature', sortable: false, width: '60%' },
];

// Computed
const filteredServices = computed(() => {
  if (!searchQuery.value) return allServices.value;

  const search = searchQuery.value.toLowerCase();
  return allServices.value.filter(service =>
    service.name.toLowerCase().includes(search)
  );
});

const filteredMethods = computed(() => {
  if (!selectedServiceDetails.value?.methods) return [];

  if (!methodSearch.value) return selectedServiceDetails.value.methods;

  const search = methodSearch.value.toLowerCase();
  return selectedServiceDetails.value.methods.filter(method =>
    method.name.toLowerCase().includes(search) ||
    method.signature?.toLowerCase().includes(search) ||
    method.docstring?.toLowerCase().includes(search) ||
    method.doc?.toLowerCase().includes(search)
  );
});

// Methods
async function loadServices() {
  if (!clientsStore.isConnected || !clientsStore.activeClient?.id) return;

  loading.value = true;
  error.value = null;

  try {
    const response = await clientApi.listServices(clientsStore.activeClient.id);
    if (response.success) {
      allServices.value = response.services;
    } else {
      throw new Error(response.error || 'Failed to load services');
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load services';
    allServices.value = [];
  } finally {
    loading.value = false;
  }
}

function handleRowClick(event: any, { item }: any) {
  selectService(item);
}

async function selectService(service: ServiceInfo) {
  if (!clientsStore.activeClient?.id) return;

  // Don't set table loading - use dialog loading instead
  error.value = null;
  methodSearch.value = '';

  // Open dialog immediately to show loading state
  detailsDialog.value = true;
  selectedServiceDetails.value = null; // Clear previous data

  try {
    const response = await clientApi.getServiceDetails(clientsStore.activeClient.id, service.name);
    if (response.success && response.service) {
      selectedServiceDetails.value = response.service;
    } else {
      detailsDialog.value = false;
      throw new Error(response.error || 'Failed to load service details');
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load service details';
    detailsDialog.value = false;
  }
}

// Lifecycle
onMounted(() => {
  if (clientsStore.isConnected) {
    loadServices();
  }
});

// Watch for connection changes
watch(() => clientsStore.isConnected, (connected) => {
  if (connected) {
    loadServices();
  } else {
    allServices.value = [];
    selectedServiceDetails.value = null;
  }
});

// Watch for active client changes (client switching)
watch(() => clientsStore.activeClientId, (newClientId, oldClientId) => {
  // Only reload if we actually switched between different clients (both connected)
  if (newClientId && oldClientId && newClientId !== oldClientId) {
    loadServices();
  }
});
</script>

<style scoped lang="scss">
// Table row hover
:deep(.v-data-table__tr) {
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    .v-data-table__td {
      background: rgba(var(--v-theme-primary), 0.04);
    }
  }
}

// Code styling
.method-name {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.875em;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.signature-code {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.8em;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

// Remove card elevation
.glass-card {
  transition: none !important;

  &:hover {
    box-shadow: none !important;
    transform: none !important;
  }
}
</style>
