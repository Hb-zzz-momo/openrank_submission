import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import FavoritesView from '@/views/FavoritesView.vue'
import LLMSummaryView from '../views/LLMSummaryView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { keepAlive: true } // ✅ 首页保活：不重复拉项目树/图表数据
    },
    {
      path: '/llm-summary',
      name: 'llm-summary',
      component: LLMSummaryView,
      meta: { keepAlive: true } // ✅ 汇总看板保活：不重复拉 summary
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: FavoritesView,
      meta: { requiresAuth: true, keepAlive: true } // ✅ 收藏页保活：不重复拉 favorites
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    }
  ]
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  next()
})

export default router
