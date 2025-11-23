<template>
  <v-navigation-drawer rail expand-on-hover permanent class="navigation-rail gradient-sidebar">
    <!-- Logo Section -->
    <v-list>
      <v-list-item>
        <v-avatar>
      <v-img
        src="..\assets\Orbu_Small_Transparent_Logo.png"
      ></v-img></v-avatar>
      </v-list-item>
    </v-list>
    <v-divider class="my-2"></v-divider>

    <!-- Navigation Items -->
    <v-list density="compact" nav class="navigation-rail__list">
      <v-list-item v-for="item in navigationItems" :key="item.path" :to="item.path" class="navigation-item"
        rounded="lg">
        <template v-slot:prepend>
          <v-icon :icon="item.icon"></v-icon>
        </template>
        <v-list-item-title>{{ item.title }}</v-list-item-title>
      </v-list-item>
    </v-list>

    <!-- Bottom Section -->
    <template v-slot:append>
      <v-divider class="mb-2"></v-divider>

      <v-list density="compact" nav class="navigation-rail__list">
        <!-- Settings -->
        <v-list-item to="/settings" class="navigation-item" rounded="lg">
          <template v-slot:prepend>
            <v-icon icon="mdi-cog"></v-icon>
          </template>
          <v-list-item-title>Settings</v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue';
interface NavigationItem {
  title: string;
  icon: string;
  path: string;
}

const navigationItems = computed<NavigationItem[]>(() => [
  {
    title: 'Dashboard',
    icon: 'mdi-view-dashboard',
    path: '/',
  },
  {
    title: 'Clients',
    icon: 'mdi-domain',
    path: '/clients',
  },
  {
    title: 'Endpoints',
    icon: 'mdi-api',
    path: '/endpoints',
  },
  {
    title: 'Services',
    icon: 'mdi-cogs',
    path: '/servicebrowser',
  },
  {
    title: 'Models',
    icon: 'mdi-database',
    path: '/modelbrowser',
  },
]);
</script>

<style scoped lang="scss">
.navigation-rail {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)) !important;

  &::v-deep(.v-navigation-drawer__content) {
    display: flex;
    flex-direction: column;
  }
}

.navigation-rail__list {
  padding: 0 0.5rem;
}

.navigation-item {
  margin-bottom: 0.25rem;
  transition: all 0.2s ease;

  &:not(.v-list-item--disabled):hover {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.12) 100%);
  }

  &.v-list-item--active {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);

    &::before {
      opacity: 0;
    }

    .v-theme--dark & {
      background: linear-gradient(135deg, rgba(129, 140, 248, 0.2) 0%, rgba(167, 139, 250, 0.2) 100%);
    }
  }

  &.v-list-item--disabled {
    opacity: 0.5;
  }
}

// Logo section styling
.logo-section {
  display: flex;
  align-items: center;
  padding: 12px !important;
  min-height: 72px;
}

.nav-logo {
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  padding: 6px;

  .v-theme--dark & {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
  }
}

.logo-text {
  font-size: 1.1rem;
  font-weight: 600;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s ease;
}

// Show logo text on hover
.navigation-rail:hover .logo-text {
  opacity: 1;
}

// Fade transition for logo text
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
