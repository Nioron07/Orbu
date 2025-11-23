<template>
  <v-container class="dashboard-container">
    <!-- Hero Section -->
    <v-row>
      <v-col cols="12">
        <div class="hero-section gradient-bg-subtle">
          <div class="hero-content">
            <h1 class="text-h3 font-weight-bold mb-4">
              Welcome to <span class="gradient-text-primary">Orbu</span>
            </h1>
            <p class="text-h6 mb-6" style="opacity: 0.9;">
              Browse and explore your Acumatica REST API endpoints with an intuitive GUI
            </p>

            <!-- Connection Status Alert -->
            <v-alert
              v-if="!clientsStore.isConnected"
              type="info"
              variant="tonal"
              class="status-alert mx-auto"
              max-width="600"
            >
              Get started by connecting to your Acumatica instance
            </v-alert>

            <v-alert
              v-else
              type="success"
              variant="tonal"
              class="status-alert mx-auto gradient-card-hover"
              max-width="600"
            >
              Connected to <strong>{{ clientsStore.activeClient?.name || 'Acumatica' }}</strong>
            </v-alert>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Quick Actions -->
    <v-row class="my-8">
      <v-col cols="12" sm="6" md="4">
        <v-card
          class="action-card gradient-card-hover"
          hover
          @click="router.push('/clients')"
        >
          <div class="action-card__icon-bg gradient-primary"></div>
          <v-card-text class="text-center pa-6 position-relative">
            <v-icon size="64" color="primary" class="mb-4">mdi-domain</v-icon>
            <h3 class="text-h6 font-weight-semibold mb-2">
              {{ clientsStore.isConnected ? 'Manage Clients' : 'Connect to Client' }}
            </h3>
            <p class="text-body-2" style="opacity: 0.7;">
              Configure and manage your Acumatica connections
            </p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="4">
        <v-card
          class="action-card gradient-card-hover"
          hover
          :disabled="!clientsStore.isConnected"
          @click="clientsStore.isConnected && router.push('/servicebrowser')"
        >
          <div class="action-card__icon-bg gradient-accent"></div>
          <v-card-text class="text-center pa-6 position-relative">
            <v-icon size="64" :color="clientsStore.isConnected ? 'secondary' : 'grey'" class="mb-4">
              mdi-api
            </v-icon>
            <h3 class="text-h6 font-weight-semibold mb-2">Browse Services</h3>
            <p class="text-body-2" style="opacity: 0.7;">
              Explore available API services and methods
            </p>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="4">
        <v-card
          class="action-card gradient-card-hover"
          hover
          :disabled="!clientsStore.isConnected"
          @click="clientsStore.isConnected && router.push('/modelbrowser')"
        >
          <div class="action-card__icon-bg gradient-cyan"></div>
          <v-card-text class="text-center pa-6 position-relative">
            <v-icon size="64" :color="clientsStore.isConnected ? 'accent' : 'grey'" class="mb-4">
              mdi-database
            </v-icon>
            <h3 class="text-h6 font-weight-semibold mb-2">Browse Models</h3>
            <p class="text-body-2" style="opacity: 0.7;">
              View data models, fields, and schemas
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useClientsStore } from '@/stores/clients';

const router = useRouter();
const clientsStore = useClientsStore();

// Lifecycle
onMounted(() => {
  // Load clients on mount
  clientsStore.loadClients();
});
</script>

<style scoped lang="scss">
.dashboard-container {
  max-width: 1400px;
  padding: 2rem 1rem;
}

.hero-section {
  padding: 4rem 2rem;
  border-radius: 16px;
  text-align: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
    z-index: 0;
  }

  .v-theme--dark & {
    &::before {
      background: linear-gradient(135deg, rgba(129, 140, 248, 0.15) 0%, rgba(167, 139, 250, 0.15) 100%);
    }
  }
}

.hero-content {
  position: relative;
  z-index: 1;
}

.status-alert {
  animation: fade-in 0.5s ease-out;
}

.action-card {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;

  &:not([disabled]) {
    cursor: pointer;

    &:hover {
      transform: translateY(-4px);

      .action-card__icon-bg {
        transform: scale(1.2);
        opacity: 0.2;
      }
    }
  }

  &[disabled] {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.action-card__icon-bg {
  position: absolute;
  top: -50%;
  right: -20%;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  opacity: 0.1;
  transition: all 0.4s ease;
  z-index: 0;
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
