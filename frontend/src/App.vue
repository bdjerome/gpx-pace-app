<template>
  <v-app>
    <v-app-bar color="primary" elevation="2">
      <v-app-bar-title>
        <RouterLink to="/" class="app-title">
          <v-icon icon="mdi-map-marker-path" class="mr-2" />
          GPX Pace Planner
        </RouterLink>
      </v-app-bar-title>

      <template #append>
        <v-btn :to="{ name: 'analyze' }" variant="text" prepend-icon="mdi-run-fast">
          Analyze
        </v-btn>
        <v-btn :to="{ name: 'tutorial' }" variant="text" prepend-icon="mdi-book-open-outline">
          Tutorial
        </v-btn>

        <template v-if="auth.isAuthenticated">
          <v-btn :to="{ name: 'plans' }" variant="text" prepend-icon="mdi-bookmark-multiple-outline">
            My Plans
          </v-btn>
          <v-btn variant="text" prepend-icon="mdi-logout" @click="handleLogout">Logout</v-btn>
        </template>
        <template v-else>
          <v-btn :to="{ name: 'login' }" variant="text" prepend-icon="mdi-login">Login</v-btn>
          <v-btn :to="{ name: 'register' }" variant="outlined" class="ml-1">Sign up</v-btn>
        </template>
      </template>
    </v-app-bar>

    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push({ name: 'login' })
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
</style>
