<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon start>mdi-account-group</v-icon>
            User Management
            <v-spacer />
            <v-btn-toggle v-model="statusFilter" mandatory variant="outlined" density="compact">
              <v-btn value="all">All</v-btn>
              <v-btn value="pending">
                Pending
                <v-badge v-if="pendingCount > 0" :content="pendingCount" color="warning" inline />
              </v-btn>
              <v-btn value="approved">Approved</v-btn>
              <v-btn value="deactivated">Deactivated</v-btn>
            </v-btn-toggle>
          </v-card-title>

          <v-card-text>
            <v-alert
              v-if="error"
              type="error"
              variant="tonal"
              class="mb-4"
              closable
              @click:close="error = ''"
            >
              {{ error }}
            </v-alert>

            <v-data-table
              :headers="headers"
              :items="filteredUsers"
              :loading="loading"
              class="elevation-1"
            >
              <template #item.is_admin="{ item }">
                <v-chip
                  v-if="item.is_admin"
                  color="primary"
                  size="small"
                >
                  Admin
                </v-chip>
              </template>

              <template #item.status="{ item }">
                <v-chip
                  :color="getStatusColor(item)"
                  size="small"
                >
                  {{ getStatusText(item) }}
                </v-chip>
              </template>

              <template #item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>

              <template #item.last_login_at="{ item }">
                {{ item.last_login_at ? formatDate(item.last_login_at) : 'Never' }}
              </template>

              <template #item.actions="{ item }">
                <!-- Pending user actions -->
                <template v-if="!item.is_approved">
                  <v-btn
                    icon
                    variant="text"
                    color="success"
                    size="small"
                    title="Approve"
                    @click="approveUser(item)"
                  >
                    <v-icon>mdi-check</v-icon>
                  </v-btn>
                  <v-btn
                    icon
                    variant="text"
                    color="error"
                    size="small"
                    title="Deny"
                    @click="denyUser(item)"
                  >
                    <v-icon>mdi-close</v-icon>
                  </v-btn>
                </template>

                <!-- Approved user actions -->
                <template v-else>
                  <v-menu>
                    <template #activator="{ props }">
                      <v-btn
                        icon
                        variant="text"
                        size="small"
                        v-bind="props"
                      >
                        <v-icon>mdi-dots-vertical</v-icon>
                      </v-btn>
                    </template>
                    <v-list density="compact">
                      <v-list-item
                        v-if="!item.is_admin"
                        prepend-icon="mdi-shield-account"
                        @click="makeAdmin(item)"
                      >
                        <v-list-item-title>Make Admin</v-list-item-title>
                      </v-list-item>
                      <v-list-item
                        v-else-if="item.id !== currentUser?.id"
                        prepend-icon="mdi-shield-off"
                        @click="removeAdmin(item)"
                      >
                        <v-list-item-title>Remove Admin</v-list-item-title>
                      </v-list-item>
                      <v-list-item
                        v-if="item.is_active && item.id !== currentUser?.id"
                        prepend-icon="mdi-account-off"
                        @click="deactivateUser(item)"
                      >
                        <v-list-item-title>Deactivate</v-list-item-title>
                      </v-list-item>
                      <v-list-item
                        v-else-if="!item.is_active"
                        prepend-icon="mdi-account-check"
                        @click="activateUser(item)"
                      >
                        <v-list-item-title>Activate</v-list-item-title>
                      </v-list-item>
                      <v-divider v-if="item.id !== currentUser?.id" />
                      <v-list-item
                        v-if="item.id !== currentUser?.id"
                        prepend-icon="mdi-delete"
                        class="text-error"
                        @click="confirmDeleteUser(item)"
                      >
                        <v-list-item-title>Delete</v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </template>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete User</v-card-title>
        <v-card-text>
          Are you sure you want to delete <strong>{{ userToDelete?.name }}</strong> ({{ userToDelete?.email }})?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" variant="elevated" @click="deleteUser">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { authApi, type User } from '@/services/authApi'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

const users = ref<User[]>([])
const loading = ref(false)
const error = ref('')
const statusFilter = ref('all')
const deleteDialog = ref(false)
const userToDelete = ref<User | null>(null)

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Email', key: 'email' },
  { title: 'Role', key: 'is_admin', sortable: false },
  { title: 'Status', key: 'status', sortable: false },
  { title: 'Created', key: 'created_at' },
  { title: 'Last Login', key: 'last_login_at' },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' as const },
]

const pendingCount = computed(() =>
  users.value.filter(u => !u.is_approved).length
)

const filteredUsers = computed(() => {
  switch (statusFilter.value) {
    case 'pending':
      return users.value.filter(u => !u.is_approved)
    case 'approved':
      return users.value.filter(u => u.is_approved && u.is_active)
    case 'deactivated':
      return users.value.filter(u => !u.is_active)
    default:
      return users.value
  }
})

function getStatusColor(user: User): string {
  if (!user.is_approved) return 'warning'
  if (!user.is_active) return 'error'
  return 'success'
}

function getStatusText(user: User): string {
  if (!user.is_approved) return 'Pending'
  if (!user.is_active) return 'Deactivated'
  return 'Active'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    const response = await authApi.listUsers()
    users.value = response.users
  } catch (e: any) {
    error.value = e.message || 'Failed to load users'
  } finally {
    loading.value = false
  }
}

async function approveUser(user: User) {
  try {
    await authApi.approveUser(user.id)
    await loadUsers()
  } catch (e: any) {
    error.value = e.message || 'Failed to approve user'
  }
}

async function denyUser(user: User) {
  try {
    await authApi.denyUser(user.id)
    await loadUsers()
  } catch (e: any) {
    error.value = e.message || 'Failed to deny user'
  }
}

async function makeAdmin(user: User) {
  try {
    await authApi.updateUser(user.id, { is_admin: true })
    await loadUsers()
  } catch (e: any) {
    error.value = e.message || 'Failed to update user'
  }
}

async function removeAdmin(user: User) {
  try {
    await authApi.updateUser(user.id, { is_admin: false })
    await loadUsers()
  } catch (e: any) {
    error.value = e.message || 'Failed to update user'
  }
}

async function deactivateUser(user: User) {
  try {
    await authApi.updateUser(user.id, { is_active: false })
    await loadUsers()
  } catch (e: any) {
    error.value = e.message || 'Failed to deactivate user'
  }
}

async function activateUser(user: User) {
  try {
    await authApi.updateUser(user.id, { is_active: true })
    await loadUsers()
  } catch (e: any) {
    error.value = e.message || 'Failed to activate user'
  }
}

function confirmDeleteUser(user: User) {
  userToDelete.value = user
  deleteDialog.value = true
}

async function deleteUser() {
  if (!userToDelete.value) return
  try {
    await authApi.deleteUser(userToDelete.value.id)
    deleteDialog.value = false
    userToDelete.value = null
    await loadUsers()
  } catch (e: any) {
    error.value = e.message || 'Failed to delete user'
  }
}

onMounted(() => {
  loadUsers()
})
</script>
