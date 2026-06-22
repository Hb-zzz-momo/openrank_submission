<template>
  <div class="page-root">
    <!-- 顶部标题区 -->
    <header class="page-header">
      <div>
        <h1 class="page-title">LLM 生态健康度总览</h1>
        <p class="page-subtitle">
          基于 OpenDigger / GitHub 数据，从活跃度、治理质量、多样性、LLM 适配度与可持续性五个维度，
          对主流 LLM 相关项目进行生态健康度评估与对比。
        </p>
      </div>
      <div class="header-tags">
        <span class="tag tag-secondary">数据源：OpenDigger</span>
      </div>
    </header>

    <div class="home-layout">
      <!-- 左侧：项目选择 -->
      <aside class="sidebar glass-card">
        <h3 class="sidebar-title">LLM 项目库</h3>
        <!-- 🔥 已选项目栏 -->
        <div v-if="!treeLoading" class="selected-projects">
          <div class="selected-header">
            <span class="selected-icon">📌</span>
            <span class="selected-text">已选中</span>
            <span class="selected-count">({{ selectedIds.length }}/{{ MAX_RADAR_SELECTION }})</span>
          </div>

          <!-- 没有选中项时的提示 -->
          <div v-if="selectedIds.length === 0" class="selected-empty">
            请在下方选择项目进行对比
          </div>

          <!-- 已选项目列表 -->
          <div v-else class="selected-list">
            <div
              v-for="id in selectedIds"
              :key="id"
              class="selected-item"
              :title="findProjectInfo(id)?.description"
            >
              <span class="selected-item-label">
                {{ findProjectInfo(id)?.label || id }}
              </span>
              <button
                class="selected-item-remove"
                @click="removeSelection(id)"
                title="取消选择"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <!-- 分割线 -->
        <div v-if="!treeLoading" class="divider"></div>
        <!-- 加载提示 -->
        <div v-if="treeLoading" class="loading-hint">
          <div class="spinner-mini"></div>
          <span>正在加载项目列表...</span>
        </div>

        <!-- 🔥 新版：可折叠的树结构 -->
        <div v-else class="tree-container">
          <!-- 一级分类（大类：AI 基础设施、基础模型等） -->
          <div v-for="c1 in llmTree" :key="c1.value" class="level1">
            <!-- 大类标题（可点击展开/收起） -->
            <div class="level1-header" @click="toggleExpand(c1.value)">
              <span class="expand-icon">{{ isExpanded(c1.value) ? '▼' : '▶' }}</span>
              <span class="level1-title">{{ c1.label }}</span>
              <span class="level1-count">({{ (c1.children || []).length }})</span>
            </div>

            <!-- 大类的子分类（仅在展开时显示） -->
            <div v-show="isExpanded(c1.value)" class="level1-content">
              <div v-for="c2 in c1.children || []" :key="c2.value" class="level2">
                <!-- 子分类标题（可点击展开/收起） -->
                <div class="level2-header" @click="toggleExpand(c2.value)">
                  <span class="expand-icon">{{ isExpanded(c2.value) ? '▼' : '▶' }}</span>
                  <span class="level2-title">{{ c2.label }}</span>
                  <span class="level2-count">({{ (c2.children || []).length }})</span>
                </div>

                <!-- 具体项目列表（仅在展开时显示） -->
                <div v-show="isExpanded(c2.value)" class="level3-list">
                  <label
                    v-for="leaf in c2.children || []"
                    :key="leaf.value"
                    class="leaf-item"
                    :title="leaf.description"
                  >
                    <input
                      type="checkbox"
                      :checked="selectedIds.includes(leaf.value)"
                      @change="onRepoToggle($event, leaf.value)"
                    />
                    <span class="leaf-label">{{ leaf.label }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 提示信息 -->
        <p class="sidebar-tip">
          最多可同时选择 <strong>3</strong> 个项目进行对比。
          <span v-if="llmTree.length">当前库中共 <strong>{{ allLeafIds.length }}</strong> 个项目。</span>
        </p>
      </aside>

      <!-- 右侧：图表 + 汇总表 -->
      <section class="content">
        <div class="panel glass-card">
          <!-- 顶部：图表切换 + 智能分析按钮 -->
          <div class="panel-header-row">
            <div class="chart-tabs">
              <button
                :class="{ active: activeChart === 'radar' }"
                @click="activeChart = 'radar'"
              >
                健康度雷达图
              </button>
              <button
                :class="{ active: activeChart === 'line' }"
                @click="activeChart = 'line'"
              >
                指标走势折线图
              </button>
            </div>

            <div class="report-controls">
              <select v-model="reportTone" class="tone-select" :disabled="reportLoading">
                <option v-for="opt in reportToneOptions" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </option>
              </select>

              <button
                class="report-btn"
                :disabled="!radarData.length || reportLoading"
                @click="generateReport"
              >
                {{ reportLoading ? '生成中…' : '生成智能分析' }}
              </button>
            </div>

          </div>

          <!-- 雷达图视图 -->
          <div v-if="activeChart === 'radar'" class="panel-body">
            <div v-if="radarLoading" class="loading-box">
              <div class="spinner"></div>
              <p class="loading-text">
                正在从 OpenDigger 拉取最近 12 个月的数据并计算五维指标…
              </p>
            </div>

            <div v-else>
              <RadarCompare
                v-if="radarData.length"
                :data="radarData"
              />
              <p v-else class="empty-tip">
                请在左侧勾选 1–3 个项目，以查看生态健康度雷达图对比。
              </p>

              <!-- 汇总表 -->
              <div v-if="radarData.length" class="table-wrapper">
                <div class="table-header">
                  <h3>项目生态指标对比</h3>
                  <p>支持点击表头按不同维度排序，快速发现“谁更健康”。</p>
                </div>
                <table class="metric-table">
                  <thead>
                    <tr>
                      <th @click="sortBy('repo')">
                        项目
                        <span v-if="sortKey === 'repo'">
                          {{ sortAsc ? '▲' : '▼' }}
                        </span>
                      </th>
                      <th @click="sortBy('activity')">
                        活跃度
                        <span v-if="sortKey === 'activity'">
                          {{ sortAsc ? '▲' : '▼' }}
                        </span>
                      </th>
                      <th @click="sortBy('governance')">
                        治理质量
                        <span v-if="sortKey === 'governance'">
                          {{ sortAsc ? '▲' : '▼' }}
                        </span>
                      </th>
                      <th @click="sortBy('diversity')">
                        多样性
                        <span v-if="sortKey === 'diversity'">
                          {{ sortAsc ? '▲' : '▼' }}
                        </span>
                      </th>
                      <th @click="sortBy('llm_fit')">
                        LLM 适配度
                        <span v-if="sortKey === 'llm_fit'">
                          {{ sortAsc ? '▲' : '▼' }}
                        </span>
                      </th>
                      <th @click="sortBy('sustainability')">
                        可持续性
                        <span v-if="sortKey === 'sustainability'">
                          {{ sortAsc ? '▲' : '▼' }}
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in sortedRadarData" :key="item.repo">
                      <td class="repo-cell">{{ item.repo }}</td>
                      
                      <!-- 活跃度 -->
                      <td class="metric-cell" :class="{ 'is-favorited': isFav(item.repo, 'activity') }">
                        <span class="metric-value">{{ (item.metrics.activity * 100).toFixed(1) }}%</span>
                        <button 
                          class="fav-icon" 
                          @click.stop="toggleFav(item.repo, 'activity')"
                          :title="isFav(item.repo, 'activity') ? '取消收藏' : '收藏该指标'"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                          </svg>
                        </button>
                      </td>
                      
                      <!-- 治理质量 -->
                      <td class="metric-cell" :class="{ 'is-favorited': isFav(item.repo, 'governance') }">
                        <span class="metric-value">{{ (item.metrics.governance * 100).toFixed(1) }}%</span>
                        <button 
                          class="fav-icon" 
                          @click.stop="toggleFav(item.repo, 'governance')"
                          :title="isFav(item.repo, 'governance') ? '取消收藏' : '收藏该指标'"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                          </svg>
                        </button>
                      </td>
                      
                      <!-- 多样性 -->
                      <td class="metric-cell" :class="{ 'is-favorited': isFav(item.repo, 'diversity') }">
                        <span class="metric-value">{{ (item.metrics.diversity * 100).toFixed(1) }}%</span>
                        <button 
                          class="fav-icon" 
                          @click.stop="toggleFav(item.repo, 'diversity')"
                          :title="isFav(item.repo, 'diversity') ? '取消收藏' : '收藏该指标'"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                          </svg>
                        </button>
                      </td>
                      
                      <!-- LLM适配度 -->
                      <td class="metric-cell" :class="{ 'is-favorited': isFav(item.repo, 'llm_fit') }">
                        <span class="metric-value">{{ (item.metrics.llm_fit * 100).toFixed(1) }}%</span>
                        <button 
                          class="fav-icon" 
                          @click.stop="toggleFav(item.repo, 'llm_fit')"
                          :title="isFav(item.repo, 'llm_fit') ? '取消收藏' : '收藏该指标'"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                          </svg>
                        </button>
                      </td>
                      
                      <!-- 可持续性 -->
                      <td class="metric-cell" :class="{ 'is-favorited': isFav(item.repo, 'sustainability') }">
                        <span class="metric-value">{{ (item.metrics.sustainability * 100).toFixed(1) }}%</span>
                        <button 
                          class="fav-icon" 
                          @click.stop="toggleFav(item.repo, 'sustainability')"
                          :title="isFav(item.repo, 'sustainability') ? '取消收藏' : '收藏该指标'"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                          </svg>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <!-- ✨ 创新功能：智能对比结论 -->
              <div v-if="autoConclusion && radarData.length >= 2" class="conclusion-section">
                <div class="conclusion-header">
                  <span class="conclusion-icon">🎯</span>
                  <h3>智能选型建议</h3>
                  <span class="conclusion-badge">AI 分析</span>
                </div>

                <!-- 一句话结论 -->
                <div class="one-liner">
                  <p>{{ oneLinerConclusion }}</p>
                </div>

                <!-- 综合排名 -->
                <div class="ranking-row">
                  <div 
                    v-for="(item, index) in autoConclusion.projectScores" 
                    :key="item.repo"
                    class="rank-item"
                    :class="{ 'rank-first': index === 0 }"
                  >
                    <span class="rank-medal">{{ index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉' }}</span>
                    <span class="rank-name">{{ item.repo.split('/')[1] }}</span>
                    <span class="rank-score">{{ item.score }}分</span>
                  </div>
                </div>

                <!-- 场景化推荐 -->
                <div class="recommendations-grid">
                  <div 
                    v-for="rec in autoConclusion.recommendations" 
                    :key="rec.scenario"
                    class="rec-card"
                  >
                    <div class="rec-scenario">{{ rec.scenario }}</div>
                    <div class="rec-project">👉 {{ rec.project.split('/')[1] }}</div>
                    <div class="rec-reason">{{ rec.reason }}</div>
                  </div>
                </div>

                <!-- 洞察提醒 -->
                <div v-if="autoConclusion.insights.length" class="insights-list">
                  <div 
                    v-for="(insight, idx) in autoConclusion.insights" 
                    :key="idx"
                    class="insight-item"
                    :class="insight.type"
                  >
                    <span class="insight-icon">{{ insight.type === 'warning' ? '⚠️' : '✨' }}</span>
                    <span>{{ insight.text }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 折线图视图 -->
          <div v-else class="panel-body">
            <MetricLineChart :ids="selectedIds" />
          </div>
        </div>
      </section>
    </div>

   <!-- 全屏居中分析弹窗 -->
    <transition name="modal-fade">
      <div v-if="reportDrawerOpen" class="analysis-modal-overlay" @click.self="reportDrawerOpen = false">
        
        <div class="analysis-modal" :class="{ fullscreen: reportFullscreen }">
          <!-- 1. 顶部 Header -->
          <div class="modal-header">
            <div class="header-left">
              <span class="header-tag">INTELLIGENCE REPORT</span>
              <h2 class="header-title">LLM 生态对比分析报告</h2>
            </div>
            <div class="header-right">
              <span class="report-meta">
                基于 OpenDigger 数据深度分析 | 模式：{{ reportToneLabel }} | {{ radarData.length }} 个项目对比
              </span>

              <!-- ✅ 新增：全屏阅读/还原按钮 -->
              <button
                class="modal-max-btn"
                @click="toggleReportFullscreen"
                :title="reportFullscreen ? '退出全屏阅读' : '全屏阅读（放大右侧报告）'"
              >
                {{ reportFullscreen ? '🗗' : '🗖' }}
              </button>

              <button class="modal-close-btn" @click="closeReportModal">×</button>
            </div>

          </div>

          <!-- 2. 内容主体 -->
          <div class="modal-body" :class="{ 'report-only': reportFullscreen }">

            
            <!-- ======= 左侧：图表展示区 (雷达图) ======= -->
            <div class="chart-section">
              <div class="chart-wrapper">
                <RadarCompare 
                  v-if="radarData.length" 
                  :data="radarData" 
                />
                <div v-else class="empty-chart">正在加载图表数据...</div>
              </div>
              <div class="chart-caption">
                * 数据维度：活跃度、治理质量、多样性、LLM适配度、可持续性
              </div>
            </div>

            <!-- ======= 右侧：结构化报告区 (动态生成) ======= -->
            <div class="report-section custom-scrollbar">
              
              <!-- Loading 状态 -->
              <div v-if="reportLoading && !reportText" class="loading-state">
                <div class="spinner-large"></div>
                <p>正在生成深度分析报告...</p>
              </div>

              <!-- 报告内容 -->
              <div v-else class="structured-report">
                
                <!-- 卡片1: 总体评估 -->
                <div class="report-card summary-card">
                  <div class="card-header">
                    <div class="header-icon">📊</div>
                    <h4>总体评估</h4>
                    <span class="time-tag">生成时间：{{ currentTime }}</span>
                  </div>
                  <div class="summary-body">
                    <div class="score-box">
                      <!-- 动态平均分 -->
                      <div class="big-score">{{ averageScore }}</div>
                      <div class="score-label">综合得分</div>
                    </div>
                    <div class="summary-desc">
                      <p><strong>核心结论：</strong> {{ summaryConclusion }}</p>
                      <div class="tags-row">
                        <span class="tag-pill" :class="getRiskLevel(averageScore).class">
                          {{ getRiskLevel(averageScore).text }}
                        </span>
                        <span class="tag-pill medium" v-if="lowActivityCount > 0">
                          {{ lowActivityCount }}个项目活跃度不足
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 卡片2: 项目对比表格 -->
                <div class="report-card">
                  <div class="card-header">
                    <div class="header-icon">📈</div>
                    <h4>项目对比分析</h4>
                  </div>
                  <div class="comparison-table-wrapper">
                    <table class="comp-table">
                      <thead>
                        <tr>
                          <th>项目</th>
                          <th>综合评分</th>
                          <th>核心优势</th>
                          <th>主要风险</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="item in radarData" :key="item.repo">
                          <td class="project-cell">
                            <div class="p-name">{{ item.repo.split('/')[1] }}</div>
                            <div class="p-sub">{{ item.repo.split('/')[0] }}</div>
                          </td>
                          <td>
                            <span class="score-badge">{{ calculateItemScore(item) }}</span>
                          </td>
                          <!-- 动态优势分析 -->
                          <td class="text-green">
                            <ul class="mini-list">
                              <li v-for="adv in getAdvantages(item)" :key="adv">• {{ adv }}</li>
                              <li v-if="getAdvantages(item).length === 0" style="color: #64748b">• 表现平稳</li>
                            </ul>
                          </td>
                          <!-- 动态风险分析 -->
                          <td class="text-red">
                            <ul class="mini-list">
                              <li v-for="risk in getRisks(item)" :key="risk">• {{ risk }}</li>
                              <li v-if="getRisks(item).length === 0" style="color: #64748b">• 暂无显著风险</li>
                            </ul>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                <!-- 卡片2.5: 贡献者健康预警（Bus Factor） -->
                <div class="report-card">
                  <div class="card-header">
                    <div class="header-icon">🧑‍💻</div>
                    <h4>贡献者健康预警（Bus Factor）</h4>
                  </div>

                  <div class="risk-grid">
                    <ContributorRiskCard
                      v-for="id in selectedIds"
                      :key="id"
                      :project="id"
                      platform="github"
                    />
                  </div>
                </div>

                <!-- 卡片3: 关键发现 -->
                <div class="report-card">
                  <div class="card-header">
                    <div class="header-icon">🔍</div>
                    <h4>关键发现</h4>
                  </div>
                  <div class="insights-grid">
                    <!-- 动态渲染关键指标卡片 -->
                    <div class="insight-box">
                      <div class="ib-icon">📉</div>
                      <div class="ib-content">
                        <h5>活跃度概览</h5>
                        <p>平均活跃度 <strong>{{ avgMetrics.activity }}</strong>。{{ avgMetrics.activity < 0.5 ? '整体社区活跃度较低，需加强运营。' : '社区交互频繁，开发者参与度高。' }}</p>
                      </div>
                    </div>
                    <div class="insight-box">
                      <div class="ib-icon">🏛️</div>
                      <div class="ib-content">
                        <h5>治理质量</h5>
                        <p>平均治理分 <strong>{{ avgMetrics.governance }}</strong>。{{ avgMetrics.governance < 0.5 ? '缺乏有效的贡献者治理机制。' : '项目管理规范，决策透明。' }}</p>
                      </div>
                    </div>
                    
                    <!-- AI 生成的补充文字 (如果有) -->
                    <div class="insight-box full-width" v-if="reportText">
                      <div class="ib-icon">🤖</div>
                      <div class="ib-content">
                        <h5>AI 深度洞察</h5>
                        <div class="ai-text-preview" v-html="renderedReport"></div>
                        <span v-if="reportLoading" class="typing-cursor">▍</span>

                      </div>
                    </div>
                  </div>
                </div>

              </div> <!-- End Report -->
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { useFavoritesStore } from '@/stores/favorites'
import { useAuthStore } from '@/stores/auth'
import { onMounted, computed, watch, ref } from 'vue'
import MarkdownIt from 'markdown-it'
import ContributorRiskCard from '../components/ContributorRiskCard.vue'

const reportDrawerOpen = ref(false)
const reportLoading = ref(false)
const reportText = ref('')
const reportError = ref('')
const REPORT_TONE_STORAGE_KEY = 'openrank_report_tone'

const reportToneOptions = [
  { value: 'pro',      label: '📊 专业分析' },
  { value: 'cto',      label: '🧠 CTO 尽调' },
  { value: 'investor', label: '💰 投资人视角' },
  { value: 'audit',    label: '⚡ 挑刺审计（毒舌但专业）' }
]

const reportTone = ref(localStorage.getItem(REPORT_TONE_STORAGE_KEY) || 'pro')

watch(reportTone, (v) => {
  localStorage.setItem(REPORT_TONE_STORAGE_KEY, v)
})

const reportToneLabel = computed(() => {
  return reportToneOptions.find(o => o.value === reportTone.value)?.label || '📊 专业分析'
})

const reportFullscreen = ref(false)

// ✅ 点击最大化按钮：切换阅读模式
const toggleReportFullscreen = () => {
  reportFullscreen.value = !reportFullscreen.value
}

// ✅ 关闭弹窗：顺便退出全屏（避免下次打开还是全屏）
const closeReportModal = () => {
  reportDrawerOpen.value = false
  reportFullscreen.value = false
}

// 创建Markdown解析器实例（安全配置）
const md = new MarkdownIt({
  html: false,     // ✅ 禁止HTML标签以防止XSS（报告内容来自AI，应使用纯Markdown）
  breaks: true,    // 将换行符转换为 <br>
  linkify: true    // 自动将URL转换为链接
})


// 计算属性：将 markdown 转换为 HTML
const renderedReport = computed(() => {
  if (!reportText.value || reportText.value.trim() === '') {
    return '<p>暂无报告内容</p>'
  }
  return md.render(reportText.value)
})


const favStore = useFavoritesStore()
const authStore = useAuthStore()
const expandedNodes = ref(new Set())  // 存储展开的节点 key

const initExpandedState = () => {
  if (llmTree.value.length > 0) {
    // 默认展开第一个一级分类（AI 基础设施）
    expandedNodes.value.add(llmTree.value[0].value)
  }
}

// 🔥 切换展开/收起状态
const toggleExpand = (key) => {
  if (expandedNodes.value.has(key)) {
    expandedNodes.value.delete(key)
  } else {
    expandedNodes.value.add(key)
  }
}

// 🔥 检查是否展开
const isExpanded = (key) => {
  return expandedNodes.value.has(key)
}

onMounted(async () => {
  // 🔥 关键：用 try-finally 确保即使出错也能继续后续流程
  
  // ===== 1️⃣ 先加载项目树（必须等它完成） =====
  try {
    await loadProjectTree()
    console.log('✅ 项目树加载完成，共', allLeafIds.value.length, '个项目')
  } catch (err) {
    console.error('❌ 项目树加载失败:', err)
    // 即使失败也继续后续流程
  }

  // ===== 2️⃣ 恢复上次选中的项目（现在 allLeafIds 有值了） =====
  try {
    let ids = []
    const saved = localStorage.getItem(STORAGE_KEY_SELECTED)
    if (saved) {
      ids = JSON.parse(saved)
    }

    // 🔥 关键：现在 allLeafIds.value 已经有数据了，过滤才有意义
    ids = ids.filter(id => allLeafIds.value.includes(id)).slice(0, MAX_RADAR_SELECTION)
    
    selectedIds.value = ids
    
    if (ids.length > 0) {
      console.log('✅ 恢复了', ids.length, '个选中项目:', ids)
    }
  } catch (err) {
    console.error('❌ 恢复选中项目失败:', err)
    selectedIds.value = []
  }

  // ===== 3️⃣ 如果已登录，拉取收藏列表 =====
  if (authStore.token) {
    try {
      await favStore.fetchFavorites()
      console.log('✅ 收藏列表加载完成')
    } catch (err) {
      console.error('❌ 收藏列表加载失败:', err)
    }
  }
})


// 组装“收藏对象”
const buildFavProject = (repoFullName, dimKey) => {
  const metric = radarMetricMap[dimKey]     // 映射成真实 opendigger metric
  const [org, repo] = repoFullName.split('/')

  return {
    fullName: repoFullName,
    metric,
    platform: 'github',
    title: `${repoFullName} - ${metric}`,
    url: `https://github.com/${org}/${repo}`
  }
}

const toggleFav = async (repoFullName, dimKey) => {
  if (!authStore.token) {
    window.alert('请先登录，再使用收藏功能')
    return
  }
  const project = buildFavProject(repoFullName, dimKey)
  await favStore.toggleFavorite(project)
}
const isFav = (repoFullName, dimKey) => {
  const metric = radarMetricMap[dimKey]
  return favStore.isFavorited(repoFullName, metric)
}
import RadarCompare from '../components/RadarCompare.vue'
import MetricLineChart from '../components/MetricLineChart.vue'
import { opendiggerApi, llmApi } from '../api/api'

const MAX_RADAR_SELECTION = 3

// 左侧项目树
const llmTree = ref([])
const treeLoading = ref(false)

// 加载项目树
const loadProjectTree = async () => {
  treeLoading.value = true
  try {
    const res = await llmApi.getProjects()
    llmTree.value = res.data.tree || []
    initExpandedState()
    console.log(`✅ 成功加载 ${res.data.total_projects} 个 LLM 项目`)
  } catch (err) {
    console.error('❌ 加载项目树失败:', err)
    // fallback：如果接口失败，可以用一个最小的树作为降级方案
    llmTree.value = [
      {
        label: '基础设施',
        value: 'infra',
        children: [
          {
            label: '训练框架',
            value: 'training',
            children: [
              { label: 'PyTorch', value: 'pytorch/pytorch' }
            ]
          }
        ]
      }
    ]
    initExpandedState()
  } finally {
    treeLoading.value = false
  }
}

const STORAGE_KEY_SELECTED = 'openrank_home_selected_ids'

// 把树上所有叶子节点 value 拍平成数组（用于校验/默认勾选）
const allLeafIds = computed(() => {
  return llmTree.value.flatMap(c1 =>
    (c1.children || []).flatMap(c2 =>
      (c2.children || []).map(leaf => leaf.value)
    )
  )
})


const selectedIds = ref([])
const activeChart = ref('radar')

const radarData = ref([])
const radarLoading = ref(false)

// 表格排序
const sortKey = ref('activity')
const sortAsc = ref(false)

const sortedRadarData = computed(() => {
  const data = [...radarData.value]
  if (!sortKey.value) return data

  return data.sort((a, b) => {
    if (sortKey.value === 'repo') {
      return sortAsc.value
        ? a.repo.localeCompare(b.repo)
        : b.repo.localeCompare(a.repo)
    }
    const av = a.metrics[sortKey.value] ?? 0
    const bv = b.metrics[sortKey.value] ?? 0
    return sortAsc.value ? av - bv : bv - av
  })
})

// ===========================
// 🎯 创新功能：智能对比结论生成器
// ===========================

/**
 * 自动分析对比结果，生成选型建议
 */
const autoConclusion = computed(() => {
  if (radarData.value.length < 2) return null
  
  const dimensions = [
    { key: 'activity', name: '活跃度', weight: 0.25 },
    { key: 'governance', name: '治理质量', weight: 0.25 },
    { key: 'diversity', name: '多样性', weight: 0.2 },
    { key: 'llm_fit', name: 'LLM适配度', weight: 0.15 },
    { key: 'sustainability', name: '可持续性', weight: 0.15 }
  ]
  
  // 1. 找出各维度的领先者
  const leaders = {}
  dimensions.forEach(dim => {
    const sorted = [...radarData.value].sort((a, b) => 
      (b.metrics[dim.key] || 0) - (a.metrics[dim.key] || 0)
    )
    leaders[dim.key] = {
      repo: sorted[0].repo,
      value: sorted[0].metrics[dim.key] || 0,
      name: dim.name
    }
  })
  
  // 2. 计算各项目的加权总分
  const projectScores = radarData.value.map(item => {
    let weightedSum = 0
    dimensions.forEach(dim => {
      weightedSum += (item.metrics[dim.key] || 0) * dim.weight
    })
    return {
      repo: item.repo,
      score: weightedSum,
      metrics: item.metrics
    }
  }).sort((a, b) => b.score - a.score)
  
  // 3. 统计各项目领先维度数
  const winCounts = {}
  radarData.value.forEach(item => {
    winCounts[item.repo] = 0
  })
  Object.values(leaders).forEach(leader => {
    winCounts[leader.repo] = (winCounts[leader.repo] || 0) + 1
  })
  
  // 4. 找出综合冠军和各场景推荐
  const overallWinner = projectScores[0]
  const mostWins = Object.entries(winCounts).sort((a, b) => b[1] - a[1])[0]
  
  // 5. 生成场景化建议
  const recommendations = []
  
  // 追求稳定性
  const stabilityLeader = [...radarData.value].sort((a, b) => 
    (b.metrics.sustainability || 0) - (a.metrics.sustainability || 0)
  )[0]
  if (stabilityLeader) {
    recommendations.push({
      scenario: '追求长期稳定',
      project: stabilityLeader.repo,
      reason: `可持续性得分 ${(stabilityLeader.metrics.sustainability * 100).toFixed(0)}%`
    })
  }
  
  // 追求活跃社区
  const activityLeader = [...radarData.value].sort((a, b) => 
    (b.metrics.activity || 0) - (a.metrics.activity || 0)
  )[0]
  if (activityLeader) {
    recommendations.push({
      scenario: '需要活跃社区支持',
      project: activityLeader.repo,
      reason: `活跃度得分 ${(activityLeader.metrics.activity * 100).toFixed(0)}%`
    })
  }
  
  // 新手友好
  const diversityLeader = [...radarData.value].sort((a, b) => 
    (b.metrics.diversity || 0) - (a.metrics.diversity || 0)
  )[0]
  if (diversityLeader) {
    recommendations.push({
      scenario: '新手入门首选',
      project: diversityLeader.repo,
      reason: `社区多样性得分 ${(diversityLeader.metrics.diversity * 100).toFixed(0)}%，新贡献者友好`
    })
  }
  
  // 6. 生成差异化洞察
  const insights = []
  
  // 检查是否有明显短板
  radarData.value.forEach(item => {
    const metrics = item.metrics
    const weakDims = dimensions.filter(d => (metrics[d.key] || 0) < 0.3)
    if (weakDims.length > 0) {
      insights.push({
        type: 'warning',
        project: item.repo,
        text: `${item.repo.split('/')[1]} 在「${weakDims.map(d => d.name).join('、')}」维度表现较弱`
      })
    }
  })
  
  // 检查是否存在压倒性优势
  if (overallWinner.score > projectScores[1]?.score * 1.3) {
    insights.push({
      type: 'highlight',
      project: overallWinner.repo,
      text: `${overallWinner.repo.split('/')[1]} 综合表现显著优于其他项目`
    })
  }
  
  return {
    overallWinner: {
      repo: overallWinner.repo,
      score: (overallWinner.score * 100).toFixed(1),
      winCount: winCounts[overallWinner.repo]
    },
    mostWins: {
      repo: mostWins[0],
      count: mostWins[1]
    },
    leaders,
    recommendations,
    insights,
    projectScores: projectScores.map(p => ({
      repo: p.repo,
      score: (p.score * 100).toFixed(1)
    }))
  }
})

/**
 * 生成一句话结论
 */
const oneLinerConclusion = computed(() => {
  if (!autoConclusion.value) return ''
  
  const winner = autoConclusion.value.overallWinner
  const projects = radarData.value.length
  
  if (winner.winCount >= 4) {
    return `在 ${projects} 个项目中，${winner.repo.split('/')[1]} 表现最为全面，在 ${winner.winCount}/5 个维度领先，综合得分 ${winner.score} 分。`
  } else if (winner.winCount >= 2) {
    return `综合评估 ${projects} 个项目，${winner.repo.split('/')[1]} 以 ${winner.score} 分领先，但各项目各有优势。`
  } else {
    return `${projects} 个项目各有千秋，${winner.repo.split('/')[1]} 综合得分 ${winner.score} 分略胜一筹，建议根据具体场景选择。`
  }
})
const sortBy = key => {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = key === 'repo'
  }
}

/**
 * 雷达图 5 维 -> OpenDigger 指标映射
 */
const radarMetricMap = {
  activity: 'activity',
  governance: 'openrank',
  diversity: 'new_contributors',
  llm_fit: 'stars',
  sustainability: 'bus_factor'
}
const radarKeys = Object.keys(radarMetricMap)

const findProjectInfo = (projectValue) => {
  for (const c1 of llmTree.value) {
    for (const c2 of c1.children || []) {
      for (const leaf of c2.children || []) {
        if (leaf.value === projectValue) {
          return {
            label: leaf.label,
            value: leaf.value,
            category: `${c1.label} / ${c2.label}`,
            description: leaf.description
          }
        }
      }
    }
  }
  return null
}

// 🔥 快速移除选中项目（点击叉号时调用）
const removeSelection = (projectValue) => {
  selectedIds.value = selectedIds.value.filter(id => id !== projectValue)
}
// 勾选时限制最多 3 个
const onRepoToggle = (event, id) => {
  const checked = event.target.checked

  if (checked) {
    //现有checked然后才有selectedIds
    if (!selectedIds.value.includes(id)) {
      if (selectedIds.value.length >= MAX_RADAR_SELECTION) {
        event.target.checked = false
        window.alert(`雷达图最多只能同时对比 ${MAX_RADAR_SELECTION} 个项目。`)
        return
      }
      selectedIds.value.push(id)
    }
  } else {
    selectedIds.value = selectedIds.value.filter(x => x !== id)
  }
}

// 拉一个仓库的某个指标的最近 12 个月平均值
const fetchAvgMetric = async (org, repo, odMetric) => {
  try {
    const res = await opendiggerApi.getRepoData('github', org, repo, odMetric)
    const raw = res.data.data || []
    if (!raw.length) return 0

    let points
    if (Array.isArray(raw[0])) {
      points = raw.map(([month, value]) => ({ month, value }))
    } else {
      points = raw.map(p => ({ month: p.month, value: p.count }))
    }

    points.sort((a, b) => a.month.localeCompare(b.month))
    const lastPoints = points.slice(-12)
    if (!lastPoints.length) return 0

    const sum = lastPoints.reduce((s, p) => s + (Number(p.value) || 0), 0)
    return sum / lastPoints.length
  } catch (e) {
    console.error(`获取 ${org}/${repo} 的 ${odMetric} 失败：`, e)
    return 0
  }
}

// 构建雷达图数据
const loadRadarData = async () => {
  radarLoading.value = true
  radarData.value = []

  if (!selectedIds.value.length) {
    radarLoading.value = false
    return
  }

  try {
    const repoMetrics = await Promise.all(
      selectedIds.value.map(async id => {
        const [org, repo] = id.split('/')
        const raw = {}

        for (const key of radarKeys) {
          const odMetric = radarMetricMap[key]
          raw[key] = await fetchAvgMetric(org, repo, odMetric)
        }

        return { id, raw }
      })
    )

    const maxByKey = {}
    const minByKey = {}
    for (const key of radarKeys) {
      const values = repoMetrics.map(r => r.raw[key] || 0)
      maxByKey[key] = Math.max(...values, 0)
      minByKey[key] = Math.min(...values, 0)
    }

    radarData.value = repoMetrics.map(r => ({
      repo: r.id,
      metrics: radarKeys.reduce((acc, key) => {
        const raw = r.raw[key] || 0
        const max = maxByKey[key]
        const min = minByKey[key]
        let norm = 0
        if (max === min) {
          norm = raw === 0 ? 0 : 0.5
        } else {
          norm = (raw - min) / (max - min)
        }
        acc[key] = norm
        return acc
      }, {})
    }))
  } finally {
    radarLoading.value = false
  }
}

watch(
  () => selectedIds.value,
  (val) => {
    // ⭐ 记录勾选（刷新后能恢复）
    localStorage.setItem(STORAGE_KEY_SELECTED, JSON.stringify(val))

    // 原来的逻辑：勾选变化就刷新雷达
    if (activeChart.value === 'radar') {
      loadRadarData()
    }
  },
  { deep: true }
)


watch(reportDrawerOpen, (open) => {
  if (!open) stopTypewriter()
})
// ---------- 智能报告相关状态 & 方法 ----------

// ===== 打字机配置 =====
let typeTimer = null
const TYPE_INTERVAL_MS = 35           // 每次吐字间隔（越小越快）
const TARGET_DURATION_MS = 8000       // 目标：整篇报告大约 8 秒打完（方便录 GIF）

const stopTypewriter = () => {
  if (typeTimer) {
    clearInterval(typeTimer)
    typeTimer = null
  }
}

// fullText：完整报告；会自动计算每次吐多少字符，保证总时长接近 TARGET_DURATION_MS
const startTypewriter = (fullText) => {
  stopTypewriter()
  reportText.value = ''

  const totalLen = fullText.length
  const ticks = Math.max(1, Math.floor(TARGET_DURATION_MS / TYPE_INTERVAL_MS))
  const step = Math.max(1, Math.ceil(totalLen / ticks)) // 每 tick 输出多少字符

  let i = 0
  typeTimer = setInterval(() => {
    // 如果用户关了弹窗，就停止（避免后台还在打字）
    if (!reportDrawerOpen.value) {
      stopTypewriter()
      reportLoading.value = false
      return
    }

    reportText.value += fullText.slice(i, i + step)
    i += step

    if (i >= totalLen) {
      stopTypewriter()
      reportLoading.value = false
    }
  }, TYPE_INTERVAL_MS)
}

const generateReport = async () => {
  if (!radarData.value.length) {
    reportError.value = '请先在左侧选择至少一个项目并生成雷达图。'
    reportText.value = ''
    reportDrawerOpen.value = true
    return
  }

  reportDrawerOpen.value = true
  reportLoading.value = true
  reportError.value = ''
  reportText.value = ''
  stopTypewriter()

  try {
    const payload = {
      tone: reportTone.value, // 告诉后端使用哪套提示词
      projects: radarData.value.map(item => ({
        repo: item.repo,
        metrics: item.metrics
      }))
    }


    const res = await Promise.race([
      llmApi.getReport(payload),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), 18000) // 18s 超时兜底
      )
    ])

    const rawReport = res.data.report || '（后端未返回报告内容）'
    const full =
      `### 📊 ${radarData.value.length} 个项目生态深度对比\n` +
      `> 模式：${reportToneLabel.value}\n\n` +
      rawReport

    // ✅ 打字机开始
    startTypewriter(full)
  } catch (e) {
    console.error('生成报告失败', e)
    reportError.value = (String(e?.message).includes('timeout'))
      ? '生成超时：后端报告接口未在 18 秒内返回（已自动中止）。'
      : '生成报告失败，请稍后重试。'
    reportLoading.value = false
  }

}


// 在 <script setup> 中添加：

const currentTime = ref(new Date().toLocaleDateString())

// --- 1. 计算单个项目分数 ---
const calculateItemScore = (item) => {
  const vals = Object.values(item.metrics)
  if(!vals.length) return '0.00'
  const score = vals.reduce((a, b) => a + b, 0) / vals.length
  return score.toFixed(2)
}

// --- 2. 计算整体平均分 ---
const averageScore = computed(() => {
  if (!radarData.value.length) return '0.00'
  let total = 0
  radarData.value.forEach(item => total += parseFloat(calculateItemScore(item)))
  return (total / radarData.value.length).toFixed(2)
})

// --- 3. 动态生成核心结论 ---
const summaryConclusion = computed(() => {
  const score = parseFloat(averageScore.value)
  if (score < 0.3) return "所有项目均处于早期阶段，核心指标有待提升。"
  if (score < 0.6) return "项目发展呈现分化，部分指标表现良好但整体仍需优化。"
  return "整体生态非常健康，在活跃度和治理上表现卓越。"
})

// --- 4. 辅助函数：根据规则生成优势文案 ---
const getAdvantages = (item) => {
  const tips = []
  const m = item.metrics
  if (m.activity > 0.7) tips.push("社区活跃度极高")
  if (m.governance > 0.7) tips.push("治理机制完善")
  if (m.llm_fit > 0.7) tips.push("模型适配性强")
  if (m.diversity > 0.7) tips.push("贡献者背景多元")
  return tips.slice(0, 2) // 最多显示2条
}

// --- 5. 辅助函数：根据规则生成风险文案 ---
const getRisks = (item) => {
  const tips = []
  const m = item.metrics
  if (m.activity < 0.3) tips.push("活跃度不足")
  if (m.governance < 0.3) tips.push("治理质量低")
  if (m.sustainability < 0.3) tips.push("维护响应慢")
  return tips.slice(0, 2)
}

// --- 6. 辅助函数：风险等级 ---
const getRiskLevel = (score) => {
  if (score < 0.4) return { text: '高优先改进', class: 'high' }
  if (score < 0.7) return { text: '中等风险', class: 'medium' }
  return { text: '低风险', class: 'low' }
}

// --- 7. 统计低活跃项目数 ---
const lowActivityCount = computed(() => {
  return radarData.value.filter(i => (i.metrics.activity || 0) < 0.3).length
})

// --- 8. 计算各项平均指标 ---
const avgMetrics = computed(() => {
  if (!radarData.value.length) return { activity: '0.00', governance: '0.00' }
  let act = 0, gov = 0
  radarData.value.forEach(i => {
    act += i.metrics.activity || 0
    gov += i.metrics.governance || 0
  })
  return {
    activity: (act / radarData.value.length).toFixed(2),
    governance: (gov / radarData.value.length).toFixed(2)
  }
})

// 6. 分数颜色辅助函数
const getScoreColor = (score) => {
  if (score < 0.4) return 'text-red'
  if (score < 0.7) return 'text-yellow'
  return 'text-green'
}

</script>

<style scoped>
.page-root {
  min-height: 100vh;
  padding:  24px 32px 24px;
  margin-top: 0px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 0% 0%, #1d4ed8 0, transparent 55%),
    radial-gradient(circle at 100% 0%, #a855f7 0, transparent 55%),
    radial-gradient(circle at 50% 100%, #22c55e 0, #020617 60%);
  color: #e5e7eb;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* 顶部标题 */

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
}

.page-title {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 700;
}

.page-subtitle {
  margin: 0;
  font-size: 13px;
  color: #cbd5f5;
}

.header-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  border: 1px solid rgba(191, 219, 254, 0.5);
  background: rgba(15, 23, 42, 0.7);
}

.tag-secondary {
  border-color: rgba(96, 165, 250, 0.7);
}

/* 主体布局 */

.home-layout {
  display: flex;
  gap: 16px;
  margin-top: 18px;
}

/* 通用玻璃卡片 */

.glass-card {
  background: radial-gradient(circle at 0 0, rgba(148, 163, 184, 0.18), transparent 55%),
    rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(18px);
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.85);
}

/* 左侧栏 */

.sidebar {
  width: 260px;
  padding: 16px 14px 14px;
  box-sizing: border-box;
  font-size: 13px;
}

.sidebar-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
}

.level1 + .level1 {
  margin-top: 10px;
}

.level1-title {
  font-weight: 600;
  margin-bottom: 4px;
  color: #e5e7eb;
}

.level2 {
  margin-left: 6px;
  margin-bottom: 4px;
}

.level2-title {
  font-weight: 500;
  margin-bottom: 2px;
  color: #cbd5f5;
}

.level3-list {
  margin-left: 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.leaf-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 4px;
  border-radius: 6px;
  transition: background 0.15s ease;
}

.leaf-item:hover {
  background: rgba(51, 65, 85, 0.6);
}

.leaf-item input[type="checkbox"] {
  accent-color: #38bdf8;
}

.leaf-label {
  font-size: 13px;
}

.sidebar-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #9ca3af;
}

/* 右侧内容区 */

.content {
  flex: 1;
}

.panel {
  padding: 14px 16px 16px;
  box-sizing: border-box;
}

.panel-body {
  margin-top: 8px;
}

/* 顶部行：tabs + 按钮 */

.panel-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

/* 图表 Tab 按钮 */

.chart-tabs {
  display: inline-flex;
  padding: 3px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.4);
}

.chart-tabs button {
  padding: 5px 14px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: #cbd5f5;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chart-tabs button.active {
  background: linear-gradient(135deg, #22c55e, #38bdf8);
  color: #0b1120;
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
}

/* 智能分析按钮 */

.report-btn {
  padding: 5px 12px;
  border-radius: 999px;
  border: none;
  font-size: 12px;
  cursor: pointer;
  background: linear-gradient(135deg, #f97316, #ec4899);
  color: #0b1120;
  box-shadow: 0 0 14px rgba(236, 72, 153, 0.6);
}

.report-btn[disabled] {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

/* 加载、空状态 */

.loading-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0 36px;
  gap: 10px;
}

.spinner {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 3px solid rgba(148, 163, 184, 0.5);
  border-top-color: #38bdf8;
  animation: spin 0.9s linear infinite;
}

.loading-text {
  font-size: 13px;
  color: #cbd5f5;
}

.empty-tip {
  margin-top: 24px;
  font-size: 13px;
  color: #9ca3af;
  text-align: center;
}

/* 汇总表格 */

.table-wrapper {
  margin-top: 18px;
}

.table-header h3 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
}

.table-header p {
  margin: 0;
  font-size: 12px;
  color: #9ca3af;
}

.metric-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-top: 8px;
}

.metric-table th,
.metric-table td {
  border: 1px solid rgba(51, 65, 85, 0.9);
  padding: 6px 8px;
  text-align: center;
}

.metric-table th {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 64, 175, 0.9));
  color: #e5e7eb;
  cursor: pointer;
  user-select: none;
  position: sticky;
  top: 0;
  z-index: 1;
}

.metric-table th span {
  margin-left: 4px;
  font-size: 10px;
}

.metric-table tbody tr:nth-child(odd) {
  background: rgba(15, 23, 42, 0.85);
}

.metric-table tbody tr:nth-child(even) {
  background: rgba(15, 23, 42, 0.7);
}

.metric-table tbody tr:hover {
  background: rgba(56, 189, 248, 0.18);
}

/* =========================================
   居中弹窗 & 赛博风格 (Left Chart - Right Report)
   ========================================= */

/* 1. 遮罩层 */
.analysis-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(2, 6, 23, 0.85);
  backdrop-filter: blur(8px);
  display: flex; justify-content: center; align-items: center;
  z-index: 9999;
}

/* 2. 弹窗主体 */
.analysis-modal {
  width: 95vw; max-width: 1300px; height: 85vh;
  /* 深色背景 + 径向光晕 */
  background: #0f172a;
  background-image: radial-gradient(circle at 0% 0%, rgba(76, 29, 149, 0.2), transparent 40%);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 20px;
  box-shadow: 0 0 80px rgba(0,0,0,0.8);
  display: flex; flex-direction: column;
  overflow: hidden;
  animation: popIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Header */
.modal-header {
  height: 70px; padding: 0 30px;
  background: rgba(15, 23, 42, 0.6);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex; justify-content: space-between; align-items: center;
  flex-shrink: 0;
}
.header-tag { font-size: 10px; color: #38bdf8; letter-spacing: 2px; font-weight: 800; display: block; margin-bottom: 2px; }
.header-title { font-size: 20px; color: #fff; margin: 0; font-weight: 700; }
.report-meta { font-size: 12px; color: #94a3b8; margin-right: 20px; }
.modal-close-btn { font-size: 24px; color: #94a3b8; background: none; border: none; cursor: pointer; transition: 0.2s; }
.modal-close-btn:hover { color: #fff; transform: scale(1.1); }

/* Body Layout */
.modal-body {
  flex: 1; display: grid; grid-template-columns: 1fr 1fr; overflow: hidden;
}

/* --- 左侧：图表区 --- */
.chart-section {
  background: rgba(15, 23, 42, 0.3);
  border-right: 1px solid rgba(255,255,255,0.05);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  position: relative; padding: 20px;
}
.chart-wrapper { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
.chart-caption { margin-top: 10px; color: #64748b; font-size: 12px; }
.empty-chart { color: #64748b; font-size: 14px; }

/* --- 右侧：报告区 --- */
.report-section {
  padding: 30px; overflow-y: auto; background: #0b1120;
}

/* 卡片通用样式 */
.report-card {
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}
.card-header { display: flex; align-items: center; margin-bottom: 15px; }
.header-icon { font-size: 18px; margin-right: 10px; background: rgba(255,255,255,0.05); width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.card-header h4 { margin: 0; font-size: 16px; color: #fff; font-weight: 600; flex: 1; }
.time-tag { font-size: 12px; color: #64748b; }

/* 总体评估 */
.summary-card .summary-body { display: flex; align-items: center; gap: 24px; }
.score-box { text-align: center; min-width: 90px; }
.big-score { font-size: 40px; font-weight: 800; color: #ef4444; line-height: 1; text-shadow: 0 0 20px rgba(239, 68, 68, 0.4); }
.score-label { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.summary-desc p { font-size: 13px; color: #e2e8f0; margin: 0 0 12px 0; line-height: 1.5; }
.tags-row { display: flex; gap: 8px; }
.tag-pill { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.tag-pill.high { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); }
.tag-pill.medium { background: rgba(234, 179, 8, 0.15); color: #fde047; border: 1px solid rgba(234, 179, 8, 0.3); }
.tag-pill.low { background: rgba(34, 197, 94, 0.15); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.3); }

/* 对比表格 */
.comp-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.comp-table th { text-align: left; color: #94a3b8; font-weight: 500; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.comp-table td { padding: 16px 0; border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: top; }
.p-name { color: #fff; font-weight: 600; font-size: 14px; }
.p-sub { color: #64748b; font-size: 11px; }
.score-badge { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.1); padding: 2px 8px; border-radius: 4px; font-family: monospace; color: #ef4444; font-weight: bold; }
.mini-list { list-style: none; padding: 0; margin: 0; font-size: 12px; line-height: 1.5; }
.text-green { color: #86efac; }
.text-red { color: #fca5a5; }

/* 关键发现 Grid */
.insights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.insight-box { background: rgba(15, 23, 42, 0.6); border-radius: 8px; padding: 15px; display: flex; gap: 12px; border: 1px solid rgba(255,255,255,0.05); }
/* 让“AI 深度洞察”卡片更高一些 */
.insight-box.full-width{
  grid-column: span 2;
  padding-top: 18px;      /* 上下更宽松 */
  padding-bottom: 18px;
  min-height: 260px;      /* ✅整体卡片最小高度变高 */
  align-items: flex-start; /* 防止内容垂直居中导致“更挤” */
}

/* 让预览区显示更多文本，再需要时才滚动 */
.ai-text-preview{
  max-height: 220px;      /* ✅原来 150 -> 220，能多显示不少内容 */
  overflow-y: auto;
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.6;
  padding-right: 6px;     /* 给滚动条留一点空间，视觉更舒服 */
}

.ib-icon { font-size: 24px; width: 40px; height: 40px; background: rgba(255,255,255,0.05); border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ib-content h5 { margin: 0 0 4px 0; color: #f1f5f9; font-size: 13px; font-weight: 600; }
.ib-content p { margin: 0; color: #94a3b8; font-size: 12px; line-height: 1.4; }



/* Loading & Scrollbar */
.loading-state { height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #94a3b8; gap: 10px; }
.spinner-large { width: 40px; height: 40px; border: 3px solid rgba(56,189,248,0.2); border-top-color: #38bdf8; border-radius: 50%; animation: spin 1s infinite; }
.report-section::-webkit-scrollbar { width: 6px; }
.report-section::-webkit-scrollbar-track { background: transparent; }
.report-section::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 10px; }

@keyframes popIn { 0% { opacity: 0; transform: scale(0.95); } 100% { opacity: 1; transform: scale(1); } }

/* --- 补充：加载和错误状态的样式 --- */
.status-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60%; /* 居中显示 */
  text-align: center;
  color: #94a3b8;
  gap: 16px;
}

/* 加载圈圈 */
.spinner-mini {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* 错误提示 */
.status-box.error {
  color: #fca5a5; /* 红色文字 */
}
.error-title {
  font-size: 16px;
  font-weight: bold;
  margin: 0;
}
.error-tip {
  font-size: 12px;
  color: #64748b;
}
/* 加载提示样式 */
.loading-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: #94a3b8;
  font-size: 13px;
}

.spinner-mini {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* ========== 侧边栏基础样式（保持不变）========== */
.sidebar {
  width: 260px;
  padding: 16px 14px 14px;
  box-sizing: border-box;
  font-size: 13px;
}

.sidebar-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 600;
}

/* ========== 树容器 ========== */
.tree-container {
  max-height: calc(100vh - 280px);  /* 限制高度，支持滚动 */
  overflow-y: auto;
  overflow-x: hidden;
}

/* 自定义滚动条（可选） */
.tree-container::-webkit-scrollbar {
  width: 6px;
}

.tree-container::-webkit-scrollbar-track {
  background: rgba(148, 163, 184, 0.1);
  border-radius: 3px;
}

.tree-container::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.tree-container::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

/* ========== 一级分类（大类）========== */
.level1 {
  margin-bottom: 8px;
}

.level1-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;  /* 防止双击选中文字 */
}

.level1-header:hover {
  background: rgba(56, 189, 248, 0.15);
}

.expand-icon {
  font-size: 10px;
  color: #94a3b8;
  width: 12px;
  text-align: center;
  transition: transform 0.2s ease;
}

.level1-title {
  font-weight: 600;
  color: #e5e7eb;
  flex: 1;
}

.level1-count {
  font-size: 11px;
  color: #64748b;
  background: rgba(148, 163, 184, 0.15);
  padding: 1px 6px;
  border-radius: 999px;
}

.level1-content {
  margin-left: 12px;
  margin-top: 4px;
  border-left: 1px solid rgba(148, 163, 184, 0.2);
  padding-left: 8px;
}

/* ========== 二级分类（子类）========== */
.level2 {
  margin-bottom: 6px;
}

.level2-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.level2-header:hover {
  background: rgba(34, 197, 94, 0.15);
}

.level2-title {
  font-weight: 500;
  color: #cbd5f5;
  font-size: 12px;
  flex: 1;
}

.level2-count {
  font-size: 10px;
  color: #64748b;
  background: rgba(148, 163, 184, 0.1);
  padding: 1px 5px;
  border-radius: 999px;
}

/* ========== 三级列表（具体项目）========== */
.level3-list {
  margin-left: 12px;
  margin-top: 3px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.leaf-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 6px;
  border-radius: 6px;
  transition: background 0.15s ease;
  cursor: pointer;
}

.leaf-item:hover {
  background: rgba(51, 65, 85, 0.6);
}

.leaf-item input[type="checkbox"] {
  accent-color: #38bdf8;
  cursor: pointer;
}

.leaf-label {
  font-size: 12px;
  color: #cbd5f5;
  cursor: pointer;
}

/* ========== 提示信息 ========== */
.sidebar-tip {
  margin-top: 12px;
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.5;
}

.sidebar-tip strong {
  color: #38bdf8;
}

/* ========== 加载提示（保持不变）========== */
.loading-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: #94a3b8;
  font-size: 13px;
}

.spinner-mini {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 🎭 展开/收起的平滑过渡动画 */
.level1-content,
.level3-list {
  overflow: hidden;
  transition: max-height 0.3s ease, opacity 0.2s ease;
}

/* 配合 v-show 的淡入淡出 */
.v-enter-active,
.v-leave-active {
  transition: opacity 0.2s ease;
}

.v-enter-from,
.v-leave-to {
  opacity: 0;
}

/* ========== 已选项目栏 ========== */
.selected-projects {
  margin-bottom: 12px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 8px;
  padding: 10px;
}

.selected-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #e5e7eb;
}

.selected-icon {
  font-size: 14px;
}

.selected-text {
  font-weight: 600;
  flex: 1;
}

.selected-count {
  font-size: 11px;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  padding: 2px 6px;
  border-radius: 999px;
}

/* 空状态提示 */
.selected-empty {
  font-size: 11px;
  color: #94a3b8;
  text-align: center;
  padding: 8px 0;
  font-style: italic;
}

/* 已选项目列表 */
.selected-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selected-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.selected-item:hover {
  background: rgba(15, 23, 42, 0.8);
  border-color: rgba(56, 189, 248, 0.4);
  transform: translateX(2px);
}

.selected-item-label {
  font-size: 12px;
  color: #e5e7eb;
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-item-remove {
  width: 18px;
  height: 18px;
  padding: 0;
  border: none;
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
  border-radius: 50%;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.selected-item-remove:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #fecaca;
  transform: scale(1.15);
}

/* 分割线 */
.divider {
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    rgba(148, 163, 184, 0.3) 20%,
    rgba(148, 163, 184, 0.3) 80%,
    transparent
  );
  margin-bottom: 12px;
}

/* ========== 树容器高度调整（给已选项目栏留空间）========== */
.tree-container {
  max-height: calc(100vh - 380px);  /* 原来是 280px，现在减去已选项目栏的高度 */
  overflow-y: auto;
  overflow-x: hidden;
}

/* ========== 其他样式保持不变 ========== */

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== 指标单元格：悬停显示收藏按钮 ===== */
.metric-cell {
  position: relative;
  padding: 8px 12px !important;
  transition: background 0.2s ease;
}

.metric-cell .metric-value {
  position: relative;
  z-index: 1;
}

/* 收藏按钮：默认隐藏 */
.metric-cell .fav-icon {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  
  width: 24px;
  height: 24px;
  padding: 4px;
  
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 6px;
  
  cursor: pointer;
  opacity: 0;
  transition: all 0.25s ease;
}

.metric-cell .fav-icon svg {
  width: 100%;
  height: 100%;
  stroke: rgba(129, 140, 248, 0.8);
  fill: transparent;
  transition: all 0.2s ease;
}

/* 悬停单元格时显示按钮 */
.metric-cell:hover .fav-icon {
  opacity: 1;
}

/* 悬停按钮时的效果 */
.metric-cell .fav-icon:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: rgba(129, 140, 248, 0.6);
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
  transform: translateY(-50%) scale(1.1);
}

.metric-cell .fav-icon:hover svg {
  stroke: #a5b4fc;
}

/* ===== 已收藏状态 ===== */
.metric-cell.is-favorited .fav-icon {
  opacity: 1;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-color: transparent;
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.4);
}

.metric-cell.is-favorited .fav-icon svg {
  stroke: white;
  fill: rgba(255, 255, 255, 0.9);
}

.metric-cell.is-favorited .fav-icon:hover {
  box-shadow: 0 0 16px rgba(139, 92, 246, 0.6);
  transform: translateY(-50%) scale(1.15);
}

/* 已收藏的单元格背景微调 */
.metric-cell.is-favorited {
  background: rgba(99, 102, 241, 0.08);
}

/* 项目名称列样式 */
.repo-cell {
  font-weight: 500;
  color: #e5e7eb;
}

/* ===========================
   智能选型建议样式
   =========================== */
.conclusion-section {
  margin-top: 24px;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.1), rgba(168, 85, 247, 0.1));
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 16px;
  padding: 20px;
}

.conclusion-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.conclusion-icon {
  font-size: 24px;
}

.conclusion-header h3 {
  margin: 0;
  font-size: 18px;
  color: #e5e7eb;
  flex: 1;
}

.conclusion-badge {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: white;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.one-liner {
  background: rgba(83, 107, 164, 0.6);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.one-liner p {
  margin: 0;
  font-size: 15px;
  color: #e5e7eb;
  line-height: 1.6;
}

.ranking-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(51, 65, 85, 0.5);
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.rank-item.rank-first {
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.2), rgba(249, 115, 22, 0.2));
  border-color: rgba(234, 179, 8, 0.4);
}

.rank-medal {
  font-size: 20px;
}

.rank-name {
  font-weight: 600;
  color: #e5e7eb;
  font-size: 14px;
}

.rank-score {
  color: #38bdf8;
  font-weight: 700;
  font-size: 14px;
}

.recommendations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.rec-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 14px;
  transition: all 0.2s ease;
}

.rec-card:hover {
  border-color: rgba(56, 189, 248, 0.4);
  transform: translateY(-2px);
}

.rec-scenario {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
}

.rec-project {
  font-size: 15px;
  font-weight: 600;
  color: #22c55e;
  margin-bottom: 4px;
}

.rec-reason {
  font-size: 12px;
  color: #cbd5f5;
}

.insights-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.insight-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.insight-item.warning {
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.3);
  color: #fef3c7;
}

.insight-item.highlight {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #bbf7d0;
}

.insight-icon {
  font-size: 16px;
}

.typing-cursor{
  display:inline-block;
  margin-left:6px;
  animation: blink 1s infinite;
}
@keyframes blink{
  0%,50%{opacity:1}
  51%,100%{opacity:0}
}
.risk-grid{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

/* ✅ Header 最大化按钮样式（仿窗口最大化） */
.modal-max-btn{
  font-size: 18px;
  color: #94a3b8;
  background: none;
  border: none;
  cursor: pointer;
  margin-right: 8px;
  transition: 0.2s;
}
.modal-max-btn:hover{
  color: #fff;
  transform: scale(1.08);
}

/* ✅ 全屏阅读模式：弹窗铺满 */
.analysis-modal.fullscreen{
  width: 100vw;
  height: 100vh;
  max-width: none;
  border-radius: 0;
}

/* ✅ 全屏阅读模式：只显示右侧报告 */
.modal-body.report-only{
  grid-template-columns: 1fr;
}
.analysis-modal.fullscreen .chart-section{
  display: none;
}

/* ✅ 全屏阅读模式：右侧报告更宽松 + 字体更大 */
.analysis-modal.fullscreen .report-section{
  zoom: 1.22;              /* 建议 1.18 ~ 1.28 之间调 */
  font-size: 16px;         /* 兜底：即使内部用 rem/em 也能正常 */
  line-height: 1.75;
}


.analysis-modal.fullscreen .summary-desc p{ font-size: 15px; line-height: 1.8; }
.analysis-modal.fullscreen .comp-table{ font-size: 15px; }
.analysis-modal.fullscreen .mini-list{ font-size: 14px; line-height: 1.8; }
.analysis-modal.fullscreen .ib-content p{ font-size: 14px; line-height: 1.7; }

.analysis-modal.fullscreen .report-card{
  padding: 18px 18px;
}
/* AI 文字预览区：放大+显示更多 */
.analysis-modal.fullscreen .ai-text-preview{
  font-size: 14px;
  max-height: 60vh;
}
/* ✅ 标题/关键数值：明确放大 */
.analysis-modal.fullscreen .report-section h3,
.analysis-modal.fullscreen .report-section h4{
  font-size: 18px;
  line-height: 1.3;
}

.analysis-modal.fullscreen .summary-score{
  font-size: 46px; /* 你截图里 0.49 那个分数 */
}

/* ✅ 右侧分析的正文（核心阅读区） */
.analysis-modal.fullscreen .report-section p,
.analysis-modal.fullscreen .report-section li{
  font-size: 15px;
  line-height: 1.8;
}

/* ✅ 表格区（项目对比分析那块） */
.analysis-modal.fullscreen .comp-table{
  font-size: 15px;
}
.analysis-modal.fullscreen .comp-table th,
.analysis-modal.fullscreen .comp-table td{
  padding: 10px 12px;
}

/* ✅ badge/小标签：别小到看不清 */
.analysis-modal.fullscreen .risk-badge,
.analysis-modal.fullscreen .tag,
.analysis-modal.fullscreen .pill{
  font-size: 13px;
  padding: 4px 10px;
}

/* ✅ AI 文本区：最容易觉得小，把它单独加大 */
.analysis-modal.fullscreen .ai-text-preview{
  font-size: 15px;
  line-height: 1.85;
  max-height: 62vh;
}
/* =========================
   阅读增强：右侧报告区字体整体变大（含项目对比表格）
   ========================= */

/* 1) 默认弹窗：就让它达到“正常阅读” */
.analysis-modal .report-section{
  font-size: 15px;
  line-height: 1.75;
}

/* 项目对比分析表格（你截图这一块） */
.analysis-modal .comp-table{
  font-size: 15px;             /* 原来 13px */
}
.analysis-modal .comp-table th{
  font-size: 14px;             /* 原来 12px 左右 */
  padding-bottom: 14px;
}
.analysis-modal .comp-table td{
  padding: 18px 0;             /* 原来 16px 0，行高更舒服 */
}

/* 项目名/组织名 */
.analysis-modal .p-name{
  font-size: 16px;             /* 原来 14px */
  line-height: 1.3;
}
.analysis-modal .p-sub{
  font-size: 13px;             /* 原来 11px */
  margin-top: 4px;
}

/* 优势/风险列表 */
.analysis-modal .mini-list{
  font-size: 14px;             /* 原来 12px */
  line-height: 1.8;
}

/* 分数 badge 也放大一点 */
.analysis-modal .score-badge{
  font-size: 14px;
  padding: 4px 10px;           /* 原来 2px 8px */
}

/* 2) 全屏阅读模式：再大一档（如果你用了 fullscreen） */
.analysis-modal.fullscreen .report-section{
  font-size: 17px;
}
.analysis-modal.fullscreen .comp-table{
  font-size: 17px;
}
.analysis-modal.fullscreen .mini-list{
  font-size: 16px;
}
.analysis-modal.fullscreen .p-name{
  font-size: 18px;
}
.analysis-modal.fullscreen .p-sub{
  font-size: 14px;
}
.analysis-modal.fullscreen .score-badge{
  font-size: 15px;
}
.report-controls{
  display:flex;
  align-items:center;
  gap:10px;
}

.tone-select{
  height: 36px;
  padding: 0 10px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.25);
  color: #e5e7eb;
  font-size: 13px;
  outline: none;
}

.tone-select:focus{
  border-color: rgba(56, 189, 248, 0.55);
  box-shadow: 0 0 0 3px rgba(56,189,248,0.12);
}

</style>
