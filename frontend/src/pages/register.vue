<template>
  <v-container class="register-container" fluid>
    <v-row justify="center" align="center" class="fill-height">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Request Account</v-toolbar-title>
          </v-toolbar>

          <v-card-text>
            <v-alert
              v-if="success"
              type="success"
              variant="tonal"
              class="mb-4"
            >
              {{ successMessage }}
            </v-alert>

            <v-form v-if="!success" ref="form" v-model="valid" @submit.prevent="handleRegister">
              <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                class="mb-4"
                closable
                @click:close="error = ''"
              >
                {{ error }}
              </v-alert>

              <v-text-field
                v-model="name"
                label="Full Name"
                prepend-icon="mdi-account"
                :rules="nameRules"
                required
                autofocus
              />

              <v-text-field
                v-model="email"
                label="Email"
                type="email"
                prepend-icon="mdi-email"
                :rules="emailRules"
                required
              />

              <v-text-field
                v-model="password"
                label="Password"
                :type="showPassword ? 'text' : 'password'"
                prepend-icon="mdi-lock"
                :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                :rules="passwordRules"
                required
                hint="At least 8 characters with uppercase, lowercase, and number"
                @click:append="showPassword = !showPassword"
              />

              <v-text-field
                v-model="confirmPassword"
                label="Confirm Password"
                :type="showPassword ? 'text' : 'password'"
                prepend-icon="mdi-lock-check"
                :rules="confirmPasswordRules"
                required
              />
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-btn
              variant="text"
              color="primary"
              :to="{ name: '/login' }"
            >
              Back to Login
            </v-btn>
            <v-spacer />
            <v-btn
              v-if="!success"
              color="primary"
              variant="elevated"
              :loading="loading"
              :disabled="!valid"
              @click="handleRegister"
            >
              Request Account
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const form = ref()
const valid = ref(false)
const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref(false)
const successMessage = ref('')

const nameRules = [
  (v: string) => !!v || 'Name is required',
  (v: string) => v.length >= 2 || 'Name must be at least 2 characters',
]

const emailRules = [
  (v: string) => !!v || 'Email is required',
  (v: string) => /.+@.+/.test(v) || 'Email must be valid',
]

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 8 || 'Password must be at least 8 characters',
  (v: string) => /[A-Z]/.test(v) || 'Password must contain at least one uppercase letter',
  (v: string) => /[a-z]/.test(v) || 'Password must contain at least one lowercase letter',
  (v: string) => /[0-9]/.test(v) || 'Password must contain at least one number',
]

const confirmPasswordRules = computed(() => [
  (v: string) => !!v || 'Please confirm your password',
  (v: string) => v === password.value || 'Passwords do not match',
])

async function handleRegister() {
  if (!form.value) return

  const { valid: isValid } = await form.value.validate()
  if (!isValid) return

  loading.value = true
  error.value = ''

  try {
    const response = await authStore.register(name.value, email.value, password.value)
    success.value = true
    successMessage.value = response.message || 'Account request submitted. Please wait for admin approval.'
  } catch (e: any) {
    error.value = e.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
