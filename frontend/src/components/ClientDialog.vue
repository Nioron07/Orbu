<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800"
    scrollable
  >
    <v-card>
      <v-card-title>
        {{ isEditing ? 'Edit Client' : 'Add New Client' }}
      </v-card-title>

      <v-card-text>
        <v-form ref="form" v-model="valid">
          <!-- Basic Information -->
          <div class="text-subtitle-2 mb-2">Basic Information</div>

          <v-text-field
            v-model="formData.name"
            label="Client Name"
            :rules="[rules.required]"
            placeholder="Production Acumatica"
            class="mb-2"
          />

          <v-textarea
            v-model="formData.description"
            label="Description"
            rows="2"
            placeholder="Optional description for this client"
            class="mb-4"
          />

          <!-- Connection Details -->
          <div class="text-subtitle-2 mb-2">Connection Details</div>

          <v-text-field
            v-model="formData.base_url"
            label="Acumatica URL"
            :rules="[rules.required, rules.url]"
            placeholder="https://your-instance.acumatica.com"
            class="mb-2"
          />

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.tenant"
                label="Tenant"
                :rules="[rules.required]"
                placeholder="Company"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.branch"
                label="Branch (Optional)"
                placeholder="MAIN"
              />
            </v-col>
          </v-row>

          <!-- Credentials -->
          <div class="text-subtitle-2 mb-2">Credentials</div>

          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.username"
                label="Username"
                :rules="[!isEditing || formData.username ? rules.required : () => true]"
                :placeholder="isEditing ? 'Leave blank to keep current' : 'api_user'"
                autocomplete="username"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.password"
                label="Password"
                type="password"
                :rules="[!isEditing || formData.password ? rules.required : () => true]"
                :placeholder="isEditing ? 'Leave blank to keep current' : '••••••••'"
                autocomplete="current-password"
              />
            </v-col>
          </v-row>

          <!-- API Configuration -->
          <v-expansion-panels class="mt-4">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <div class="text-subtitle-2">Advanced Settings</div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="formData.endpoint_name"
                      label="Endpoint Name"
                      placeholder="Default"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="formData.endpoint_version"
                      label="Endpoint Version"
                      placeholder="23.200.001"
                    />
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="formData.locale"
                      label="Locale"
                      :items="['en-US', 'en-GB', 'fr-FR', 'de-DE', 'es-ES']"
                      placeholder="en-US"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="formData.timeout"
                      label="Timeout (seconds)"
                      type="number"
                      :rules="[rules.positiveNumber]"
                      placeholder="60"
                    />
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="formData.rate_limit_calls_per_second"
                      label="Rate Limit (calls/sec)"
                      type="number"
                      step="0.1"
                      :rules="[rules.positiveNumber]"
                      placeholder="10.0"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="formData.cache_ttl_hours"
                      label="Cache TTL (hours)"
                      type="number"
                      :rules="[rules.positiveNumber]"
                      placeholder="24"
                    />
                  </v-col>
                </v-row>

                <!-- Switches -->
                <v-row>
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="formData.verify_ssl"
                      label="Verify SSL Certificate"
                      color="primary"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="formData.persistent_login"
                      label="Persistent Login"
                      color="primary"
                    />
                  </v-col>
                </v-row>

                <v-row>
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="formData.retry_on_idle_logout"
                      label="Retry on Idle Logout"
                      color="primary"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-switch
                      v-model="formData.cache_methods"
                      label="Cache Methods"
                      color="primary"
                    />
                  </v-col>
                </v-row>

              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="cancel">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          @click="save"
          :disabled="!valid"
        >
          {{ isEditing ? 'Update' : 'Create' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { Client } from '@/services/clientApi';

// Props
const props = defineProps<{
  modelValue: boolean;
  client: Client | null;
}>();

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  save: [client: Client];
}>();

// Form reference
const form = ref();
const valid = ref(false);

// Form data
const formData = ref<Client>({
  name: '',
  description: '',
  base_url: '',
  tenant: '',
  branch: '',
  username: '',
  password: '',
  endpoint_name: 'Default',
  endpoint_version: '',
  locale: 'en-US',
  verify_ssl: true,
  persistent_login: true,
  retry_on_idle_logout: true,
  timeout: 60,
  rate_limit_calls_per_second: 10.0,
  cache_methods: true,
  cache_ttl_hours: 24,
  is_active: true
});

// Computed
const isEditing = computed(() => !!props.client?.id);

// Validation rules
const rules = {
  required: (v: any) => !!v || 'Required',
  url: (v: string) => {
    if (!v) return true;
    try {
      new URL(v);
      return true;
    } catch {
      return 'Must be a valid URL';
    }
  },
  positiveNumber: (v: any) => {
    if (!v && v !== 0) return true;
    const num = typeof v === 'string' ? parseFloat(v) : v;
    return !isNaN(num) && num > 0 || 'Must be a positive number';
  }
};

// Watch for client prop changes
watch(() => props.client, (newClient) => {
  if (newClient) {
    // Copy client data to form, including password for duplication
    formData.value = {
      ...formData.value,
      ...newClient
    };
  } else {
    // Reset form
    formData.value = {
      name: '',
      description: '',
      base_url: '',
      tenant: '',
      branch: '',
      username: '',
      password: '',
      endpoint_name: 'Default',
      endpoint_version: '',
      locale: 'en-US',
      verify_ssl: true,
      persistent_login: true,
      retry_on_idle_logout: true,
      timeout: 60,
      rate_limit_calls_per_second: 10.0,
      cache_methods: true,
      cache_ttl_hours: 24,
      is_active: true
    };
  }
}, { immediate: true });

// Methods
function cancel() {
  emit('update:modelValue', false);
}

async function save() {
  const validation = await form.value?.validate();
  if (!validation?.valid) return;

  // Prepare data for save
  const dataToSave: Client = { ...formData.value };

  // If editing and no new password provided, remove it from the payload
  if (isEditing.value && !dataToSave.password) {
    delete dataToSave.password;
    // Also remove username if not changed
    if (!dataToSave.username) {
      delete dataToSave.username;
    }
  }

  emit('save', dataToSave);
}
</script>