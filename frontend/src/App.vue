<template>
  <v-app>
    <!-- Mobile navigation drawer -->
    <v-navigation-drawer v-model="drawer" temporary>
      <v-list nav>
        <v-list-item :to="{ name: 'analyze' }" title="Analyze" @click="drawer = false" />
        <v-list-item :to="{ name: 'tutorial' }" title="Tutorial" @click="drawer = false" />
        <template v-if="auth.isAuthenticated">
          <v-list-item :to="{ name: 'plans' }" title="My Plans" @click="drawer = false" />
          <v-list-item title="Account Settings" @click="showSettings = true" />
        </template>
        <template v-else>
          <v-list-item :to="{ name: 'login' }" prepend-icon="mdi-login" title="Login" @click="drawer = false" />
          <v-list-item :to="{ name: 'register' }" prepend-icon="mdi-account-plus-outline" title="Sign up" @click="drawer = false" />
        </template>
        <v-divider class="my-2" />
        <v-list-item
          :prepend-icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          :title="isDark ? 'Light mode' : 'Dark mode'"
          @click="toggleDark"
        />
      </v-list>
    </v-navigation-drawer>

    <v-app-bar color="primary" elevation="2">
      <!-- Hamburger icon — visible only on small screens -->
      <v-app-bar-nav-icon class="d-flex d-md-none" @click="drawer = !drawer" />

      <v-app-bar-title>
        <RouterLink to="/" class="app-title">
          <img src="@/assets/logo.svg" alt="" class="app-logo mr-2" />
          Omne Enduro
        </RouterLink>
      </v-app-bar-title>

      <!-- Nav buttons — hidden on small screens -->
      <template #append>
        <div class="d-none d-md-flex align-center">
          <v-btn :to="{ name: 'analyze' }" variant="text">Analyze</v-btn>
          <v-btn :to="{ name: 'tutorial' }" variant="text">Tutorial</v-btn>

          <template v-if="auth.isAuthenticated">
            <v-btn :to="{ name: 'plans' }" variant="text">
              My Plans
            </v-btn>
            <v-btn icon="mdi-account-circle" class="ml-2" @click="showSettings = true" />
          </template>
          <template v-else>
            <v-btn :to="{ name: 'login' }" variant="text" prepend-icon="mdi-login">Login</v-btn>
            <v-btn :to="{ name: 'register' }" variant="outlined" class="ml-1">Sign up</v-btn>
          </template>
          <v-btn
            :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
            variant="text"
            class="ml-1"
            @click="toggleDark"
          />
        </div>
      </template>

    </v-app-bar>

    <v-main>
      <RouterView />
    </v-main>

    <!-- Settings modal -->
    <v-dialog v-model="showSettings" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-account-circle" class="mr-2" />
          Account
          <v-spacer />
          <v-btn icon="mdi-close" size="x-small" variant="text" @click="showSettings = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div v-if="auth.user" class="mb-2">
            <div class="text-caption text-medium-emphasis">Display name</div>
            <div class="text-body-1">{{ auth.user.display_name ?? '—' }}</div>
          </div>
          <div v-if="auth.user">
            <div class="text-caption text-medium-emphasis">Email</div>
            <div class="text-body-1">{{ auth.user.email }}</div>
          </div>
        </v-card-text>
        <v-divider />
        <v-card-actions class="flex-column align-start pa-4 gap-2">
          <v-btn
            block
            variant="outlined"
            prepend-icon="mdi-logout"
            @click="handleLogout"
          >
            Logout
          </v-btn>
          <v-btn
            block
            variant="outlined"
            color="error"
            prepend-icon="mdi-delete-forever"
            @click="confirmDelete = true"
          >
            Delete Account
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete account confirmation -->
    <v-dialog v-model="confirmDelete" max-width="360">
      <v-card>
        <v-card-title>Delete account?</v-card-title>
        <v-card-text>
          This will permanently delete your account, all saved plans, and uploaded files. This cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDelete = false">Cancel</v-btn>
          <v-btn color="error" :loading="isDeleting" @click="handleDeleteAccount">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useTheme } from 'vuetify'

const auth = useAuthStore()
const router = useRouter()
const theme = useTheme()
const drawer = ref(false)
const showSettings = ref(false)
const confirmDelete = ref(false)
const isDeleting = ref(false)

const isDark = computed(() => theme.global.name.value === 'dark')

// Restore saved preference on load
const _saved = localStorage.getItem('theme')
if (_saved === 'dark' || _saved === 'light') {
  theme.global.name.value = _saved
}

function toggleDark() {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
  localStorage.setItem('theme', theme.global.name.value)
}

function handleLogout() {
  showSettings.value = false
  auth.logout()
  router.push({ name: 'login' })
}

async function handleDeleteAccount() {
  if (!auth.user) return
  isDeleting.value = true
  try {
    await authApi.deleteAccount(auth.user.id)
    confirmDelete.value = false
    showSettings.value = false
    auth.logout()
    router.push({ name: 'login' })
  } finally {
    isDeleting.value = false
  }
}
</script>

<style>
.app-title {
  color: white;
  text-decoration: none;
  font-weight: 600;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
}
.app-logo {
  height: 28px;
  width: auto;
  display: block;
}
</style>
