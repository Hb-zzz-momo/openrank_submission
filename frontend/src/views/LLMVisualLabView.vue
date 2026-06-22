<template>
  <div class="visual-lab-view">
    <header class="lab-hero">
      <div class="hero-copy">
        <p class="eyebrow">OpenRank Visual Lab</p>
        <h1>LLM 生态可视化工坊</h1>
        <p>
          用统一筛选条件集中管理 OpenRank 可生成的排名、趋势、结构、关系与风险图表，
          从图表库进入可导出的大图分析工作台。
        </p>
      </div>

      <dl class="hero-stats" aria-label="当前数据概览">
        <div>
          <dt>项目</dt>
          <dd>{{ normalizedProjects.length }}</dd>
        </div>
        <div>
          <dt>类别</dt>
          <dd>{{ projectCategoryOptions.length - 1 }}</dd>
        </div>
        <div>
          <dt>图表</dt>
          <dd>{{ chartRegistry.length }}</dd>
        </div>
      </dl>
    </header>

    <section class="filter-bar" aria-label="全局筛选">
      <label class="filter-field">
        <span>指标</span>
        <select v-model="selectedMetric">
          <option v-for="metric in metricOptions" :key="metric.value" :value="metric.value">
            {{ metric.label }}
          </option>
        </select>
      </label>

      <label class="filter-field">
        <span>时间</span>
        <select v-model="selectedTimeRange">
          <option v-for="option in timeRangeOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="filter-field">
        <span>类别</span>
        <select v-model="selectedProjectCategory">
          <option v-for="option in projectCategoryOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="filter-field compact">
        <span>Top N</span>
        <select v-model.number="selectedTopN">
          <option v-for="value in topNOptions" :key="value" :value="value">{{ value }}</option>
        </select>
      </label>

      <label class="filter-field">
        <span>用途</span>
        <select v-model="selectedUseCase">
          <option v-for="option in useCaseOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>

      <label class="filter-field search-field">
        <span>搜索</span>
        <input
          v-model.trim="searchQuery"
          type="search"
          name="visual-lab-search"
          autocomplete="off"
          placeholder="项目 / 组织…"
        />
      </label>

      <button class="primary-action" type="button" :disabled="loading || !activeChart" @click="openChart(activeChart)">
        进入大图
      </button>
    </section>

    <section class="lab-shell" aria-label="图表工坊主体">
      <aside class="category-rail" aria-label="图表分类">
        <button
          v-for="category in chartCategories"
          :key="category.id"
          class="category-item"
          type="button"
          :class="{ active: selectedChartCategory === category.id }"
          @click="selectedChartCategory = category.id"
        >
          <span>{{ category.label }}</span>
          <strong>{{ categoryCount(category.id) }}</strong>
        </button>
      </aside>

      <main class="gallery-region">
        <div class="section-head">
          <div>
            <p class="section-kicker">图表总览模式</p>
            <h2>图表总览</h2>
          </div>
          <p>{{ scopedProjects.length }} 个项目参与当前筛选，点击卡片进入大图分析模式。</p>
        </div>

        <div v-if="loading" class="gallery-grid" aria-busy="true" aria-label="正在加载图表">
          <article v-for="i in 6" :key="i" class="chart-card skeleton-card">
            <div class="skeleton-line wide"></div>
            <div class="skeleton-visual"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line short"></div>
          </article>
        </div>

        <div v-else-if="error" class="state-box error-state" role="alert">
          <h3>数据加载失败</h3>
          <p>{{ error }}</p>
          <button type="button" @click="loadSummary">重新加载</button>
        </div>

        <div v-else-if="!visibleCharts.length" class="state-box">
          <h3>没有匹配的图表</h3>
          <p>可以切换分类、用途或清空收藏筛选后再试。</p>
          <button type="button" @click="resetChartFilters">重置图表筛选</button>
        </div>

        <div v-else class="gallery-grid">
          <article
            v-for="chart in visibleCharts"
            :key="chart.id"
            class="chart-card"
            :class="{ recommended: chart.recommended, selected: chart.id === activeChart?.id }"
            tabindex="0"
            @click="openChart(chart)"
            @keydown.enter.prevent="openChart(chart)"
            @keydown.space.prevent="openChart(chart)"
            @focus="selectedChartId = chart.id"
            @mouseenter="selectedChartId = chart.id"
          >
            <div class="card-topline">
              <span class="chart-type">{{ chart.type }}</span>
              <span v-if="chart.recommended" class="recommend-chip">首屏推荐</span>
            </div>
            <h3>{{ chart.name }}</h3>
            <p>{{ chart.question }}</p>

            <div class="preview-frame" :class="`preview-${chart.preview}`" aria-hidden="true">
              <span v-for="i in 12" :key="i"></span>
            </div>

            <div class="card-meta">
              <span>{{ categoryLabel(chart.category) }}</span>
              <span>{{ useCaseLabel(chart.useCase) }}</span>
            </div>
          </article>
        </div>
      </main>

      <aside class="insight-panel" aria-label="图表说明与洞察">
        <div class="panel-block">
          <p class="section-kicker">图表说明 / AI 洞察</p>
          <h2>{{ activeChart?.name || '图表说明' }}</h2>
          <p>{{ activeChart?.description }}</p>
        </div>

        <div class="panel-block">
          <h3>适合回答的问题</h3>
          <p class="question-text">{{ activeChart?.question }}</p>
        </div>

        <div class="panel-block">
          <h3>当前筛选</h3>
          <div class="filter-chips">
            <span v-for="chip in filterChips" :key="chip">{{ chip }}</span>
          </div>
        </div>

        <div class="panel-block">
          <h3>推荐洞察</h3>
          <ul class="insight-list">
            <li v-for="item in activeInsights.slice(0, 4)" :key="item">{{ item }}</li>
          </ul>
        </div>

        <div class="panel-actions">
          <button type="button" @click="openChart(activeChart)">查看大图</button>
          <button type="button" @click="toggleActiveFavorite" :disabled="!activeChart">
            {{ isActiveFavorite ? '取消收藏' : '收藏图表' }}
          </button>
          <button type="button" @click="exportReport" :disabled="!activeChart || !scopedProjects.length">
            导出报告
          </button>
        </div>
      </aside>
    </section>

    <div v-if="analysisOpen" class="analysis-overlay" role="dialog" aria-modal="true" aria-labelledby="analysis-title">
      <section class="analysis-workbench">
        <aside class="analysis-controls" aria-label="大图参数">
          <button ref="closeButtonRef" class="close-button" type="button" aria-label="关闭大图分析模式" @click="closeAnalysis">
            ×
          </button>

          <p class="section-kicker">大图分析模式</p>
          <h2>参数配置</h2>

          <label>
            图表
            <select v-model="selectedChartId">
              <option v-for="chart in chartRegistry" :key="chart.id" :value="chart.id">
                {{ chart.name }}
              </option>
            </select>
          </label>

          <label>
            指标
            <select v-model="selectedMetric">
              <option v-for="metric in metricOptions" :key="metric.value" :value="metric.value">
                {{ metric.shortLabel }}
              </option>
            </select>
          </label>

          <label>
            时间窗口
            <select v-model="selectedTimeRange">
              <option v-for="option in timeRangeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>

          <label>
            项目范围
            <select v-model="selectedProjectCategory">
              <option v-for="option in projectCategoryOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>

          <label>
            Top N
            <input
              v-model.number="selectedTopN"
              min="3"
              max="50"
              type="number"
              name="visual-lab-topn"
              inputmode="numeric"
              autocomplete="off"
            />
          </label>

          <div class="mini-ranking">
            <h3>当前 Top 项目</h3>
            <ol>
              <li v-for="project in scopedProjects.slice(0, 6)" :key="project.project_key">
                <span>{{ project.displayName }}</span>
                <strong>{{ metricDisplay(project) }}</strong>
              </li>
            </ol>
          </div>
        </aside>

        <main ref="exportPanelRef" class="analysis-canvas-panel">
          <header class="analysis-titlebar">
            <div>
              <p class="section-kicker">{{ activeChart?.type }} / {{ categoryLabel(activeChart?.category) }}</p>
              <h2 id="analysis-title">{{ activeChart?.name }}</h2>
              <p>{{ activeChart?.question }}</p>
            </div>
            <span class="data-badge">{{ scopedProjects.length }} projects</span>
          </header>

          <div class="chart-stage">
            <div v-if="chartStatusText" class="chart-status" role="status">
              {{ chartStatusText }}
            </div>
            <div ref="chartRef" class="analysis-chart" aria-label="当前 ECharts 图表"></div>
          </div>
        </main>

        <aside class="analysis-insights" aria-label="大图洞察与导出">
          <p class="section-kicker">AI 洞察</p>
          <h2>图表解释</h2>
          <ul class="insight-list">
            <li v-for="item in activeInsights" :key="item">{{ item }}</li>
          </ul>

          <div v-if="aiReport" class="ai-report">
            <h3>生成报告摘录</h3>
            <p>{{ aiReport }}</p>
          </div>

          <div v-if="actionMessage" class="action-message" role="status">
            {{ actionMessage }}
          </div>

          <div class="analysis-actions">
            <button type="button" :disabled="aiLoading || !scopedProjects.length" @click="generateAiInsight">
              {{ aiLoading ? '解读中…' : 'AI 解读' }}
            </button>
            <button type="button" :disabled="!activeChart" @click="toggleActiveFavorite">
              {{ isActiveFavorite ? '取消收藏' : '收藏图表' }}
            </button>
            <button type="button" :disabled="!chartReady" @click="exportPng">导出 PNG</button>
            <button type="button" :disabled="!activeChart || !scopedProjects.length" @click="exportReport">导出报告</button>
          </div>
        </aside>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import * as echarts from 'echarts'

import { llmApi, opendiggerApi } from '@/api/api'
import { useAuthStore } from '@/stores/auth'
import { useFavoritesStore } from '@/stores/favorites'
import {
  buildChartOption,
  buildLocalInsights,
  buildReportMarkdown,
  chartCategories,
  chartRegistry,
  compactProjectName,
  formatNumber,
  getChartById,
  getMetricLabel,
  metricOptions,
  normalizeProjects,
  renderCategory,
  sortProjects,
  timeRangeOptions,
  topNOptions,
  useCaseOptions
} from '@/data/llmVisualLab'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const favStore = useFavoritesStore()
const { token } = storeToRefs(authStore)

const allProjects = ref([])
const loading = ref(false)
const error = ref('')
const selectedMetric = ref('health_score')
const selectedTimeRange = ref('12m')
const selectedTopN = ref(30)
const selectedProjectCategory = ref('all')
const selectedUseCase = ref('all')
const selectedChartCategory = ref('all')
const selectedChartId = ref('ranking-bar')
const searchQuery = ref('')
const analysisOpen = ref(false)
const trendData = ref({})
const trendLoading = ref(false)
const trendError = ref('')
const aiLoading = ref(false)
const aiReport = ref('')
const actionMessage = ref('')
const chartReady = ref(false)

const chartRef = ref(null)
const closeButtonRef = ref(null)
const exportPanelRef = ref(null)
let chartInstance = null

const normalizedProjects = computed(() => normalizeProjects(allProjects.value))

const projectCategoryOptions = computed(() => {
  const map = new Map()
  normalizedProjects.value.forEach(project => {
    map.set(project.category || 'unknown', project.categoryLabel)
  })
  return [
    { value: 'all', label: '全部类别' },
    ...Array.from(map.entries())
      .sort((a, b) => a[1].localeCompare(b[1], 'zh-Hans-CN'))
      .map(([value, label]) => ({ value, label }))
  ]
})

const filteredProjects = computed(() => {
  const query = searchQuery.value.toLowerCase()
  return normalizedProjects.value.filter(project => {
    const categoryMatched = selectedProjectCategory.value === 'all' || project.category === selectedProjectCategory.value
    const queryMatched = !query ||
      project.displayName.toLowerCase().includes(query) ||
      String(project.org || '').toLowerCase().includes(query) ||
      String(project.repo || '').toLowerCase().includes(query)
    return categoryMatched && queryMatched
  })
})

const scopedProjects = computed(() => {
  return sortProjects(filteredProjects.value, selectedMetric.value).slice(0, selectedTopN.value)
})

const favoriteChartIds = computed(() => {
  return favStore.favorites
    .filter(item => item?.payload?.type === 'visual_lab_chart')
    .map(item => item.payload.chartId)
    .filter(Boolean)
})

const visibleCharts = computed(() => {
  return chartRegistry.filter(chart => {
    const categoryMatched =
      selectedChartCategory.value === 'all' ||
      selectedChartCategory.value === chart.category ||
      (selectedChartCategory.value === 'favorites' && favoriteChartIds.value.includes(chart.id))
    const useCaseMatched = selectedUseCase.value === 'all' || selectedUseCase.value === chart.useCase
    return categoryMatched && useCaseMatched
  })
})

const activeChart = computed(() => {
  const selected = getChartById(selectedChartId.value)
  if (visibleCharts.value.some(chart => chart.id === selected.id)) return selected
  return visibleCharts.value[0] || selected
})

const activeInsights = computed(() => {
  return buildLocalInsights(activeChart.value, scopedProjects.value, selectedMetric.value)
})

const selectedTimeRangeLabel = computed(() => {
  return timeRangeOptions.find(option => option.value === selectedTimeRange.value)?.label || '近 12 个月'
})

const selectedCategoryLabel = computed(() => {
  return projectCategoryOptions.value.find(option => option.value === selectedProjectCategory.value)?.label || '全部类别'
})

const filterChips = computed(() => [
  getMetricLabel(selectedMetric.value),
  selectedTimeRangeLabel.value,
  selectedCategoryLabel.value,
  `Top ${selectedTopN.value}`,
  useCaseLabel(selectedUseCase.value)
])

const chartStatusText = computed(() => {
  if (trendLoading.value) return '正在加载 OpenRank 月度序列…'
  if (trendError.value && activeChart.value?.needsTrendData) return trendError.value
  if (!scopedProjects.value.length) return '当前筛选没有可绘制项目'
  return ''
})

const activeFavoriteKey = computed(() => {
  if (!activeChart.value) return ''
  return [
    'visual-lab',
    activeChart.value.id,
    selectedMetric.value,
    selectedTimeRange.value,
    selectedProjectCategory.value,
    selectedTopN.value
  ].join(':')
})

const isActiveFavorite = computed(() => {
  return !!activeFavoriteKey.value && favStore.isPlanKeyFavorited(activeFavoriteKey.value)
})

const categoryCount = (categoryId) => {
  if (categoryId === 'all') return chartRegistry.length
  if (categoryId === 'favorites') return favoriteChartIds.value.length
  return chartRegistry.filter(chart => chart.category === categoryId).length
}

const categoryLabel = (categoryId) => {
  return chartCategories.find(category => category.id === categoryId)?.label || '全部图表'
}

const useCaseLabel = (useCaseId) => {
  return useCaseOptions.find(option => option.value === useCaseId)?.label || '全部用途'
}

const metricDisplay = (project) => {
  return formatNumber(Number(project?.[selectedMetric.value]) || 0)
}

const resetChartFilters = () => {
  selectedChartCategory.value = 'all'
  selectedUseCase.value = 'all'
}

const loadSummary = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await llmApi.getSummary()
    allProjects.value = res.data.projects || []
    if (!allProjects.value.length) {
      error.value = '汇总接口返回为空，请确认后端已经生成 LLM 生态数据。'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || '无法连接 LLM 汇总接口'
  } finally {
    loading.value = false
    await nextTick()
    if (analysisOpen.value) await renderActiveChart()
  }
}

const openChart = async (chart) => {
  if (!chart) return
  selectedChartId.value = chart.id
  analysisOpen.value = true
  aiReport.value = ''
  actionMessage.value = ''
  await router.replace({ name: 'llm-visual-lab', params: { chartId: chart.id } })
  await nextTick()
  closeButtonRef.value?.focus()
  await renderActiveChart()
}

const closeAnalysis = async () => {
  disposeChart()
  analysisOpen.value = false
  actionMessage.value = ''
  await router.replace({ name: 'llm-visual-lab' })
}

const renderActiveChart = async () => {
  if (!analysisOpen.value || !chartRef.value || !activeChart.value) return
  chartReady.value = false
  await ensureTrendData()
  await nextTick()
  await new Promise(resolve => window.requestAnimationFrame(resolve))

  if (chartInstance && chartInstance.getDom() !== chartRef.value) {
    disposeChart()
  }

  if (!chartInstance && chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option = buildChartOption({
    chartId: activeChart.value.id,
    projects: scopedProjects.value,
    metric: selectedMetric.value,
    timeRange: selectedTimeRange.value,
    trendData: trendData.value
  })

  chartInstance.setOption(option, true)
  chartInstance.resize()
  chartReady.value = true
}

const disposeChart = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  chartReady.value = false
}

const ensureTrendData = async () => {
  trendError.value = ''
  if (!activeChart.value?.needsTrendData) return

  const targets = scopedProjects.value.slice(0, 8)
  const missing = targets.filter(project => !trendData.value[project.project_key])
  if (!missing.length) return

  trendLoading.value = true
  try {
    const entries = await Promise.all(missing.map(async project => {
      const series = await fetchOpenRankSeries(project)
      return [project.project_key, series]
    }))
    trendData.value = {
      ...trendData.value,
      ...Object.fromEntries(entries)
    }
  } catch (err) {
    trendError.value = '部分趋势数据不可用，当前图表会使用汇总指标保持可视化。'
  } finally {
    trendLoading.value = false
  }
}

const fetchOpenRankSeries = async (project) => {
  try {
    const res = await opendiggerApi.getRepoData(project.platform || 'github', project.org, project.repo, 'openrank')
    const raw = res.data.data || []
    return raw
      .map(point => {
        if (Array.isArray(point)) return { month: point[0], value: Number(point[1]) || 0 }
        return { month: point.month, value: Number(point.count ?? point.value) || 0 }
      })
      .filter(point => point.month)
      .sort((a, b) => pointMonth(a.month).localeCompare(pointMonth(b.month)))
  } catch (err) {
    return []
  }
}

const pointMonth = (month) => String(month || '').slice(0, 7)

const toggleActiveFavorite = async () => {
  if (!activeChart.value) return
  if (!token.value) {
    window.alert('请先登录再收藏图表')
    return
  }

  if (!favStore.favorites.length) await favStore.fetchFavorites()

  const repos = scopedProjects.value.map(project => compactProjectName(project.project_key))
  const payload = {
    type: 'visual_lab_chart',
    chartId: activeChart.value.id,
    chartName: activeChart.value.name,
    metric: selectedMetric.value,
    topN: selectedTopN.value,
    timeRange: selectedTimeRange.value,
    category: selectedProjectCategory.value,
    repos,
    projects: repos,
    filters: {
      metricLabel: getMetricLabel(selectedMetric.value),
      timeRangeLabel: selectedTimeRangeLabel.value,
      categoryLabel: selectedCategoryLabel.value
    }
  }

  const ok = await favStore.togglePlanByKey({
    uniq_key: activeFavoriteKey.value,
    title: `可视化工坊：${activeChart.value.name}`,
    payload
  })
  actionMessage.value = ok ? (isActiveFavorite.value ? '已收藏当前图表方案' : '已取消收藏') : '收藏操作未完成'
}

const generateAiInsight = async () => {
  if (!scopedProjects.value.length) return
  aiLoading.value = true
  actionMessage.value = ''
  try {
    const projects = scopedProjects.value.slice(0, 5).map(project => ({
      repo: project.displayName,
      metrics: {
        activity: project.activityNorm,
        governance: project.openrankNorm,
        diversity: project.health,
        llm_fit: project.stability,
        sustainability: 1 - project.riskScore
      }
    }))
    const res = await llmApi.getReport({ projects })
    aiReport.value = res.data.report || ''
    actionMessage.value = res.data.from_llm ? '已生成 AI 解读' : '已生成规则兜底解读'
  } catch (err) {
    aiReport.value = activeInsights.value.join('\n')
    actionMessage.value = 'AI 接口不可用，已保留本地洞察'
  } finally {
    aiLoading.value = false
  }
}

const exportPng = () => {
  if (!chartInstance || !activeChart.value) return
  const url = chartInstance.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#07111f'
  })
  downloadUrl(url, `${activeChart.value.id}.png`)
  actionMessage.value = 'PNG 已导出'
}

const exportReport = () => {
  if (!activeChart.value) return
  const markdown = buildReportMarkdown({
    chart: activeChart.value,
    projects: scopedProjects.value,
    metric: selectedMetric.value,
    filters: {
      timeRangeLabel: selectedTimeRangeLabel.value,
      categoryLabel: selectedCategoryLabel.value,
      topN: selectedTopN.value
    },
    insights: activeInsights.value,
    aiReport: aiReport.value
  })
  downloadText(markdown, `${activeChart.value.id}-report.md`, 'text/markdown;charset=utf-8')
  actionMessage.value = '报告已导出'
}

const downloadText = (content, filename, type) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  downloadUrl(url, filename)
  URL.revokeObjectURL(url)
}

const downloadUrl = (url, filename) => {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const handleResize = () => {
  chartInstance?.resize()
}

watch(
  () => route.params.chartId,
  async chartId => {
    if (!chartId) {
      disposeChart()
      analysisOpen.value = false
      return
    }
    selectedChartId.value = String(chartId)
    analysisOpen.value = true
    await nextTick()
    await renderActiveChart()
  },
  { immediate: true }
)

watch(
  [selectedChartId, selectedMetric, selectedTimeRange, selectedTopN, selectedProjectCategory, searchQuery],
  async () => {
    aiReport.value = ''
    actionMessage.value = ''
    await nextTick()
    await renderActiveChart()
  }
)

watch(visibleCharts, charts => {
  if (charts.length && !charts.some(chart => chart.id === selectedChartId.value)) {
    selectedChartId.value = charts[0].id
  }
})

onMounted(async () => {
  await loadSummary()
  if (token.value) await favStore.fetchFavorites()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  disposeChart()
})
</script>

<style scoped>
.visual-lab-view {
  --lab-bg: #07111f;
  --lab-panel: rgba(10, 18, 38, 0.92);
  --lab-panel-strong: rgba(13, 23, 48, 0.98);
  --lab-border: rgba(125, 169, 230, 0.28);
  --lab-border-strong: rgba(56, 189, 248, 0.55);
  --lab-text: #e5f2ff;
  --lab-muted: #9fb2d8;
  --lab-soft: #12213d;
  --lab-blue: #38bdf8;
  --lab-green: #22c55e;
  --lab-pink: #fb7185;

  min-height: calc(100vh - 70px);
  margin: -2.5rem;
  padding: 28px;
  color: var(--lab-text);
  background:
    radial-gradient(circle at 12% 0%, rgba(20, 184, 166, 0.28), transparent 32%),
    radial-gradient(circle at 88% 8%, rgba(59, 130, 246, 0.25), transparent 34%),
    linear-gradient(135deg, #07111f 0%, #0b1730 52%, #111827 100%);
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.lab-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  align-items: end;
  max-width: 1500px;
  margin: 0 auto 20px;
}

.hero-copy {
  min-width: 0;
}

.eyebrow,
.section-kicker {
  margin: 0 0 8px;
  color: #7dd3fc;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.lab-hero h1 {
  margin: 0;
  color: #f8fbff;
  font-size: 34px;
  line-height: 1.16;
  font-weight: 850;
}

.lab-hero p {
  max-width: 760px;
  margin: 12px 0 0;
  color: #b7c7e7;
  font-size: 15px;
  line-height: 1.7;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(88px, 1fr));
  gap: 10px;
  margin: 0;
}

.hero-stats div {
  padding: 14px 16px;
  border: 1px solid var(--lab-border);
  border-radius: 8px;
  background: rgba(8, 15, 32, 0.68);
}

.hero-stats dt {
  color: var(--lab-muted);
  font-size: 12px;
}

.hero-stats dd {
  margin: 2px 0 0;
  color: #f8fbff;
  font-size: 24px;
  font-weight: 850;
}

.filter-bar {
  max-width: 1500px;
  margin: 0 auto 18px;
  display: grid;
  grid-template-columns: minmax(150px, 1.1fr) minmax(126px, 0.75fr) minmax(150px, 0.9fr) 96px minmax(132px, 0.8fr) minmax(180px, 1fr) auto;
  gap: 12px;
  align-items: end;
  padding: 14px;
  border: 1px solid rgba(125, 169, 230, 0.25);
  border-radius: 8px;
  background: rgba(6, 12, 28, 0.78);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.2);
}

.filter-field,
.analysis-controls label {
  display: grid;
  gap: 6px;
  min-width: 0;
  color: #b7c7e7;
  font-size: 12px;
  font-weight: 700;
}

.filter-field select,
.filter-field input,
.analysis-controls select,
.analysis-controls input {
  width: 100%;
  min-width: 0;
  height: 38px;
  padding: 0 12px;
  border: 1px solid rgba(125, 169, 230, 0.38);
  border-radius: 8px;
  color: #e5f2ff;
  background: rgba(8, 15, 32, 0.92);
}

.filter-field input::placeholder {
  color: #64748b;
}

.filter-field select:focus,
.filter-field input:focus,
.analysis-controls select:focus,
.analysis-controls input:focus,
.category-item:focus,
.chart-card:focus,
button:focus-visible {
  outline: none;
  border-color: var(--lab-blue);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.18);
}

.primary-action,
.panel-actions button,
.analysis-actions button,
.state-box button {
  height: 38px;
  padding: 0 16px;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #06111f;
  background: linear-gradient(135deg, #2dd4bf, #60a5fa);
  font-weight: 850;
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease, border-color 0.18s ease;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.46;
}

button:not(:disabled):hover {
  transform: translateY(-1px);
}

.lab-shell {
  max-width: 1500px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr) 286px;
  gap: 18px;
  align-items: start;
}

.category-rail,
.insight-panel,
.gallery-region {
  border: 1px solid var(--lab-border);
  border-radius: 8px;
  background: var(--lab-panel);
  box-shadow: 0 20px 54px rgba(0, 0, 0, 0.24);
}

.category-rail {
  position: sticky;
  top: 86px;
  display: grid;
  gap: 8px;
  padding: 12px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #c7d2fe;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.category-item strong {
  color: #7dd3fc;
  font-weight: 850;
}

.category-item.active,
.category-item:hover {
  border-color: rgba(56, 189, 248, 0.42);
  color: #f8fbff;
  background: rgba(56, 189, 248, 0.12);
}

.gallery-region {
  min-width: 0;
  padding: 18px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: end;
  margin-bottom: 14px;
}

.section-head h2,
.insight-panel h2,
.analysis-controls h2,
.analysis-titlebar h2,
.analysis-insights h2 {
  margin: 0;
  color: #f8fbff;
  font-size: 20px;
  font-weight: 850;
  line-height: 1.25;
}

.section-head p {
  max-width: 420px;
  margin: 0;
  color: var(--lab-muted);
  font-size: 13px;
  line-height: 1.6;
  text-align: right;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 14px;
}

.chart-card {
  display: grid;
  gap: 12px;
  min-height: 286px;
  padding: 16px;
  border: 1px solid rgba(125, 169, 230, 0.26);
  border-radius: 8px;
  color: inherit;
  background: rgba(8, 15, 32, 0.76);
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.chart-card:hover,
.chart-card.selected {
  transform: translateY(-2px);
  border-color: var(--lab-border-strong);
  background: rgba(13, 23, 48, 0.98);
}

.chart-card.recommended {
  border-color: rgba(45, 212, 191, 0.42);
}

.card-topline,
.card-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.chart-type,
.recommend-chip,
.card-meta span,
.filter-chips span,
.data-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid rgba(125, 169, 230, 0.25);
  border-radius: 999px;
  color: #b7c7e7;
  background: rgba(15, 23, 42, 0.72);
  font-size: 11px;
  font-weight: 750;
}

.recommend-chip {
  color: #bbf7d0;
  border-color: rgba(34, 197, 94, 0.36);
}

.chart-card h3 {
  margin: 0;
  color: #f8fbff;
  font-size: 17px;
  font-weight: 850;
  line-height: 1.35;
}

.chart-card p {
  min-height: 42px;
  margin: 0;
  color: #aabadd;
  font-size: 13px;
  line-height: 1.6;
}

.preview-frame {
  position: relative;
  display: grid;
  height: 94px;
  overflow: hidden;
  border: 1px solid rgba(125, 169, 230, 0.22);
  border-radius: 8px;
  background:
    linear-gradient(rgba(125, 169, 230, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(125, 169, 230, 0.08) 1px, transparent 1px),
    rgba(5, 10, 25, 0.72);
  background-size: 24px 24px;
}

.preview-bars {
  align-content: end;
  grid-template-columns: 1fr;
  padding: 14px;
  gap: 5px;
}

.preview-bars span {
  height: 7px;
  border-radius: 999px;
  background: linear-gradient(90deg, #22c55e, #38bdf8);
}

.preview-bars span:nth-child(1) { width: 86%; }
.preview-bars span:nth-child(2) { width: 72%; }
.preview-bars span:nth-child(3) { width: 66%; }
.preview-bars span:nth-child(4) { width: 54%; }
.preview-bars span:nth-child(n + 5) { display: none; }

.preview-matrix,
.preview-risk {
  grid-template-columns: repeat(6, 1fr);
  gap: 6px;
  padding: 14px;
}

.preview-matrix span,
.preview-risk span {
  border-radius: 5px;
  background: #0ea5e9;
}

.preview-matrix span:nth-child(3n),
.preview-risk span:nth-child(4n) { background: #22c55e; }
.preview-risk span:nth-child(5n) { background: #fb7185; }

.preview-sunburst::before,
.preview-radar::before {
  content: "";
  width: 74px;
  height: 74px;
  margin: auto;
  border-radius: 50%;
  background: conic-gradient(#22c55e, #38bdf8, #a78bfa, #f59e0b, #22c55e);
}

.preview-radar::before {
  border-radius: 28% 72% 50% 50%;
  clip-path: polygon(50% 0, 90% 34%, 72% 94%, 28% 94%, 10% 34%);
}

.preview-treemap {
  grid-template-columns: 1.2fr 0.8fr 1fr;
  grid-template-rows: 1fr 0.8fr;
  gap: 6px;
  padding: 12px;
}

.preview-treemap span {
  border-radius: 6px;
  background: #38bdf8;
}

.preview-treemap span:nth-child(1) { grid-row: span 2; background: #22c55e; }
.preview-treemap span:nth-child(2) { background: #a78bfa; }
.preview-treemap span:nth-child(3) { background: #f59e0b; }
.preview-treemap span:nth-child(n + 5) { display: none; }

.preview-bubble,
.preview-network {
  display: block;
}

.preview-bubble span,
.preview-network span {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #38bdf8;
}

.preview-bubble span:nth-child(1) { width: 32px; height: 32px; left: 24%; top: 42%; background: #22c55e; }
.preview-bubble span:nth-child(2) { width: 22px; height: 22px; left: 52%; top: 26%; background: #a78bfa; }
.preview-bubble span:nth-child(3) { width: 18px; height: 18px; left: 68%; top: 58%; background: #f59e0b; }
.preview-bubble span:nth-child(n + 4) { display: none; }

.preview-line,
.preview-bump,
.preview-sankey {
  display: block;
}

.preview-line::before,
.preview-bump::before,
.preview-sankey::before {
  content: "";
  position: absolute;
  inset: 18px 14px;
  background:
    linear-gradient(140deg, transparent 0 20%, #38bdf8 21% 23%, transparent 24% 44%, #22c55e 45% 47%, transparent 48% 70%, #a78bfa 71% 73%, transparent 74%),
    linear-gradient(35deg, transparent 0 34%, rgba(45, 212, 191, 0.9) 35% 37%, transparent 38%);
}

.preview-bump::before {
  background:
    linear-gradient(25deg, transparent 0 24%, #f472b6 25% 27%, transparent 28% 48%, #38bdf8 49% 51%, transparent 52%),
    linear-gradient(150deg, transparent 0 24%, #22c55e 25% 27%, transparent 28% 62%, #f59e0b 63% 65%, transparent 66%);
}

.preview-sankey::before {
  inset: 20px 18px;
  border-left: 10px solid #22c55e;
  border-right: 10px solid #38bdf8;
  border-radius: 10px;
  background: linear-gradient(100deg, rgba(34, 197, 94, 0.6), rgba(56, 189, 248, 0.62));
  filter: blur(0.2px);
}

.preview-network span:nth-child(1) { left: 20%; top: 50%; background: #22c55e; }
.preview-network span:nth-child(2) { left: 42%; top: 30%; background: #38bdf8; }
.preview-network span:nth-child(3) { left: 62%; top: 55%; background: #a78bfa; }
.preview-network span:nth-child(4) { left: 76%; top: 28%; background: #f59e0b; }
.preview-network span:nth-child(n + 5) { display: none; }

.preview-network::before {
  content: "";
  position: absolute;
  inset: 26px 34px;
  background:
    linear-gradient(25deg, transparent 0 48%, rgba(56, 189, 248, 0.55) 49% 51%, transparent 52%),
    linear-gradient(145deg, transparent 0 48%, rgba(34, 197, 94, 0.55) 49% 51%, transparent 52%);
}

.insight-panel {
  position: sticky;
  top: 86px;
  display: grid;
  gap: 16px;
  padding: 18px;
}

.panel-block {
  display: grid;
  gap: 8px;
}

.panel-block p,
.question-text {
  margin: 0;
  color: #b7c7e7;
  font-size: 13px;
  line-height: 1.65;
}

.panel-block h3,
.mini-ranking h3,
.ai-report h3 {
  margin: 0;
  color: #f8fbff;
  font-size: 14px;
  font-weight: 850;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.insight-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.insight-list li {
  position: relative;
  padding-left: 16px;
  color: #b7c7e7;
  font-size: 13px;
  line-height: 1.6;
}

.insight-list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.7em;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #22c55e;
}

.panel-actions,
.analysis-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.panel-actions button,
.analysis-actions button,
.state-box button {
  height: 34px;
  padding: 0 12px;
  color: #dbeafe;
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.32);
}

.state-box {
  display: grid;
  place-items: center;
  gap: 10px;
  min-height: 300px;
  text-align: center;
  color: #b7c7e7;
}

.state-box h3 {
  margin: 0;
  color: #f8fbff;
  font-weight: 850;
}

.state-box p {
  margin: 0;
}

.error-state {
  color: #fecaca;
}

.skeleton-card {
  pointer-events: none;
}

.skeleton-line,
.skeleton-visual {
  overflow: hidden;
  border-radius: 8px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.12), rgba(56, 189, 248, 0.2), rgba(148, 163, 184, 0.12));
  background-size: 200% 100%;
  animation: pulse 1.4s infinite linear;
}

.skeleton-line {
  width: 70%;
  height: 14px;
}

.skeleton-line.wide { width: 90%; }
.skeleton-line.short { width: 46%; }

.skeleton-visual {
  height: 94px;
}

@keyframes pulse {
  to { background-position: -200% 0; }
}

.analysis-overlay {
  position: fixed;
  inset: 0;
  z-index: 1800;
  padding: 24px;
  background: rgba(2, 6, 23, 0.82);
  backdrop-filter: blur(10px);
}

.analysis-workbench {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr) 300px;
  gap: 16px;
  width: min(1560px, 100%);
  height: min(860px, calc(100vh - 48px));
  margin: 0 auto;
}

.analysis-controls,
.analysis-canvas-panel,
.analysis-insights {
  min-height: 0;
  overflow: auto;
  border: 1px solid var(--lab-border);
  border-radius: 8px;
  background: var(--lab-panel-strong);
  box-shadow: 0 26px 80px rgba(0, 0, 0, 0.42);
}

.analysis-controls,
.analysis-insights {
  position: relative;
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 18px;
}

.close-button {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 34px;
  height: 34px;
  border: 1px solid rgba(125, 169, 230, 0.26);
  border-radius: 8px;
  color: #dbeafe;
  background: rgba(15, 23, 42, 0.88);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.mini-ranking {
  display: grid;
  gap: 10px;
  margin-top: 4px;
}

.mini-ranking ol {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.mini-ranking li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid rgba(125, 169, 230, 0.2);
  border-radius: 8px;
  background: rgba(8, 15, 32, 0.72);
}

.mini-ranking span {
  min-width: 0;
  overflow: hidden;
  color: #dbeafe;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mini-ranking strong {
  color: #7dd3fc;
  font-weight: 850;
}

.analysis-canvas-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  padding: 18px;
}

.analysis-titlebar {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: start;
  margin-bottom: 12px;
}

.analysis-titlebar p {
  margin: 8px 0 0;
  color: #b7c7e7;
  line-height: 1.6;
}

.chart-stage {
  position: relative;
  min-height: 420px;
  overflow: hidden;
  border: 1px solid rgba(125, 169, 230, 0.2);
  border-radius: 8px;
  background:
    linear-gradient(rgba(125, 169, 230, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(125, 169, 230, 0.06) 1px, transparent 1px),
    rgba(5, 10, 25, 0.58);
  background-size: 28px 28px;
}

.analysis-chart {
  position: absolute;
  inset: 0;
  min-width: 0;
  min-height: 420px;
}

.chart-status {
  position: absolute;
  left: 16px;
  top: 16px;
  z-index: 1;
  padding: 8px 10px;
  border: 1px solid rgba(56, 189, 248, 0.24);
  border-radius: 8px;
  color: #bfdbfe;
  background: rgba(8, 15, 32, 0.88);
  font-size: 12px;
}

.ai-report {
  display: grid;
  gap: 8px;
  max-height: 230px;
  overflow: auto;
  padding: 12px;
  border: 1px solid rgba(125, 169, 230, 0.22);
  border-radius: 8px;
  background: rgba(8, 15, 32, 0.72);
}

.ai-report p {
  margin: 0;
  color: #c7d2fe;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
}

.action-message {
  padding: 9px 10px;
  border: 1px solid rgba(34, 197, 94, 0.28);
  border-radius: 8px;
  color: #bbf7d0;
  background: rgba(34, 197, 94, 0.1);
  font-size: 12px;
}

@media (max-width: 1180px) {
  .filter-bar {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .lab-shell {
    grid-template-columns: 180px minmax(0, 1fr);
  }

  .insight-panel {
    position: static;
    grid-column: 1 / -1;
  }

  .analysis-workbench {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .analysis-insights {
    grid-column: 1 / -1;
    max-height: 260px;
  }
}

@media (max-width: 760px) {
  .visual-lab-view {
    margin: -1rem;
    padding: 14px;
  }

  .lab-hero,
  .filter-bar,
  .lab-shell,
  .analysis-workbench {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    grid-template-columns: repeat(3, 1fr);
  }

  .section-head,
  .analysis-titlebar {
    display: grid;
  }

  .section-head p {
    max-width: none;
    text-align: left;
  }

  .category-rail {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .insight-panel {
    position: static;
  }

  .analysis-overlay {
    padding: 10px;
    overflow: auto;
  }

  .analysis-workbench {
    height: auto;
  }

  .analysis-controls,
  .analysis-canvas-panel,
  .analysis-insights {
    overflow: visible;
  }

  .chart-stage,
  .analysis-chart {
    min-height: 360px;
  }
}

@media (max-width: 420px) {
  .hero-stats,
  .category-rail,
  .gallery-grid {
    grid-template-columns: 1fr;
  }

  .lab-hero h1 {
    font-size: 28px;
  }
}
</style>
