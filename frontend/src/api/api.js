// frontend/src/api/api.js
// 统一封装所有后端 HTTP 请求：OpenDigger + LLM + 认证

import axios from 'axios'

// ================== 1. 创建 axios 实例 ==================
const http = axios.create({
  baseURL: 'http://127.0.0.1:8000',   // 现在后端是 Flask，端口 8000
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ================== 2. 请求拦截器：自动挂上 token ==================
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ================== 3. 响应拦截器==================
http.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('auth_user')
      // 不引入 router 依赖，直接跳（最不容易循环依赖）
      if (location.pathname !== '/login') location.href = '/login'
    }
    return Promise.reject(error)
  }
)


// ================== 4. OpenDigger 指标相关接口 ==================
export const opendiggerApi = {
  // 1. 获取平台列表
  getPlatforms() {
    return http.get('/api/platforms')
  },

  // 2. 获取平台下的组织/用户
  getEntities(platform) {
    return http.get(`/api/entities/${platform}`)
  },

  // 3. 获取对应类型的指标
  getMetrics(entityType) {
    return http.get(`/api/metrics/${entityType}`)
  },

  // 4. 获取组织下的仓库列表
  getRepos(platform, org) {
    return http.get(`/api/repos/${platform}/${org}`)
  },

  // 5. 获取“开发者”指标（不带 repo）
  getUserData(platform, entity, metric) {
    return http.get(`/api/data/${platform}/${entity}/${metric}`)
  },

  // 6. 获取“仓库”指标（带 repo）
  getRepoData(platform, entity, repo, metric) {
    return http.get(`/api/data/${platform}/${entity}/${repo}/${metric}`)
  }
}

// ================== 5. LLM 生态看板相关接口 ==================
export const llmApi = {
  // 汇总数据：/api/llm/summary
  getSummary() {
    return http.get('/api/llm/summary')
  },

  // 排名：/api/llm/rank/<metric>?top=10
  getRank(metric = 'health_score', top = 10) {
    return http.get(`/api/llm/rank/${metric}`, {
      params: { top }
    })
  },

  // 报告生成：/api/llm/report   POST
  getReport(payload) {
    // payload: { projects: [{ repo, metrics: {...} }, ...] }
    return http.post('/api/llm/report', payload)
  },
    getProjects() {
    return http.get('/api/llm/projects')
  }
}


// ================== 6. 认证相关接口（注册 / 登录 / me） ==================
export const authApi = {
  // 注册：POST /api/auth/register
  register(payload) {
    // payload: { username, email, password }
    return http.post('/api/auth/register', payload)
  },

  // 登录：POST /api/auth/login
  login(payload) {
    // payload: { username: '账号(用户名或邮箱)', password }
    return http.post('/api/auth/login', payload)
  },

  // 获取当前登录用户：GET /api/auth/me
  getMe() {
    return http.get('/api/auth/me')
  },
  getProjects() {
    return http.get('/api/llm/projects')
  }
}

// ================== 7.（可选）收藏相关接口占位 ==================
export const favoritesApi = {
  list() {
    return http.get('/api/favorites')
  },
  add(payload) {
    // payload: { full_name, metric, platform, title, url }
    return http.post('/api/favorites', payload)
  },
  remove(id) {
    return http.delete(`/api/favorites/${id}`)
  }
}

// 给外面用的默认导出：如果有地方直接 import http
export default http

export { http }