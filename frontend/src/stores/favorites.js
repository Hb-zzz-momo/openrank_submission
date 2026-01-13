// frontend/src/stores/favorites.js
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { favoritesApi } from '../api/api'

export const useFavoritesStore = defineStore('favorites', () => {
  const favorites = ref([])
  const loading = ref(false)
  const error = ref(null)

  const KIND_SINGLE = 'single'
  const KIND_PLAN = 'plan'

  const normKind = (k) => (k || KIND_SINGLE).trim()

  const fetchFavorites = async () => {
    loading.value = true
    error.value = null
    try {
      const res = await favoritesApi.list()
      favorites.value = res.data.favorites || []
    } catch (e) {
      error.value = e.response?.data?.detail || '加载收藏失败'
      favorites.value = []
    } finally {
      loading.value = false
    }
  }

  const removeFavorite = async (favId) => {
    try {
      await favoritesApi.remove(favId)
      favorites.value = favorites.value.filter(x => x.id !== favId)
      return true
    } catch (e) {
      alert(e.response?.data?.detail || '删除失败')
      return false
    }
  }

  const clear = () => { favorites.value = [] }

  const unshiftIfNotExists = (fav) => {
    const exists = favorites.value.some(x =>
      x.id === fav.id || (x.uniq_key && fav.uniq_key && x.uniq_key === fav.uniq_key)
    )
    if (!exists) favorites.value.unshift(fav)
  }

  // =========================
  // SINGLE：兼容 full_name / fullName
  // =========================
  const normalizeSingleInput = (arg1, arg2) => {
    // 传对象：FavoriteButton、HomeView 常用
    if (arg1 && typeof arg1 === 'object') {
      return {
        full_name: (arg1.full_name ?? arg1.fullName ?? arg1.repo ?? '').trim(),
        metric: (arg1.metric ?? '').trim(),
        platform: (arg1.platform ?? 'github').trim(),
        title: arg1.title ?? '',
        url: arg1.url ?? ''
      }
    }
    // 传两个字符串：isFavorited('a/b','activity') 这种写法
    return {
      full_name: (arg1 ?? '').toString().trim(),
      metric: (arg2 ?? '').toString().trim(),
      platform: 'github',
      title: '',
      url: ''
    }
  }

  const findSingle = (full_name, metric) => {
    return favorites.value.find(x => {
      const k = normKind(x.kind)
      // 兼容旧 kind=metric
      return (k === KIND_SINGLE || k === 'metric') && x.full_name === full_name && x.metric === metric
    })
  }

  const isFavorited = (arg1, arg2) => {
    const { full_name, metric } = normalizeSingleInput(arg1, arg2)
    if (!full_name || !metric) return false
    return !!findSingle(full_name, metric)
  }

  const addSingle = async (arg1, arg2) => {
    const { full_name, metric, platform, title, url } = normalizeSingleInput(arg1, arg2)
    if (!full_name || !metric) {
      alert('single 收藏需要 full_name 和 metric')
      return false
    }

    const body = {
      kind: KIND_SINGLE,
      uniq_key: `single:${platform}:${full_name}:${metric}`,
      full_name,
      metric,
      platform,
      title,
      url
    }

    try {
      const res = await favoritesApi.add(body)
      unshiftIfNotExists(res.data.favorite)
      return true
    } catch (e) {
      alert(e.response?.data?.detail || '收藏失败')
      return false
    }
  }

  const toggleSingle = async (arg1, arg2) => {
    const { full_name, metric, platform, title, url } = normalizeSingleInput(arg1, arg2)
    if (!full_name || !metric) {
      alert('single 收藏需要 full_name 和 metric')
      return false
    }
    const existed = findSingle(full_name, metric)
    if (existed) return await removeFavorite(existed.id)
    return await addSingle({ full_name, metric, platform, title, url })
  }

  // 旧接口兜底（你很多组件可能还在用）
  const addFavorite = addSingle
  const toggleFavorite = toggleSingle

  // =========================
  // PLAN：榜单/方案（后端认 kind=plan）
  // =========================
  const findPlanByKey = (uniq_key) => {
    return favorites.value.find(x => {
      const k = normKind(x.kind)
      // 兼容旧 kind=compare
      return (k === KIND_PLAN || k === 'compare') && x.uniq_key === uniq_key
    })
  }

  const isPlanKeyFavorited = (uniq_key) => !!findPlanByKey(uniq_key)

  const addPlan = async ({ uniq_key, title = '', payload = {} }) => {
    if (!uniq_key) {
      alert('榜单收藏缺少 uniq_key')
      return false
    }

    // 兼容 payload.projects / payload.repos
    const repos = Array.isArray(payload.repos)
      ? payload.repos
      : (Array.isArray(payload.projects) ? payload.projects : [])

    const body = {
      kind: KIND_PLAN,          // ✅关键：发 plan
      uniq_key,
      title,
      payload: { ...payload, repos, projects: repos } // ✅双写，收藏页怎么读都行
    }

    try {
      const res = await favoritesApi.add(body)
      unshiftIfNotExists(res.data.favorite)
      return true
    } catch (e) {
      alert(e.response?.data?.detail || '收藏榜单失败')
      return false
    }
  }

  const togglePlanByKey = async ({ uniq_key, title, payload }) => {
    const existed = findPlanByKey(uniq_key)
    if (existed) return await removeFavorite(existed.id)
    return await addPlan({ uniq_key, title, payload })
  }

  return {
    favorites, loading, error,
    fetchFavorites, removeFavorite, clear,

    // single
    isFavorited, addSingle, toggleSingle,
    addFavorite, toggleFavorite,

    // plan
    isPlanKeyFavorited, togglePlanByKey
  }
})
