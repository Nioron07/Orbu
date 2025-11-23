<template>
  <v-dialog
    v-model="dialog"
    fullscreen
    transition="dialog-bottom-transition"
  >
    <v-card>
      <!-- Header -->
      <v-toolbar color="primary" dark>
        <v-btn icon @click="close">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>
          <v-icon class="mr-2">mdi-text-box-outline</v-icon>
          Endpoint Logs - {{ endpoint?.display_name || endpoint?.service_name + '.' + endpoint?.method_name }}
        </v-toolbar-title>
        <v-spacer />
        <v-chip
          v-if="autoRefresh"
          color="success"
          size="small"
          class="mr-2"
        >
          <v-icon start size="small">mdi-sync</v-icon>
          Auto-refresh
        </v-chip>
        <v-btn icon @click="refreshLogs" :loading="loading">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </v-toolbar>

      <!-- Filters Toolbar -->
      <v-toolbar color="surface" flat>
        <v-text-field
          v-model="filters.search"
          prepend-inner-icon="mdi-magnify"
          label="Search logs"
          density="compact"
          variant="outlined"
          hide-details
          clearable
          class="mr-2"
          style="max-width: 300px;"
          @update:model-value="debouncedSearch"
        />

        <v-select
          v-model="filters.status"
          :items="statusOptions"
          label="Status"
          density="compact"
          variant="outlined"
          hide-details
          clearable
          class="mr-2"
          style="max-width: 150px;"
          @update:model-value="applyFilters"
        />

        <v-select
          v-model="filters.timeRange"
          :items="timeRangeOptions"
          label="Time Range"
          density="compact"
          variant="outlined"
          hide-details
          class="mr-2"
          style="max-width: 150px;"
          @update:model-value="applyFilters"
        />

        <v-spacer />

        <v-chip class="mr-2">
          {{ totalLogs }} total logs
        </v-chip>

        <v-btn
          variant="text"
          @click="clearFilters"
        >
          Clear Filters
        </v-btn>
      </v-toolbar>

      <!-- Stats Bar -->
      <v-container fluid class="py-2 px-4 bg-surface-variant">
        <v-row dense>
          <v-col cols="auto">
            <v-chip size="small" color="success" variant="tonal">
              <v-icon start size="small">mdi-check-circle</v-icon>
              {{ successCount }} successful
            </v-chip>
          </v-col>
          <v-col cols="auto">
            <v-chip size="small" color="error" variant="tonal">
              <v-icon start size="small">mdi-alert-circle</v-icon>
              {{ errorCount }} errors
            </v-chip>
          </v-col>
          <v-col cols="auto">
            <v-chip size="small" variant="tonal">
              <v-icon start size="small">mdi-clock-outline</v-icon>
              Avg: {{ avgDuration }}ms
            </v-chip>
          </v-col>
        </v-row>
      </v-container>

      <!-- Log List with Infinite Scroll -->
      <v-card-text class="pa-4" style="height: calc(100vh - 240px); overflow-y: auto;" ref="scrollContainer">
        <div v-if="loading && logs.length === 0" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
          <p class="mt-4">Loading logs...</p>
        </div>

        <div v-else-if="logs.length === 0" class="text-center py-8">
          <v-icon size="64" color="grey">mdi-text-box-off-outline</v-icon>
          <p class="text-h6 mt-4">No logs found</p>
          <p class="text-caption">Try adjusting your filters</p>
        </div>

        <div v-else>
          <LogEntry
            v-for="log in logs"
            :key="log.id"
            :log="log"
          />

          <!-- Load more indicator -->
          <div v-if="hasMore" class="text-center py-4">
            <v-btn
              v-if="!loadingMore"
              @click="loadMore"
              variant="outlined"
              color="primary"
            >
              Load More
            </v-btn>
            <v-progress-circular v-else indeterminate color="primary" />
          </div>

          <div v-else-if="logs.length > 0" class="text-center py-4 text-caption text-medium-emphasis">
            End of logs
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import type { Endpoint, EndpointExecution } from '@/services/clientApi'
import { useEndpointsStore } from '@/stores/endpoints'
import LogEntry from './LogEntry.vue'

const props = defineProps<{
  modelValue: boolean
  endpoint: Endpoint | null
}>()

const emit = defineEmits(['update:modelValue'])

const endpointsStore = useEndpointsStore()

const dialog = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const logs = ref<EndpointExecution[]>([])
const totalLogs = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const autoRefresh = ref(true)
const scrollContainer = ref<HTMLElement | null>(null)

const filters = ref({
  search: '',
  status: null as number | null,
  timeRange: '24h',
  offset: 0,
  limit: 50
})

const statusOptions = [
  { title: 'All', value: null },
  { title: '2xx Success', value: 200 },
  { title: '4xx Client Error', value: 400 },
  { title: '5xx Server Error', value: 500 }
]

const timeRangeOptions = [
  { title: 'Last hour', value: '1h' },
  { title: 'Last 6 hours', value: '6h' },
  { title: 'Last 24 hours', value: '24h' },
  { title: 'Last 7 days', value: '7d' },
  { title: 'All time', value: 'all' }
]

let refreshInterval: number | null = null
let searchTimeout: number | null = null

const hasMore = computed(() => {
  return logs.value.length < totalLogs.value
})

const successCount = computed(() => {
  return logs.value.filter(log => log.status_code >= 200 && log.status_code < 300).length
})

const errorCount = computed(() => {
  return logs.value.filter(log => log.status_code >= 500).length
})

const avgDuration = computed(() => {
  if (logs.value.length === 0) return 0
  const total = logs.value.reduce((sum, log) => sum + (log.duration_ms || 0), 0)
  return Math.round(total / logs.value.length)
})

function getTimeRangeFilter() {
  const now = new Date()
  switch (filters.value.timeRange) {
    case '1h':
      return new Date(now.getTime() - 60 * 60 * 1000).toISOString()
    case '6h':
      return new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString()
    case '24h':
      return new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
    case '7d':
      return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
    default:
      return undefined
  }
}

async function loadLogs(append = false) {
  if (!props.endpoint) return

  if (append) {
    loadingMore.value = true
  } else {
    loading.value = true
    filters.value.offset = 0
  }

  try {
    const result = await endpointsStore.loadEndpointLogs(props.endpoint.id, {
      limit: filters.value.limit,
      offset: filters.value.offset,
      status: filters.value.status || undefined,
      search: filters.value.search || undefined,
      since: getTimeRangeFilter()
    })

    if (result.success) {
      if (append) {
        logs.value.push(...(result.logs || []))
      } else {
        logs.value = result.logs || []
      }
      totalLogs.value = result.total || 0
    } else {
      console.error('Failed to load logs:', result.error)
    }
  } catch (err: any) {
    console.error('Error loading logs:', err)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function loadMore() {
  filters.value.offset += filters.value.limit
  await loadLogs(true)
}

async function refreshLogs() {
  // Only refresh if at the top (offset = 0)
  if (filters.value.offset === 0) {
    await loadLogs(false)
  }
}

function applyFilters() {
  filters.value.offset = 0
  loadLogs(false)
}

function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = window.setTimeout(() => {
    applyFilters()
  }, 500)
}

function clearFilters() {
  filters.value.search = ''
  filters.value.status = null
  filters.value.timeRange = '24h'
  applyFilters()
}

function close() {
  dialog.value = false
}

// Auto-refresh setup
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    loadLogs(false)
    // Start auto-refresh every 5 seconds
    if (autoRefresh.value) {
      refreshInterval = window.setInterval(refreshLogs, 5000)
    }
  } else {
    // Stop auto-refresh when dialog closes
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (searchTimeout) clearTimeout(searchTimeout)
})
</script>

<style scoped>
/* Custom scrollbar for terminal feel */
:deep(.v-card-text::-webkit-scrollbar) {
  width: 8px;
}

:deep(.v-card-text::-webkit-scrollbar-track) {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

:deep(.v-card-text::-webkit-scrollbar-thumb) {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 4px;
}

:deep(.v-card-text::-webkit-scrollbar-thumb:hover) {
  background: rgba(var(--v-theme-on-surface), 0.3);
}
</style>
