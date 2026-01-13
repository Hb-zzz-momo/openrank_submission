<template>
  <div ref="chartRef" class="rank-chart"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  payload: {
    type: Object,
    required: true
  },
  metricLabel: {
    type: String,
    default: '综合健康度'
  }
})

const chartRef = ref(null)
let chartInstance = null

// 渲染图表（完全对齐LLMSummaryView的配置）
const renderChart = () => {
  if (!chartRef.value || !props.payload?.items) return
  
  // 销毁旧实例避免内存泄漏
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)

  // 从payload提取数据
  const names = props.payload.items.map(item => item.repo)
  const values = props.payload.items.map(item => item.value)

  // 复用LLMSummaryView的ECharts配置
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '5%', right: '5%', bottom: '8%', top: '10%', containLabel: true },
    xAxis: { 
      type: 'value', 
      name: props.metricLabel,
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
        // 与LLMSummaryView一致的渐变颜色
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#22c55e' },
          { offset: 1, color: '#38bdf8' }
        ])
      }
    }],
    backgroundColor: 'transparent'
  })
}

// 窗口大小变化时自适应
const handleResize = () => {
  if (chartInstance) chartInstance.resize()
}

// 监听payload变化重新渲染
watch(() => props.payload, () => {
  renderChart()
}, { deep: true })

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.rank-chart {
  width: 100%;
  max-width: 100%;
  height: 360px; /* 与LLMSummaryView的图表高度一致 */
}
</style>