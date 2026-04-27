<template>
  <v-container class="d-flex align-center justify-center" style="min-height: calc(100vh - 64px)">
    <v-card width="420" elevation="4">
      <v-card-title class="text-h6 pt-6 pb-2 px-6">Create account</v-card-title>
      <v-card-text class="px-6">
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = ''">
          {{ error }}
        </v-alert>
        <v-alert v-if="success" type="success" variant="tonal" class="mb-4">
          Account created! <RouterLink :to="{ name: 'login' }">Sign in now →</RouterLink>
        </v-alert>

        <v-form ref="formRef" @submit.prevent="submit">
          <v-text-field
            v-model="displayName"
            label="Display name (optional)"
            prepend-inner-icon="mdi-account-outline"
            density="compact"
            class="mb-2"
          />
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
            :rules="[required, minLength]"
            class="mb-2"
            @click:append-inner="showPassword = !showPassword"
          />
          <v-text-field
            v-model="confirmPassword"
            label="Confirm password"
            :type="showPassword ? 'text' : 'password'"
            prepend-inner-icon="mdi-lock-check-outline"
            density="compact"
            :rules="[required, passwordMatch]"
            class="mb-4"
          />
          <v-btn type="submit" color="primary" block :loading="isLoading">Create account</v-btn>
        </v-form>
      </v-card-text>
      <v-card-text class="pt-0 text-center text-body-2">
        Already have an account?
        <RouterLink :to="{ name: 'login' }">Sign in</RouterLink>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const displayName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const error = ref('')
const success = ref(false)
const isLoading = ref(false)
const formRef = ref()

const required = (v: string) => !!v || 'Required'
const emailRule = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Invalid email'
const minLength = (v: string) => v.length >= 8 || 'Minimum 8 characters'
const passwordMatch = (v: string) => v === password.value || 'Passwords do not match'

async function submit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  isLoading.value = true
  error.value = ''
  try {
    await auth.register({
      email: email.value,
      password: password.value,
      display_name: displayName.value || undefined,
    })
    success.value = true
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    error.value = axiosErr.response?.data?.detail ?? 'Registration failed.'
  } finally {
    isLoading.value = false
  }
}
</script>
