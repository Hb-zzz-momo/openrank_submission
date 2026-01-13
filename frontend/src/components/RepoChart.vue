<template>
  <div class="repo-chart-container">
    <!-- 加载/错误提示 -->
    <div v-if="loading" class="status-tip">
      <div class="spinner-small"></div>
      <span>加载中...</span>
    </div>
    <div v-else-if="errorMsg" class="status-tip error">
      <span>{{ errorMsg }}</span>
    </div>

    <!-- 主内容区 -->
    <div v-else-if="dataStats.hasData" class="chart-content">
      <!-- 🔥 股票风格数据面板 -->
      <div class="data-panel">
        <!-- 左侧：当前值 + 涨跌幅 -->
        <div class="panel-left">
          <div class="current-value">{{ dataStats.currentValue }}</div>
          <div class="change-info" :class="`trend-${dataStats.trend}`">
            <span class="change-icon">
              {{ dataStats.trend === 'up' ? '▲' : dataStats.trend === 'down' ? '▼' : '━' }}
            </span>
            <span class="change-value">
              {{ dataStats.change >= 0 ? '+' : '' }}{{ dataStats.change }}
            </span>
            <span class="change-percent">
              ({{ dataStats.changePercent >= 0 ? '+' : '' }}{{ dataStats.changePercent }}%)
            </span>
          </div>
        </div>

        <!-- 右侧：对比数据 -->
        <div class="panel-right">
          <div class="info-row">
            <span class="info-label">上期值:</span>
            <span class="info-value">{{ dataStats.previousValue }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">上期时间:</span>
            <span class="info-value">{{ dataStats.previousTime }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">当前时间:</span>
            <span class="info-value">{{ dataStats.updateTime }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">12月均值:</span>
            <span class="info-value">{{ dataStats.avgValue }}</span>
            <span class="info-value" :class="dataStats.vsAvg >= 0 ? 'text-green' : 'text-red'">
              ({{ dataStats.vsAvg >= 0 ? '+' : '' }}{{ dataStats.vsAvgPercent }}%)
            </span>
          </div>
        </div>
        <button class="refresh-btn" @click="loadData" title="刷新数据">
          🔄
        </button>
      </div>

      <!-- 图表区域 -->
      <div ref="chartRef" class="chart"></div>
    </div>

    <!-- 无数据提示 -->
    <div v-else class="status-tip">
      <span>暂无可用数据</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { opendiggerApi } from '@/api/api'

/**
 * 这个组件只做一件事：
 * 给定 org/repo/metric，去后端拉数据，然后用 ECharts 画折线图。
 */
const props = defineProps({
  platform: { type: String, default: 'github' },
  org: { type: String, default: '' },
  repo: { type: String, default: '' },
  metric: { type: String, required: true },
  title: { type: String, default: '' }
})

const loading = ref(false)
const errorMsg = ref('')
const chartRef = ref(null)
let chartInstance = null
const chartData = ref([])

const dataStats = computed(() => {
  if (!chartData.value.length) {
    return {
      hasData: false,
      currentValue: 0,
      previousValue: 0,
      change: 0,
      changePercent: 0,
      trend: 'neutral',
      updateTime: '-'
    }
  }

  const sorted = [...chartData.value].sort((a, b) => a.month.localeCompare(b.month))
  const latest = sorted[sorted.length - 1]
  const previous = sorted.length > 1 ? sorted[sorted.length - 2] : null

  const currentValue = latest.count
  const previousValue = previous ? previous.count : currentValue
  const change = currentValue - previousValue
  const changePercent = previousValue !== 0 ? ((change / previousValue) * 100) : 0
  const recentData = sorted.slice(-12)  // 取最近12个月
  const avgValue = recentData.reduce((sum, d) => sum + d.count, 0) / recentData.length

  let trend = 'neutral'
  if (change > 0) trend = 'up'
  else if (change < 0) trend = 'down'

  return {
    hasData: true,
    currentValue: Number(currentValue).toFixed(2),
    previousValue: Number(previousValue).toFixed(2),
    change: Number(change).toFixed(2),
    changePercent: Number(changePercent).toFixed(2),
    trend,
    updateTime: latest.month,
    previousTime: previous ? previous.month : '-',
    avgValue: Number(avgValue).toFixed(2),
    vsAvg: Number(currentValue - avgValue).toFixed(2),
    vsAvgPercent: avgValue !== 0 ? Number(((currentValue - avgValue) / avgValue) * 100).toFixed(2) : 0
  }
})

const finalTitle = computed(() => {
  if (props.title) return props.title
  if (props.org && props.repo) return `${props.org}/${props.repo} - ${props.metric}`
  return props.metric
})

function ensureChart() {
  if (!chartRef.value) return
  // 避免 “There is a chart instance already initialized on the dom”
  const existed = echarts.getInstanceByDom(chartRef.value)
  chartInstance = existed || echarts.init(chartRef.value)
}

function normalizeRecords(raw) {
  if (!Array.isArray(raw)) return []
  // 兼容两种格式：[{month,count}] 或 [[month,value]]
  if (raw.length && Array.isArray(raw[0])) {
    return raw
      .map(x => ({ month: x?.[0], count: x?.[1] }))
      .filter(x => x.month && typeof x.count === 'number')
  }
  return raw
    .map(x => ({ month: x?.month, count: x?.count ?? x?.value }))
    .filter(x => x.month && typeof x.count === 'number')
}

function renderChart() {
  if (!chartRef.value) return
  if (!chartData.value.length) return

  ensureChart()

  const months = chartData.value.map(d => d.month)
  const values = chartData.value.map(d => d.count)

  const option = {
    title: { text: finalTitle.value, left: 'center', top: 6, textStyle: { fontSize: 12 } },
    tooltip: { trigger: 'axis' },
    grid: { left: '6%', right: '4%', top: '18%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value' },
    series: [{ type: 'line', data: values, smooth: true, symbol: 'none' }]
  }

  chartInstance.setOption(option, true)
  setTimeout(() => {
    if (chartInstance) {
      chartInstance.resize()
    }
  }, 100)
}

async function loadData() {
  // ✅ 防御：缺参数就别请求，直接提示
  if (!props.org || !props.repo) {
    chartData.value = []
    errorMsg.value = '仓库信息不完整（缺 org/repo），无法加载图表'
    return
  }

  loading.value = true
  errorMsg.value = ''
  chartData.value = []

  try {
    const res = await opendiggerApi.getRepoData(props.platform, props.org, props.repo, props.metric)
    const records = normalizeRecords(res?.data?.data)
    chartData.value = records

    if (!records.length) {
      errorMsg.value = '暂无可用数据'
      return
    }

    // 等 DOM 稳定后再画
    requestAnimationFrame(renderChart)
  } catch (e) {
    errorMsg.value = e?.response?.data?.detail || '加载数据失败'
  } finally {
    loading.value = false
  }
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
  if (chartRef.value) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && chartInstance) {
          // 图表进入视口时，延迟 100ms 后 resize
          setTimeout(() => {
            chartInstance.resize()
          }, 100)
        }
      })
    })
    
    observer.observe(chartRef.value)

    // 清理观察器
    onBeforeUnmount(() => {
      observer.disconnect()
    })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})

// ✅ 当用户切换 metric/org/repo 时自动刷新
watch(
  () => [props.platform, props.org, props.repo, props.metric],
  () => loadData()
)
</script>

<style scoped>
.repo-chart {
  width: 100%;
  height: 100%;
}
.chart {
  flex: 1;
  min-height: 280px;  /* 🔥 新增：确保最小高度 */
  max-height: 400px;  /* 🔥 新增：限制最大高度，避免过高 */
  width: 100%;
}
.tip {
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}
.tip.error {
  color: #ef4444;
}

.repo-chart-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* ========== 状态提示 ========== */
.status-tip {
  height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #64748b;
  font-size: 14px;
}

.status-tip.error {
  color: #ef4444;
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========== 主内容区 ========== */
.chart-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

/* ========== 股票风格数据面板 ========== */
.data-panel {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9));
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 10px;
  backdrop-filter: blur(10px);
}

/* 左侧：当前值 + 涨跌幅 */
.panel-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.current-value {
  font-size: 28px;
  font-weight: 700;
  color: #e5e7eb;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  line-height: 1;
}

.change-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

/* 涨跌趋势颜色 */
.change-info.trend-up {
  color: #22c55e;
}

.change-info.trend-down {
  color: #ef4444;
}

.change-info.trend-neutral {
  color: #94a3b8;
}

.change-icon {
  font-size: 12px;
}

.change-value {
  font-weight: 700;
}

.change-percent {
  opacity: 0.8;
}

/* 右侧：对比数据 */
.panel-right {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: right;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.info-label {
  color: #94a3b8;
}

.info-value {
  color: #cbd5e1;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-weight: 500;
}

/* ========== 图表区域 ========== */
.chart {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.refresh-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.refresh-btn:hover {
  background: rgba(56, 189, 248, 0.3);
  transform: rotate(180deg);
}

</style>
