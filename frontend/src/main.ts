import './assets/main.css'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#E65100',
          secondary: '#37474F',
          accent: '#FF8F00',
          surface: '#FFFFFF',
          background: '#F5F5F5',
        },
      },
    },
  },
})

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(vuetify)

// Attempt a silent token refresh before first render so that users with a
// valid refresh-token cookie are immediately authenticated without a login
// redirect. The error is intentionally swallowed — if the cookie is missing
// or expired the user simply stays unauthenticated.
const auth = useAuthStore()
auth.silentRefresh().catch(() => {}).finally(() => {
  app.mount('#app')
})
