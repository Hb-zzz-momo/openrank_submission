import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// ✅ 提前恢复登录态（在任何页面 mounted 前）
const auth = useAuthStore(pinia)
auth.loadFromStorage()

app.mount('#app')
