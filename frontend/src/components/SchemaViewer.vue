<template>
  <div>
    <!-- Endpoint URL -->
    <div v-if="showUrl && urlPath" class="mb-6">
      <div class="d-flex align-center mb-2">
        <div class="text-subtitle-1 font-weight-medium">Endpoint URL</div>
        <v-spacer />
        <v-btn
          icon="mdi-content-copy"
          variant="text"
          size="small"
          @click="copyUrl"
        />
      </div>
      <v-sheet class="pa-4 bg-surface-variant rounded">
        <code class="text-body-2">{{ fullUrl }}</code>
      </v-sheet>
    </div>

    <!-- Request Parameters Table (if exists) -->
    <div v-if="requestParams.length > 0" class="mb-6">
      <div class="text-subtitle-1 font-weight-medium mb-3">Request Parameters</div>
      <v-table density="compact">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Type</th>
            <th>Required</th>
            <th>Default</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="param in requestParams" :key="param.name">
            <td><code>{{ param.name }}</code></td>
            <td><v-chip size="x-small" variant="tonal">{{ param.type }}</v-chip></td>
            <td>
              <v-chip
                :color="param.required ? 'error' : 'success'"
                size="x-small"
                variant="flat"
              >
                {{ param.required ? 'Yes' : 'No' }}
              </v-chip>
            </td>
            <td>{{ param.default || '-' }}</td>
          </tr>
        </tbody>
      </v-table>
    </div>

    <!-- Horizontal Layout: Schemas and Examples Side by Side -->
    <v-row>
      <!-- Left Column: Request -->
      <v-col cols="6">
        <!-- Request Schema -->
        <div v-if="requestSchema" class="mb-4">
          <div class="d-flex align-center mb-2">
            <div class="text-subtitle-1 font-weight-medium">Request Schema</div>
            <v-spacer />
            <v-chip size="x-small" variant="tonal" class="mr-2">POST</v-chip>
            <v-btn
              icon="mdi-content-copy"
              variant="text"
              size="x-small"
              @click="copy(formattedRequestSchema)"
            />
          </div>
          <v-sheet class="pa-3 bg-surface-variant rounded">
            <pre class="schema-json">{{ formattedRequestSchema }}</pre>
          </v-sheet>
        </div>

        <!-- Example Request -->
        <div v-if="exampleRequest">
          <div class="d-flex align-center mb-2">
            <div class="text-subtitle-1 font-weight-medium">Example Request Body</div>
            <v-spacer />
            <v-btn
              icon="mdi-content-copy"
              variant="text"
              size="x-small"
              @click="copy(formattedExampleRequest)"
            />
          </div>
          <v-sheet class="pa-3 bg-surface-variant rounded">
            <pre class="schema-json">{{ formattedExampleRequest }}</pre>
          </v-sheet>
        </div>
      </v-col>

      <!-- Right Column: Response -->
      <v-col cols="6">
        <!-- Response Schema -->
        <div v-if="responseSchema" class="mb-4">
          <div class="d-flex align-center mb-2">
            <div class="text-subtitle-1 font-weight-medium">Response Schema</div>
            <v-spacer />
            <v-btn
              icon="mdi-content-copy"
              variant="text"
              size="x-small"
              @click="copy(formattedResponseSchema)"
            />
          </div>
          <v-sheet class="pa-3 bg-surface-variant rounded">
            <pre class="schema-json">{{ formattedResponseSchema }}</pre>
          </v-sheet>
        </div>
      </v-col>
    </v-row>

    <!-- cURL Example (Full Width at Bottom) -->
    <div v-if="showCurl && apiKey" class="mt-4">
      <div class="d-flex align-center mb-2">
        <div class="text-subtitle-1 font-weight-medium">cURL Example</div>
        <v-spacer />
        <v-btn
          variant="tonal"
          size="small"
          prepend-icon="mdi-content-copy"
          @click="copyCurl"
        >
          Copy cURL
        </v-btn>
      </div>
      <v-sheet class="pa-4 bg-surface-variant rounded">
        <pre class="schema-json">{{ curlCommand }}</pre>
      </v-sheet>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useClipboard } from '@vueuse/core'

interface Props {
  title?: string
  requestSchema?: any
  responseSchema?: any
  urlPath?: string
  apiKey?: string
  showUrl?: boolean
  showCurl?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Schema',
  showUrl: true,
  showCurl: true
})

// Get base URL
const baseUrl = computed(() => {
  return window.location.origin
})

const fullUrl = computed(() => {
  if (!props.urlPath) return ''
  return `${baseUrl.value}${props.urlPath}`
})

// Format schemas for display
const formattedRequestSchema = computed(() => {
  if (!props.requestSchema) return ''
  return JSON.stringify(props.requestSchema, null, 2)
})

const formattedResponseSchema = computed(() => {
  if (!props.responseSchema) return ''
  return JSON.stringify(props.responseSchema, null, 2)
})

// Parse request parameters from schema
const requestParams = computed(() => {
  if (!props.requestSchema?.properties) return []

  const required = props.requestSchema.required || []

  return Object.entries(props.requestSchema.properties).map(([name, prop]: [string, any]) => ({
    name,
    type: prop.type || 'any',
    required: required.includes(name),
    default: prop.default
  }))
})

// Generate example request (includes all parameters)
const exampleRequest = computed(() => {
  if (!props.requestSchema?.properties) return null

  const example: any = {}

  Object.entries(props.requestSchema.properties).forEach(([name, prop]: [string, any]) => {
    if (prop.default !== undefined) {
      example[name] = prop.default
    } else {
      // Generate example based on type
      switch (prop.type) {
        case 'string':
          example[name] = `example_${name}`
          break
        case 'integer':
        case 'number':
          example[name] = 0
          break
        case 'boolean':
          example[name] = true
          break
        case 'array':
          example[name] = []
          break
        case 'object':
          example[name] = {}
          break
        default:
          example[name] = null
      }
    }
  })

  return example
})

const formattedExampleRequest = computed(() => {
  if (!exampleRequest.value) return ''
  return JSON.stringify(exampleRequest.value, null, 2)
})

// Generate minimal example for cURL (only required parameters)
const curlExampleRequest = computed(() => {
  if (!props.requestSchema?.properties) return {}

  const required = props.requestSchema.required || []
  const example: any = {}

  // Only include required parameters
  Object.entries(props.requestSchema.properties).forEach(([name, prop]: [string, any]) => {
    if (required.includes(name)) {
      // Generate placeholder based on type
      switch (prop.type) {
        case 'string':
          example[name] = `<${name}>`
          break
        case 'integer':
        case 'number':
          example[name] = 0
          break
        case 'boolean':
          example[name] = false
          break
        case 'array':
          example[name] = []
          break
        case 'object':
          example[name] = {}
          break
        default:
          example[name] = null
      }
    }
  })

  return example
})

// Generate cURL command
const curlCommand = computed(() => {
  if (!props.urlPath || !props.apiKey) return ''

  const example = curlExampleRequest.value

  return `curl -X POST "${fullUrl.value}" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: ${props.apiKey}" \\
  -d '${JSON.stringify(example, null, 2)}'`
})

// Clipboard functionality
const { copy, copied } = useClipboard()

function copyUrl() {
  copy(fullUrl.value)
}

function copyCurl() {
  copy(curlCommand.value)
}
</script>

<style scoped lang="scss">
.schema-json {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  max-height: 300px;
  overflow-y: auto;
  color: rgb(var(--v-theme-on-surface));

  // Increase contrast for better readability
  .v-theme--light & {
    color: rgba(0, 0, 0, 0.87);
  }

  .v-theme--dark & {
    color: rgba(255, 255, 255, 0.95);
  }
}

code {
  font-family: 'Courier New', monospace;
  padding: 2px 6px;
  border-radius: 3px;

  // Increase background opacity and ensure text is visible
  .v-theme--light & {
    background-color: rgba(0, 0, 0, 0.08);
    color: rgba(0, 0, 0, 0.87);
  }

  .v-theme--dark & {
    background-color: rgba(255, 255, 255, 0.12);
    color: rgba(255, 255, 255, 0.95);
  }
}
</style>
