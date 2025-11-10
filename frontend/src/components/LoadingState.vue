<template>
  <div :class="['loading-state', `loading-state--${size}`, { 'loading-state--fullscreen': fullscreen }]">
    <div v-if="type === 'spinner'" class="loading-spinner">
      <div class="spinner-gradient"></div>
      <v-icon v-if="icon" :size="iconSize" class="spinner-icon">
        {{ icon }}
      </v-icon>
    </div>

    <div v-else-if="type === 'skeleton'" class="loading-skeleton">
      <slot name="skeleton">
        <!-- Default skeleton loader -->
        <div v-for="n in skeletonCount" :key="n" class="skeleton-item gradient-shimmer">
          <div class="skeleton-line" :style="{ width: getSkeletonWidth(n) }"></div>
        </div>
      </slot>
    </div>

    <div v-else-if="type === 'card'" class="loading-cards">
      <v-row>
        <v-col v-for="n in cardCount" :key="n" :cols="cardCols" :sm="cardSm" :md="cardMd" :lg="cardLg">
          <v-card class="loading-card gradient-shimmer">
            <v-card-title>
              <div class="skeleton-line" style="width: 60%; height: 20px;"></div>
            </v-card-title>
            <v-card-text>
              <div class="skeleton-line mb-2" style="width: 100%; height: 14px;"></div>
              <div class="skeleton-line mb-2" style="width: 80%; height: 14px;"></div>
              <div class="skeleton-line" style="width: 40%; height: 14px;"></div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <div v-else-if="type === 'table'" class="loading-table">
      <v-skeleton-loader
        :type="tableType"
        :loading="true"
        class="gradient-shimmer"
      ></v-skeleton-loader>
    </div>

    <div v-if="message" class="loading-message">
      <span class="gradient-text-primary">{{ message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  type?: 'spinner' | 'skeleton' | 'card' | 'table';
  size?: 'small' | 'medium' | 'large';
  fullscreen?: boolean;
  message?: string;
  icon?: string;
  skeletonCount?: number;
  cardCount?: number;
  cardCols?: number | string;
  cardSm?: number | string;
  cardMd?: number | string;
  cardLg?: number | string;
  tableType?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'spinner',
  size: 'medium',
  fullscreen: false,
  skeletonCount: 5,
  cardCount: 6,
  cardCols: 12,
  cardSm: 6,
  cardMd: 4,
  cardLg: 3,
  tableType: 'table-tbody',
});

const iconSize = computed(() => {
  switch (props.size) {
    case 'small':
      return 24;
    case 'large':
      return 64;
    default:
      return 40;
  }
});

function getSkeletonWidth(index: number): string {
  const widths = ['100%', '90%', '75%', '85%', '95%'];
  return widths[(index - 1) % widths.length] || '100%';
}
</script>

<style scoped lang="scss">
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  width: 100%;

  &--fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
    background: rgba(var(--v-theme-background), 0.95);
    backdrop-filter: blur(8px);
  }

  &--small {
    padding: 1rem;
  }

  &--large {
    padding: 3rem;
    min-height: 400px;
  }
}

.loading-spinner {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;

  .spinner-gradient {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
    animation: pulse-glow 2s ease-in-out infinite;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      top: 4px;
      left: 4px;
      right: 4px;
      bottom: 4px;
      border-radius: 50%;
      background: rgb(var(--v-theme-surface));
    }

    &::after {
      content: '';
      position: absolute;
      inset: -4px;
      border-radius: 50%;
      background: linear-gradient(135deg, #6366F1, #8B5CF6, #EC4899);
      filter: blur(12px);
      opacity: 0.6;
      animation: spin 3s linear infinite;
    }
  }

  .spinner-icon {
    position: absolute;
    z-index: 1;
    color: rgb(var(--v-theme-primary));
    animation: pulse 2s ease-in-out infinite;
  }
}

.loading-state--small .loading-spinner .spinner-gradient {
  width: 40px;
  height: 40px;

  &::before {
    top: 3px;
    left: 3px;
    right: 3px;
    bottom: 3px;
  }
}

.loading-state--large .loading-spinner .spinner-gradient {
  width: 96px;
  height: 96px;

  &::before {
    top: 6px;
    left: 6px;
    right: 6px;
    bottom: 6px;
  }
}

.loading-skeleton {
  width: 100%;
  max-width: 600px;
}

.skeleton-item {
  margin-bottom: 1rem;
}

.skeleton-line {
  height: 16px;
  background: linear-gradient(
    90deg,
    rgb(var(--v-theme-surface-variant)) 0%,
    rgb(var(--v-theme-surface-bright)) 50%,
    rgb(var(--v-theme-surface-variant)) 100%
  );
  background-size: 200% 100%;
  border-radius: 8px;
  animation: shimmer 2s infinite;
}

.loading-cards {
  width: 100%;
}

.loading-card {
  opacity: 0.7;

  .skeleton-line {
    background: linear-gradient(
      90deg,
      rgba(var(--v-theme-primary), 0.1) 0%,
      rgba(var(--v-theme-secondary), 0.1) 50%,
      rgba(var(--v-theme-primary), 0.1) 100%
    );
    background-size: 200% 100%;
  }
}

.loading-table {
  width: 100%;
}

.loading-message {
  margin-top: 1.5rem;
  font-weight: 500;
  font-size: 0.875rem;
  text-align: center;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(0.95);
  }
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>
