<template>
  <v-navigation-drawer
    :model-value="true"
    :rail="rail"
    :expand-on-hover="expandOnHover"
    permanent
    class="navigation-rail gradient-sidebar"
  >
    <!-- Logo Section -->
    <div class="navigation-rail__logo">
      <v-avatar :size="rail ? 40 : 48" class="logo-avatar">
        <v-img src="@/assets/logo.svg" alt="AcuNexus Logo"></v-img>
      </v-avatar>
      <transition name="fade">
        <span v-if="!rail" class="logo-text gradient-text-primary">AcuNexus</span>
      </transition>
    </div>

    <v-divider class="my-2"></v-divider>

    <!-- Navigation Items -->
    <v-list density="compact" nav class="navigation-rail__list">
      <v-list-item
        v-for="item in navigationItems"
        :key="item.path"
        :to="item.path"
        :disabled="item.requiresConnection && !clientsStore.isConnected"
        class="navigation-item"
        rounded="lg"
      >
        <template v-slot:prepend>
          <v-icon :icon="item.icon"></v-icon>
        </template>
        <v-list-item-title>{{ item.title }}</v-list-item-title>

        <template v-if="item.requiresConnection && !clientsStore.isConnected" v-slot:append>
          <v-tooltip location="right">
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" size="small" color="warning">mdi-lock</v-icon>
            </template>
            <span>Connect to a client first</span>
          </v-tooltip>
        </template>
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
import { useClientsStore } from '@/stores/clients';

interface NavigationItem {
  title: string;
  icon: string;
  path: string;
  requiresConnection?: boolean;
}

interface Props {
  rail?: boolean;
  expandOnHover?: boolean;
}

withDefaults(defineProps<Props>(), {
  rail: true,
  expandOnHover: true,
});

const clientsStore = useClientsStore();

const navigationItems = computed<NavigationItem[]>(() => [
  {
    title: 'Dashboard',
    icon: 'mdi-view-dashboard',
    path: '/',
    requiresConnection: false,
  },
  {
    title: 'Clients',
    icon: 'mdi-domain',
    path: '/clients',
    requiresConnection: false,
  },
  {
    title: 'Services',
    icon: 'mdi-api',
    path: '/servicebrowser',
    requiresConnection: true,
  },
  {
    title: 'Models',
    icon: 'mdi-database',
    path: '/modelbrowser',
    requiresConnection: true,
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

.navigation-rail__logo {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem 1rem;
  min-height: 72px;

  .logo-avatar {
    flex-shrink: 0;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    padding: 4px;
  }

  .logo-text {
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    white-space: nowrap;
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
