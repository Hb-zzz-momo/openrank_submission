<template>
  <button class="fav-btn" :class="{ on: on }" @click="onClick" :title="on ? '取消收藏' : '收藏'">
    <span v-if="on">❤️</span>
    <span v-else>🤍</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useFavoritesStore } from '@/stores/favorites'

const props = defineProps({
  payload: { type: Object, required: true } // { platform, full_name, metric, title, url }
})

const auth = useAuthStore()
const fav = useFavoritesStore()
const router = useRouter()
const route = useRoute()

const on = computed(() => fav.isFavorited(props.payload))

const onClick = async () => {
  if (!auth.token) {
    // 未登录：跳登录页，带回跳地址
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  await fav.toggleFavorite(props.payload)
}
</script>

<style scoped>
.fav-btn{
  border:none;
  background: transparent;
  cursor:pointer;
  font-size: 18px;
  line-height: 1;
  padding: 6px 8px;
  border-radius: 8px;
}
.fav-btn:hover{ background: rgba(0,0,0,0.06); }
.fav-btn.on{ transform: scale(1.05); }
</style>
