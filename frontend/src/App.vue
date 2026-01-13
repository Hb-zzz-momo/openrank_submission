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
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()

watch(() => route.fullPath, async () => {
  await nextTick()
  window.dispatchEvent(new Event('resize'))
})

const auth = useAuthStore()
onMounted(async() => {
  auth.loadFromStorage()  // 刷新后恢复登录状态
  await auth.fetchMe()
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
</style>