<template>
  <v-dialog v-model="dialog" max-width="1600" persistent scrollable>
    <template #activator="{ props: activatorProps }">
      <v-btn
        v-bind="activatorProps"
        color="primary"
        prepend-icon="mdi-cart-plus"
      >
        Deploy Endpoints
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="d-flex align-center bg-primary pa-4">
        <v-icon start color="white">mdi-rocket-launch</v-icon>
        <span class="text-white">Deploy Endpoints</span>
        <v-spacer />
        <v-chip v-if="selectedCount > 0" color="white" variant="elevated" class="mr-3">
          {{ selectedCount }} method{{ selectedCount === 1 ? '' : 's' }} selected
        </v-chip>
        <v-btn icon="mdi-close" variant="text" color="white" @click="close" />
      </v-card-title>

      <v-card-text class="pa-0">
        <v-row no-gutters style="height: 700px;">
          <!-- Left side: Services table -->
          <v-col cols="8" class="border-e">
            <div class="pa-6">
              <v-text-field
                v-model="searchQuery"
                prepend-inner-icon="mdi-magnify"
                placeholder="Search services..."
                variant="outlined"
                density="compact"
                clearable
                hide-details
                class="mb-4"
              />

              <v-alert v-if="!clientConnected" type="warning" variant="tonal" class="mb-4">
                <div class="text-subtitle-2">Client Not Connected</div>
                <div class="text-body-2">
                  Please connect to the client first to browse available services.
                </div>
              </v-alert>

              <v-data-table
                :headers="headers"
                :items="filteredServices"
                :loading="loadingServices"
                :items-per-page="-1"
                density="compact"
                item-value="name"
                :expanded="expanded"
                show-expand
                class="services-table"
              >
                <!-- Service checkbox column -->
                <template #item.select="{ item }">
                  <v-checkbox-btn
                    :model-value="isServiceSelected(item.name)"
                    :indeterminate="isServiceIndeterminate(item.name)"
                    @click.stop="toggleService(item.name)"
                  />
                </template>

                <!-- Service name -->
                <template #item.name="{ item }">
                  <div class="d-flex align-center">
                    <v-icon size="small" class="mr-2" color="primary">mdi-cube</v-icon>
                    <span class="font-weight-medium">{{ item.name }}</span>
                  </div>
                </template>

                <!-- Method count -->
                <template #item.method_count="{ item }">
                  <v-chip size="small" variant="tonal">
                    {{ item.method_count }} method{{ item.method_count === 1 ? '' : 's' }}
                  </v-chip>
                </template>

                <!-- Expanded row content (methods) -->
                <template #expanded-row="{ item }">
                  <tr>
                    <td :colspan="headers.length" class="pa-0">
                      <v-list density="compact" class="methods-list">
                        <v-list-item
                          v-for="method in item.methods"
                          :key="method.name"
                          class="method-item"
                        >
                          <template #prepend>
                            <v-checkbox-btn
                              :model-value="isMethodSelected(item.name, method.name)"
                              @click.stop="toggleMethod(item.name, method.name)"
                            />
                          </template>

                          <v-list-item-title class="text-body-2">
                            <v-icon size="small" class="mr-1">mdi-function</v-icon>
                            {{ method.name }}
                          </v-list-item-title>

                          <template #append>
                            <v-chip
                              v-if="method.parameter_count > 0"
                              size="x-small"
                              variant="text"
                              class="text-caption"
                            >
                              {{ method.parameter_count }} param{{ method.parameter_count === 1 ? '' : 's' }}
                            </v-chip>
                          </template>
                        </v-list-item>
                      </v-list>
                    </td>
                  </tr>
                </template>

                <!-- Loading state -->
                <template #loading>
                  <v-skeleton-loader type="table-row@5" />
                </template>

                <!-- Empty state -->
                <template #no-data>
                  <div class="text-center py-8">
                    <v-icon size="48" color="grey">mdi-inbox</v-icon>
                    <div class="text-body-2 text-medium-emphasis mt-2">
                      No services available
                    </div>
                  </div>
                </template>
              </v-data-table>
            </div>
          </v-col>

          <!-- Right side: Shopping cart -->
          <v-col cols="4" class="d-flex flex-column">
            <div class="pa-6">
              <div class="text-h6 mb-4">
                <v-icon start>mdi-cart</v-icon>
                Selected Endpoints
              </div>

              <v-switch
                v-model="autoGenerateSchema"
                label="Auto-generate schemas"
                color="primary"
                density="compact"
                hide-details
                class="mb-4"
              />

              <v-divider class="mb-4" />
            </div>

            <!-- Selected methods list with fixed height -->
            <div class="cart-list-container">
              <!-- Empty state -->
              <div v-if="selectedCount === 0" class="text-center py-8">
                <v-icon size="48" color="grey-lighten-1">mdi-cart-outline</v-icon>
                <div class="text-body-2 text-medium-emphasis mt-2">
                  No methods selected
                </div>
                <div class="text-caption text-medium-emphasis">
                  Select services or methods to deploy
                </div>
              </div>

              <!-- Selected items -->
              <v-list v-else density="compact" class="selected-list">
                <template v-for="(methods, serviceName) in selectedMethods" :key="serviceName">
                  <v-list-subheader v-if="methods.length > 0" class="text-uppercase">
                    {{ serviceName }}
                  </v-list-subheader>
                  <v-list-item
                    v-for="method in methods"
                    :key="`${serviceName}.${method}`"
                    class="selected-method-item"
                  >
                    <template #prepend>
                      <v-icon size="small">mdi-function</v-icon>
                    </template>

                    <v-list-item-title class="text-body-2">
                      {{ method }}
                    </v-list-item-title>

                    <template #append>
                      <v-btn
                        icon="mdi-close"
                        size="x-small"
                        variant="text"
                        @click="toggleMethod(serviceName, method)"
                      />
                    </template>
                  </v-list-item>
                </template>
              </v-list>
            </div>

            <!-- Deployment result -->
            <div v-if="deploymentResult" class="pa-6 border-t">
              <v-alert
                :type="deploymentResult.success ? 'success' : 'error'"
                variant="tonal"
                density="comfortable"
              >
                <div class="text-subtitle-2 mb-2">{{ deploymentResult.message }}</div>
                <div v-if="deploymentResult.summary" class="text-caption">
                  <div class="mb-1">Created: {{ deploymentResult.summary.created_count }}</div>
                  <div class="mb-1">Skipped: {{ deploymentResult.summary.skipped_count }}</div>
                  <div v-if="deploymentResult.summary.error_count > 0">
                    Errors: {{ deploymentResult.summary.error_count }}
                  </div>
                </div>
              </v-alert>
            </div>

            <!-- Actions -->
            <div class="pa-6 border-t">
              <v-btn
                v-if="!deploymentResult"
                color="primary"
                block
                size="large"
                :disabled="selectedCount === 0"
                :loading="deploying"
                @click="deployEndpoints"
              >
                <v-icon start>mdi-rocket-launch</v-icon>
                Deploy {{ selectedCount }} Endpoint{{ selectedCount === 1 ? '' : 's' }}
              </v-btn>
              <v-btn
                v-else
                color="primary"
                block
                size="large"
                @click="close"
              >
                Done
              </v-btn>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEndpointsStore } from '@/stores/endpoints'
import { clientApi } from '@/services/clientApi'

interface Props {
  clientId: string
  clientConnected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  clientConnected: false
})

const emit = defineEmits<{
  deployed: []
}>()

const endpointsStore = useEndpointsStore()

// Dialog state
const dialog = ref(false)
const searchQuery = ref('')
const expanded = ref<string[]>([])

// Services data
const services = ref<any[]>([])
const loadingServices = ref(false)

// Selection state - using a Map: service name -> array of selected method names
const selectedMethods = ref<Record<string, string[]>>({})

// Deployment
const autoGenerateSchema = ref(true)
const deploying = ref(false)
const deploymentResult = ref<any>(null)

// Table headers
const headers = [
  { title: '', key: 'select', sortable: false, width: '50px' },
  { title: 'Service', key: 'name', sortable: true },
  { title: 'Methods', key: 'method_count', sortable: true, width: '120px' },
  { title: '', key: 'data-table-expand', sortable: false, width: '50px' }
]

// Computed
const filteredServices = computed(() => {
  if (!searchQuery.value) return services.value

  const query = searchQuery.value.toLowerCase()
  return services.value.filter(s =>
    s.name.toLowerCase().includes(query) ||
    s.description?.toLowerCase().includes(query)
  )
})

const selectedCount = computed(() => {
  return Object.values(selectedMethods.value).reduce((sum, methods) => sum + methods.length, 0)
})

// Watch dialog open
watch(dialog, async (isOpen) => {
  if (isOpen) {
    resetForm()
    if (props.clientConnected) {
      await loadServices()
    }
  }
})

// Methods
async function loadServices() {
  loadingServices.value = true
  try {
    const response = await clientApi.listServices(props.clientId)
    if (response.success && Array.isArray(response.services)) {
      // Load details for each service
      const serviceDetails = await Promise.all(
        response.services.map(async (service: any) => {
          try {
            const detailResponse = await clientApi.getServiceDetails(props.clientId, service.name)
            if (detailResponse.success) {
              return {
                name: service.name,
                description: detailResponse.service.description,
                method_count: detailResponse.service.methods.length,
                methods: detailResponse.service.methods
              }
            }
          } catch (error) {
            console.error(`Failed to load details for ${service.name}:`, error)
          }
          return null
        })
      )

      services.value = serviceDetails.filter(s => s !== null)
    }
  } catch (error: any) {
    console.error('Failed to load services:', error)
  } finally {
    loadingServices.value = false
  }
}

function isServiceSelected(serviceName: string): boolean {
  const service = services.value.find(s => s.name === serviceName)
  if (!service) return false

  const selectedForService = selectedMethods.value[serviceName] || []
  return selectedForService.length === service.methods.length && service.methods.length > 0
}

function isServiceIndeterminate(serviceName: string): boolean {
  const selectedForService = selectedMethods.value[serviceName] || []
  const service = services.value.find(s => s.name === serviceName)
  if (!service) return false

  return selectedForService.length > 0 && selectedForService.length < service.methods.length
}

function isMethodSelected(serviceName: string, methodName: string): boolean {
  const selectedForService = selectedMethods.value[serviceName] || []
  return selectedForService.includes(methodName)
}

function toggleService(serviceName: string) {
  const service = services.value.find(s => s.name === serviceName)
  if (!service) return

  const isCurrentlySelected = isServiceSelected(serviceName)

  if (isCurrentlySelected) {
    // Deselect all methods
    selectedMethods.value[serviceName] = []
  } else {
    // Select all methods
    selectedMethods.value[serviceName] = service.methods.map((m: any) => m.name)
  }
}

function toggleMethod(serviceName: string, methodName: string) {
  if (!selectedMethods.value[serviceName]) {
    selectedMethods.value[serviceName] = []
  }

  const index = selectedMethods.value[serviceName].indexOf(methodName)
  if (index > -1) {
    selectedMethods.value[serviceName].splice(index, 1)
  } else {
    selectedMethods.value[serviceName].push(methodName)
  }
}

async function deployEndpoints() {
  deploying.value = true
  deploymentResult.value = null

  try {
    // Deploy each service's selected methods
    const deploymentPromises = Object.entries(selectedMethods.value)
      .filter(([_, methods]) => methods.length > 0)
      .map(([serviceName, methods]) => {
        return endpointsStore.deployService(props.clientId, {
          service_name: serviceName,
          methods: methods,
          auto_generate_schema: autoGenerateSchema.value
        })
      })

    const results = await Promise.all(deploymentPromises)

    // Aggregate results
    const allSuccess = results.every(r => r.success)
    const totalCreated = results.reduce((sum, r) => sum + (r.summary?.created_count || 0), 0)
    const totalSkipped = results.reduce((sum, r) => sum + (r.summary?.skipped_count || 0), 0)
    const totalErrors = results.reduce((sum, r) => sum + (r.summary?.error_count || 0), 0)

    deploymentResult.value = {
      success: allSuccess,
      message: allSuccess ? 'Deployment successful!' : 'Some deployments failed',
      summary: {
        created_count: totalCreated,
        skipped_count: totalSkipped,
        error_count: totalErrors
      }
    }

    if (allSuccess) {
      emit('deployed')
    }
  } catch (error: any) {
    deploymentResult.value = {
      success: false,
      message: error.message || 'Deployment failed'
    }
  } finally {
    deploying.value = false
  }
}

function resetForm() {
  searchQuery.value = ''
  selectedMethods.value = {}
  autoGenerateSchema.value = true
  deploymentResult.value = null
  expanded.value = []
}

function close() {
  dialog.value = false
}
</script>

<style scoped lang="scss">
.services-table {
  :deep(.v-data-table__tr) {
    cursor: pointer;
  }
}

.methods-list {
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
}

.method-item {
  border-left: 3px solid rgb(var(--v-theme-primary));

  &:hover {
    background-color: rgba(var(--v-theme-primary), 0.08);
  }
}

.cart-list-container {
  flex: 1;
  max-height: 400px;
  overflow-y: auto;
  padding: 0 24px;
}

.selected-method-item {
  border-left: 2px solid rgb(var(--v-theme-primary));

  &:hover {
    background-color: rgba(var(--v-theme-primary), 0.04);
  }
}

.selected-list {
  :deep(.v-list-subheader) {
    font-size: 0.75rem;
    font-weight: 600;
    color: rgb(var(--v-theme-primary));
  }
}
</style>
