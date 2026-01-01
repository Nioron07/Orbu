<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="600" persistent>
    <v-card>
      <v-card-title class="d-flex align-center bg-primary pa-4">
        <v-icon start color="white">{{ isEditing ? 'mdi-pencil' : 'mdi-folder-plus' }}</v-icon>
        <span class="text-white">{{ isEditing ? 'Edit Service Group' : 'Create Service Group' }}</span>
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" color="white" @click="close" />
      </v-card-title>

      <v-card-text class="pa-6">
        <v-form ref="form" v-model="isValid" @submit.prevent="save">
          <!-- Name Field -->
          <v-text-field
            v-model="formData.name"
            label="Name"
            hint="This will be converted to a URL-safe slug (e.g., 'Inventory App' becomes 'inventory-app')"
            persistent-hint
            :rules="nameRules"
            variant="outlined"
            density="comfortable"
            class="mb-4"
          />

          <!-- Display Name Field -->
          <v-text-field
            v-model="formData.display_name"
            label="Display Name"
            hint="Human-readable name shown in the UI (optional)"
            persistent-hint
            variant="outlined"
            density="comfortable"
            class="mb-4"
          />

          <!-- Description Field -->
          <v-textarea
            v-model="formData.description"
            label="Description"
            hint="Brief description of this service group's purpose (optional)"
            persistent-hint
            variant="outlined"
            density="comfortable"
            rows="3"
            class="mb-4"
          />

          <!-- Active Toggle -->
          <v-switch
            v-model="formData.is_active"
            label="Active"
            hint="Inactive service groups cannot deploy new endpoints"
            persistent-hint
            color="primary"
          />

          <!-- Error Alert -->
          <v-alert v-if="error" type="error" variant="tonal" class="mt-4" density="compact">
            {{ error }}
          </v-alert>
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="text" @click="close">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          @click="save"
          :loading="saving"
          :disabled="!isValid"
        >
          {{ isEditing ? 'Update' : 'Create' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useServiceGroupsStore } from '@/stores/serviceGroups'
import type { ServiceGroup } from '@/services/clientApi'

interface Props {
  modelValue: boolean
  serviceGroup?: ServiceGroup | null
  clientId?: string
}

const props = withDefaults(defineProps<Props>(), {
  serviceGroup: null
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
  close: []
}>()

const serviceGroupsStore = useServiceGroupsStore()

// Form state
const form = ref<any>(null)
const isValid = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const formData = ref({
  name: '',
  display_name: '',
  description: '',
  is_active: true
})

// Validation rules
const nameRules = [
  (v: string) => !!v || 'Name is required',
  (v: string) => v.length >= 2 || 'Name must be at least 2 characters',
  (v: string) => /^[a-zA-Z0-9\s\-_]+$/.test(v) || 'Name can only contain letters, numbers, spaces, hyphens, and underscores'
]

// Computed
const isEditing = computed(() => !!props.serviceGroup?.id)

// Watch for serviceGroup changes to populate form
watch(() => props.serviceGroup, (serviceGroup) => {
  if (serviceGroup) {
    formData.value = {
      name: serviceGroup.display_name || serviceGroup.name,
      display_name: serviceGroup.display_name || '',
      description: serviceGroup.description || '',
      is_active: serviceGroup.is_active
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// Watch for dialog open
watch(() => props.modelValue, (isOpen) => {
  if (isOpen && !props.serviceGroup) {
    resetForm()
  }
  error.value = null
})

// Methods
function resetForm() {
  formData.value = {
    name: '',
    display_name: '',
    description: '',
    is_active: true
  }
  if (form.value) {
    form.value.resetValidation()
  }
}

async function save() {
  if (!props.clientId) {
    error.value = 'No client selected'
    return
  }

  const { valid } = await form.value.validate()
  if (!valid) return

  saving.value = true
  error.value = null

  try {
    if (isEditing.value && props.serviceGroup) {
      // Update existing service group
      const result = await serviceGroupsStore.updateServiceGroup(
        props.clientId,
        props.serviceGroup.id,
        {
          name: formData.value.name,
          display_name: formData.value.display_name || formData.value.name,
          description: formData.value.description,
          is_active: formData.value.is_active
        }
      )

      if (result.success) {
        emit('saved')
      } else {
        error.value = result.error || 'Failed to update service group'
      }
    } else {
      // Create new service group
      const result = await serviceGroupsStore.createServiceGroup(
        props.clientId,
        {
          name: formData.value.name,
          display_name: formData.value.display_name || formData.value.name,
          description: formData.value.description,
          is_active: formData.value.is_active
        }
      )

      if (result.success) {
        emit('saved')
      } else {
        error.value = result.error || 'Failed to create service group'
      }
    }
  } finally {
    saving.value = false
  }
}

function close() {
  emit('close')
  emit('update:modelValue', false)
}
</script>
