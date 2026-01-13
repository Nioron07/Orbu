import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useAuthStore } from './auth';

export type AutoConnectMode = 'manual' | 'last' | 'default';

export interface SettingsState {
  autoConnectMode: AutoConnectMode;
  defaultClientId: string | null;
  lastConnectedClientId: string | null;
  theme: 'light' | 'dark';
}

export const useSettingsStore = defineStore('settings', () => {
  // State
  const autoConnectMode = ref<AutoConnectMode>('manual');
  const defaultClientId = ref<string | null>(null);
  const lastConnectedClientId = ref<string | null>(null);
  const theme = ref<'light' | 'dark'>('dark');
  const isLoading = ref(false);
  const isInitialized = ref(false);

  // Computed
  const shouldAutoConnect = computed(() => autoConnectMode.value !== 'manual');

  const autoConnectClientId = computed(() => {
    if (autoConnectMode.value === 'default') {
      return defaultClientId.value;
    } else if (autoConnectMode.value === 'last') {
      return lastConnectedClientId.value;
    }
    return null;
  });

  // Actions

  /**
   * Load settings from backend (if authenticated) or localStorage
   * @param forceReload - If true, reload even if already initialized (used after login)
   */
  async function loadSettings(forceReload = false) {
    // Skip if already initialized and not forcing reload
    if (isInitialized.value && !forceReload) {
      console.log('[Settings] Already initialized, skipping load');
      return;
    }

    try {
      const authStore = useAuthStore();

      console.log('[Settings] loadSettings called, forceReload:', forceReload);
      console.log('[Settings] isAuthenticated:', authStore.isAuthenticated);
      console.log('[Settings] user:', authStore.user);
      console.log('[Settings] user.settings:', authStore.user?.settings);

      // If authenticated, sync with backend (backend is source of truth)
      if (authStore.isAuthenticated && authStore.user?.settings) {
        const userSettings = authStore.user.settings;

        console.log('[Settings] Applying user settings from backend:', userSettings);

        // Apply user settings from backend (these override any localStorage values)
        autoConnectMode.value = userSettings.autoConnectMode || 'manual';
        defaultClientId.value = userSettings.defaultClientId ?? null;
        lastConnectedClientId.value = userSettings.lastConnectedClientId ?? null;
        theme.value = userSettings.theme || 'dark';

        console.log('[Settings] Applied theme:', theme.value);
      } else {
        // Not authenticated or no user settings, load from localStorage as fallback
        console.log('[Settings] No user settings, falling back to localStorage');
        loadFromLocalStorage();
      }
    } catch (error) {
      console.warn('Failed to load settings from backend:', error);
      // Fallback to localStorage
      loadFromLocalStorage();
    }

    isInitialized.value = true;
  }

  /**
   * Load settings from localStorage only
   */
  function loadFromLocalStorage() {
    try {
      const saved = localStorage.getItem('orbu_settings');
      if (saved) {
        const settings: SettingsState = JSON.parse(saved);
        autoConnectMode.value = settings.autoConnectMode || 'manual';
        defaultClientId.value = settings.defaultClientId || null;
        lastConnectedClientId.value = settings.lastConnectedClientId || null;
        theme.value = settings.theme || 'dark';
      }
    } catch (error) {
      console.error('Failed to load settings from localStorage:', error);
    }
  }

  /**
   * Save settings to backend (if authenticated) and localStorage
   */
  async function saveSettings() {
    console.log('[Settings] saveSettings called, isInitialized:', isInitialized.value);

    // Don't save if we're in the middle of a reset/logout
    if (!isInitialized.value) {
      console.log('[Settings] Not initialized, skipping save');
      return;
    }

    // Always save to localStorage as backup
    saveToLocalStorage();
    console.log('[Settings] Saved to localStorage');

    // If authenticated, also save to backend
    const authStore = useAuthStore();
    console.log('[Settings] isAuthenticated:', authStore.isAuthenticated);

    if (authStore.isAuthenticated) {
      try {
        const settingsToSave = {
          autoConnectMode: autoConnectMode.value,
          defaultClientId: defaultClientId.value,
          lastConnectedClientId: lastConnectedClientId.value,
          theme: theme.value,
        };
        console.log('[Settings] Saving to backend:', settingsToSave);
        await authStore.updateSettings(settingsToSave);
        console.log('[Settings] Backend save successful');
      } catch (error) {
        console.error('[Settings] Failed to save settings to backend:', error);
      }
    }
  }

  /**
   * Save settings to localStorage only
   */
  function saveToLocalStorage() {
    try {
      const settings: SettingsState = {
        autoConnectMode: autoConnectMode.value,
        defaultClientId: defaultClientId.value,
        lastConnectedClientId: lastConnectedClientId.value,
        theme: theme.value,
      };
      localStorage.setItem('orbu_settings', JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save settings to localStorage:', error);
    }
  }

  function setAutoConnectMode(mode: AutoConnectMode) {
    autoConnectMode.value = mode;
    saveSettings();
  }

  function setDefaultClientId(clientId: string | null) {
    defaultClientId.value = clientId;
    saveSettings();
  }

  function setLastConnectedClientId(clientId: string | null) {
    lastConnectedClientId.value = clientId;
    saveSettings();
  }

  function setTheme(newTheme: 'light' | 'dark') {
    console.log('[Settings] setTheme called with:', newTheme);
    theme.value = newTheme;
    saveSettings();
  }

  function resetToManual() {
    autoConnectMode.value = 'manual';
    saveSettings();
  }

  /**
   * Reset state when user logs out - clears localStorage and resets to defaults
   * Does NOT save to backend (user is logging out)
   */
  function reset() {
    // Mark as not initialized FIRST to prevent any saveSettings calls
    isInitialized.value = false;

    // Clear localStorage (both the settings key and legacy theme key)
    localStorage.removeItem('orbu_settings');
    localStorage.removeItem('orbu_theme'); // Legacy key from appStore

    // Reset to defaults (saveSettings will bail out since isInitialized is false)
    autoConnectMode.value = 'manual';
    defaultClientId.value = null;
    lastConnectedClientId.value = null;
    theme.value = 'dark';
  }

  return {
    // State
    autoConnectMode,
    defaultClientId,
    lastConnectedClientId,
    theme,
    isLoading,
    isInitialized,

    // Computed
    shouldAutoConnect,
    autoConnectClientId,

    // Actions
    loadSettings,
    loadFromLocalStorage,
    saveSettings,
    saveToLocalStorage,
    setAutoConnectMode,
    setDefaultClientId,
    setLastConnectedClientId,
    setTheme,
    resetToManual,
    reset,
  };
});
