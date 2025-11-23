<template>
  <div class="endpoints-page">
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4">Endpoints</h1>
        <p class="text-medium-emphasis">Manage deployed API endpoints for your Acumatica services</p>
      </div>
      <v-spacer />
      <EndpointBuilder
        v-if="clientsStore.activeClient"
        :client-id="clientsStore.activeClient.id!"
        :client-connected="clientsStore.isConnected"
        @deployed="handleDeployed"
      />
    </div>

    <!-- Not Connected State -->
    <v-card v-if="!clientsStore.activeClient" class="glass-card" elevation="0">
      <v-card-text class="pa-12">
        <div class="text-center">
          <v-icon size="80" color="primary" class="mb-4">mdi-link-off</v-icon>
          <h2 class="text-h5 font-weight-bold mb-3">No Client Connected</h2>
          <p class="text-body-1 text-medium-emphasis mb-6" style="max-width: 500px; margin: 0 auto;">
            Connect to an Acumatica client to view and manage your deployed API endpoints.
          </p>
          <v-btn
            color="primary"
            size="large"
            prepend-icon="mdi-domain"
            to="/clients"
          >
            Go to Clients Page
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- Endpoints Table -->
    <v-card v-else>
      <v-card-title class="d-flex align-center pa-6">
        <span v-if="selectedCount === 0">Deployed Endpoints</span>
        <div v-else class="d-flex align-center gap-3">
          <span class="mr-2">{{ selectedCount }} selected</span>
          <v-btn
            color="success"
            variant="tonal"
            size="small"
            prepend-icon="mdi-play"
            class="mr-2"
            @click="showBulkActivateDialog = true"
          >
            Activate
          </v-btn>
          <v-btn
            color="warning"
            variant="tonal"
            size="small"
            prepend-icon="mdi-pause"
            class="mr-2"
            @click="showBulkDeactivateDialog = true"
          >
            Deactivate
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            size="small"
            prepend-icon="mdi-delete"
            @click="showBulkDeleteDialog = true"
          >
            Delete
          </v-btn>
        </div>
        <v-spacer />
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Search"
          single-line
          hide-details
          density="compact"
          clearable
          class="mr-4"
          style="max-width: 300px;"
        />
        <v-btn-toggle
          v-model="statusFilter"
          variant="outlined"
          density="compact"
          divided
          mandatory
        >
          <v-btn value="all">All</v-btn>
          <v-btn value="active">Active</v-btn>
          <v-btn value="inactive">Inactive</v-btn>
        </v-btn-toggle>
      </v-card-title>

      <v-data-table
        v-model="selectedEndpoints"
        :headers="headers"
        :items="filteredEndpoints"
        :loading="endpointsStore.isLoading"
        :search="search"
        item-value="id"
        show-select
        return-object
      >
        <!-- Status -->
        <template #item.is_active="{ item }">
          <v-chip
            :color="item.is_active ? 'success' : 'grey'"
            size="small"
            variant="flat"
          >
            {{ item.is_active ? 'Active' : 'Inactive' }}
          </v-chip>
        </template>

        <!-- Service.Method -->
        <template #item.method="{ item }">
          <div class="d-flex flex-column">
            <span class="font-weight-medium">{{ item.service_name }}</span>
            <span class="text-caption text-medium-emphasis">.{{ item.method_name }}</span>
          </div>
        </template>

        <!-- URL -->
        <template #item.url_path="{ item }">
          <div class="d-flex align-center">
            <code class="text-caption">{{ item.url_path }}</code>
            <v-btn
              icon="mdi-content-copy"
              variant="text"
              size="x-small"
              @click="copyUrl(item.url_path)"
            />
          </div>
        </template>

        <!-- Stats -->
        <template #item.stats="{ item }">
          <div v-if="item.stats" class="text-caption">
            <div>{{ item.stats.total_executions }} calls</div>
            <div class="text-medium-emphasis">{{ item.stats.avg_duration_ms }}ms avg</div>
          </div>
          <span v-else class="text-caption text-medium-emphasis">No data</span>
        </template>

        <!-- Actions -->
        <template #item.actions="{ item }">
          <div class="d-flex align-center gap-1">
            <v-tooltip text="View Schema" location="top">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-code-json"
                  variant="text"
                  size="small"
                  @click="viewSchema(item)"
                />
              </template>
            </v-tooltip>

            <v-tooltip :text="item.is_active ? 'Deactivate' : 'Activate'" location="top">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  :icon="item.is_active ? 'mdi-pause' : 'mdi-play'"
                  :color="item.is_active ? 'warning' : 'success'"
                  variant="text"
                  size="small"
                  @click="item.is_active ? confirmDeactivateEndpoint(item) : confirmActivateEndpoint(item)"
                />
              </template>
            </v-tooltip>

            <v-tooltip text="Delete" location="top">
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon="mdi-delete"
                  color="error"
                  variant="text"
                  size="small"
                  @click="confirmDeleteEndpoint(item)"
                />
              </template>
            </v-tooltip>

            <v-menu>
              <template #activator="{ props: menuProps }">
                <v-btn
                  v-bind="menuProps"
                  icon="mdi-dots-vertical"
                  variant="text"
                  size="small"
                />
              </template>

              <v-list density="compact">
                <v-list-item @click="testEndpoint(item)">
                  <template #prepend>
                    <v-icon>mdi-play-circle</v-icon>
                  </template>
                  <v-list-item-title>Test Endpoint</v-list-item-title>
                </v-list-item>

                <v-list-item @click="viewLogs(item)">
                  <template #prepend>
                    <v-icon>mdi-history</v-icon>
                  </template>
                  <v-list-item-title>View Logs</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Schema Dialog -->
    <v-dialog v-model="schemaDialog" max-width="1400" scrollable>
      <v-card v-if="selectedEndpoint">
        <v-card-title class="d-flex align-center bg-primary pa-4">
          <v-icon start color="white">mdi-code-json</v-icon>
          <span class="text-white">{{ selectedEndpoint.service_name }}.{{ selectedEndpoint.method_name }}</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" color="white" @click="schemaDialog = false" />
        </v-card-title>
        <v-card-text class="pa-8">
          <SchemaViewer
            :request-schema="selectedEndpoint.request_schema"
            :response-schema="selectedEndpoint.response_schema"
            :url-path="selectedEndpoint.url_path"
            :api-key="clientsStore.activeClient?.api_key"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Test Endpoint Dialog -->
    <TestEndpointDialog
      v-model="showTestDialog"
      :endpoint="endpointToTest"
    />

    <!-- Log Viewer Dialog -->
    <LogViewer
      v-model="showLogsDialog"
      :endpoint="endpointToViewLogs"
    />

    <!-- Bulk Activate Confirmation Dialog -->
    <v-dialog v-model="showBulkActivateDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center bg-success pa-4">
          <v-icon start>mdi-play</v-icon>
          <span>Activate Endpoints?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="showBulkActivateDialog = false" />
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="text-h6 mb-2">
            Activate {{ selectedCount }} endpoint{{ selectedCount === 1 ? '' : 's' }}?
          </p>
          <p class="text-body-2 text-medium-emphasis">
            These endpoints will become active and start accepting requests.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="success" variant="flat" @click="bulkActivate">Activate</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Bulk Deactivate Confirmation Dialog -->
    <v-dialog v-model="showBulkDeactivateDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center bg-warning pa-4">
          <v-icon start>mdi-pause</v-icon>
          <span>Deactivate Endpoints?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="showBulkDeactivateDialog = false" />
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="text-h6 mb-2">
            Deactivate {{ selectedCount }} endpoint{{ selectedCount === 1 ? '' : 's' }}?
          </p>
          <p class="text-body-2 text-medium-emphasis">
            These endpoints will stop accepting requests but will not be deleted.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="warning" variant="flat" @click="bulkDeactivate">Deactivate</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Bulk Delete Confirmation Dialog -->
    <v-dialog v-model="showBulkDeleteDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center bg-error pa-4">
          <v-icon start>mdi-delete</v-icon>
          <span>Delete Endpoints?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="showBulkDeleteDialog = false" />
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="text-h6 mb-2">
            Delete {{ selectedCount }} endpoint{{ selectedCount === 1 ? '' : 's' }}?
          </p>
          <v-alert type="error" variant="tonal" class="mt-4">
            This action cannot be undone. All endpoint configuration and execution logs will be permanently deleted.
          </v-alert>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="error" variant="flat" @click="bulkDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Single Endpoint Activate Dialog -->
    <v-dialog v-model="showActivateDialog" max-width="600">
      <v-card v-if="endpointToAction">
        <v-card-title class="d-flex align-center bg-success pa-4">
          <v-icon start>mdi-play</v-icon>
          <span>Activate Endpoint?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="showActivateDialog = false" />
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="text-h6 mb-2">
            {{ endpointToAction.service_name }}.{{ endpointToAction.method_name }}
          </p>
          <p class="text-body-2 text-medium-emphasis">
            This endpoint will become active and start accepting requests.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="success" variant="flat" @click="activateEndpoint(endpointToAction)">Activate</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Single Endpoint Deactivate Dialog -->
    <v-dialog v-model="showDeactivateDialog" max-width="600">
      <v-card v-if="endpointToAction">
        <v-card-title class="d-flex align-center bg-warning pa-4">
          <v-icon start>mdi-pause</v-icon>
          <span>Deactivate Endpoint?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="showDeactivateDialog = false" />
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="text-h6 mb-2">
            {{ endpointToAction.service_name }}.{{ endpointToAction.method_name }}
          </p>
          <p class="text-body-2 text-medium-emphasis">
            This endpoint will stop accepting requests but will not be deleted.
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="warning" variant="flat" @click="deactivateEndpoint(endpointToAction)">Deactivate</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Single Endpoint Delete Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="600">
      <v-card v-if="endpointToAction">
        <v-card-title class="d-flex align-center bg-error pa-4">
          <v-icon start>mdi-delete</v-icon>
          <span>Delete Endpoint?</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="showDeleteDialog = false" />
        </v-card-title>
        <v-card-text class="pa-6">
          <p class="text-h6 mb-2">
            {{ endpointToAction.service_name }}.{{ endpointToAction.method_name }}
          </p>
          <v-alert type="error" variant="tonal" class="mt-4">
            This action cannot be undone. The endpoint configuration and all execution logs will be permanently deleted.
          </v-alert>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn color="error" variant="flat" @click="deleteEndpoint(endpointToAction)">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor">
      {{ snackbarMessage }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useClientsStore } from '@/stores/clients'
import { useEndpointsStore } from '@/stores/endpoints'
import { useClipboard } from '@vueuse/core'
import type { Endpoint } from '@/services/clientApi'
import EndpointBuilder from '@/components/EndpointBuilder.vue'
import TestEndpointDialog from '@/components/TestEndpointDialog.vue'
import SchemaViewer from '@/components/SchemaViewer.vue'
import LogViewer from '@/components/LogViewer.vue'

const clientsStore = useClientsStore()
const endpointsStore = useEndpointsStore()
const { copy } = useClipboard()

// State
const search = ref('')
const statusFilter = ref('all')
const schemaDialog = ref(false)
const selectedEndpoint = ref<Endpoint | null>(null)
const selectedEndpoints = ref<Endpoint[]>([]) // Array of endpoint objects
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Dialog state
const showBulkActivateDialog = ref(false)
const showBulkDeactivateDialog = ref(false)
const showBulkDeleteDialog = ref(false)
const showActivateDialog = ref(false)
const showDeactivateDialog = ref(false)
const showDeleteDialog = ref(false)
const showTestDialog = ref(false)
const showLogsDialog = ref(false)
const endpointToAction = ref<Endpoint | null>(null)
const endpointToTest = ref<Endpoint | null>(null)
const endpointToViewLogs = ref<Endpoint | null>(null)

// Computed
const filteredEndpoints = computed(() => {
  let endpoints = endpointsStore.endpoints

  // Filter by status
  if (statusFilter.value === 'active') {
    endpoints = endpoints.filter(e => e.is_active)
  } else if (statusFilter.value === 'inactive') {
    endpoints = endpoints.filter(e => !e.is_active)
  }

  return endpoints
})

// Computed
const selectedCount = computed(() => selectedEndpoints.value.length)

// Table headers
const headers = [
  { title: 'Status', key: 'is_active', sortable: true },
  { title: 'Service / Method', key: 'method', sortable: false },
  { title: 'Endpoint URL', key: 'url_path', sortable: false },
  { title: 'Stats', key: 'stats', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' as const }
]

// Watch active client
watch(() => clientsStore.activeClient, async (client) => {
  if (client?.id) {
    await endpointsStore.loadEndpoints(client.id)
  } else {
    endpointsStore.endpoints = []
  }
}, { immediate: true })

// Methods
function copyUrl(url: string) {
  const fullUrl = `${window.location.origin}${url}`
  copy(fullUrl)
  showSnackbar('URL copied to clipboard!', 'success')
}

function viewSchema(endpoint: Endpoint) {
  selectedEndpoint.value = endpoint
  schemaDialog.value = true
}

async function testEndpoint(endpoint: Endpoint) {
  endpointToTest.value = endpoint
  showTestDialog.value = true
}

function viewLogs(endpoint: Endpoint) {
  endpointToViewLogs.value = endpoint
  showLogsDialog.value = true
}

function confirmActivateEndpoint(endpoint: Endpoint) {
  endpointToAction.value = endpoint
  showActivateDialog.value = true
}

function confirmDeactivateEndpoint(endpoint: Endpoint) {
  endpointToAction.value = endpoint
  showDeactivateDialog.value = true
}

function confirmDeleteEndpoint(endpoint: Endpoint) {
  endpointToAction.value = endpoint
  showDeleteDialog.value = true
}

async function activateEndpoint(endpoint: Endpoint) {
  showActivateDialog.value = false
  const result = await endpointsStore.activateEndpoint(endpoint.id)
  if (result.success) {
    showSnackbar('Endpoint activated', 'success')
  } else {
    showSnackbar(result.error || 'Failed to activate endpoint', 'error')
  }
  endpointToAction.value = null
}

async function deactivateEndpoint(endpoint: Endpoint) {
  showDeactivateDialog.value = false
  const result = await endpointsStore.deactivateEndpoint(endpoint.id)
  if (result.success) {
    showSnackbar('Endpoint deactivated', 'success')
  } else {
    showSnackbar(result.error || 'Failed to deactivate endpoint', 'error')
  }
  endpointToAction.value = null
}

async function deleteEndpoint(endpoint: Endpoint) {
  showDeleteDialog.value = false
  const result = await endpointsStore.deleteEndpoint(endpoint.id)
  if (result.success) {
    showSnackbar('Endpoint deleted', 'success')
  } else {
    showSnackbar(result.error || 'Failed to delete endpoint', 'error')
  }
  endpointToAction.value = null
}

async function handleDeployed() {
  if (clientsStore.activeClient?.id) {
    await endpointsStore.loadEndpoints(clientsStore.activeClient.id)
  }
  showSnackbar('Endpoints deployed successfully!', 'success')
}

async function bulkActivate() {
  if (selectedEndpoints.value.length === 0) return
  showBulkActivateDialog.value = false

  let successCount = 0
  let errorCount = 0

  for (const endpoint of selectedEndpoints.value) {
    const result = await endpointsStore.activateEndpoint(endpoint.id)
    if (result.success) {
      successCount++
    } else {
      errorCount++
    }
  }

  selectedEndpoints.value = []

  if (errorCount === 0) {
    showSnackbar(`Successfully activated ${successCount} endpoint${successCount === 1 ? '' : 's'}`, 'success')
  } else {
    showSnackbar(`Activated ${successCount}, failed ${errorCount}`, 'warning')
  }
}

async function bulkDeactivate() {
  if (selectedEndpoints.value.length === 0) return
  showBulkDeactivateDialog.value = false

  let successCount = 0
  let errorCount = 0

  for (const endpoint of selectedEndpoints.value) {
    const result = await endpointsStore.deactivateEndpoint(endpoint.id)
    if (result.success) {
      successCount++
    } else {
      errorCount++
    }
  }

  selectedEndpoints.value = []

  if (errorCount === 0) {
    showSnackbar(`Successfully deactivated ${successCount} endpoint${successCount === 1 ? '' : 's'}`, 'success')
  } else {
    showSnackbar(`Deactivated ${successCount}, failed ${errorCount}`, 'warning')
  }
}

async function bulkDelete() {
  if (selectedEndpoints.value.length === 0) return
  showBulkDeleteDialog.value = false

  let successCount = 0
  let errorCount = 0

  for (const endpoint of selectedEndpoints.value) {
    const result = await endpointsStore.deleteEndpoint(endpoint.id)
    if (result.success) {
      successCount++
    } else {
      errorCount++
    }
  }

  selectedEndpoints.value = []

  if (errorCount === 0) {
    showSnackbar(`Successfully deleted ${successCount} endpoint${successCount === 1 ? '' : 's'}`, 'success')
  } else {
    showSnackbar(`Deleted ${successCount}, failed ${errorCount}`, 'warning')
  }
}

function showSnackbar(message: string, color: string) {
  snackbarMessage.value = message
  snackbarColor.value = color
  snackbar.value = true
}
</script>

<style scoped>
.endpoints-page {
  padding: 24px;
}

code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}
</style>
