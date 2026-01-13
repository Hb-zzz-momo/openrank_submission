<template>
  <div ref="chartRef" class="radar-chart"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null

const indicators = [
  { name: '活跃度',       key: 'activity',       max: 1 },
  { name: '治理质量',     key: 'governance',     max: 1 },
  { name: '多样性',       key: 'diversity',      max: 1 },
  { name: 'LLM 适配度',   key: 'llm_fit',        max: 1 },
  { name: '可持续性',     key: 'sustainability', max: 1 }
]

// 自定义颜色方案：青色 / 紫色 / 黄色 / 绿色 / 粉色
const colorPalette = ['#38bdf8', '#a855f7', '#facc15', '#22c55e', '#fb7185']

const renderChart = () => {
  if (!chartRef.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const seriesData = props.data.map((item, idx) => ({
    name: item.repo,
    value: indicators.map(ind =>
      Number((item.metrics?.[ind.key] ?? 0).toFixed(3))
    ),
    lineStyle: {
      width: 2.4,
      color: colorPalette[idx % colorPalette.length],
      opacity: 0.9
    },
    areaStyle: {
      opacity: 0.16,
      color: colorPalette[idx % colorPalette.length]
    },
    symbolSize: 4
  }))

  const option = {
    backgroundColor: 'transparent',
    color: colorPalette,
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: 'rgba(148, 163, 184, 0.7)',
      textStyle: { color: '#e5e7eb', fontSize: 12 }
    },
    legend: {
      data: props.data.map(item => item.repo),
      top: 8,
      textStyle: {
        color: '#e5e7eb',
        fontSize: 11
      },
      icon: 'circle'
    },
    radar: {
      radius: '65%',
      splitNumber: 5,
      indicator: indicators.map(i => ({
        name: i.name,
        max: i.max
      })),
      axisName: {
        color: '#cbd5f5',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: [
            'rgba(148, 163, 184, 0.5)',
            'rgba(148, 163, 184, 0.35)',
            'rgba(148, 163, 184, 0.25)',
            'rgba(148, 163, 184, 0.18)',
            'rgba(148, 163, 184, 0.1)'
          ]
        }
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(15, 23, 42, 0.9)',
            'rgba(15, 23, 42, 0.92)',
            'rgba(15, 23, 42, 0.95)',
            'rgba(15, 23, 42, 0.98)',
            'rgba(15, 23, 42, 1)'
          ]
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(148, 163, 184, 0.6)'
        }
      }
    },
    series: [
      {
        type: 'radar',
        data: seriesData,
        emphasis: {
          lineStyle: {
            width: 3.6
          },
          areaStyle: {
            opacity: 0.28
          }
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance && chartInstance.resize()
}

onMounted(() => {
  if (props.data && props.data.length) {
    renderChart()
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance && chartInstance.dispose()
})

watch(
  () => props.data,
  () => {
    if (props.data && props.data.length) {
      renderChart()
    } else if (chartInstance) {
      chartInstance.clear()
    }
  },
  { deep: true }
)
</script>

<style scoped>
.radar-chart {
  width: 100%;
  height: 380px;
  border-radius: 14px;
  background:
    radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.12), transparent 55%),
    radial-gradient(circle at 0% 100%, rgba(168, 85, 247, 0.12), transparent 55%),
    radial-gradient(circle at 100% 100%, rgba(250, 204, 21, 0.14), transparent 55%);
  box-shadow: inset 0 0 0 1px rgba(30, 64, 175, 0.4);
}
</style>
