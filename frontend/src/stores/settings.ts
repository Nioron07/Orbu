import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export type AutoConnectMode = 'manual' | 'last' | 'default';

export interface SettingsState {
  autoConnectMode: AutoConnectMode;
  defaultClientId: string | null;
  lastConnectedClientId: string | null;
}

export const useSettingsStore = defineStore('settings', () => {
  // State
  const autoConnectMode = ref<AutoConnectMode>('manual');
  const defaultClientId = ref<string | null>(null);
  const lastConnectedClientId = ref<string | null>(null);

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
  function loadSettings() {
    try {
      const saved = localStorage.getItem('acunexus_settings');
      if (saved) {
        const settings: SettingsState = JSON.parse(saved);
        autoConnectMode.value = settings.autoConnectMode || 'manual';
        defaultClientId.value = settings.defaultClientId || null;
        lastConnectedClientId.value = settings.lastConnectedClientId || null;
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  }

  function saveSettings() {
    try {
      const settings: SettingsState = {
        autoConnectMode: autoConnectMode.value,
        defaultClientId: defaultClientId.value,
        lastConnectedClientId: lastConnectedClientId.value,
      };
      localStorage.setItem('acunexus_settings', JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save settings:', error);
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

  function resetToManual() {
    autoConnectMode.value = 'manual';
    saveSettings();
  }

  return {
    // State
    autoConnectMode,
    defaultClientId,
    lastConnectedClientId,

    // Computed
    shouldAutoConnect,
    autoConnectClientId,

    // Actions
    loadSettings,
    saveSettings,
    setAutoConnectMode,
    setDefaultClientId,
    setLastConnectedClientId,
    resetToManual,
  };
});
