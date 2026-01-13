<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="logo">OpenDigger 可视化平台</div>
      <nav class="app-nav">
        <router-link to="/" class="nav-link">首页大屏</router-link>
        <router-link to="/llm-summary" class="nav-link">LLM 生态看板</router-link>
        <router-link to="/favorites" class="nav-link">我的收藏</router-link>
        <span class="nav-divider"></span>
        <!-- 未登录：显示登录/注册 -->
        <template v-if="!auth.user">
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-link">注册</router-link>
        </template>

        <!-- 已登录：显示用户名 + 退出 -->
        <template v-else>
          <span class="nav-user">👤 {{ auth.user.username }}</span>
          <button class="nav-logout" @click="auth.logout()">退出</button>
        </template>
      </nav>
    </header>
    <main class="app-main-content">
      <router-view v-slot="{ Component, route }">
        <template v-if="route.meta.keepAlive">
          <keep-alive>
            <component :is="Component" :key="route.name" />
          </keep-alive>
        </template>

        <template v-else>
          <component :is="Component" :key="route.fullPath" />
        </template>
      </router-view>
      
    </main>
        <!-- 鼠标跟随品牌标识（情况B） -->
    <div
      v-if="showCursorBrand"
      ref="cursorBrandEl"
      class="cursor-brand"
      aria-hidden="true"
    >
      OPENRANK
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const auth = useAuthStore()

/* ========= 你原来的：切换路由后触发 resize（给 ECharts 用） ========= */
watch(() => route.fullPath, async () => {
  await nextTick()
  window.dispatchEvent(new Event('resize'))
})

onMounted(async () => {
  auth.loadFromStorage()  // 刷新后恢复登录状态
  await auth.fetchMe()
})

/* ========= 情况B：鼠标跟随 OPENRANK ========= */
const cursorBrandEl = ref(null)
const showCursorBrand = ref(true)

const isTouchDevice = () =>
  'ontouchstart' in window || navigator.maxTouchPoints > 0

let rafId = 0
let lastX = 0
let lastY = 0

const onMouseMove = (e) => {
  lastX = e.clientX
  lastY = e.clientY

  // 用 requestAnimationFrame 合并高频事件，避免抖动/性能浪费
  if (rafId) return
  rafId = window.requestAnimationFrame(() => {
    rafId = 0
    const el = cursorBrandEl.value
    if (!el) return

    // 让标识在鼠标右下角一点，避免挡住指针
    const offsetX = 15
    const offsetY = 15
    el.style.transform = `translate(${lastX + offsetX}px, ${lastY + offsetY}px)`
  })
}

// 只在“非登录/注册页”显示
watch(() => route.path, (p) => {
  showCursorBrand.value = !['/login', '/register'].includes(p)
}, { immediate: true })

onMounted(() => {
  // 移动端不显示，避免奇怪的触控体验
  if (isTouchDevice()) {
    showCursorBrand.value = false
    return
  }

  // 如果系统偏好减少动画，也不显示
  const prefersReduced = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches
  if (prefersReduced) {
    showCursorBrand.value = false
    return
  }

  window.addEventListener('mousemove', onMouseMove, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMouseMove)
  if (rafId) cancelAnimationFrame(rafId)
})
</script>


<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2.5rem; /* 使用rem单位，更具弹性 */
  height: 70px;
  background-color: var(--card-bg-color);
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.logo {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color-dark);
}

.app-nav {
  display: flex;
  gap: 1rem;
}

.nav-link {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-color-light);
  text-decoration: none;
  border-radius: 6px;
  transition: background-color 0.2s, color 0.2s;
  position: relative;
}

.nav-link:hover {
  background-color: #f1f5f9;
  color: var(--text-color-dark);
}

/* 激活状态的链接样式 */
.nav-link.router-link-exact-active {
  color: var(--primary-color);
  background-color: var(--primary-color-light);
}

/* 内容区 */
.app-main-content {
  flex-grow: 1; /* 占据剩余所有空间 */
  width: 100%;
  max-width: 1600px; /* 限制最大宽度，防止内容过散 */
  margin: 0 auto;
  padding: 2.5rem; /* 使用rem增加呼吸感 */
}
/*登录登出界面*/
.nav-divider {
  width: 1px;
  height: 16px;
  margin: 0 8px;
  background: rgba(148, 163, 184, 0.6);
}
.nav-user {
  font-size: 13px;
  color: #e5e7eb;
  margin-right: 4px;
}
.nav-logout {
  border: none;
  background: transparent;
  color: #fecaca;
  font-size: 13px;
  cursor: pointer;
}
/* ===== 鼠标跟随品牌标识（情况B） ===== */
.cursor-brand{
  position: fixed;
  top: 0;
  left: 0;
  z-index: 2000;            /* 比 header(1000) 更高 */

  pointer-events: none;     /* ✅不挡点击 */
  user-select: none;

  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.14em;

  color: rgba(255, 255, 255, 0.55);
  text-shadow: 0 6px 22px rgba(0, 0, 0, 0.35);

  transform: translate(-9999px, -9999px);

  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(6px);

  transition: none
}

</style>