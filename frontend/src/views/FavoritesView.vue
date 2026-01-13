<template>
  <div class="favorites-view">
    <h1 class="title">我的收藏项目</h1>

    <div v-if="loading" class="hint">加载中...</div>
    <div v-else-if="error" class="hint error">{{ error }}</div>

    <div v-else class="grid">
      <div v-for="fav in favorites" :key="fav.id" class="card">
        <div class="card-head">
          <div class="card-title">
            <!-- single：显示 org/repo - metric；plan：显示 title -->
            <template v-if="isSingle(fav)">
              {{ safeFullName(fav.full_name) }} - {{ fav.metric }}
            </template>
            <template v-else>
              {{ fav.title || '收藏方案/榜单' }}
            </template>
          </div>

          <button class="del" @click="remove(fav.id)">×</button>
        </div>

        <!-- single：显示仓库链接 + 图 -->
        <template v-if="isSingle(fav)">
          <a
            class="sub"
            :href="fav.url || `https://github.com/${safeFullName(fav.full_name)}`"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ safeFullName(fav.full_name) }}
          </a>

          <RepoChart
            :platform="fav.platform || 'github'"
            :org="parseOrgRepo(fav.full_name).org"
            :repo="parseOrgRepo(fav.full_name).repo"
            :metric="fav.metric"
            :title="`${safeFullName(fav.full_name)} - ${fav.metric}`"
            :dark-mode="true"
          />
        </template>

        <!-- plan：显示 payload 信息 + 对齐LLMSummaryView的图表容器 -->
        <template v-else>
          <div class="plan-box">
            <div>类型：{{ fav.payload?.type || 'rank' }}</div>
            <div>指标：{{ fav.payload?.metric || '-' }}, TopN：{{ fav.payload?.topN || '-' }}</div>
            <div>项目数：{{ planRepos(fav).length }}</div>

            <ul v-if="planRepos(fav).length" class="repo-list">
              <li v-for="(r, i) in planRepos(fav)" :key="i">{{ r }}</li>
            </ul>

            <!-- 复用LLMSummaryView的chart-wrapper容器 -->
            <div class="chart-wrapper">
              <h2>Top {{ fav.payload?.topN }} 项目 {{ getMetricLabel(fav.payload?.metric) }} 对比</h2>
              <RankChart
                v-if="fav.payload?.type === 'rank'"
                :payload="fav.payload"
                :metric-label="getMetricLabel(fav.payload?.metric)"
              />
            </div>
          </div>
        </template>
      </div>

      <div v-if="!favorites.length" class="hint">暂无收藏</div>
    </div>
  </div>
</template>

<script setup>
import RankChart from '@/components/RankChart.vue'
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useFavoritesStore } from '@/stores/favorites'
import RepoChart from '@/components/RepoChart.vue'

const favStore = useFavoritesStore()
const { favorites, loading, error } = storeToRefs(favStore)

// 与LLMSummaryView一致的指标名称映射
const metricLabelMap = {
  health_score: '综合健康度',
  openrank_mean_12m: 'OpenRank 近 12 个月均值',
  activity_mean_12m: '活跃度近 12 个月均值'
}

// 获取指标对应的显示名称
function getMetricLabel(metric) {
  return metricLabelMap[metric] || metric
}

onMounted(async () => {
  await favStore.fetchFavorites()
})

function isSingle(fav) {
  const k = (fav?.kind || '').trim()
  // 兼容旧数据（metric）
  return (k === 'single' || k === 'metric') && !!fav?.full_name && !!fav?.metric
}

function safeFullName(fullName) {
  if (!fullName) return ''
  const s = String(fullName).trim()
  // 兼容 "github/org/repo" -> "org/repo"
  const parts = s.split('/').filter(Boolean)
  if (parts.length === 3 && (parts[0] === 'github' || parts[0] === 'gitee')) {
    return `${parts[1]}/${parts[2]}`
  }
  return s
}

function parseOrgRepo(fullName) {
  const s = safeFullName(fullName)
  const parts = s.split('/').filter(Boolean)
  return {
    org: parts[0] || '',
    repo: parts[1] || ''
  }
}

function planRepos(fav) {
  const p = fav?.payload || {}
  const repos = Array.isArray(p.repos) ? p.repos : (Array.isArray(p.projects) ? p.projects : [])
  return repos.map(safeFullName).filter(Boolean)
}

async function remove(id) {
  await favStore.removeFavorite(id)
}
</script>

<style scoped>
.favorites-view {
  padding: 24px 32px;
  min-height: 100vh;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 0% 0%, #1d4ed8 0, transparent 55%),
    radial-gradient(circle at 100% 0%, #a855f7 0, transparent 55%),
    radial-gradient(circle at 50% 100%, #22c55e 0, #020617 60%);
  color: #e5e7eb;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.title {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 20px;
  color: #e5e7eb;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 24px;
}

.card {
  background: radial-gradient(circle at 0 0, rgba(148, 163, 184, 0.18), transparent 55%),
    rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(18px);
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  padding: 22px;
  min-height: 480px;  /* 🔥 从 420px 改成 480px，给数据面板留空间 */
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.85);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 25px 60px rgba(15, 23, 42, 1);
  border-color: rgba(56, 189, 248, 0.6);
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-title {
  font-weight: 700;
  font-size: 18px;
  color: #e5e7eb;
  line-height: 1.4;
  flex: 1;
  word-break: break-word;
  background: linear-gradient(135deg, #22c55e, #38bdf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sub {
  display: inline-block;
  margin: 6px 0 16px;
  color: #38bdf8;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 8px;
  background: rgba(56, 189, 248, 0.1);
  border: 1px solid rgba(56, 189, 248, 0.3);
  transition: all 0.2s ease;
}

.sub:hover {
  text-decoration: none;
  color: #22c55e;
  background: rgba(56, 189, 248, 0.2);
  border-color: rgba(56, 189, 248, 0.6);
  box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
}

.del {
  border: none;
  background: rgba(239, 68, 68, 0.15);
  font-size: 22px;
  cursor: pointer;
  color: #fca5a5;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  margin-left: 8px;
  flex-shrink: 0;
}

.del:hover {
  color: #fecaca;
  background: rgba(239, 68, 68, 0.3);
  transform: scale(1.1);
}

.plan-box {
  border: 1px solid rgba(148, 163, 184, 0.4);
  border-radius: 12px;
  padding: 16px;
  color: #cbd5f5;
  background: rgba(15, 23, 42, 0.6);
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.6;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.plan-box > div {
  margin-bottom: 6px;
}

.repo-list {
  margin: 12px 0 0;
  padding-left: 20px;
  max-height: 120px;
  overflow-y: auto;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  padding-top: 8px;
  flex-shrink: 0;
}

.repo-list li {
  margin-bottom: 4px;
  color: #94a3b8;
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.repo-list li:hover {
  background: rgba(56, 189, 248, 0.15);
  color: #e5e7eb;
  padding-left: 12px;
  border-color: rgba(56, 189, 248, 0.3);
}

.hint {
  color: #cbd5f5;
  padding: 30px;
  text-align: center;
  font-size: 16px;
  background: rgba(15, 23, 42, 0.7);
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  margin: 30px 0;
  backdrop-filter: blur(10px);
}

.hint.error {
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.15);
}

/* 复用LLMSummaryView的chart-wrapper样式 */
.chart-wrapper {
  background: radial-gradient(circle at 0 0, rgba(148, 163, 184, 0.18), transparent 55%),
    rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(18px);
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  padding: 1.5rem;
  min-width: 0;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.85);
  margin-top: 1rem;
}

.chart-wrapper h2 {
  margin: 0 0 1rem;
  font-size: 1.2rem;
  color: #e5e7eb;
  font-weight: 600;
}

/* 确保图表深色主题适配 */
:deep(.echarts) {
  background: transparent !important;
}

:deep(.echarts-tooltip) {
  background: rgba(15, 23, 42, 0.95) !important;
  border: 1px solid rgba(148, 163, 184, 0.4) !important;
  color: #e5e7eb !important;
}

@media (max-width: 960px) {
  .grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .favorites-view {
    padding: 16px;
  }
  
  .card {
    min-height: 380px;
    padding: 16px;
  }
  
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
  }
}

@media (max-width: 768px) {
  .title {
    font-size: 22px;
  }
  
  .card-title {
    font-size: 16px;
  }
}


</style>