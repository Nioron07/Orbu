<template>
  <v-container fluid class="pa-6">
    <!-- Compact Page Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h5 font-weight-bold">Acumatica Clients</h1>
        <p class="text-caption text-medium-emphasis mb-0">
          Manage your Acumatica instance connections
        </p>
      </div>
      <v-spacer />
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        @click="showCreateDialog = true"
      >
        Add Client
      </v-btn>
    </div>

    <!-- Filters Toolbar -->
    <div class="d-flex gap-3 mb-4 align-center">
      <v-text-field
        v-model="searchQuery"
        prepend-inner-icon="mdi-magnify"
        placeholder="Search clients..."
        density="compact"
        hide-details
        variant="outlined"
        clearable
        class="flex-grow-1"
        style="max-width: 600px"
      />

      <v-spacer />

      <v-btn-toggle
        v-model="filterActive"
        density="compact"
        divided
        mandatory
      >
        <v-btn value="all" size="small">All</v-btn>
        <v-btn value="active" size="small">Active</v-btn>
        <v-btn value="inactive" size="small">Inactive</v-btn>
      </v-btn-toggle>

      <v-chip size="small" variant="text" class="text-medium-emphasis ml-2">
        <v-icon start size="small">mdi-database</v-icon>
        {{ filteredClients.length }} {{ filteredClients.length === 1 ? 'client' : 'clients' }}
      </v-chip>
    </div>

    <!-- Modern Data Table -->
    <v-card class="glass-card data-table" elevation="0">
      <v-data-table
        :headers="tableHeaders"
        :items="filteredClients"
        :loading="clientsStore.isLoading"
        :items-per-page="15"
        density="comfortable"
        hover
        @click:row="handleRowClick"
      >
        <!-- Status Column -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item)"
            size="small"
            variant="flat"
            label
          >
            <v-icon start size="x-small">
              {{ getStatusIcon(item) }}
            </v-icon>
            {{ getStatusText(item) }}
          </v-chip>
        </template>

        <!-- Name Column with Icon -->
        <template v-slot:item.name="{ item }">
          <div class="d-flex align-center">
            <v-icon
              :color="item.is_active ? 'primary' : 'grey'"
              size="small"
              class="mr-2"
            >
              mdi-database
            </v-icon>
            <span class="font-weight-medium">{{ item.name }}</span>
          </div>
        </template>

        <!-- URL Column (truncated) -->
        <template v-slot:item.base_url="{ item }">
          <v-tooltip :text="item.base_url" location="top">
            <template v-slot:activator="{ props }">
              <span
                v-bind="props"
                class="text-caption text-truncate d-inline-block"
                style="max-width: 250px"
              >
                {{ item.base_url }}
              </span>
            </template>
          </v-tooltip>
        </template>

        <!-- API Key Column -->
        <template v-slot:item.api_key="{ item }">
          <div class="d-flex align-center">
            <code class="text-caption mr-2">{{ item.api_key }}</code>
            <v-btn
              icon="mdi-content-copy"
              variant="text"
              size="x-small"
              @click.stop="copyApiKeyFromRow(item)"
            />
          </div>
        </template>

        <!-- Last Connected Column -->
        <template v-slot:item.last_connected_at="{ item }">
          <span class="text-caption">
            {{ item.last_connected_at ? formatDate(item.last_connected_at) : '—' }}
          </span>
        </template>

        <!-- Actions Column -->
        <template v-slot:item.actions="{ item }">
          <div class="d-flex gap-2 justify-end action-buttons">
            <v-tooltip
              :text="!item.is_active ? 'Client is inactive' : (isConnected(item) ? 'Disconnect' : 'Connect')"
              location="top"
            >
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  :icon="isConnected(item) ? 'mdi-lan-disconnect' : 'mdi-lan-connect'"
                  size="small"
                  variant="tonal"
                  :color="isConnected(item) ? 'warning' : 'primary'"
                  @click.stop="isConnected(item) ? disconnect() : connect(item.id!)"
                  :loading="connectingId === item.id"
                  :disabled="!item.is_active && !isConnected(item)"
                />
              </template>
            </v-tooltip>

            <v-tooltip
              :text="!item.is_active ? 'Client is inactive' : 'Test Connection'"
              location="top"
            >
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-test-tube"
                  size="small"
                  variant="tonal"
                  color="secondary"
                  @click.stop="testConnection(item.id!)"
                  :loading="testingId === item.id"
                  :disabled="!item.is_active"
                />
              </template>
            </v-tooltip>

            <v-tooltip
              :text="!item.is_active ? 'Client is inactive' : 'Rebuild/Refresh (invalidate cache)'"
              location="top"
            >
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-refresh"
                  size="small"
                  variant="tonal"
                  color="info"
                  @click.stop="rebuildConnection(item.id!)"
                  :loading="rebuildingId === item.id"
                  :disabled="!item.is_active"
                />
              </template>
            </v-tooltip>

            <v-menu>
              <template v-slot:activator="{ props }">
                <v-btn
                  icon="mdi-dots-vertical"
                  size="small"
                  variant="text"
                  v-bind="props"
                  @click.stop
                />
              </template>
              <v-list density="compact">
                <v-list-item @click="editClient(item)">
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-pencil</v-icon>
                  </template>
                  <v-list-item-title>Edit</v-list-item-title>
                </v-list-item>
                <v-list-item @click="duplicateClient(item)">
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-content-copy</v-icon>
                  </template>
                  <v-list-item-title>Duplicate</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="regenerateApiKey(item)">
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-key-refresh</v-icon>
                  </template>
                  <v-list-item-title>Regenerate API Key</v-list-item-title>
                </v-list-item>
                <v-list-item @click="viewEndpoints(item)">
                  <template v-slot:prepend>
                    <v-icon size="small">mdi-api</v-icon>
                  </template>
                  <v-list-item-title>View Endpoints</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item
                  v-if="item.is_active"
                  @click="deactivateClient(item)"
                >
                  <template v-slot:prepend>
                    <v-icon size="small" color="warning">mdi-pause</v-icon>
                  </template>
                  <v-list-item-title class="text-warning">Deactivate</v-list-item-title>
                </v-list-item>
                <v-list-item
                  v-else
                  @click="activateClient(item)"
                >
                  <template v-slot:prepend>
                    <v-icon size="small" color="success">mdi-play</v-icon>
                  </template>
                  <v-list-item-title class="text-success">Activate</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="confirmDelete(item)">
                  <template v-slot:prepend>
                    <v-icon size="small" color="error">mdi-delete</v-icon>
                  </template>
                  <v-list-item-title class="text-error">Delete</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </template>

        <!-- Loading State -->
        <template v-slot:loading>
          <v-skeleton-loader type="table-row@5" />
        </template>

        <!-- Empty State -->
        <template v-slot:no-data>
          <div class="text-center py-12">
            <!-- No clients at all -->
            <template v-if="clientsStore.clients.length === 0">
              <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-database-off</v-icon>
              <h3 class="text-h6">No Clients Yet</h3>
              <p class="text-body-2 text-medium-emphasis mt-2">
                Add your first Acumatica client to get started
              </p>
              <v-btn
                color="primary"
                class="mt-4"
                prepend-icon="mdi-plus"
                @click="showCreateDialog = true"
              >
                Add Your First Client
              </v-btn>
            </template>

            <!-- No active clients (but clients exist) -->
            <template v-else-if="filterActive === 'active'">
              <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-pause-circle-outline</v-icon>
              <h3 class="text-h6">No Active Clients</h3>
              <p class="text-body-2 text-medium-emphasis mt-2">
                All clients are currently inactive
              </p>
            </template>

            <!-- No inactive clients (but clients exist) -->
            <template v-else-if="filterActive === 'inactive'">
              <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-check-circle-outline</v-icon>
              <h3 class="text-h6">No Inactive Clients</h3>
              <p class="text-body-2 text-medium-emphasis mt-2">
                All clients are currently active
              </p>
            </template>

            <!-- Search returned no results -->
            <template v-else-if="searchQuery">
              <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-magnify</v-icon>
              <h3 class="text-h6">No Results Found</h3>
              <p class="text-body-2 text-medium-emphasis mt-2">
                No clients match your search: "{{ searchQuery }}"
              </p>
            </template>
          </div>
        </template>

        <!-- Bottom Actions -->
        <template v-slot:bottom>
          <div class="text-center pt-2">
            <v-pagination
              v-model="page"
              :length="pageCount"
              :total-visible="7"
              density="compact"
            />
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Create/Edit Dialog -->
    <ClientDialog
      v-model="showCreateDialog"
      :client="editingClient"
      @save="saveClient"
    />

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center bg-error pa-4">
          <v-icon start>mdi-delete</v-icon>
          <span>Delete Client?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="showDeleteDialog = false" />
        </v-card-title>

        <v-card-text class="pa-6">
          <p class="text-h6 mb-3">
            Delete <strong>{{ deletingClient?.name }}</strong>?
          </p>
          <v-alert type="error" variant="tonal">
            This action cannot be undone. All client configuration and associated endpoints will be permanently deleted.
          </v-alert>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            @click="deleteClient"
            :loading="isDeleting"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for messages -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="bottom"
    >
      <v-icon v-if="snackbar.color === 'success'" start>mdi-check-circle</v-icon>
      <v-icon v-else-if="snackbar.color === 'error'" start>mdi-alert-circle</v-icon>
      <v-icon v-else start>mdi-information</v-icon>
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>

    <!-- Regenerate API Key Confirmation Dialog -->
    <v-dialog v-model="regenerateDialog.show" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center bg-warning pa-4">
          <v-icon start>mdi-alert</v-icon>
          <span>Regenerate API Key?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="regenerateDialog.show = false" />
        </v-card-title>

        <v-card-text class="pa-6">
          <p class="text-h6 mb-3">
            Regenerate API key for <strong>{{ regenerateDialog.clientName }}</strong>?
          </p>

          <v-alert type="warning" variant="tonal">
            This will invalidate the existing key and all external services using it will need to be updated.
          </v-alert>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="regenerateDialog.show = false">Cancel</v-btn>
          <v-btn
            color="warning"
            variant="flat"
            @click="confirmRegenerateApiKey"
            :loading="regenerateDialog.loading"
          >
            <v-icon start>mdi-key-refresh</v-icon>
            Regenerate
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useClientsStore } from '@/stores/clients';
import ClientDialog from '@/components/ClientDialog.vue';
import { clientApi, type Client } from '@/services/clientApi';

const clientsStore = useClientsStore();
const router = useRouter();

// Reactive data
const searchQuery = ref('');
const filterActive = ref<'all' | 'active' | 'inactive'>('all');
const showCreateDialog = ref(false);
const showDeleteDialog = ref(false);
const editingClient = ref<Client | null>(null);
const deletingClient = ref<Client | null>(null);
const connectingId = ref<string | null>(null);
const testingId = ref<string | null>(null);
const rebuildingId = ref<string | null>(null);
const isDeleting = ref(false);
const page = ref(1);

const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
});

const regenerateDialog = ref({
  show: false,
  clientName: '',
  clientId: '',
  loading: false
});

// Table configuration
const tableHeaders = [
  {
    title: 'Status',
    key: 'status',
    sortable: false,
    width: '120px'
  },
  {
    title: 'Name',
    key: 'name',
    sortable: true
  },
  {
    title: 'Description',
    key: 'description',
    sortable: false
  },
  {
    title: 'URL',
    key: 'base_url',
    sortable: true
  },
  {
    title: 'Tenant',
    key: 'tenant',
    sortable: true,
    width: '150px'
  },
  {
    title: 'API Key',
    key: 'api_key',
    sortable: false,
    width: '220px'
  },
  {
    title: 'Last Connected',
    key: 'last_connected_at',
    sortable: true,
    width: '180px'
  },
  {
    title: '',
    key: 'actions',
    sortable: false,
    width: '180px',
    align: 'end' as const
  },
];

// Computed
const filteredClients = computed(() => {
  let result = clientsStore.clients;

  // Filter by active status
  if (filterActive.value === 'active') {
    result = result.filter(c => c.is_active !== false);
  } else if (filterActive.value === 'inactive') {
    result = result.filter(c => c.is_active === false);
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(c =>
      c.name.toLowerCase().includes(query) ||
      c.description?.toLowerCase().includes(query) ||
      c.base_url.toLowerCase().includes(query) ||
      c.tenant.toLowerCase().includes(query)
    );
  }

  return result;
});

const pageCount = computed(() => Math.ceil(filteredClients.value.length / 15));

// Helper methods
function isConnected(client: Client) {
  return clientsStore.activeClientId === client.id && clientsStore.isConnected;
}

function getStatusColor(client: Client) {
  if (isConnected(client)) return 'success';
  if (client.is_active) return 'info';
  return 'grey';
}

function getStatusIcon(client: Client) {
  if (isConnected(client)) return 'mdi-check-circle';
  if (client.is_active) return 'mdi-circle';
  return 'mdi-circle-outline';
}

function getStatusText(client: Client) {
  if (isConnected(client)) return 'Connected';
  if (client.is_active) return 'Active';
  return 'Inactive';
}

function handleRowClick(event: any, { item }: any) {
  // Optional: Could expand details or navigate to detail view
  console.log('Row clicked:', item);
}

function formatDate(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;

  return date.toLocaleDateString();
}

// Actions
async function loadClients() {
  await clientsStore.loadClients();
}

async function connect(clientId: string) {
  connectingId.value = clientId;
  const result = await clientsStore.connectToClient(clientId);
  connectingId.value = null;

  if (result.success) {
    showSnackbar('Connected successfully', 'success');
  } else {
    showSnackbar(result.error || 'Connection failed', 'error');
  }
}

async function disconnect() {
  await clientsStore.disconnectFromClient();
  showSnackbar('Disconnected', 'info');
}

async function testConnection(clientId: string) {
  testingId.value = clientId;
  const result = await clientsStore.testClient(clientId);
  testingId.value = null;

  if (result.success) {
    showSnackbar('Connection test successful', 'success');
  } else {
    showSnackbar(result.error || 'Connection test failed', 'error');
  }
}

async function rebuildConnection(clientId: string) {
  rebuildingId.value = clientId;
  const result = await clientsStore.rebuildClient(clientId);
  rebuildingId.value = null;

  if (result.success) {
    showSnackbar(result.message || 'Client rebuilt successfully', 'success');
  } else {
    showSnackbar(result.error || 'Client rebuild failed', 'error');
  }
}

function editClient(client: Client) {
  editingClient.value = { ...client };
  showCreateDialog.value = true;
}

function duplicateClient(client: Client) {
  // Keep all settings including credentials when duplicating
  editingClient.value = {
    ...client,
    id: undefined,
    name: `${client.name} (Copy)`,
    created_at: undefined,
    updated_at: undefined,
    last_connected_at: undefined,
  };
  showCreateDialog.value = true;
}

async function copyApiKeyFromRow(client: Client) {
  if (!client.id) return;

  try {
    // Fetch the full API key from the backend
    const response = await clientApi.getApiKey(client.id);
    if (response.success && response.api_key) {
      navigator.clipboard.writeText(response.api_key);
      showSnackbar('API key copied to clipboard', 'success');
    } else {
      showSnackbar(response.error || 'Failed to get API key', 'error');
    }
  } catch (error: any) {
    showSnackbar(error.message || 'Failed to get API key', 'error');
  }
}

function regenerateApiKey(client: Client) {
  if (!client.id) return;

  regenerateDialog.value = {
    show: true,
    clientName: client.name,
    clientId: client.id,
    loading: false
  };
}

async function confirmRegenerateApiKey() {
  const clientId = regenerateDialog.value.clientId;
  if (!clientId) return;

  regenerateDialog.value.loading = true;

  try {
    const response = await clientApi.regenerateApiKey(clientId);
    if (response.success) {
      showSnackbar(`API key regenerated successfully. New key: ${response.api_key}`, 'success');
      // Reload clients to update the table
      await clientsStore.loadClients();
      regenerateDialog.value.show = false;
    } else {
      showSnackbar(response.error || 'Failed to regenerate API key', 'error');
    }
  } catch (error: any) {
    showSnackbar(error.message || 'Failed to regenerate API key', 'error');
  } finally {
    regenerateDialog.value.loading = false;
  }
}

function viewEndpoints(client: Client) {
  // Navigate to endpoints page with this client selected
  router.push({ path: '/endpoints', query: { client: client.id } });
}

async function saveClient(client: Client) {
  let result;
  if (client.id) {
    result = await clientsStore.updateClient(client.id, client);
  } else {
    result = await clientsStore.createClient(client);
  }

  if (result.success) {
    showSnackbar(
      client.id ? 'Client updated successfully' : 'Client created successfully',
      'success'
    );
    showCreateDialog.value = false;
    editingClient.value = null;
  } else {
    showSnackbar(result.error || 'Operation failed', 'error');
  }
}

function confirmDelete(client: Client) {
  deletingClient.value = client;
  showDeleteDialog.value = true;
}

async function deleteClient() {
  if (!deletingClient.value?.id) return;

  isDeleting.value = true;
  const result = await clientsStore.deleteClient(deletingClient.value.id);
  isDeleting.value = false;

  if (result.success) {
    showSnackbar('Client deleted successfully', 'success');
    showDeleteDialog.value = false;
    deletingClient.value = null;
  } else {
    showSnackbar(result.error || 'Delete failed', 'error');
  }
}

async function activateClient(client: Client) {
  if (!client.id) return;

  const result = await clientsStore.activateClient(client.id);

  if (result.success) {
    showSnackbar('Client activated successfully', 'success');
  } else {
    showSnackbar(result.error || 'Activation failed', 'error');
  }
}

async function deactivateClient(client: Client) {
  if (!client.id) return;

  // Show warning if client is currently connected
  if (isConnected(client)) {
    showSnackbar('Deactivating and disconnecting client...', 'warning');
  }

  const result = await clientsStore.deactivateClient(client.id);

  if (result.success) {
    const message = result.wasConnected
      ? 'Client deactivated and disconnected'
      : 'Client deactivated successfully';
    showSnackbar(message, 'success');
  } else {
    showSnackbar(result.error || 'Deactivation failed', 'error');
  }
}

let searchTimeout: ReturnType<typeof setTimeout>;
function debouncedSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    // Search is reactive via computed property
  }, 300);
}

function showSnackbar(message: string, color: string) {
  snackbar.value = {
    show: true,
    message,
    color
  };
}

// Lifecycle
onMounted(() => {
  loadClients();
});
</script>

<style scoped lang="scss">
// Table row - no elevation on hover
:deep(.v-data-table__tr) {
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    .v-data-table__td {
      background: rgba(var(--v-theme-primary), 0.04);
    }
  }
}

// Ensure chip in table doesn't wrap
:deep(.v-chip__content) {
  white-space: nowrap;
}

// Remove card elevation on hover
.glass-card {
  transition: none !important;

  &:hover {
    box-shadow: none !important;
    transform: none !important;
  }
}

// Add spacing between action buttons
.action-buttons {
  margin: 1vh;
  gap: 8px;
}

</style>