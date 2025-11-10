// Utilities
import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    theme: 'dark' as 'light' | 'dark',
  }),
  actions: {
    setTheme(theme: 'light' | 'dark') {
      this.theme = theme;
      localStorage.setItem('theme', theme);
    },
  },
})
