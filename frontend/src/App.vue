<template>
  <v-app>
    <!-- Mobile navigation drawer -->
    <v-navigation-drawer v-model="drawer" temporary>
      <v-list nav>
        <v-list-item :to="{ name: 'analyze' }" prepend-icon="mdi-map-search-outline" title="Analyze" @click="drawer = false" />
        <v-list-item :to="{ name: 'tutorial' }" prepend-icon="mdi-school-outline" title="Tutorial" @click="drawer = false" />
        <template v-if="auth.isAuthenticated">
          <v-list-item :to="{ name: 'plans' }" prepend-icon="mdi-bookmark-multiple-outline" title="My Plans" @click="drawer = false" />
          <v-list-item prepend-icon="mdi-logout" title="Logout" @click="handleLogout" />
        </template>
        <template v-else>
          <v-list-item :to="{ name: 'login' }" prepend-icon="mdi-login" title="Login" @click="drawer = false" />
          <v-list-item :to="{ name: 'register' }" prepend-icon="mdi-account-plus-outline" title="Sign up" @click="drawer = false" />
        </template>
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
            <v-btn :to="{ name: 'plans' }" variant="text" prepend-icon="mdi-bookmark-multiple-outline">
              My Plans
            </v-btn>
            <v-btn variant="text" prepend-icon="mdi-logout" @click="handleLogout">Logout</v-btn>
          </template>
          <template v-else>
            <v-btn :to="{ name: 'login' }" variant="text" prepend-icon="mdi-login">Login</v-btn>
            <v-btn :to="{ name: 'register' }" variant="outlined" class="ml-1">Sign up</v-btn>
          </template>
        </div>
      </template>
    </v-app-bar>

    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const drawer = ref(false)

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
.app-logo {
  height: 28px;
  width: auto;
  display: block;
}
</style>
