import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
const enableDevTools = process.env.VITE_ENABLE_DEVTOOLS === 'true'

export default defineConfig({
  plugins: [
    vue(),
    enableDevTools && vueDevTools()
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
//翻译.vue语言到机器可懂的URL
