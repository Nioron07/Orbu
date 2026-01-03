<template>
  <v-container fluid class="pa-6">
    <!-- Page Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h5 font-weight-bold">Service Groups</h1>
        <p class="text-caption text-medium-emphasis mb-0">
          Organize your endpoints into logical groups
        </p>
      </div>
      <v-spacer />
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        @click="showCreateDialog = true"
        :disabled="!clientsStore.activeClient"
      >
        Add Service Group
      </v-btn>
    </div>

    <!-- Not Connected State -->
    <v-card v-if="!clientsStore.activeClient" class="glass-card" elevation="0">
      <v-card-text class="pa-12">
        <div class="text-center">
          <v-icon size="80" color="primary" class="mb-4">mdi-link-off</v-icon>
          <h2 class="text-h5 font-weight-bold mb-3">No Client Connected</h2>
          <p class="text-body-1 text-medium-emphasis mb-6">
            Connect to an Acumatica client to manage service groups.
          </p>
          <v-btn color="primary" size="large" prepend-icon="mdi-domain" to="/clients">
            Go to Clients Page
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- Connected State -->
    <template v-else>
      <!-- Filters Toolbar -->
      <div class="d-flex gap-3 mb-4 align-center">
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          placeholder="Search service groups..."
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
          <v-icon start size="small">mdi-folder-multiple</v-icon>
          {{ filteredServiceGroups.length }} {{ filteredServiceGroups.length === 1 ? 'group' : 'groups' }}
        </v-chip>
      </div>

      <!-- Data Table -->
      <v-card class="glass-card" elevation="0">
        <v-data-table
          :headers="tableHeaders"
          :items="filteredServiceGroups"
          :loading="serviceGroupsStore.isLoading"
          :items-per-page="15"
          density="comfortable"
          hover
        >
          <!-- Status Column -->
          <template v-slot:item.is_active="{ item }">
            <v-chip
              :color="item.is_active ? 'success' : 'grey'"
              size="small"
              variant="flat"
              label
            >
              {{ item.is_active ? 'Active' : 'Inactive' }}
            </v-chip>
          </template>

          <!-- Name Column -->
          <template v-slot:item.name="{ item }">
            <div class="d-flex flex-column">
              <div class="d-flex align-center">
                <v-icon
                  :color="item.is_active ? 'primary' : 'grey'"
                  size="small"
                  class="mr-2"
                >
                  mdi-folder-outline
                </v-icon>
                <span class="font-weight-medium">{{ item.display_name || item.name }}</span>
              </div>
              <span class="text-caption text-medium-emphasis ml-6">{{ item.name }}</span>
            </div>
          </template>

          <!-- Description Column -->
          <template v-slot:item.description="{ item }">
            <span class="text-caption text-medium-emphasis">
              {{ item.description || '—' }}
            </span>
          </template>

          <!-- Endpoint Count Column -->
          <template v-slot:item.endpoint_count="{ item }">
            <v-chip size="small" variant="tonal" color="primary">
              {{ item.endpoint_count || 0 }} endpoint{{ (item.endpoint_count || 0) === 1 ? '' : 's' }}
            </v-chip>
          </template>

          <!-- Actions Column -->
          <template v-slot:item.actions="{ item }">
            <div class="d-flex justify-end">
              <v-tooltip text="View Endpoints" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    icon="mdi-api"
                    size="small"
                    variant="tonal"
                    color="primary"
                    class="mr-2"
                    @click="viewEndpoints(item)"
                  />
                </template>
              </v-tooltip>

              <v-tooltip text="Edit" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    icon="mdi-pencil"
                    size="small"
                    variant="tonal"
                    class="mr-2"
                    @click="editServiceGroup(item)"
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
                  />
                </template>
                <v-list density="compact">
                  <v-list-item v-if="!item.is_active" @click="activateGroup(item)">
                    <template v-slot:prepend>
                      <v-icon size="small" color="success">mdi-check-circle</v-icon>
                    </template>
                    <v-list-item-title>Activate</v-list-item-title>
                  </v-list-item>
                  <v-list-item v-else @click="deactivateGroup(item)">
                    <template v-slot:prepend>
                      <v-icon size="small" color="warning">mdi-pause-circle</v-icon>
                    </template>
                    <v-list-item-title>Deactivate</v-list-item-title>
                  </v-list-item>
                  <v-divider />
                  <v-list-item @click="confirmDelete(item)" class="text-error">
                    <template v-slot:prepend>
                      <v-icon size="small" color="error">mdi-delete</v-icon>
                    </template>
                    <v-list-item-title>Delete</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
          </template>

          <!-- Empty state -->
          <template v-slot:no-data>
            <div class="text-center py-8">
              <v-icon size="48" color="grey">mdi-folder-outline</v-icon>
              <div class="text-body-2 text-medium-emphasis mt-2">
                No service groups found
              </div>
              <v-btn
                color="primary"
                variant="text"
                class="mt-2"
                @click="showCreateDialog = true"
              >
                Create your first service group
              </v-btn>
            </div>
          </template>
        </v-data-table>
      </v-card>
    </template>

    <!-- Create/Edit Dialog -->
    <ServiceGroupDialog
      v-model="showCreateDialog"
      :service-group="editingServiceGroup"
      :client-id="clientsStore.activeClient?.id"
      @saved="handleSaved"
      @close="closeDialog"
    />

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          Delete Service Group
        </v-card-title>
        <v-card-text>
          <p class="mb-2">
            Are you sure you want to delete <strong>{{ deletingServiceGroup?.display_name || deletingServiceGroup?.name }}</strong>?
          </p>
          <v-alert type="warning" variant="tonal" density="compact">
            This will also delete all {{ deletingServiceGroup?.endpoint_count || 0 }} endpoints in this group.
            This action cannot be undone.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            variant="flat"
            @click="deleteGroup"
            :loading="deleting"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useClientsStore } from '@/stores/clients'
import { useServiceGroupsStore } from '@/stores/serviceGroups'
import ServiceGroupDialog from '@/components/ServiceGroupDialog.vue'
import type { ServiceGroup } from '@/services/clientApi'

const router = useRouter()
const clientsStore = useClientsStore()
const serviceGroupsStore = useServiceGroupsStore()

// State
const searchQuery = ref('')
const filterActive = ref<'all' | 'active' | 'inactive'>('all')
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const editingServiceGroup = ref<ServiceGroup | null>(null)
const deletingServiceGroup = ref<ServiceGroup | null>(null)
const deleting = ref(false)

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Table headers
const tableHeaders = [
  { title: 'Status', key: 'is_active', width: '100px' },
  { title: 'Name', key: 'name' },
  { title: 'Description', key: 'description' },
  { title: 'Endpoints', key: 'endpoint_count', width: '120px' },
  { title: 'Actions', key: 'actions', width: '150px', sortable: false }
]

// Computed
const filteredServiceGroups = computed(() => {
  let groups = serviceGroupsStore.serviceGroups

  // Filter by active status
  if (filterActive.value === 'active') {
    groups = groups.filter(g => g.is_active)
  } else if (filterActive.value === 'inactive') {
    groups = groups.filter(g => !g.is_active)
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    groups = groups.filter(g =>
      g.name.toLowerCase().includes(query) ||
      g.display_name?.toLowerCase().includes(query) ||
      g.description?.toLowerCase().includes(query)
    )
  }

  return groups
})

// Watch for active client changes
watch(() => clientsStore.activeClient, async (client) => {
  if (client?.id) {
    await loadServiceGroups()
  } else {
    serviceGroupsStore.$reset()
  }
}, { immediate: true })

// Methods
async function loadServiceGroups() {
  if (!clientsStore.activeClient?.id) return
  await serviceGroupsStore.loadServiceGroups(clientsStore.activeClient.id)
}

function editServiceGroup(group: ServiceGroup) {
  editingServiceGroup.value = { ...group }
  showCreateDialog.value = true
}

function viewEndpoints(group: ServiceGroup) {
  // Navigate to endpoints page with this service group pre-selected
  serviceGroupsStore.setSelectedServiceGroup(group)
  router.push('/endpoints')
}

function confirmDelete(group: ServiceGroup) {
  deletingServiceGroup.value = group
  showDeleteDialog.value = true
}

async function deleteGroup() {
  if (!clientsStore.activeClient?.id || !deletingServiceGroup.value) return

  deleting.value = true
  try {
    const result = await serviceGroupsStore.deleteServiceGroup(
      clientsStore.activeClient.id,
      deletingServiceGroup.value.id
    )

    if (result.success) {
      showSnackbar('Service group deleted successfully', 'success')
    } else {
      showSnackbar(result.error || 'Failed to delete service group', 'error')
    }
  } finally {
    deleting.value = false
    showDeleteDialog.value = false
    deletingServiceGroup.value = null
  }
}

async function activateGroup(group: ServiceGroup) {
  if (!clientsStore.activeClient?.id) return

  const result = await serviceGroupsStore.activateServiceGroup(
    clientsStore.activeClient.id,
    group.id
  )

  if (result.success) {
    showSnackbar('Service group activated', 'success')
  } else {
    showSnackbar(result.error || 'Failed to activate service group', 'error')
  }
}

async function deactivateGroup(group: ServiceGroup) {
  if (!clientsStore.activeClient?.id) return

  const result = await serviceGroupsStore.deactivateServiceGroup(
    clientsStore.activeClient.id,
    group.id
  )

  if (result.success) {
    showSnackbar('Service group deactivated', 'success')
  } else {
    showSnackbar(result.error || 'Failed to deactivate service group', 'error')
  }
}

function handleSaved() {
  showSnackbar(
    editingServiceGroup.value ? 'Service group updated' : 'Service group created',
    'success'
  )
  closeDialog()
  loadServiceGroups()
}

function closeDialog() {
  showCreateDialog.value = false
  editingServiceGroup.value = null
}

function showSnackbar(text: string, color: string) {
  snackbar.value = { show: true, text, color }
}

onMounted(async () => {
  if (clientsStore.activeClient?.id) {
    await loadServiceGroups()
  }
})
</script>

<style scoped lang="scss">
.glass-card {
  background: rgba(var(--v-theme-surface), 0.8);
  backdrop-filter: blur(10px);
}
</style>
