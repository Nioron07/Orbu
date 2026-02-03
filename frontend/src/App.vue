<template>
  <v-app>
    <!-- Navigation Rail Sidebar (only when authenticated) -->
    <NavigationRail v-if="authStore.isAuthenticated" />

    <!-- Top App Bar -->
    <v-app-bar
      v-if="authStore.isAuthenticated"
      elevation="0"
      class="gradient-app-bar"
      height="64"
    >
      <!-- Organization Name / App Title -->
      <div class="d-flex align-center px-4">
        <span class="text-h6 font-weight-bold">{{ authStore.orgName }}</span>
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

        <!-- User Menu -->
        <v-menu>
          <template #activator="{ props }">
            <v-btn
              icon
              variant="text"
              v-bind="props"
            >
              <v-avatar color="primary" size="32">
                <span class="text-white text-body-2">{{ userInitials }}</span>
              </v-avatar>
            </v-btn>
          </template>
          <v-list density="compact" min-width="200">
            <v-list-item>
              <v-list-item-title class="font-weight-bold">{{ authStore.userName }}</v-list-item-title>
              <v-list-item-subtitle>{{ authStore.userEmail }}</v-list-item-subtitle>
            </v-list-item>
            <v-divider />
            <v-list-item
              v-if="authStore.isAdmin"
              prepend-icon="mdi-account-group"
              :to="{ path: '/admin/users' }"
            >
              <v-list-item-title>User Management</v-list-item-title>
            </v-list-item>
            <v-list-item
              prepend-icon="mdi-logout"
              @click="handleLogout"
            >
              <v-list-item-title>Logout</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
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

    <!-- Footer (only when authenticated) -->
    <AppFooter v-if="authStore.isAuthenticated" />

    <!-- Update Banner (only for admins) -->
    <UpdateBanner v-if="authStore.isAuthenticated" />
  </v-app>
</template>

<script lang="ts" setup>
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useTheme } from 'vuetify';
import { useAppStore } from '@/stores/app';
import { useAuthStore } from '@/stores/auth';
import { useClientsStore } from '@/stores/clients';
import { useSettingsStore } from '@/stores/settings';
import NavigationRail from '@/components/NavigationRail.vue';
import ClientSwitcher from '@/components/ClientSwitcher.vue';
import AppFooter from '@/components/AppFooter.vue';
import UpdateBanner from '@/components/UpdateBanner.vue';
import { useUpdateStore } from '@/stores/updates';

const router = useRouter();
const theme = useTheme();
const appStore = useAppStore();
const authStore = useAuthStore();
const clientsStore = useClientsStore();
const settingsStore = useSettingsStore();
const updateStore = useUpdateStore();

// Computed
const userInitials = computed(() => {
  const name = authStore.userName || '';
  const parts = name.split(' ').filter(Boolean);
  if (parts.length >= 2) {
    const first = parts[0] ?? '';
    const last = parts[parts.length - 1] ?? '';
    if (first.length > 0 && last.length > 0) {
      return (first.charAt(0) + last.charAt(0)).toUpperCase();
    }
  }
  return name.substring(0, 2).toUpperCase() || '??';
});

// Methods
function toggleTheme() {
  appStore.toggleTheme();
  settingsStore.setTheme(appStore.theme);
  theme.global.name.value = appStore.theme;
}

async function handleLogout() {
  // Disconnect from any active client
  if (clientsStore.isConnected) {
    clientsStore.disconnectFromClient();
  }
  // Reset settings (clears localStorage so next user gets fresh settings)
  settingsStore.reset();
  // Logout from auth
  await authStore.logout();
  // Navigate to login
  router.push('/login');
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
  // Wait for auth initialization to complete before making API calls
  // The router guard handles initialization, but we need to wait for it
  if (!authStore.isInitialized) {
    // Wait for initialization (router guard will trigger it)
    await new Promise<void>((resolve) => {
      const checkInit = () => {
        if (authStore.isInitialized) {
          resolve();
        } else {
          setTimeout(checkInit, 50);
        }
      };
      checkInit();
    });
  }

  // Only proceed with API calls if authenticated (after initialization is complete)
  if (authStore.isAuthenticated) {
    // Load full settings from backend (login page may have already done this)
    await settingsStore.loadSettings();

    // Apply theme from user's settings
    appStore.setTheme(settingsStore.theme);
    theme.global.name.value = settingsStore.theme;

    // Load clients
    await clientsStore.loadClients();

    // Attempt auto-connect if configured
    await handleAutoConnect();

    // Initialize update store (checks for updates if admin)
    if (authStore.isAdmin) {
      updateStore.initialize();
    }
  } else {
    // Not authenticated - apply default dark theme
    appStore.setTheme('dark');
    theme.global.name.value = 'dark';
  }
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
