<template>
  <div :class="['empty-state', `empty-state--${size}`]">
    <div class="empty-state__icon-wrapper">
      <div class="icon-gradient-bg"></div>
      <v-icon :size="iconSize" class="empty-state__icon">
        {{ icon }}
      </v-icon>
    </div>

    <h3 class="empty-state__title">{{ title }}</h3>

    <p v-if="description" class="empty-state__description">
      {{ description }}
    </p>

    <div v-if="$slots.actions || actionText" class="empty-state__actions">
      <slot name="actions">
        <v-btn
          v-if="actionText"
          :color="actionColor"
          :variant="actionVariant"
          size="large"
          @click="handleAction"
        >
          <v-icon v-if="actionIcon" start>{{ actionIcon }}</v-icon>
          {{ actionText }}
        </v-btn>
      </slot>
    </div>

    <div v-if="$slots.secondary" class="empty-state__secondary">
      <slot name="secondary"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  icon: string;
  title: string;
  description?: string;
  size?: 'small' | 'medium' | 'large';
  actionText?: string;
  actionIcon?: string;
  actionColor?: string;
  actionVariant?: 'elevated' | 'flat' | 'tonal' | 'outlined' | 'text' | 'plain';
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  actionColor: 'primary',
  actionVariant: 'elevated',
});

const emit = defineEmits<{
  action: [];
}>();

const iconSize = computed(() => {
  switch (props.size) {
    case 'small':
      return 48;
    case 'large':
      return 96;
    default:
      return 64;
  }
});

function handleAction() {
  emit('action');
}
</script>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem 1.5rem;
  max-width: 600px;
  margin: 0 auto;

  &--small {
    padding: 2rem 1rem;
    max-width: 400px;
  }

  &--large {
    padding: 4rem 2rem;
    max-width: 800px;
  }
}

.empty-state__icon-wrapper {
  position: relative;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;

  .icon-gradient-bg {
    position: absolute;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
    animation: pulse-bg 3s ease-in-out infinite;
    z-index: 0;
  }

  .v-theme--dark & .icon-gradient-bg {
    background: linear-gradient(135deg, rgba(129, 140, 248, 0.2) 0%, rgba(167, 139, 250, 0.2) 100%);
  }
}

.empty-state--small .empty-state__icon-wrapper .icon-gradient-bg {
  width: 80px;
  height: 80px;
}

.empty-state--large .empty-state__icon-wrapper .icon-gradient-bg {
  width: 160px;
  height: 160px;
}

.empty-state__icon {
  position: relative;
  z-index: 1;
  color: rgb(var(--v-theme-primary));
  opacity: 0.9;
}

.empty-state__title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: rgb(var(--v-theme-on-surface));
  letter-spacing: -0.01em;
}

.empty-state--small .empty-state__title {
  font-size: 1.25rem;
}

.empty-state--large .empty-state__title {
  font-size: 2rem;
}

.empty-state__description {
  font-size: 0.938rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 2rem;
  line-height: 1.6;
  max-width: 500px;
}

.empty-state--small .empty-state__description {
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

.empty-state--large .empty-state__description {
  font-size: 1rem;
  margin-bottom: 2.5rem;
}

.empty-state__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: center;
}

.empty-state__secondary {
  margin-top: 1.5rem;
  opacity: 0.7;
}

@keyframes pulse-bg {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}

// Fade-in animation
.empty-state {
  animation: fade-in 0.4s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
