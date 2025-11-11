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
      <!-- Logo and Brand -->
      <div class="d-flex align-center px-4">
        <v-img
          src="@/assets/AcuNexus_Logo_Big.png"
          class="app-logo mr-3"
          height="50"
          width="150"
        />
      </div>

      <v-spacer />

      <!-- Right Side Actions -->
      <div class="d-flex align-center gap-3 px-4">
        <!-- Theme Toggle -->
        <v-btn
          icon
          variant="text"
          @click="toggleTheme"
          class="theme-toggle-btn"
        >
          <v-icon>{{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
        </v-btn>

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
    <AppFooter />
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
import AppFooter from '@/components/AppFooter.vue';

const router = useRouter();
const theme = useTheme();
const appStore = useAppStore();
const clientsStore = useClientsStore();
const settingsStore = useSettingsStore();

// Methods
function toggleTheme() {
  appStore.toggleTheme();
  theme.global.name.value = appStore.theme;
}

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

// Logo styling with frame
.app-logo {
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 6px;
  background: rgba(255, 255, 255, 0.95);

  .v-theme--dark & {
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  }
}

// Global tooltip color fix for light/dark mode
.v-tooltip .v-overlay__content {
  // Light theme: dark tooltip with white text (standard)
  background: rgba(97, 97, 97, 0.95) !important;
  color: #FFFFFF !important;

  .v-theme--dark & {
    // Dark theme: keep dark tooltip with white text for consistency
    background: rgba(97, 97, 97, 0.95) !important;
    color: #FFFFFF !important;
  }
}
</style>
