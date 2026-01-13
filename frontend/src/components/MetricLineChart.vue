<!-- frontend/src/components/MetricLineChart.vue -->
<template>
  <div class="metric-line-wrapper">
    <div class="metric-toolbar">
      <label>指标：</label>
      <select v-model="metric" @change="loadData">
        <option value="activity">活跃度（activity）</option>
        <option value="governance">治理质量（openrank）</option>
        <option value="diversity">多样性（new_contributors）</option>
        <option value="llm_fit">LLM 适配度（stars）</option>
        <option value="sustainability">可持续性（bus_factor）</option>
      </select>

      <label style="margin-left: 12px;">时间粒度：</label>
      <select v-model="granularity" disabled>
        <option value="month">按月</option>
      </select>
    </div>

    <div ref="chartRef" style="width: 100%; height: 380px;"></div>

    <p v-if="noData" class="empty-tip">
      当前选中的项目在该指标上暂无时间序列数据，请尝试更换指标或项目。
    </p>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { opendiggerApi } from '../api/api'

// 父组件传进来的：选中的项目（值是 "org/repo"）
const props = defineProps({
  ids: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null

const metric = ref('diversity')  // 默认选“多样性”
const granularity = ref('month')

const noData = ref(false)
const timeAxis = ref([])   // x 轴时间
const seriesData = ref([]) // 折线数据

// 前端指标 -> OpenDigger metric 的映射（你后面可以按需要改）
const metricMap = {
  activity: 'activity',
  governance: 'openrank',
  diversity: 'new_contributors',
  llm_fit: 'stars',
  sustainability: 'bus_factor'
}

const initChart = () => {
  if (!chartInstance && chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
  }
}

const renderChart = () => {
  if (!chartInstance) return

  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: seriesData.value.map(s => s.name)
    },
    xAxis: {
      type: 'category',
      data: timeAxis.value
    },
    yAxis: {
      type: 'value'
    },
    series: seriesData.value
  }

  chartInstance.setOption(option)
}

const loadData = async () => {
  if (!props.ids.length) {
    noData.value = true
    timeAxis.value = []
    seriesData.value = []
    chartInstance && chartInstance.clear()
    return
  }

  initChart()

  const odMetric = metricMap[metric.value] || 'activity'
  console.log('请求 OpenDigger metric =', odMetric)

  try {
    // 对每一个选中的 "org/repo" 发一次 /api/data/github/org/repo/metric
    const requests = props.ids.map(async id => {
      const [org, repo] = id.split('/')
      const res = await opendiggerApi.getRepoData('github', org, repo, odMetric)
      const raw = res.data.data || []

      // 兼容两种格式：
      // 1) [[month, count], ...]
      // 2) [{month: '2024-01', count: 123}, ...]
      let points
      if (raw.length && Array.isArray(raw[0])) {
        points = raw.map(([month, value]) => ({ month, value }))
      } else if (raw.length && typeof raw[0] === 'object') {
        points = raw.map(p => ({ month: p.month, value: p.count }))
      } else {
        points = []
      }

      return { id, points }
    })

    const results = await Promise.all(requests)
    const nonEmpty = results.filter(r => r.points.length)

    if (!nonEmpty.length) {
      noData.value = true
      timeAxis.value = []
      seriesData.value = []
      chartInstance && chartInstance.clear()
      return
    }

    noData.value = false

    // 汇总所有时间点，并排序
    const axis = Array.from(
      new Set(nonEmpty.flatMap(r => r.points.map(p => p.month)))
    ).sort()

    timeAxis.value = axis

    // 每个项目一条线，按统一时间轴对齐
    seriesData.value = nonEmpty.map(r => ({
      name: r.id,
      type: 'line',
      smooth: true,
      data: axis.map(month => {
        const p = r.points.find(p => p.month === month)
        return p ? Number(p.value) : null
      })
    }))

    renderChart()
  } catch (e) {
    console.error('加载时间序列失败：', e)
    noData.value = true
    timeAxis.value = []
    seriesData.value = []
    chartInstance && chartInstance.clear()
  }
}

const handleResize = () => {
  chartInstance && chartInstance.resize()
}

onMounted(() => {
  initChart()
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance && chartInstance.dispose()
})

// 当选中的项目或指标变化时，重新加载
watch(
  () => [props.ids, metric.value],
  () => {
    loadData()
  },
  { deep: true }
)
</script>

<style scoped>
.metric-toolbar {
  margin-bottom: 8px;
  font-size: 13px;
}
.empty-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}
</style>
