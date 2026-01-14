<template>
  <v-banner
    v-if="showBanner"
    color="info"
    icon="mdi-update"
    lines="one"
    class="update-banner"
    stacked
  >
    <template #text>
      <span class="text-body-2">
        A new version <strong>v{{ updateStore.latestVersion }}</strong> is available!
        <span v-if="updateStore.releaseNotes" class="text-caption ml-2 text-medium-emphasis">
          {{ truncatedNotes }}
        </span>
      </span>
    </template>
    <template #actions>
      <v-btn
        variant="text"
        size="small"
        @click="updateStore.dismiss()"
      >
        Dismiss
      </v-btn>
      <v-btn
        v-if="updateStore.canAutoUpdate"
        color="primary"
        variant="flat"
        size="small"
        :loading="updateStore.isDeploying"
        prepend-icon="mdi-download"
        @click="handleDeploy"
      >
        Update Now
      </v-btn>
      <v-btn
        v-else
        color="primary"
        variant="flat"
        size="small"
        :href="updateStore.releaseUrl || undefined"
        target="_blank"
        prepend-icon="mdi-open-in-new"
      >
        View Release
      </v-btn>
    </template>
  </v-banner>

  <!-- Deployment confirmation dialog -->
  <v-dialog v-model="showConfirmDialog" max-width="500">
    <v-card>
      <v-card-title class="text-h6">
        Update to v{{ updateStore.latestVersion }}?
      </v-card-title>
      <v-card-text>
        <p>This will update Orbu to the latest version. The application will restart and you may be briefly logged out.</p>
        <v-alert
          v-if="updateStore.releaseNotes"
          type="info"
          variant="tonal"
          class="mt-3"
        >
          <div class="text-subtitle-2 mb-1">Release Notes:</div>
          <div class="text-body-2" style="white-space: pre-wrap;">{{ updateStore.releaseNotes }}</div>
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          @click="showConfirmDialog = false"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="updateStore.isDeploying"
          @click="confirmDeploy"
        >
          Update Now
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Deployment in progress dialog -->
  <v-dialog v-model="showDeployingDialog" persistent max-width="400">
    <v-card>
      <v-card-title class="text-h6">
        Updating Orbu...
      </v-card-title>
      <v-card-text>
        <div class="d-flex align-center mb-4">
          <v-progress-circular indeterminate color="primary" class="mr-3" />
          <span>Deploying new version. This may take a few minutes.</span>
        </div>
        <v-alert type="info" variant="tonal">
          The page will automatically reload when the update is complete.
        </v-alert>
      </v-card-text>
    </v-card>
  </v-dialog>

  <!-- Error snackbar -->
  <v-snackbar
    v-model="showError"
    color="error"
    :timeout="5000"
  >
    {{ updateStore.error }}
    <template #actions>
      <v-btn variant="text" @click="showError = false">Close</v-btn>
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useUpdateStore } from '@/stores/updates'
import { useAuthStore } from '@/stores/auth'

const updateStore = useUpdateStore()
const authStore = useAuthStore()

const showConfirmDialog = ref(false)
const showDeployingDialog = ref(false)
const showError = ref(false)

// Only show banner to admins when update is available and not dismissed
const showBanner = computed(() => {
  return updateStore.updateAvailable &&
         authStore.isAdmin &&
         !updateStore.isDismissed
})

// Truncate release notes for banner display
const truncatedNotes = computed(() => {
  const notes = updateStore.releaseNotes || ''
  const firstLine = notes.split('\n')[0]
  return firstLine.length > 80 ? firstLine.substring(0, 77) + '...' : firstLine
})

// Watch for errors
watch(() => updateStore.error, (error) => {
  if (error) {
    showError.value = true
    showDeployingDialog.value = false
  }
})

function handleDeploy() {
  showConfirmDialog.value = true
}

async function confirmDeploy() {
  showConfirmDialog.value = false
  showDeployingDialog.value = true

  const success = await updateStore.deploy()

  if (success) {
    // Start polling for service restart
    startRestartPolling()
  } else {
    showDeployingDialog.value = false
  }
}

function startRestartPolling() {
  // Poll every 5 seconds to check if the service has restarted
  const pollInterval = setInterval(async () => {
    try {
      const response = await fetch('/api/health')
      if (response.ok) {
        // Service is back up, reload the page
        clearInterval(pollInterval)
        window.location.reload()
      }
    } catch {
      // Service is still restarting, continue polling
    }
  }, 5000)

  // Stop polling after 5 minutes
  setTimeout(() => {
    clearInterval(pollInterval)
    showDeployingDialog.value = false
    updateStore.error = 'Update is taking longer than expected. Please refresh the page manually.'
    showError.value = true
  }, 5 * 60 * 1000)
}
</script>

<style scoped>
.update-banner {
  position: fixed;
  top: 64px; /* Below the app bar */
  left: 0;
  right: 0;
  z-index: 100;
}
</style>
