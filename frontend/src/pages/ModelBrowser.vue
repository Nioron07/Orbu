<template>
  <v-container fluid class="pa-6">
    <!-- Page Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h5 font-weight-bold">Model Browser</h1>
        <p class="text-caption text-medium-emphasis mb-0">
          Explore Acumatica data models, fields, and schemas
        </p>
      </div>
    </div>

    <!-- Connection Required Empty State -->
    <v-card v-if="!clientsStore.isConnected" class="glass-card" elevation="0">
      <v-card-text class="pa-12">
        <div class="text-center">
          <v-icon size="80" color="primary" class="mb-4">mdi-link-off</v-icon>
          <h2 class="text-h5 font-weight-bold mb-3">No Client Connected</h2>
          <p class="text-body-1 text-medium-emphasis mb-6" style="max-width: 500px; margin: 0 auto;">
            Connect to an Acumatica client to explore data models, fields, and schemas.
          </p>
          <v-btn
            color="primary"
            size="large"
            prepend-icon="mdi-domain"
            @click="router.push('/clients')"
          >
            Go to Clients Page
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

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
        placeholder="Search models..."
        density="compact"
        hide-details
        variant="outlined"
        clearable
        class="flex-grow-1"
        style="max-width: 600px"
      />

      <v-spacer />

      <v-chip size="small" variant="text" class="text-medium-emphasis">
        <v-icon start size="small">mdi-database</v-icon>
        {{ filteredModels.length }} {{ filteredModels.length === 1 ? 'model' : 'models' }}
      </v-chip>
    </div>

    <!-- Models Data Table -->
    <v-card v-if="clientsStore.isConnected" class="glass-card" elevation="0">
      <v-data-table
        :headers="tableHeaders"
        :items="filteredModels"
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
              color="accent"
              size="small"
              class="mr-2"
            >
              mdi-database
            </v-icon>
            <span class="font-weight-medium">{{ item.name }}</span>
          </div>
        </template>

        <!-- Field Count Column -->
        <template v-slot:item.field_count="{ item }">
          <v-chip size="small" variant="tonal" color="info">
            {{ item.field_count }} {{ item.field_count === 1 ? 'field' : 'fields' }}
          </v-chip>
        </template>

        <!-- Loading State -->
        <template v-slot:loading>
          <v-skeleton-loader type="table-row@10" />
        </template>

        <!-- Empty State -->
        <template v-slot:no-data>
          <div class="text-center py-12">
            <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-database-off</v-icon>
            <h3 class="text-h6">No Models Found</h3>
            <p class="text-body-2 text-medium-emphasis mt-2">
              {{ searchQuery ? `No models match "${searchQuery}"` : 'No models available' }}
            </p>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Model Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="1600px" scrollable>
      <!-- Loading State -->
      <v-card v-if="!selectedModelDetails">
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
          <div>
            <div class="text-h5 font-weight-bold">{{ selectedModelDetails.name }}</div>
            <div v-if="selectedModelDetails.description" class="text-caption text-medium-emphasis mt-1">
              {{ selectedModelDetails.description }}
            </div>
          </div>
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="detailsDialog = false"
          />
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-6">
          <!-- Model Info and View Toggle -->
          <div class="mb-6">
            <v-row dense align="center">
              <v-col cols="auto">
                <v-chip size="small" variant="tonal" color="primary">
                  {{ selectedModelDetails.field_count }} Fields
                </v-chip>
              </v-col>
              <v-col v-if="selectedModelDetails.key_fields?.length" cols="auto">
                <v-chip
                  v-for="field in selectedModelDetails.key_fields"
                  :key="field"
                  size="small"
                  variant="tonal"
                  color="accent"
                  class="mr-1"
                  prepend-icon="mdi-key"
                >
                  {{ field }}
                </v-chip>
              </v-col>
              <v-spacer />
              <v-col cols="auto">
                <v-btn-toggle
                  v-model="viewMode"
                  mandatory
                  density="compact"
                  variant="outlined"
                  divided
                >
                  <v-btn value="table" size="small">
                    <v-icon start>mdi-table</v-icon>
                    Table
                  </v-btn>
                  <v-btn value="tree" size="small">
                    <v-icon start>mdi-file-tree</v-icon>
                    Tree
                  </v-btn>
                </v-btn-toggle>
              </v-col>
            </v-row>
          </div>

          <!-- Table View -->
          <div v-if="viewMode === 'table'" class="mb-4">
            <div class="d-flex align-center justify-end mb-3">
              <v-text-field
                v-model="fieldSearch"
                prepend-inner-icon="mdi-magnify"
                placeholder="Search fields..."
                density="compact"
                variant="outlined"
                hide-details
                clearable
                style="max-width: 300px"
              />
            </div>

            <v-data-table
              :headers="tableFieldHeaders"
              :items="filteredTableFields"
              :items-per-page="20"
              density="compact"
              class="elevation-0"
            >
              <!-- Field Name -->
              <template v-slot:item.name="{ item }">
                <code class="field-name">{{ item.name }}</code>
              </template>

              <!-- Type -->
              <template v-slot:item.type="{ item }">
                <code v-if="item.typeDisplay" class="type-code">{{ item.typeDisplay }}</code>
                <span v-else class="text-medium-emphasis">—</span>
              </template>

              <!-- Nested Model Action -->
              <template v-slot:item.actions="{ item }">
                <v-btn
                  v-if="item.isNestedModel"
                  size="small"
                  variant="text"
                  color="primary"
                  @click="openNestedModel(item.nestedModelName)"
                >
                  <v-icon start size="small">mdi-open-in-new</v-icon>
                  Open Model
                </v-btn>
                <span v-else class="text-medium-emphasis">—</span>
              </template>

              <!-- Required -->
              <template v-slot:item.required="{ item }">
                <v-chip
                  v-if="isFieldRequired(item)"
                  size="x-small"
                  variant="tonal"
                  color="warning"
                >
                  Required
                </v-chip>
                <span v-else class="text-medium-emphasis">Optional</span>
              </template>
            </v-data-table>
          </div>

          <!-- Tree View -->
          <div v-if="viewMode === 'tree'" class="mb-4">
            <div class="d-flex align-center justify-end mb-3">
              <v-text-field
                v-model="fieldSearch"
                prepend-inner-icon="mdi-magnify"
                placeholder="Search fields..."
                density="compact"
                variant="outlined"
                hide-details
                clearable
                style="max-width: 300px"
              />
            </div>

            <div class="tree-container">
              <SchemaTree
                :schema="filteredSchema"
                :search="fieldSearch"
              />
            </div>
          </div>
        </v-card-text>

        <v-divider />

        <v-card-actions class="px-6 py-4">
          <v-btn
            variant="text"
            prepend-icon="mdi-content-copy"
            @click="copyModelInfo"
          >
            Copy Schema
          </v-btn>
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

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar" :timeout="3000" color="success">
      <v-icon start>mdi-check-circle</v-icon>
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useClientsStore } from '@/stores/clients';
import { clientApi } from '@/services/clientApi';
import type { ModelInfo, ModelDetails } from '@/services/clientApi';
import SchemaTree from '@/components/SchemaTree.vue';

const router = useRouter();
const clientsStore = useClientsStore();

// State
const allModels = ref<ModelInfo[]>([]);
const selectedModelDetails = ref<ModelDetails | null>(null);
const searchQuery = ref('');
const fieldSearch = ref('');
const loading = ref(false);
const error = ref<string | null>(null);
const detailsDialog = ref(false);
const snackbar = ref(false);
const snackbarText = ref('');
const viewMode = ref<'table' | 'tree'>('table');

// Table headers
const tableHeaders = [
  {
    title: 'Model Name',
    key: 'name',
    sortable: true,
  },
  {
    title: 'Fields',
    key: 'field_count',
    sortable: true,
    width: '150px',
  },
];

const tableFieldHeaders = [
  { title: 'Field Name', key: 'name', sortable: true, width: '30%' },
  { title: 'Type', key: 'type', sortable: true, width: '25%' },
  { title: 'Nested Model', key: 'actions', sortable: false, width: '20%' },
  { title: 'Required', key: 'required', sortable: true, width: '15%' },
];

// Computed
const filteredModels = computed(() => {
  if (!searchQuery.value) return allModels.value;

  const search = searchQuery.value.toLowerCase();
  return allModels.value.filter(model =>
    model.name.toLowerCase().includes(search)
  );
});

// Helper function to check if a value is an object (nested model)
function isObject(value: any): boolean {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

// Helper function to check if a value is an array
function isArray(value: any): boolean {
  return Array.isArray(value);
}

// Helper function to check if a field has nested fields
function hasNestedFields(fieldDef: any): boolean {
  if (!isObject(fieldDef)) return false;
  return fieldDef.fields && Object.keys(fieldDef.fields).length > 0;
}

// Table view: only show level 1 fields
const filteredTableFields = computed(() => {
  if (!selectedModelDetails.value?.schema) return [];

  const schema = selectedModelDetails.value.schema;
  const fields = Object.entries(schema).map(([name, fieldDef]: [string, any]) => {
    // In 0.5.8 format, each field is { type: '...', fields: {...} }
    const typeStr = fieldDef.type || String(fieldDef);
    const hasNested = hasNestedFields(fieldDef);

    let typeDisplay = typeStr;
    let nestedModelName = '';

    if (hasNested) {
      // Extract the model name from the type (List[ModelName] or just ModelName)
      const listMatch = typeStr.match(/List\[(\w+)\]/);
      if (listMatch) {
        // It's a List[SomeModel] - extract SomeModel
        nestedModelName = listMatch[1];
      } else {
        // It's just a model type directly - use the type name
        nestedModelName = typeStr;
      }
    }

    return {
      name,
      typeDisplay,
      isNestedModel: hasNested,
      nestedModelName,
      type: fieldDef,
    };
  });

  if (!fieldSearch.value) return fields;

  const search = fieldSearch.value.toLowerCase();
  return fields.filter(field =>
    field.name.toLowerCase().includes(search) ||
    field.typeDisplay?.toLowerCase().includes(search)
  );
});

// Tree view: filtered schema
const filteredSchema = computed(() => {
  if (!selectedModelDetails.value?.schema) return {};

  // If no search, return full schema
  if (!fieldSearch.value) return selectedModelDetails.value.schema;

  // Filter schema recursively based on search
  const search = fieldSearch.value.toLowerCase();

  function filterSchema(obj: any): any {
    if (!isObject(obj)) return obj;

    const filtered: any = {};
    for (const [key, fieldDef] of Object.entries(obj)) {
      const fieldDefAny = fieldDef as any;
      // Include if key matches search
      if (key.toLowerCase().includes(search)) {
        filtered[key] = fieldDef;
      } else if (isObject(fieldDefAny) && fieldDefAny.fields && Object.keys(fieldDefAny.fields).length > 0) {
        // In 0.5.8 format, recursively filter the nested fields
        const nested = filterSchema(fieldDefAny.fields);
        if (Object.keys(nested).length > 0) {
          filtered[key] = {
            type: fieldDefAny.type,
            fields: nested
          };
        }
      }
    }
    return filtered;
  }

  return filterSchema(selectedModelDetails.value.schema);
});

// Methods
async function loadModels() {
  if (!clientsStore.isConnected || !clientsStore.activeClient?.id) return;

  loading.value = true;
  error.value = null;

  try {
    const response = await clientApi.listModels(clientsStore.activeClient.id);
    if (response.success) {
      allModels.value = response.models;
    } else {
      throw new Error(response.error || 'Failed to load models');
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load models';
    allModels.value = [];
  } finally {
    loading.value = false;
  }
}

function handleRowClick(event: any, { item }: any) {
  selectModel(item);
}

async function selectModel(model: ModelInfo) {
  if (!clientsStore.activeClient?.id) return;

  // Don't set table loading - use dialog loading instead
  error.value = null;
  fieldSearch.value = '';

  // Open dialog immediately to show loading state
  detailsDialog.value = true;
  selectedModelDetails.value = null; // Clear previous data

  try {
    const response = await clientApi.getModelDetails(clientsStore.activeClient.id, model.name);
    if (response.success && response.model) {
      selectedModelDetails.value = response.model;
    } else {
      detailsDialog.value = false;
      throw new Error(response.error || 'Failed to load model details');
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load model details';
    detailsDialog.value = false;
  }
}

function isFieldRequired(field: any): boolean {
  if (field.required === true) return true;
  if (field.required === false) return false;

  const typeStr = field.type || '';
  return !typeStr.includes('Optional');
}

function copyModelInfo() {
  if (!selectedModelDetails.value) return;

  // Copy just name and fields (which contains the schema from get_schema())
  const info = {
    name: selectedModelDetails.value.name,
    fields: selectedModelDetails.value.schema || selectedModelDetails.value.fields,
  };

  navigator.clipboard.writeText(JSON.stringify(info, null, 2));
  snackbarText.value = 'Model schema copied to clipboard';
  snackbar.value = true;
}

async function openNestedModel(modelName: string) {
  // Close current dialog
  detailsDialog.value = false;

  // Find the model in the list
  const model = allModels.value.find(m => m.name === modelName);
  if (model) {
    // Small delay to allow dialog to close smoothly
    await new Promise(resolve => setTimeout(resolve, 100));
    // Open the nested model
    selectModel(model);
  } else {
    error.value = `Model "${modelName}" not found`;
  }
}

// Lifecycle
onMounted(() => {
  if (clientsStore.isConnected) {
    loadModels();
  }
});

// Watch for connection changes
watch(() => clientsStore.isConnected, (connected) => {
  if (connected) {
    loadModels();
  } else {
    allModels.value = [];
    selectedModelDetails.value = null;
  }
});

// Watch for active client changes (client switching)
watch(() => clientsStore.activeClientId, (newClientId, oldClientId) => {
  // Only reload if we actually switched between different clients (both connected)
  if (newClientId && oldClientId && newClientId !== oldClientId) {
    loadModels();
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
.field-name {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.875em;
  font-weight: 600;
  color: rgb(var(--v-theme-accent));
  background: rgba(var(--v-theme-accent), 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.type-code {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.8em;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
}

// Remove card elevation
.glass-card {
  transition: none !important;

  &:hover {
    box-shadow: none !important;
    transform: none !important;
  }
}

// Tree container
.tree-container {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 16px;
  max-height: 600px;
  overflow-y: auto;
}
</style>
