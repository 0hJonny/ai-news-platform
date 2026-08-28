import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: true,
    watch: {
      usePolling: true,
    },
  },
  plugins: [vue(), vueJsx(), vueDevTools(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // ai_news_platform/shared — cross-service contracts (e.g. the login
      // format both this app and backend/core validate against). Not part
      // of this Vue project; see backend/core/internal/auth/domain/user.go
      // (loginRulesPath) for the Go side reading the same file.
      '@shared': fileURLToPath(new URL('../../shared', import.meta.url)),
    },
  },
})
