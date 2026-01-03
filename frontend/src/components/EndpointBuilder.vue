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
        <v-row no-gutters class="dialog-content">
          <!-- Left side: Services table -->
          <v-col cols="8" class="border-e d-flex flex-column">
            <div class="pa-6 pb-0">
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
            </div>

            <div class="services-table-container">
              <v-data-table
                :headers="headers"
                :items="filteredServices"
                :loading="loadingServices"
                loading-text="Loading services and method details..."
                :items-per-page="-1"
                density="compact"
                item-value="name"
                :expanded="expanded"
                show-expand
                class="services-table"
                fixed-header
                hide-default-footer
              >
                <!-- Service checkbox column -->
                <template #item.select="{ item }">
                  <v-checkbox-btn
                    :model-value="isServiceSelected(item.name)"
                    :indeterminate="isServiceIndeterminate(item.name)"
                    :disabled="isServiceFullyDeployed(item.name)"
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
                  <div class="d-flex align-center gap-1">
                    <v-chip size="small" variant="tonal">
                      {{ item.method_count }} method{{ item.method_count === 1 ? '' : 's' }}
                    </v-chip>
                    <v-chip
                      v-if="getAvailableMethodsCount(item.name) < item.method_count"
                      size="small"
                      color="success"
                      variant="tonal"
                    >
                      {{ item.method_count - getAvailableMethodsCount(item.name) }} deployed
                    </v-chip>
                  </div>
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
                          :class="{ 'method-deployed': isMethodDeployed(item.name, method.name) }"
                        >
                          <template #prepend>
                            <v-checkbox-btn
                              :model-value="isMethodSelected(item.name, method.name)"
                              :disabled="isMethodDeployed(item.name, method.name)"
                              @click.stop="toggleMethod(item.name, method.name)"
                            />
                          </template>

                          <v-list-item-title class="text-body-2">
                            <v-icon size="small" class="mr-1">mdi-function</v-icon>
                            {{ method.name }}
                          </v-list-item-title>

                          <template #append>
                            <v-chip
                              v-if="isMethodDeployed(item.name, method.name)"
                              size="x-small"
                              color="success"
                              variant="tonal"
                              class="mr-2"
                            >
                              Deployed
                            </v-chip>
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
          <v-col cols="4" class="d-flex flex-column cart-column">
            <div class="pa-6">
              <div class="text-h6 mb-4">
                <v-icon start>mdi-cart</v-icon>
                Selected Endpoints
              </div>

              <v-divider class="mb-4" />
            </div>

            <!-- Selected methods list with scrollable area -->
            <div class="cart-list-container flex-grow-1">
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

            <!-- Bottom sticky section -->
            <div class="cart-footer">
              <!-- Deployment Settings -->
              <div v-if="selectedCount > 0 && !deploymentResult" class="pa-6 pt-4 border-t">
                <div class="text-subtitle-2 mb-3">Deployment Settings</div>
                <v-text-field
                  v-model.number="logRetentionHours"
                  type="number"
                  label="Log Retention (hours)"
                  hint="How long to keep execution logs"
                  persistent-hint
                  variant="outlined"
                  density="compact"
                  :min="1"
                  :max="8760"
                />
              </div>

              <!-- Deployment result -->
              <div v-if="deploymentResult" class="pa-6 pt-4 border-t">
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
              <div class="pa-6 pt-4 border-t">
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
  serviceGroupId: string
  clientConnected?: boolean
  deployedMethods?: Record<string, string[]>
}

const props = withDefaults(defineProps<Props>(), {
  clientConnected: false,
  deployedMethods: () => ({})
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
const deploying = ref(false)
const deploymentResult = ref<any>(null)
const logRetentionHours = ref(24) // Default 24 hours

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

  const deployedForService = props.deployedMethods[serviceName] || []
  const availableMethods = service.methods.filter((m: any) => !deployedForService.includes(m.name))
  if (availableMethods.length === 0) return false

  const selectedForService = selectedMethods.value[serviceName] || []
  return availableMethods.every((m: any) => selectedForService.includes(m.name))
}

function isServiceIndeterminate(serviceName: string): boolean {
  const service = services.value.find(s => s.name === serviceName)
  if (!service) return false

  const deployedForService = props.deployedMethods[serviceName] || []
  const availableMethods = service.methods.filter((m: any) => !deployedForService.includes(m.name))
  const selectedForService = selectedMethods.value[serviceName] || []

  return selectedForService.length > 0 && selectedForService.length < availableMethods.length
}

function isServiceFullyDeployed(serviceName: string): boolean {
  const service = services.value.find(s => s.name === serviceName)
  if (!service) return false

  const deployedForService = props.deployedMethods[serviceName] || []
  return service.methods.every((m: any) => deployedForService.includes(m.name))
}

function isMethodSelected(serviceName: string, methodName: string): boolean {
  const selectedForService = selectedMethods.value[serviceName] || []
  return selectedForService.includes(methodName)
}

function isMethodDeployed(serviceName: string, methodName: string): boolean {
  const deployedForService = props.deployedMethods[serviceName] || []
  return deployedForService.includes(methodName)
}

function getAvailableMethodsCount(serviceName: string): number {
  const service = services.value.find(s => s.name === serviceName)
  if (!service) return 0
  const deployedForService = props.deployedMethods[serviceName] || []
  return service.methods.filter((m: any) => !deployedForService.includes(m.name)).length
}

function toggleService(serviceName: string) {
  const service = services.value.find(s => s.name === serviceName)
  if (!service) return

  const deployedForService = props.deployedMethods[serviceName] || []
  const availableMethods = service.methods.filter((m: any) => !deployedForService.includes(m.name))
  const selectedForService = selectedMethods.value[serviceName] || []
  const allAvailableSelected = availableMethods.every((m: any) => selectedForService.includes(m.name))

  if (allAvailableSelected) {
    // Deselect all methods
    selectedMethods.value[serviceName] = []
  } else {
    // Select all available (non-deployed) methods
    selectedMethods.value[serviceName] = availableMethods.map((m: any) => m.name)
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
        return endpointsStore.deployService(props.clientId, props.serviceGroupId, {
          service_name: serviceName,
          methods: methods,
          auto_generate_schema: true,
          log_retention_hours: logRetentionHours.value
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
  deploymentResult.value = null
  expanded.value = []
  logRetentionHours.value = 24
}

function close() {
  dialog.value = false
}
</script>

<style scoped lang="scss">
// Main dialog content with fixed height
.dialog-content {
  height: 900px;
  max-height: 90vh;
  overflow: hidden;
}

// Left column - services table
.services-table-container {
  flex: 1;
  overflow: hidden;
  padding: 0 24px 24px 24px;
  min-height: 0;
}

.services-table {
  height: 100%;

  :deep(.v-data-table__tr) {
    cursor: pointer;
  }

  :deep(.v-table__wrapper) {
    max-height: 750px;
    overflow-y: auto !important;
    overflow-x: hidden;
  }

  :deep(.v-data-table-footer) {
    display: none;
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

  &.method-deployed {
    opacity: 0.6;
    border-left-color: rgb(var(--v-theme-success));
  }
}

// Right column - cart
.cart-column {
  max-height: 100%;
  overflow: hidden;
}

.cart-list-container {
  overflow-y: auto;
  padding: 0 24px;
  min-height: 0; // Important for flex scrolling
}

.cart-footer {
  flex-shrink: 0;
  background-color: rgb(var(--v-theme-surface));
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
