<template>
  <v-container class="d-flex align-center justify-center" style="min-height: calc(100vh - 64px)">
    <v-card width="400" elevation="4">
      <v-card-title class="text-h6 pt-6 pb-2 px-6">Sign in</v-card-title>
      <v-card-text class="px-6">
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = ''">
          {{ error }}
        </v-alert>

        <v-form ref="formRef" @submit.prevent="submit">
          <v-text-field
            v-model="email"
            label="Email"
            type="email"
            prepend-inner-icon="mdi-email-outline"
            density="compact"
            :rules="[required, emailRule]"
            class="mb-2"
          />
          <v-text-field
            v-model="password"
            label="Password"
            :type="showPassword ? 'text' : 'password'"
            prepend-inner-icon="mdi-lock-outline"
            :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
            density="compact"
            :rules="[required]"
            class="mb-4"
            @click:append-inner="showPassword = !showPassword"
          />
          <v-btn type="submit" color="primary" block :loading="isLoading">Sign in</v-btn>
        </v-form>
      </v-card-text>
      <v-card-text class="pt-0 text-center text-body-2">
        Don't have an account?
        <RouterLink :to="{ name: 'register' }">Sign up</RouterLink>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const isLoading = ref(false)
const formRef = ref()

const required = (v: string) => !!v || 'Required'
const emailRule = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email'

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  isLoading.value = true
  error.value = ''
  try {
    await auth.login({ email: email.value, password: password.value })
    const redirect = (route.query.redirect as string) ?? '/'
    router.push(redirect)
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    error.value = axiosErr.response?.data?.detail ?? 'Login failed. Check your credentials.'
  } finally {
    isLoading.value = false
  }
}
</script>
