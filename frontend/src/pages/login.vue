<template>
  <v-container class="login-container" fluid>
    <v-row justify="center" align="center" class="fill-height">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Orbu Login</v-toolbar-title>
          </v-toolbar>

          <v-form ref="form" v-model="valid" @submit.prevent="handleLogin">
            <v-card-text>
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
                v-model="email"
                label="Email"
                type="email"
                prepend-icon="mdi-email"
                :rules="emailRules"
                required
                autofocus
              />

              <v-text-field
                v-model="password"
                label="Password"
                :type="showPassword ? 'text' : 'password'"
                prepend-icon="mdi-lock"
                :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                :rules="passwordRules"
                required
                @click:append="showPassword = !showPassword"
              />
            </v-card-text>

            <v-card-actions>
              <v-btn
                variant="text"
                color="primary"
                :to="{ name: '/register' }"
              >
                Request Account
              </v-btn>
              <v-spacer />
              <v-btn
                type="submit"
                color="primary"
                variant="elevated"
                :loading="loading"
                :disabled="!valid"
              >
                Login
              </v-btn>
            </v-card-actions>
          </v-form>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const theme = useTheme()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()
const appStore = useAppStore()

const form = ref()
const valid = ref(false)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

const emailRules = [
  (v: string) => !!v || 'Email is required',
  (v: string) => /.+@.+/.test(v) || 'Email must be valid',
]

const passwordRules = [
  (v: string) => !!v || 'Password is required',
]

async function handleLogin() {
  if (!form.value) return

  const { valid: isValid } = await form.value.validate()
  if (!isValid) return

  loading.value = true
  error.value = ''

  try {
    await authStore.login(email.value, password.value)

    // Load user's settings from backend (force reload to get new user's settings)
    await settingsStore.loadSettings(true)

    // Apply the user's theme preference
    appStore.setTheme(settingsStore.theme)
    theme.global.name.value = settingsStore.theme

    // Redirect to home or intended page
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
  } catch (e: any) {
    error.value = e.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
