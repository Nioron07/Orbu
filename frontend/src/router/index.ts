/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */

// Composables
import { createRouter, createWebHistory } from 'vue-router'
import { setupLayouts } from 'virtual:generated-layouts'
import { routes } from 'vue-router/auto-routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: setupLayouts(routes),
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  // Import auth store dynamically to avoid circular dependencies
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()

  // Initialize auth state if not already done
  if (!authStore.isInitialized && !authStore.isLoading) {
    await authStore.initialize()
  }

  // Wait for initialization to complete if in progress
  while (authStore.isLoading && !authStore.isInitialized) {
    await new Promise(resolve => setTimeout(resolve, 50))
  }

  // Public routes that don't require authentication
  const publicRoutes = ['/login', '/register']
  const isPublicRoute = publicRoutes.includes(to.path)

  // Admin-only routes
  const adminRoutes = ['/admin/users']
  const isAdminRoute = adminRoutes.some(route => to.path.startsWith(route))

  if (isPublicRoute) {
    // If already logged in, redirect to home
    if (authStore.isAuthenticated) {
      next('/')
    } else {
      next()
    }
  } else if (!authStore.isAuthenticated) {
    // Not logged in, redirect to login
    // Only add redirect query if not already going to login
    if (to.path !== '/login') {
      next({ path: '/login', query: { redirect: to.fullPath }, replace: true })
    } else {
      next()
    }
  } else if (isAdminRoute && !authStore.isAdmin) {
    // Not admin, redirect to home
    next('/')
  } else {
    next()
  }
})

// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (localStorage.getItem('vuetify:dynamic-reload')) {
      console.error('Dynamic import error, reloading page did not fix it', err)
    } else {
      console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})

export default router
