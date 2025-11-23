<template>
  <v-card
    class="log-entry mb-2"
    :class="statusClass"
    variant="tonal"
    @click="expanded = !expanded"
    style="cursor: pointer;"
  >
    <!-- Collapsed view -->
    <v-card-text class="py-2">
      <div class="d-flex align-center">
        <!-- Status indicator -->
        <v-chip
          :color="statusColor"
          size="x-small"
          class="mr-2"
          label
        >
          {{ log.status_code }}
        </v-chip>

        <!-- Timestamp -->
        <span class="text-caption text-medium-emphasis mr-3" style="font-family: monospace;">
          {{ formattedTime }}
        </span>

        <!-- Method and Path -->
        <v-chip
          v-if="log.request_method"
          size="x-small"
          variant="outlined"
          class="mr-2"
        >
          {{ log.request_method }}
        </v-chip>

        <span class="text-caption mr-3" style="font-family: monospace;">
          {{ log.request_path || 'N/A' }}
        </span>

        <!-- Duration -->
        <v-chip
          size="x-small"
          variant="text"
          class="mr-2"
        >
          {{ log.duration_ms }}ms
        </v-chip>

        <!-- Error preview or IP -->
        <span class="text-caption text-medium-emphasis text-truncate flex-grow-1">
          {{ log.error_message || log.ip_address || '' }}
        </span>

        <!-- Expand icon -->
        <v-icon size="small" :class="{ 'rotate-180': expanded }">
          mdi-chevron-down
        </v-icon>
      </div>
    </v-card-text>

    <!-- Expanded view -->
    <v-expand-transition>
      <div v-show="expanded">
        <v-divider />
        <v-card-text class="pt-3">
          <v-row dense>
            <!-- Left column: Request info -->
            <v-col cols="12" md="6">
              <div class="mb-3">
                <div class="text-caption text-medium-emphasis mb-1">Request Details</div>
                <div class="text-body-2 mb-1" style="font-family: monospace;">
                  <strong>Method:</strong> {{ log.request_method || 'N/A' }}
                </div>
                <div class="text-body-2 mb-1" style="font-family: monospace;">
                  <strong>Path:</strong> {{ log.request_path || 'N/A' }}
                </div>
                <div class="text-body-2 mb-1" style="font-family: monospace;">
                  <strong>IP:</strong> {{ log.ip_address || 'N/A' }}
                </div>
                <div class="text-body-2 mb-1" style="font-family: monospace;">
                  <strong>Duration:</strong> {{ log.duration_ms }}ms
                </div>
              </div>

              <!-- Request Data -->
              <div v-if="log.request_data" class="mb-3">
                <div class="d-flex align-center mb-1">
                  <span class="text-caption text-medium-emphasis">Request Data</span>
                  <v-spacer />
                  <v-btn
                    size="x-small"
                    variant="text"
                    icon="mdi-content-copy"
                    @click.stop="copyToClipboard(log.request_data)"
                  />
                </div>
                <pre class="log-code">{{ JSON.stringify(log.request_data, null, 2) }}</pre>
              </div>
            </v-col>

            <!-- Right column: Response/Error info -->
            <v-col cols="12" md="6">
              <!-- Error Message -->
              <div v-if="log.error_message" class="mb-3">
                <div class="d-flex align-center mb-1">
                  <span class="text-caption text-medium-emphasis text-error">Error Message</span>
                  <v-spacer />
                  <v-btn
                    size="x-small"
                    variant="text"
                    icon="mdi-content-copy"
                    @click.stop="copyToClipboard(log.error_message)"
                  />
                </div>
                <pre class="log-code error-code">{{ log.error_message }}</pre>
              </div>

              <!-- Response Data -->
              <div v-if="log.response_data" class="mb-3">
                <div class="d-flex align-center mb-1">
                  <span class="text-caption text-medium-emphasis">Response Data</span>
                  <v-spacer />
                  <v-btn
                    size="x-small"
                    variant="text"
                    icon="mdi-content-copy"
                    @click.stop="copyToClipboard(log.response_data)"
                  />
                </div>
                <pre class="log-code">{{ JSON.stringify(log.response_data, null, 2) }}</pre>
              </div>

              <!-- User Agent -->
              <div v-if="log.user_agent" class="mb-3">
                <div class="text-caption text-medium-emphasis mb-1">User Agent</div>
                <div class="text-caption" style="font-family: monospace; word-break: break-all;">
                  {{ log.user_agent }}
                </div>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </div>
    </v-expand-transition>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { EndpointExecution } from '@/services/clientApi'

const props = defineProps<{
  log: EndpointExecution
}>()

const expanded = ref(false)

const formattedTime = computed(() => {
  return new Date(props.log.executed_at).toLocaleString('en-US', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
})

const statusColor = computed(() => {
  const code = props.log.status_code
  if (code >= 200 && code < 300) return 'success'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'error'
  return 'grey'
})

const statusClass = computed(() => {
  const code = props.log.status_code
  if (code >= 500) return 'log-error'
  if (code >= 400) return 'log-warning'
  return 'log-success'
})

async function copyToClipboard(data: any) {
  try {
    const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
    await navigator.clipboard.writeText(text)
    // Successfully copied - could add a toast notification here if needed
  } catch (err) {
    console.error('Failed to copy to clipboard:', err)
  }
}
</script>

<style scoped>
.log-entry {
  transition: all 0.2s;
}

.log-entry:hover {
  transform: translateX(4px);
}

.log-success {
  border-left: 3px solid rgb(var(--v-theme-success));
}

.log-warning {
  border-left: 3px solid rgb(var(--v-theme-warning));
}

.log-error {
  border-left: 3px solid rgb(var(--v-theme-error));
}

.log-code {
  background: rgba(var(--v-theme-on-surface), 0.05);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
  padding: 8px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.error-code {
  background: rgba(var(--v-theme-error), 0.1);
  border-color: rgba(var(--v-theme-error), 0.3);
  color: rgb(var(--v-theme-error));
}

.rotate-180 {
  transform: rotate(180deg);
  transition: transform 0.2s;
}
</style>
