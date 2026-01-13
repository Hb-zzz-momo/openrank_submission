<!-- frontend/src/components/ContributorRiskCard.vue -->
<template>
  <div class="risk-card" :class="riskLevelClass">
    <!-- 头部 -->
    <div class="risk-header">
      <div class="risk-icon">{{ riskIcon }}</div>
      <div class="risk-title">
        <h4>贡献者健康预警</h4>
        <span class="risk-badge" :class="riskLevelClass">{{ riskLevelText }}</span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="risk-loading">
      <div class="spinner-small"></div>
      <span>正在分析贡献者风险...</span>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="risk-error">
      <span>⚠️ {{ error }}</span>
    </div>

    <!-- 数据展示 -->
    <div v-else-if="riskData" class="risk-content">
      <!-- 核心指标 -->
      <div class="risk-metrics">
        <div class="metric-item">
          <div class="metric-value">{{ riskData.bus_factor_avg_6m }}</div>
          <div class="metric-label">巴士因子 (6M均值)</div>
        </div>
        <div class="metric-item">
          <div class="metric-value">{{ (riskData.risk_score * 100).toFixed(0) }}%</div>
          <div class="metric-label">风险指数</div>
        </div>
        <div class="metric-item">
          <div class="metric-value trend" :class="trendClass">{{ riskData.bus_factor_trend_text }}</div>
          <div class="metric-label">变化趋势</div>
        </div>
      </div>

      <!-- 风险说明 -->
      <div class="risk-message">
        <p>{{ riskData.message }}</p>
      </div>

      <!-- 建议（如果有） -->
      <div v-if="riskData.suggestion" class="risk-suggestion">
        <div class="suggestion-icon">💡</div>
        <p>{{ riskData.suggestion }}</p>
      </div>

      <!-- 详细数据折叠 -->
      <details class="risk-details">
        <summary>查看详细数据</summary>
        <div class="details-content">
          <p><strong>近6个月数值：</strong>{{ riskData.details?.recent_values?.join(', ') || 'N/A' }}</p>
          <p><strong>6个月最小值：</strong>{{ riskData.details?.min_6m || 'N/A' }}</p>
          <p><strong>6个月最大值：</strong>{{ riskData.details?.max_6m || 'N/A' }}</p>
          <p><strong>12个月均值：</strong>{{ riskData.bus_factor_avg_12m || 'N/A' }}</p>
        </div>
      </details>
    </div>

    <!-- 空状态 -->
    <div v-else class="risk-empty">
      <span>选择项目后查看贡献者风险分析</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { http } from '@/api/api'

const res = await http.get(`/api/health/contributor-risk/${props.platform}/${org}/${repo}`)

const props = defineProps({
  project: {
    type: String,
    default: ''
  },
  platform: {
    type: String,
    default: 'github'
  }
})

const loading = ref(false)
const error = ref('')
const riskData = ref(null)

// 风险等级样式映射
const riskLevelClass = computed(() => {
  if (!riskData.value) return ''
  const level = riskData.value.risk_level
  return {
    'critical': 'level-critical',
    'high': 'level-high',
    'medium': 'level-medium',
    'low': 'level-low',
    'healthy': 'level-healthy'
  }[level] || ''
})

// 风险等级文字
const riskLevelText = computed(() => {
  if (!riskData.value) return ''
  const level = riskData.value.risk_level
  return {
    'critical': '极高风险',
    'high': '高风险',
    'medium': '中风险',
    'low': '低风险',
    'healthy': '非常健康'
  }[level] || '未知'
})

// 风险图标
const riskIcon = computed(() => {
  if (!riskData.value) return '🔍'
  const level = riskData.value.risk_level
  return {
    'critical': '🔴',
    'high': '🟠',
    'medium': '🟡',
    'low': '🟢',
    'healthy': '✅'
  }[level] || '❓'
})

// 趋势样式
const trendClass = computed(() => {
  if (!riskData.value) return ''
  const trend = riskData.value.bus_factor_trend
  return {
    'improving': 'trend-up',
    'declining': 'trend-down',
    'stable': 'trend-stable'
  }[trend] || ''
})

// 获取风险数据
const fetchRiskData = async () => {
  if (!props.project) {
    riskData.value = null
    return
  }

  const parts = props.project.split('/')
  if (parts.length !== 2) {
    error.value = '项目格式错误'
    return
  }

  const [org, repo] = parts
  loading.value = true
  error.value = ''

  try {
    const res = await axios.get(
      `/api/health/contributor-risk/${props.platform}/${org}/${repo}`
    )
    riskData.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || '获取风险数据失败'
    riskData.value = null
  } finally {
    loading.value = false
  }
}

// 监听项目变化
watch(() => props.project, fetchRiskData, { immediate: true })
</script>

<style scoped>
.risk-card {
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.risk-card.level-critical {
  border-color: rgba(239, 68, 68, 0.6);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
}

.risk-card.level-high {
  border-color: rgba(249, 115, 22, 0.6);
  box-shadow: 0 0 20px rgba(249, 115, 22, 0.2);
}

.risk-card.level-medium {
  border-color: rgba(234, 179, 8, 0.6);
  box-shadow: 0 0 20px rgba(234, 179, 8, 0.2);
}

.risk-card.level-low,
.risk-card.level-healthy {
  border-color: rgba(34, 197, 94, 0.6);
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.2);
}

.risk-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.risk-icon {
  font-size: 28px;
}

.risk-title h4 {
  margin: 0;
  font-size: 16px;
  color: #e5e7eb;
  font-weight: 600;
}

.risk-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  margin-top: 4px;
}

.risk-badge.level-critical { background: #ef4444; color: white; }
.risk-badge.level-high { background: #f97316; color: white; }
.risk-badge.level-medium { background: #eab308; color: #1f2937; }
.risk-badge.level-low,
.risk-badge.level-healthy { background: #22c55e; color: white; }

.risk-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.metric-item {
  text-align: center;
  padding: 12px 8px;
  background: rgba(51, 65, 85, 0.5);
  border-radius: 10px;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #38bdf8;
}

.metric-value.trend-up { color: #22c55e; }
.metric-value.trend-down { color: #ef4444; }
.metric-value.trend-stable { color: #eab308; }

.metric-label {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 4px;
}

.risk-message {
  background: rgba(51, 65, 85, 0.4);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.risk-message p {
  margin: 0;
  font-size: 14px;
  color: #e5e7eb;
  line-height: 1.5;
}

.risk-suggestion {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.3);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 12px;
}

.suggestion-icon {
  font-size: 18px;
}

.risk-suggestion p {
  margin: 0;
  font-size: 13px;
  color: #fef3c7;
  line-height: 1.5;
}

.risk-details {
  margin-top: 12px;
}

.risk-details summary {
  cursor: pointer;
  color: #94a3b8;
  font-size: 12px;
  padding: 8px 0;
}

.risk-details summary:hover {
  color: #38bdf8;
}

.details-content {
  padding: 12px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
  margin-top: 8px;
}

.details-content p {
  margin: 6px 0;
  font-size: 12px;
  color: #cbd5f5;
}

.risk-loading,
.risk-error,
.risk-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px;
  color: #94a3b8;
  font-size: 14px;
}

.risk-error {
  color: #fca5a5;
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
</style>