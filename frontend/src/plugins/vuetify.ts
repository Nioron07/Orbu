/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'
import { md3 } from 'vuetify/blueprints'

// Custom theme configuration with blue/purple gradient theme
export default createVuetify({
  blueprint: md3,
  theme: {
    defaultTheme: 'dark',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#6366F1',      // Indigo 500
          secondary: '#8B5CF6',    // Purple 500
          accent: '#06B6D4',       // Cyan 500
          success: '#10B981',      // Emerald 500
          warning: '#F59E0B',      // Amber 500
          error: '#EF4444',        // Red 500
          info: '#3B82F6',         // Blue 500
          background: '#F8FAFC',   // Slate 50
          surface: '#FFFFFF',      // White surface
          'surface-bright': '#FFFFFF',
          'surface-variant': '#F1F5F9',  // Slate 100
          'on-surface': '#0F172A',        // Slate 900
          'on-background': '#1E293B',     // Slate 800
        },
        variables: {
          'border-color': '#000000',
          'border-opacity': 0.12,
          'high-emphasis-opacity': 0.90,
          'medium-emphasis-opacity': 0.60,
          'disabled-opacity': 0.38,
        },
      },
      dark: {
        dark: true,
        colors: {
          primary: '#818CF8',      // Indigo 400
          secondary: '#A78BFA',    // Purple 400
          accent: '#22D3EE',       // Cyan 400
          success: '#34D399',      // Emerald 400
          warning: '#FBBF24',      // Amber 400
          error: '#F87171',        // Red 400
          info: '#60A5FA',         // Blue 400
          background: '#0F172A',   // Slate 900
          surface: '#1E293B',      // Slate 800
          'surface-bright': '#334155',    // Slate 700
          'surface-variant': '#475569',   // Slate 600
          'on-surface': '#F1F5F9',        // Slate 100
          'on-background': '#E2E8F0',     // Slate 200
        },
        variables: {
          'border-color': '#FFFFFF',
          'border-opacity': 0.08,
          'high-emphasis-opacity': 0.90,
          'medium-emphasis-opacity': 0.60,
          'disabled-opacity': 0.38,
        },
      },
    },
    variations: {
      colors: ['primary', 'secondary', 'accent', 'success', 'warning', 'error', 'info'],
      lighten: 5,
      darken: 5,
    },
  },
  defaults: {
    // Global component defaults for consistent styling
    VCard: {
      elevation: 0,
      class: 'glass-card',
    },
    VBtn: {
      elevation: 0,
      rounded: 'lg',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
    VAutocomplete: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
    VTextarea: {
      variant: 'outlined',
      rounded: 'lg',
    },
    VDataTable: {
      class: 'data-table',
    },
    VChip: {
      elevation: 0,
      rounded: 'lg',
    },
    VDialog: {
      elevation: 0,
      scrim: 'black',
      opacity: 0.6,
    },
    VNavigationDrawer: {
      elevation: 0,
    },
    VAppBar: {
      elevation: 0,
    },
  },
})