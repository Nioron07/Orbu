<template>
  <v-container fluid class="pa-6">
    <!-- Page Header -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h5 font-weight-bold">Settings</h1>
        <p class="text-caption text-medium-emphasis mb-0">
          Configure your Orbu preferences
        </p>
      </div>
    </div>

    <!-- Settings Cards -->
    <v-row>
      <!-- Appearance Settings -->
      <v-col cols="12" md="6">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center px-6 py-4">
            <v-icon class="mr-2" color="primary">mdi-palette</v-icon>
            Appearance
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">
            <div class="d-flex align-center justify-space-between">
              <div>
                <div class="text-subtitle-1 font-weight-medium">Theme</div>
                <div class="text-caption text-medium-emphasis mt-1">
                  Choose your preferred color scheme
                </div>
              </div>
              <v-btn-toggle
                :model-value="appStore.theme"
                @update:model-value="handleThemeChange"
                mandatory
                color="primary"
                variant="outlined"
                divided
              >
                <v-btn value="light" size="small">
                  <v-icon start>mdi-weather-sunny</v-icon>
                  Light
                </v-btn>
                <v-btn value="dark" size="small">
                  <v-icon start>mdi-weather-night</v-icon>
                  Dark
                </v-btn>
              </v-btn-toggle>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Connection Settings -->
      <v-col cols="12" md="6">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center px-6 py-4">
            <v-icon class="mr-2" color="primary">mdi-connection</v-icon>
            Auto-Connect
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-6">
            <div class="text-subtitle-1 font-weight-medium mb-4">
              Connection Behavior
            </div>
            <v-radio-group
              :model-value="settingsStore.autoConnectMode"
              @update:model-value="handleAutoConnectModeChange"
              hide-details
            >
              <v-radio value="manual">
                <template v-slot:label>
                  <div>
                    <div class="font-weight-medium">Manual (Default)</div>
                    <div class="text-caption text-medium-emphasis">
                      Manually select which client to connect to
                    </div>
                  </div>
                </template>
              </v-radio>

              <v-radio value="last" class="mt-3">
                <template v-slot:label>
                  <div>
                    <div class="font-weight-medium">Last Connected</div>
                    <div class="text-caption text-medium-emphasis">
                      Automatically connect to the last connected client
                    </div>
                  </div>
                </template>
              </v-radio>

              <v-radio value="default" class="mt-3">
                <template v-slot:label>
                  <div>
                    <div class="font-weight-medium">Default Client</div>
                    <div class="text-caption text-medium-emphasis">
                      Automatically connect to a specific client
                    </div>
                  </div>
                </template>
              </v-radio>
            </v-radio-group>

            <!-- Default Client Selector -->
            <v-expand-transition>
              <div v-if="settingsStore.autoConnectMode === 'default'" class="mt-4">
                <v-select
                  :model-value="settingsStore.defaultClientId"
                  @update:model-value="handleDefaultClientChange"
                  :items="activeClients"
                  item-title="name"
                  item-value="id"
                  label="Default Client"
                  placeholder="Select a client"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-domain"
                  :disabled="activeClients.length === 0"
                  hide-details
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item v-bind="props">
                      <template v-slot:prepend>
                        <v-avatar color="primary" size="32">
                          <v-icon size="18">mdi-domain</v-icon>
                        </v-avatar>
                      </template>
                      <v-list-item-title>{{ item.raw.name }}</v-list-item-title>
                      <v-list-item-subtitle>{{ item.raw.tenant }}</v-list-item-subtitle>
                    </v-list-item>
                  </template>
                </v-select>

                <v-alert
                  v-if="activeClients.length === 0"
                  type="info"
                  variant="tonal"
                  class="mt-3"
                  density="compact"
                >
                  No active clients available. Add a client first.
                </v-alert>
              </div>
            </v-expand-transition>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="bottom right"
    >
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useTheme } from 'vuetify';
import { useAppStore } from '@/stores/app';
import { useSettingsStore } from '@/stores/settings';
import { useClientsStore } from '@/stores/clients';
import type { AutoConnectMode } from '@/stores/settings';

const theme = useTheme();
const appStore = useAppStore();
const settingsStore = useSettingsStore();
const clientsStore = useClientsStore();

const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
});

// Computed
const activeClients = computed(() => clientsStore.activeClients);

// Methods
function handleThemeChange(newTheme: 'light' | 'dark') {
  appStore.setTheme(newTheme);
  theme.global.name.value = newTheme;
  showSnackbar(`Theme changed to ${newTheme} mode`, 'success');
}

function handleAutoConnectModeChange(mode: AutoConnectMode | null) {
  if (!mode) return;
  settingsStore.setAutoConnectMode(mode);
  showSnackbar('Auto-connect mode updated', 'success');
}

function handleDefaultClientChange(clientId: string) {
  settingsStore.setDefaultClientId(clientId);
  showSnackbar('Default client updated', 'success');
}

function showSnackbar(message: string, color: 'success' | 'error' | 'warning' | 'info') {
  snackbar.value = {
    show: true,
    message,
    color,
  };
}

// Lifecycle
onMounted(() => {
  settingsStore.loadSettings();
});
</script>

<style scoped lang="scss">
.glass-card {
  transition: none !important;

  &:hover {
    box-shadow: none !important;
    transform: none !important;
  }
}

// Radio group spacing
:deep(.v-radio) {
  .v-selection-control__wrapper {
    margin-right: 12px;
  }
}
</style>
