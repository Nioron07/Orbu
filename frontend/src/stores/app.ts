// Utilities
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    // Theme is managed here for immediate UI updates
    // The settingsStore is the source of truth and persists to backend/localStorage
    theme: 'dark' as 'light' | 'dark',
  }),
  actions: {
    setTheme(theme: 'light' | 'dark') {
      this.theme = theme;
      // Note: Do NOT save to localStorage here - settingsStore handles persistence
    },
    toggleTheme() {
      const newTheme = this.theme === 'dark' ? 'light' : 'dark';
      this.setTheme(newTheme);
    },
  },
})
