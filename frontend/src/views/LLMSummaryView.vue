<template>
  <div class="llm-summary-view">
    <header class="view-header">
      <h1>LLM 生态健康度总览</h1>
      <p>基于 OpenRank 与活跃度，对典型大模型开源项目进行综合评估与排序。</p>
    </header>

    <!-- 控制区：选择排序指标 & TopN -->
    <section class="control-panel">
      <label>
        排序指标：
        <select v-model="selectedMetric" @change="updateSortedProjects">
          <option value="health_score">综合健康度（推荐）</option>
          <option value="openrank_mean_12m">OpenRank 近 12 个月均值</option>
          <option value="activity_mean_12m">活跃度近 12 个月均值</option>
        </select>
      </label>

      <label>
        Top N：
        <input type="number" v-model.number="topN" min="3" max="20" @change="updateSortedProjects" />
      </label>
      <button class="fav-rank-btn" @click="toggleRankFav" :disabled="!sortedProjects.length">
        {{ isRankFav ? '★ 已收藏榜单' : '☆ 收藏当前榜单' }}
      </button>

    </section>

    <!-- 主体区：左侧表格，右侧柱状图 -->
    <section class="content-layout">
      <!-- 表格区 -->
      <div class="table-wrapper">
        <h2>项目指标明细</h2>

        <!--一层 table-scroll，支持横向滚动 -->
        <div class="table-scroll" v-if="sortedProjects.length">
          <table class="llm-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>项目</th>
                <th>类别</th>
                <th>OpenRank 均值(12M)</th>
                <th>活跃度均值(12M)</th>
                <th>OpenRank 波动</th>
                <th>综合健康度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, idx) in sortedProjects" :key="p.project_key">
                <td>{{ idx + 1 }}</td>
                <td>
                  <a
                    :href="`https://github.com/${p.project_key}`"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {{ p.project_key }}
                  </a>
                </td>
                <td>{{ renderCategory(p.category) }}</td>
                <td>{{ p.openrank_mean_12m }}</td>
                <td>{{ p.activity_mean_12m }}</td>
                <td>{{ p.openrank_std_12m }}</td>
                <td>
                  <span class="score-chip">
                    {{ p.health_score }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="empty-tip">
          正在加载数据或暂无数据……
        </div>
      </div>


      <!-- 柱状图区 -->
      <div class="chart-wrapper">
        <h2>Top {{ Math.min(topN, sortedProjects.length) }} 项目 {{ metricLabelMap[selectedMetric] }} 对比</h2>

        <div ref="chartRef" class="rank-chart"></div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { storeToRefs } from 'pinia'
import { llmApi } from '../api/api'
import { useAuthStore } from '@/stores/auth'
import { useFavoritesStore } from '@/stores/favorites.js'

// ===== 1) 基础状态（必须放前面） =====
const allProjects = ref([])
const sortedProjects = ref([])

const selectedMetric = ref('health_score')
const topN = ref(10)

const metricLabelMap = {
  health_score: '综合健康度',
  openrank_mean_12m: 'OpenRank 近 12 个月均值',
  activity_mean_12m: '活跃度近 12 个月均值'
}

// ===== 2) store（可以放这里） =====
const authStore = useAuthStore()
const favStore = useFavoritesStore()
const { token } = storeToRefs(authStore)

// ===== 3) 收藏榜单（依赖 selectedMetric/topN，所以必须在它们后面） =====
const rankUniqKey = computed(() => `rank:${selectedMetric.value}:${topN.value}`)

const isRankFav = computed(() => {
  return favStore.isPlanKeyFavorited(rankUniqKey.value)
})

const toggleRankFav = async () => {
  if (!token.value) {
    alert('请先登录再收藏榜单')
    return
  }

  if (!favStore.favorites.length) {
    await favStore.fetchFavorites()
  }

  const normalizeRepo = (s) => {
    const parts = String(s || '').trim().split('/').filter(Boolean)
    // 兼容 "github/org/repo"
    if (parts.length === 3 && parts[0] === 'github') return `${parts[1]}/${parts[2]}`
    return parts.join('/')
  }

  const metricKey = selectedMetric.value
  const snapItems = sortedProjects.value.map(p => ({
    repo: normalizeRepo(p.project_key),
    value: Number(p[metricKey]) || 0
  }))

  const payload = {
    type: 'rank',
    metric: selectedMetric.value,
    topN: topN.value,
    repos: snapItems.map(x => x.repo),
    items: snapItems // ✅ 这就是"收藏时的榜单快照"
  }

  await favStore.togglePlanByKey({
    uniq_key: rankUniqKey.value,
    title: `LLM 榜单：${metricLabelMap[selectedMetric.value]} Top${topN.value}`,
    payload
  })
}

// ===== 4) 其它业务逻辑 =====
const chartRef = ref(null)
let chartInstance = null

const renderCategory = (category) => {
  switch (category) {
    case 'training_framework': return '训练框架'
    case 'llm_framework': return 'LLM 模型框架'
    case 'llm_app_framework': return 'LLM 应用框架'
    case 'llm_inference': return 'LLM 推理引擎'
    default: return category || '未知'
  }
}

const loadSummary = async () => {
  try {
    const res = await llmApi.getSummary()
    allProjects.value = res.data.projects || []
    updateSortedProjects()
  } catch (err) {
    console.error('加载 LLM 汇总数据失败：', err)
  }
}

const updateSortedProjects = () => {
  if (!allProjects.value.length) {
    sortedProjects.value = []
    return
  }
  const metric = selectedMetric.value
  const top = topN.value || 10
  const temp = [...allProjects.value].sort((a, b) => (b[metric] || 0) - (a[metric] || 0))
  sortedProjects.value = temp.slice(0, top)
  renderChart()
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value)

  const names = sortedProjects.value.map(p => p.project_key)
  const values = sortedProjects.value.map(p => p[selectedMetric.value] || 0)

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '5%', right: '5%', bottom: '8%', top: '10%', containLabel: true },
    xAxis: { 
      type: 'value', 
      name: metricLabelMap[selectedMetric.value],
      nameTextStyle: { color: '#cbd5f5' },
      axisLine: { lineStyle: { color: '#475569' } },
      splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: { 
      type: 'category', 
      data: names,
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#cbd5f5' }
    },
    series: [{ 
      type: 'bar', 
      data: values,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#22c55e' },
          { offset: 1, color: '#38bdf8' }
        ])
      }
    }],
    backgroundColor: 'transparent'
  })
}

const handleResize = () => chartInstance && chartInstance.resize()

onMounted(async () => {
  await loadSummary()
  if (token.value) await favStore.fetchFavorites()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

watch([selectedMetric, topN], updateSortedProjects)
</script>


<style scoped>
.llm-summary-view {
  padding: 24px 32px 24px;
  min-height: 100vh;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 0% 0%, #1d4ed8 0, transparent 55%),
    radial-gradient(circle at 100% 0%, #a855f7 0, transparent 55%),
    radial-gradient(circle at 50% 100%, #22c55e 0, #020617 60%);
  color: #e5e7eb;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.view-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.view-header h1 {
  margin: 0 0 0.5rem;
  font-size: 26px;
  font-weight: 700;
}

.view-header p {
  margin: 0;
  font-size: 13px;
  color: #cbd5f5;
}

.control-panel {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  background: radial-gradient(circle at 0 0, rgba(148, 163, 184, 0.18), transparent 55%),
    rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(18px);
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  padding: 1rem 1.5rem;
  box-shadow: 0 8px 30px rgba(15, 23, 42, 0.85);
}

.control-panel label {
  font-size: 0.95rem;
  color: #e5e7eb;
}

.control-panel select,
.control-panel input {
  margin-left: 0.5rem;
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  background: rgba(15, 23, 42, 0.8);
  color: #e5e7eb;
  font-size: 0.9rem;
}

.control-panel select:focus,
.control-panel input:focus {
  outline: none;
  border-color: #38bdf8;
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
}

/* 左表右图的布局，允许子元素压缩 */
.content-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1.1fr);
  gap: 1.5rem;
  align-items: stretch;
  min-width: 0;
}

.table-wrapper,
.chart-wrapper {
  background: radial-gradient(circle at 0 0, rgba(148, 163, 184, 0.18), transparent 55%),
    rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(18px);
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  padding: 1.5rem;
  min-width: 0;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.85);
}

.table-wrapper h2,
.chart-wrapper h2 {
  margin: 0 0 1rem;
  font-size: 1.2rem;
  color: #e5e7eb;
  font-weight: 600;
}

/* 表格滚动容器 */
.table-scroll {
  width: 100%;
  overflow-x: auto;
}

/* 表格本身给一个最小宽度，列不会挤成一团 */
.llm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  min-width: 720px;
}

.llm-table thead {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 64, 175, 0.9));
}

.llm-table th,
.llm-table td {
  border: 1px solid rgba(51, 65, 85, 0.9);
  padding: 0.5rem 0.8rem;
  text-align: left;
  white-space: nowrap;
  color: #e5e7eb;
}

.llm-table th {
  font-weight: 600;
  color: #e5e7eb;
}

.llm-table tbody tr:nth-child(odd) {
  background: rgba(15, 23, 42, 0.85);
}

.llm-table tbody tr:nth-child(even) {
  background: rgba(15, 23, 42, 0.7);
}

.llm-table tbody tr:hover {
  background: rgba(56, 189, 248, 0.18);
}

.llm-table a {
  color: #38bdf8;
  text-decoration: none;
  font-weight: 500;
}

.llm-table a:hover {
  text-decoration: underline;
  color: #22c55e;
}

.score-chip {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: linear-gradient(135deg, #22c55e, #38bdf8);
  color: #0b1120;
  font-weight: 600;
  font-size: 0.85rem;
}

/* 图表区域不要超出卡片 */
.rank-chart {
  width: 100%;
  max-width: 100%;
  height: 360px;
}

.empty-tip {
  padding: 1.5rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.95rem;
}

/* 小屏适配 */
@media (max-width: 960px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
  
  .llm-summary-view {
    padding: 1rem;
  }
  
  .control-panel {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }
  
  .control-panel label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .control-panel select,
  .control-panel input {
    margin-left: 0;
    width: 100%;
  }
}

.fav-rank-btn {
  padding: 0.4rem 1rem;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #f97316, #ec4899);
  color: #0b1120;
  font-weight: 500;
  cursor: pointer;
  font-size: 0.9rem;
  box-shadow: 0 0 14px rgba(236, 72, 153, 0.6);
  transition: all 0.2s ease;
}

.fav-rank-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.8);
}

.fav-rank-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}
</style>