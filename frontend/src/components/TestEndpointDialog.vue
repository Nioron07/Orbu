<template>
  <v-dialog v-model="internalDialog" max-width="900px" scrollable persistent>
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between px-6 py-4">
        <div>
          <div class="text-h5 font-weight-bold">Test Endpoint</div>
          <div class="text-caption text-medium-emphasis mt-1">
            {{ endpoint?.service_name }}.{{ endpoint?.method_name }}
          </div>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="closeDialog"
          :disabled="loading"
        />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-6">
        <!-- Endpoint URL Display -->
        <div class="mb-6">
          <div class="text-subtitle-2 font-weight-medium mb-2">Endpoint URL</div>
          <v-sheet class="pa-3 bg-surface-variant rounded">
            <code class="text-body-2">{{ endpoint?.url_path }}</code>
          </v-sheet>
        </div>

        <!-- Parameters Form -->
        <v-form ref="formRef" v-model="formValid">
          <div v-if="parameters.length > 0">
            <div class="text-subtitle-1 font-weight-medium mb-4">Request Parameters</div>

            <div v-for="param in parameters" :key="param.name" class="mb-4">
              <!-- String/Text Parameters -->
              <v-text-field
                v-if="param.type === 'string' && !isComplexType(param)"
                v-model="formData[param.name]"
                :label="param.name"
                :hint="param.description"
                :rules="param.required ? [rules.required] : []"
                :required="param.required"
                variant="outlined"
                density="comfortable"
                persistent-hint
              >
                <template v-slot:append-inner v-if="param.default !== undefined">
                  <v-tooltip location="top">
                    <template v-slot:activator="{ props }">
                      <v-icon
                        v-bind="props"
                        size="small"
                        color="grey"
                      >
                        mdi-information-outline
                      </v-icon>
                    </template>
                    Default: {{ param.default }}
                  </v-tooltip>
                </template>
              </v-text-field>

              <!-- Number Parameters -->
              <v-text-field
                v-else-if="param.type === 'number' || param.type === 'integer'"
                v-model.number="formData[param.name]"
                :label="param.name"
                :hint="param.description"
                :rules="param.required ? [rules.required, rules.number] : [rules.number]"
                :required="param.required"
                type="number"
                variant="outlined"
                density="comfortable"
                persistent-hint
              >
                <template v-slot:append-inner v-if="param.default !== undefined">
                  <v-tooltip location="top">
                    <template v-slot:activator="{ props }">
                      <v-icon
                        v-bind="props"
                        size="small"
                        color="grey"
                      >
                        mdi-information-outline
                      </v-icon>
                    </template>
                    Default: {{ param.default }}
                  </v-tooltip>
                </template>
              </v-text-field>

              <!-- Boolean Parameters -->
              <div v-else-if="param.type === 'boolean'" class="d-flex align-center">
                <v-switch
                  v-model="formData[param.name]"
                  :label="param.name"
                  color="primary"
                  density="comfortable"
                  hide-details="auto"
                />
                <v-tooltip location="top" v-if="param.description">
                  <template v-slot:activator="{ props }">
                    <v-icon
                      v-bind="props"
                      size="small"
                      color="grey"
                      class="ml-2"
                    >
                      mdi-information-outline
                    </v-icon>
                  </template>
                  {{ param.description }}
                </v-tooltip>
              </div>

              <!-- Array/Object Parameters -->
              <v-textarea
                v-else
                v-model="formData[param.name]"
                :label="param.name"
                :hint="param.description || `Enter valid JSON for ${param.type}`"
                :rules="param.required ? [rules.required, rules.json] : [rules.json]"
                :required="param.required"
                variant="outlined"
                density="comfortable"
                rows="4"
                persistent-hint
                auto-grow
              >
                <template v-slot:append-inner v-if="param.default !== undefined">
                  <v-tooltip location="top">
                    <template v-slot:activator="{ props }">
                      <v-icon
                        v-bind="props"
                        size="small"
                        color="grey"
                      >
                        mdi-information-outline
                      </v-icon>
                    </template>
                    Default: {{ JSON.stringify(param.default) }}
                  </v-tooltip>
                </template>
              </v-textarea>
            </div>
          </div>

          <!-- No Parameters Message -->
          <div v-else class="text-center py-6 text-medium-emphasis">
            <v-icon size="48" class="mb-2">mdi-information-outline</v-icon>
            <p>This endpoint does not require any parameters.</p>
          </div>
        </v-form>

        <!-- Response Section -->
        <div v-if="response !== null" class="mt-6">
          <v-divider class="mb-4" />

          <div class="d-flex align-center justify-space-between mb-3">
            <div class="text-subtitle-1 font-weight-medium">Response</div>
            <v-chip
              :color="responseSuccess ? 'success' : 'error'"
              variant="tonal"
              size="small"
            >
              {{ responseSuccess ? 'Success' : 'Error' }}
            </v-chip>
          </div>

          <!-- Response Data -->
          <div class="position-relative">
            <v-btn
              icon="mdi-content-copy"
              variant="text"
              size="small"
              class="response-copy-btn"
              @click="copyResponse"
            />
            <v-sheet class="pa-4 bg-surface-variant rounded response-container">
              <pre class="response-json">{{ formattedResponse }}</pre>
            </v-sheet>
          </div>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions class="px-6 py-4">
        <v-btn
          variant="text"
          @click="closeDialog"
          :disabled="loading"
        >
          Cancel
        </v-btn>
        <v-spacer />
        <v-btn
          v-if="response !== null"
          variant="text"
          color="primary"
          @click="resetResponse"
          :disabled="loading"
        >
          Reset
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="loading"
          @click="submitTest"
        >
          <v-icon start>mdi-play</v-icon>
          Test Endpoint
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarMessage }}
    </v-snackbar>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { clientApi } from '@/services/clientApi';
import type { Endpoint } from '@/services/clientApi';

interface Props {
  modelValue: boolean;
  endpoint: Endpoint | null;
}

interface Parameter {
  name: string;
  type: string;
  required: boolean;
  description?: string;
  default?: any;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
}>();

// State
const snackbar = ref(false);
const snackbarMessage = ref('');
const snackbarColor = ref('success');

const internalDialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const formRef = ref<any>(null);
const formValid = ref(false);
const formData = ref<Record<string, any>>({});
const loading = ref(false);
const response = ref<any>(null);
const responseSuccess = ref(false);

// Helper function
function showSnackbar(message: string, color: string) {
  snackbarMessage.value = message;
  snackbarColor.value = color;
  snackbar.value = true;
}

// Validation Rules
const rules = {
  required: (value: any) => {
    if (value === null || value === undefined || value === '') {
      return 'This field is required';
    }
    return true;
  },
  number: (value: any) => {
    if (value === null || value === undefined || value === '') {
      return true; // Let required rule handle this
    }
    if (isNaN(Number(value))) {
      return 'Must be a valid number';
    }
    return true;
  },
  json: (value: any) => {
    if (!value) return true; // Let required rule handle empty values
    try {
      JSON.parse(value);
      return true;
    } catch (e) {
      return 'Must be valid JSON';
    }
  },
};

// Computed
const parameters = computed<Parameter[]>(() => {
  if (!props.endpoint?.request_schema) return [];

  const schema = props.endpoint.request_schema;
  const properties = schema.properties || {};
  const required = schema.required || [];

  return Object.entries(properties).map(([name, propSchema]: [string, any]) => ({
    name,
    type: propSchema.type || 'string',
    required: required.includes(name),
    description: propSchema.description,
    default: propSchema.default,
  }));
});

const formattedResponse = computed(() => {
  if (response.value === null) return '';
  return JSON.stringify(response.value, null, 2);
});

// Methods
function isComplexType(param: Parameter): boolean {
  return param.type === 'array' || param.type === 'object';
}

function initializeFormData() {
  formData.value = {};
  // Leave all fields empty - no autofill
  // This ensures optional parameters are truly optional and won't be sent
}

function buildRequestBody(): Record<string, any> {
  const body: Record<string, any> = {};

  parameters.value.forEach((param) => {
    const value = formData.value[param.name];

    // Skip empty optional fields completely - don't include them in the request
    // This allows the backend/library to use its own defaults
    if (!param.required && (value === '' || value === null || value === undefined)) {
      return;
    }

    // For booleans, include false values even for optional params
    if (param.type === 'boolean' && !param.required && value === false) {
      // Only include if user explicitly set it (not the default initialization)
      // We'll skip false booleans for optional params
      return;
    }

    // Parse JSON strings for complex types
    if (isComplexType(param) && typeof value === 'string') {
      try {
        body[param.name] = JSON.parse(value);
      } catch (e) {
        // Validation should have caught this, but just in case
        body[param.name] = value;
      }
    } else {
      body[param.name] = value;
    }
  });

  return body;
}

async function submitTest() {
  if (!props.endpoint) return;

  // Validate form
  const { valid } = await formRef.value.validate();
  if (!valid) {
    showSnackbar('Please fix validation errors', 'error');
    return;
  }

  loading.value = true;
  response.value = null;

  try {
    const requestBody = buildRequestBody();
    const result = await clientApi.testEndpoint(props.endpoint.id, requestBody);

    if (result.success) {
      response.value = result.data;
      responseSuccess.value = true;
      showSnackbar('Endpoint tested successfully', 'success');
    } else {
      response.value = { error: result.error || 'Unknown error' };
      responseSuccess.value = false;
      showSnackbar(result.error || 'Test failed', 'error');
    }
  } catch (error: any) {
    response.value = { error: error.message || 'Request failed' };
    responseSuccess.value = false;
    showSnackbar('Failed to test endpoint', 'error');
  } finally {
    loading.value = false;
  }
}

function resetResponse() {
  response.value = null;
  responseSuccess.value = false;
}

function closeDialog() {
  internalDialog.value = false;
  // Reset state after dialog close animation
  setTimeout(() => {
    initializeFormData();
    resetResponse();
    formRef.value?.resetValidation();
  }, 300);
}

function copyResponse() {
  if (formattedResponse.value) {
    navigator.clipboard.writeText(formattedResponse.value);
    showSnackbar('Response copied to clipboard', 'success');
  }
}

// Watch for endpoint changes and initialize form
watch(() => props.endpoint, (newEndpoint) => {
  if (newEndpoint) {
    initializeFormData();
    resetResponse();
  }
}, { immediate: true });
</script>

<style scoped lang="scss">
code {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.875rem;

  .v-theme--light & {
    color: rgba(0, 0, 0, 0.87);
  }

  .v-theme--dark & {
    color: rgba(255, 255, 255, 0.95);
  }
}

.response-container {
  position: relative;
  max-height: 400px;
  overflow-y: auto;
}

.response-json {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.875rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;

  .v-theme--light & {
    color: rgba(0, 0, 0, 0.87);
  }

  .v-theme--dark & {
    color: rgba(255, 255, 255, 0.95);
  }
}

.response-copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
}
</style>
