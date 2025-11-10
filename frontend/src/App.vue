<template>
  <v-app>
    <!-- Navigation Rail Sidebar -->
    <NavigationRail />

    <!-- Top App Bar -->
    <v-app-bar
      elevation="0"
      class="gradient-app-bar"
      height="64"
    >
      <!-- Small Logo and Brand -->
      <div class="d-flex align-center px-4">
        <v-img
          src="/logo.png"
          width="32"
          height="32"
          class="mr-3"
        />
        <span class="text-h6 font-weight-bold gradient-text-primary">AcuNexus</span>
      </div>

      <v-spacer />

      <!-- Right Side Actions -->
      <div class="d-flex align-center gap-3 px-4">
        <!-- Client Switcher -->
        <ClientSwitcher />
      </div>
    </v-app-bar>

    <!-- Main Content Area -->
    <v-main class="app-background">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </v-main>

    <!-- Footer -->
    <v-footer
      app
      height="48"
      class="gradient-app-bar"
    >
      <v-container fluid class="d-flex align-center justify-center py-2">
        <div class="text-caption d-flex align-center gap-2" style="opacity: 0.7;">
          <span class="font-weight-semibold">AcuNexus</span>
          <span>v0.1.0</span>
          <span class="mx-1">•</span>
          <span>Powered by</span>
          <a href="https://github.com/Nioron07/Easy-Acumatica" target="_blank" class="text-primary text-decoration-none font-weight-medium">Easy-Acumatica</a>
          <span class="mx-1">•</span>
          <a href="https://github.com/Nioron07/AcuNexus/blob/main/LICENSE" target="_blank" class="text-decoration-none font-weight-medium">GNU AGPL v3.0</a>
          <span class="mx-1">•</span>
          <v-btn
            href="https://github.com/Nioron07/AcuNexus/issues/new"
            target="_blank"
            variant="text"
            size="x-small"
            prepend-icon="mdi-bug"
            class="text-caption"
            style="opacity: 0.7;"
          >
            Report Issue
          </v-btn>
        </div>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useTheme } from 'vuetify';
import { useAppStore } from '@/stores/app';
import { useClientsStore } from '@/stores/clients';
import { useSettingsStore } from '@/stores/settings';
import NavigationRail from '@/components/NavigationRail.vue';
import ClientSwitcher from '@/components/ClientSwitcher.vue';

const router = useRouter();
const theme = useTheme();
const appStore = useAppStore();
const clientsStore = useClientsStore();
const settingsStore = useSettingsStore();

// Methods
function logout() {
  // Disconnect from any active client
  if (clientsStore.isConnected) {
    clientsStore.disconnectFromClient();
  }
  // Navigate to home
  router.push('/');
}

async function handleAutoConnect() {
  // Only attempt auto-connect if configured
  if (!settingsStore.shouldAutoConnect) {
    return;
  }

  const clientIdToConnect = settingsStore.autoConnectClientId;

  if (!clientIdToConnect) {
    return;
  }

  // Check if the client still exists and is active
  const client = clientsStore.getClientById(clientIdToConnect);

  if (!client) {
    // Client no longer exists, reset to manual mode
    console.warn('Auto-connect client not found, resetting to manual mode');
    settingsStore.resetToManual();
    return;
  }

  if (client.is_active === false) {
    // Client is inactive, reset to manual mode
    console.warn('Auto-connect client is inactive, resetting to manual mode');
    settingsStore.resetToManual();
    return;
  }

  // Attempt to connect
  try {
    const result = await clientsStore.connectToClient(clientIdToConnect);
    if (!result.success) {
      console.error('Auto-connect failed:', result.error);
    }
  } catch (error) {
    console.error('Auto-connect error:', error);
  }
}

// Load theme preference, settings, and clients
onMounted(async () => {
  // Load saved theme or default to dark
  const savedTheme = (localStorage.getItem('acunexus_theme') as 'light' | 'dark') || 'dark';
  appStore.setTheme(savedTheme);
  theme.global.name.value = savedTheme;

  // Load settings
  settingsStore.loadSettings();

  // Load clients
  await clientsStore.loadClients();

  // Attempt auto-connect if configured
  await handleAutoConnect();
});
</script>

<style lang="scss">
// Import styles
@use '@/styles/glass-effects.scss';

// App-specific styles
.app-background {
  background: linear-gradient(135deg,
    rgba(99, 102, 241, 0.03) 0%,
    rgba(var(--v-theme-background), 1) 50%,
    rgba(139, 92, 246, 0.03) 100%
  );
  min-height: calc(100vh - 112px); // Account for header and footer

  .v-theme--light & {
    background: linear-gradient(135deg,
      rgba(99, 102, 241, 0.02) 0%,
      rgba(248, 250, 252, 1) 50%,
      rgba(139, 92, 246, 0.02) 100%
    );
  }
}

// Page transition
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// App bar enhancements
.v-app-bar {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)) !important;
}

// Footer enhancements
.v-footer {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)) !important;

  a {
    transition: opacity 0.2s ease;

    &:hover {
      opacity: 0.8;
    }
  }
}

// Global tooltip color fix for light/dark mode
.v-tooltip .v-overlay__content {
  // Light theme: dark tooltip with white text
  .v-theme--light & {
    background: rgba(97, 97, 97, 0.92) !important;
    color: #FFFFFF !important;
  }

  // Dark theme: light tooltip with dark text
  .v-theme--dark & {
    background: rgba(238, 238, 238, 0.92) !important;
    color: rgba(0, 0, 0, 0.87) !important;
  }
}
</style>
