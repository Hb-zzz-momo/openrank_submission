import { defineStore } from 'pinia'
import { authApi } from '../api/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,          // 当前登录用户信息
    token: null,         // access_token
    loading: false,
    error: null
  }),

  actions: {
    // 从 localStorage 恢复登录状态（页面刷新后）
    loadFromStorage() {
      const token = localStorage.getItem('access_token')
      const userStr = localStorage.getItem('auth_user')
      if (token && userStr) {
        this.token = token
        this.user = JSON.parse(userStr)
      }
    },

    async register({ username, email, password }) {
      this.loading = true
      this.error = null
      try {
        await authApi.register({ username, email, password })
        // 注册成功只提示一下，真正登录交给 login
        return true
      } catch (err) {
        this.error = err.response?.data?.detail || '注册失败'
        throw err
      } finally {
        this.loading = false
      }
    },

    async login({ username, password }) {
      this.loading = true
      this.error = null
      try {
        const res = await authApi.login({ username, password })
        const { access_token, user } = res.data
        this.token = access_token
        this.user = user

        // 本地持久化
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('auth_user', JSON.stringify(user))

        return true
      } catch (err) {
        this.error = err.response?.data?.detail || '登录失败'
        throw err
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('auth_user')
    },

    async fetchMe() {
      // 可选：用 /me 再拉一次用户信息
      if (!this.token) return
      try {
        const res = await authApi.getMe()
        this.user = res.data.user
        localStorage.setItem('auth_user', JSON.stringify(this.user))
      } catch (err) {
        // token 失效了就强制登出
        this.logout()
      }
    }
  }
})