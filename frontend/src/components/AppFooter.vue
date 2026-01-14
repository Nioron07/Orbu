<template>
  <v-footer
    app
    height="56"
    class="gradient-app-bar"
  >
    <v-container fluid class="px-6">
      <v-row align="center" justify="space-between" no-gutters>
        <!-- Left: App Name and Version -->
        <v-col cols="auto">
          <div class="d-flex align-center gap-2">
            <span class="text-subtitle-2 font-weight-bold mr-1">Orbu</span>
            <v-chip size="x-small" variant="tonal" color="primary">v{{ displayVersion }}</v-chip>
          </div>
        </v-col>

        <!-- Center: Links and Info -->
        <v-col cols="auto">
          <div class="d-flex align-center gap-4">
            <!-- GitHub Repo -->
            <v-btn
              href="https://github.com/Nioron07/Orbu"
              target="_blank"
              variant="text"
              size="small"
              prepend-icon="mdi-github"
              class="text-caption"
            >
              GitHub
            </v-btn>

            <v-divider vertical thickness="2" class="my-2" />

            <!-- Powered by Easy-Acumatica -->
            <div class="d-flex align-center gap-1 text-caption">
              <span>Powered by</span>
              <v-btn
                href="https://github.com/Nioron07/Easy-Acumatica"
                target="_blank"
                variant="text"
                size="small"
                class="text-caption font-weight-medium px-1"
              >
                Easy-Acumatica
              </v-btn>
            </div>

            <v-divider vertical thickness="2" class="my-2" />

            <!-- License -->
            <v-btn
              href="https://github.com/Nioron07/Orbu/blob/main/LICENSE"
              target="_blank"
              variant="text"
              size="small"
              prepend-icon="mdi-scale-balance"
              class="text-caption"
            >
              GNU AGPL v3.0
            </v-btn>
          </div>
        </v-col>

        <!-- Right: Report Issue -->
        <v-col cols="auto">
          <v-btn
            href="https://github.com/Nioron07/Orbu/issues/new"
            target="_blank"
            variant="tonal"
            size="small"
            prepend-icon="mdi-bug"
            color="primary"
          >
            Report Issue
          </v-btn>
        </v-col>
      </v-row>
    </v-container>
  </v-footer>
</template>

<script setup lang="ts">
// Version is injected at build time from the VERSION file via vite.config.mts
declare const __APP_VERSION__: string

const displayVersion = __APP_VERSION__
</script>

<style scoped lang="scss">
.v-footer {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)) !important;

  a {
    transition: opacity 0.2s ease;

    &:hover {
      opacity: 0.8;
    }
  }
}
</style>
