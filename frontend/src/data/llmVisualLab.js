export const metricOptions = [
  {
    value: 'health_score',
    label: '综合健康度',
    shortLabel: '健康度',
    description: 'OpenRank、活跃度与稳定性的综合评分'
  },
  {
    value: 'openrank_mean_12m',
    label: 'OpenRank 近 12 个月均值',
    shortLabel: 'OpenRank',
    description: '项目在开源网络中的综合影响力'
  },
  {
    value: 'activity_mean_12m',
    label: '活跃度近 12 个月均值',
    shortLabel: '活跃度',
    description: '项目近期社区协作和开发活跃水平'
  },
  {
    value: 'openrank_std_12m',
    label: 'OpenRank 波动',
    shortLabel: '波动',
    description: '近 12 个月 OpenRank 的波动幅度'
  }
]

export const timeRangeOptions = [
  { value: '6m', label: '近 6 个月', months: 6 },
  { value: '12m', label: '近 12 个月', months: 12 },
  { value: '24m', label: '近 24 个月', months: 24 },
  { value: 'all', label: '全量可用', months: 36 }
]

export const topNOptions = [10, 20, 30, 50]

export const useCaseOptions = [
  { value: 'all', label: '全部用途' },
  { value: 'comparison', label: '排名对比' },
  { value: 'trend', label: '趋势判断' },
  { value: 'structure', label: '结构识别' },
  { value: 'relation', label: '关系追踪' },
  { value: 'diagnosis', label: '能力诊断' },
  { value: 'risk', label: '风险识别' }
]

export const chartCategories = [
  { id: 'all', label: '全部图表', description: '浏览工坊内所有分析图' },
  { id: 'ranking', label: '排名对比', description: '比较项目强弱、增长和差距' },
  { id: 'trend', label: '趋势变化', description: '判断生态热度和排名流动' },
  { id: 'structure', label: '生态结构', description: '观察类别层级与占比' },
  { id: 'relation', label: '贡献关系', description: '理解组织、项目和指标连接' },
  { id: 'evaluation', label: '多指标评估', description: '识别项目能力画像' },
  { id: 'risk', label: '风险异常', description: '定位波动、失衡和潜在衰退' },
  { id: 'favorites', label: '我的收藏', description: '查看已收藏的图表方案' }
]

export const chartRegistry = [
  {
    id: 'ranking-bar',
    name: 'Top N 排名柱状图',
    type: 'Bar',
    category: 'ranking',
    useCase: 'comparison',
    preview: 'bars',
    accent: '#2dd4bf',
    question: '哪些项目当前最健康，头部差距有多大？',
    description: '按选定指标展示项目 Top N 排名，是进入生态分析的首选视角。',
    requiredFields: ['project_key', 'category', 'health_score', 'openrank_mean_12m', 'activity_mean_12m'],
    recommended: true
  },
  {
    id: 'metric-heatmap',
    name: '项目指标热力图',
    type: 'Heatmap',
    category: 'ranking',
    useCase: 'diagnosis',
    preview: 'matrix',
    accent: '#38bdf8',
    question: '哪些项目在哪些指标上表现突出或明显短板？',
    description: '把项目与关键指标交叉成矩阵，适合快速发现强项、弱项和异常格子。',
    requiredFields: ['health_score', 'openrank_mean_12m', 'activity_mean_12m', 'openrank_std_12m'],
    recommended: true
  },
  {
    id: 'sunburst-structure',
    name: '生态结构旭日图',
    type: 'Sunburst',
    category: 'structure',
    useCase: 'structure',
    preview: 'sunburst',
    accent: '#f59e0b',
    question: 'LLM 生态的类别结构是否均衡，哪些类别占主导？',
    description: '用类别到项目的层级结构呈现生态构成，适合讲清技术版图。',
    requiredFields: ['category', 'project_key', 'health_score'],
    recommended: true
  },
  {
    id: 'treemap-share',
    name: '生态占比矩形树图',
    type: 'Treemap',
    category: 'structure',
    useCase: 'structure',
    preview: 'treemap',
    accent: '#22c55e',
    question: '不同类别和项目在生态影响力中各占多少？',
    description: '用面积表达项目和类别的影响力占比，便于发现头部集中度。',
    requiredFields: ['category', 'project_key', 'openrank_mean_12m'],
    recommended: false
  },
  {
    id: 'radar-profile',
    name: '多指标雷达画像',
    type: 'Radar',
    category: 'evaluation',
    useCase: 'diagnosis',
    preview: 'radar',
    accent: '#60a5fa',
    question: '一个项目的发展能力是否均衡？',
    description: '把健康度、影响力、活跃度、稳定性与风险控制放在同一张能力画像中。',
    requiredFields: ['health_score', 'openrank_mean_12m', 'activity_mean_12m', 'openrank_std_12m'],
    recommended: true
  },
  {
    id: 'bubble-quadrant',
    name: '健康活跃气泡图',
    type: 'Bubble',
    category: 'evaluation',
    useCase: 'diagnosis',
    preview: 'bubble',
    accent: '#a78bfa',
    question: '高活跃项目是否也具有高健康度？',
    description: '用横轴健康度、纵轴活跃度、气泡面积影响力定位项目象限。',
    requiredFields: ['health_score', 'activity_mean_12m', 'openrank_mean_12m'],
    recommended: false
  },
  {
    id: 'trend-line',
    name: 'OpenRank 趋势折线图',
    type: 'Line',
    category: 'trend',
    useCase: 'trend',
    preview: 'line',
    accent: '#06b6d4',
    question: '项目影响力是在变热、回落还是保持稳定？',
    description: '按时间窗口拉取项目 OpenRank 月度序列，适合分析长期热度变化。',
    requiredFields: ['project_key', 'openrank'],
    needsTrendData: true,
    recommended: true
  },
  {
    id: 'sankey-flow',
    name: '指标贡献桑基图',
    type: 'Sankey',
    category: 'relation',
    useCase: 'relation',
    preview: 'sankey',
    accent: '#14b8a6',
    question: '类别、项目和指标贡献之间如何流动？',
    description: '把类别、项目与指标贡献连成流向，适合展示生态贡献来源。',
    requiredFields: ['category', 'project_key', 'health_score', 'activity_mean_12m'],
    recommended: false
  },
  {
    id: 'network-relation',
    name: '项目关系网络图',
    type: 'Graph',
    category: 'relation',
    useCase: 'relation',
    preview: 'network',
    accent: '#38bdf8',
    question: '哪些项目或组织处在生态网络中心？',
    description: '连接类别、组织和项目节点，突出生态中心与跨类别桥梁。',
    requiredFields: ['category', 'org', 'repo', 'project_key'],
    recommended: true
  },
  {
    id: 'bump-rank',
    name: '排名流动图',
    type: 'Bump',
    category: 'trend',
    useCase: 'trend',
    preview: 'bump',
    accent: '#f472b6',
    question: '项目排名随月份如何变化，谁在上升或掉队？',
    description: '把 OpenRank 月度序列转为排名轨迹，适合观察生态竞争格局。',
    requiredFields: ['project_key', 'openrank'],
    needsTrendData: true,
    recommended: false
  },
  {
    id: 'risk-matrix',
    name: '风险异常矩阵',
    type: 'Matrix',
    category: 'risk',
    useCase: 'risk',
    preview: 'risk',
    accent: '#fb7185',
    question: '哪些项目存在高波动、低健康或低活跃风险？',
    description: '将健康度、波动和活跃度折算为风险格，辅助识别重点关注对象。',
    requiredFields: ['health_score', 'activity_mean_12m', 'openrank_std_12m'],
    recommended: false
  }
]

export const categoryLabelMap = {
  training_framework: '训练框架',
  llm_framework: '模型框架',
  llm_app_framework: '应用框架',
  llm_inference: '推理引擎',
  inference_engine: '推理引擎',
  code_model: '代码模型',
  foundation_model: '基础模型',
  observability: '可观测性',
  vector_database: '向量数据库',
  low_code_platform: '低代码平台',
  agent_framework: 'Agent 框架',
  evaluation: '评测工具',
  unknown: '未分类'
}

const palette = [
  '#38bdf8',
  '#22c55e',
  '#f59e0b',
  '#a78bfa',
  '#14b8a6',
  '#f472b6',
  '#60a5fa',
  '#fb7185',
  '#34d399',
  '#c084fc'
]

const metricLabelByKey = Object.fromEntries(metricOptions.map(item => [item.value, item.label]))

export function getMetricLabel(metric) {
  return metricLabelByKey[metric] || metric
}

export function getChartById(chartId) {
  return chartRegistry.find(chart => chart.id === chartId) || chartRegistry[0]
}

export function compactProjectName(projectKey = '') {
  const parts = String(projectKey).split('/').filter(Boolean)
  if (parts.length >= 3) return `${parts[1]}/${parts[2]}`
  return parts.join('/') || projectKey
}

export function shortProjectName(projectKey = '') {
  const parts = compactProjectName(projectKey).split('/')
  return parts[1] || parts[0] || projectKey
}

export function renderCategory(category) {
  return categoryLabelMap[category] || category || '未分类'
}

export function normalizeProjects(projects = []) {
  const safeProjects = projects.filter(Boolean)
  const maxOpenRank = Math.max(...safeProjects.map(p => Number(p.openrank_mean_12m) || 0), 1)
  const maxActivity = Math.max(...safeProjects.map(p => Number(p.activity_mean_12m) || 0), 1)
  const maxStd = Math.max(...safeProjects.map(p => Number(p.openrank_std_12m) || 0), 1)

  return safeProjects.map((project, index) => {
    const openrank = Number(project.openrank_mean_12m) || 0
    const activity = Number(project.activity_mean_12m) || 0
    const volatility = Number(project.openrank_std_12m) || 0
    const health = clamp01(Number(project.health_score) || 0)
    const openrankNorm = clamp01(openrank / maxOpenRank)
    const activityNorm = clamp01(activity / maxActivity)
    const volatilityNorm = clamp01(volatility / maxStd)
    const stability = clamp01(1 - volatilityNorm)
    const riskScore = clamp01((1 - health) * 0.44 + volatilityNorm * 0.36 + (1 - activityNorm) * 0.2)

    return {
      ...project,
      index,
      displayName: compactProjectName(project.project_key),
      shortName: shortProjectName(project.project_key),
      categoryLabel: renderCategory(project.category),
      openrank,
      activity,
      volatility,
      health,
      openrankNorm,
      activityNorm,
      volatilityNorm,
      stability,
      riskScore,
      metricProfile: {
        health,
        openrank: openrankNorm,
        activity: activityNorm,
        stability,
        riskControl: clamp01(1 - riskScore)
      }
    }
  })
}

export function sortProjects(projects = [], metric = 'health_score') {
  return [...projects].sort((a, b) => (Number(b[metric]) || 0) - (Number(a[metric]) || 0))
}

export function groupByCategory(projects = []) {
  return projects.reduce((acc, project) => {
    const key = project.category || 'unknown'
    if (!acc[key]) acc[key] = []
    acc[key].push(project)
    return acc
  }, {})
}

export function getProjectMetricValue(project, metric) {
  if (!project) return 0
  if (metric === 'openrank_std_12m') return Number(project.openrank_std_12m) || 0
  return Number(project[metric]) || 0
}

export function buildChartOption({ chartId, projects, metric, timeRange, trendData }) {
  const chart = getChartById(chartId)
  const sorted = sortProjects(projects, metric)
  const topProjects = sorted.slice(0, Math.min(sorted.length, 12))
  const metricLabel = getMetricLabel(metric)

  const base = {
    backgroundColor: 'transparent',
    color: palette,
    textStyle: {
      color: '#dbeafe',
      fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    },
    tooltip: {
      trigger: 'item',
      confine: true,
      backgroundColor: 'rgba(8, 13, 31, 0.94)',
      borderColor: 'rgba(56, 189, 248, 0.35)',
      textStyle: { color: '#e5f2ff' }
    }
  }

  switch (chart.id) {
    case 'ranking-bar':
      return buildRankingBarOption(base, topProjects, metric, metricLabel)
    case 'metric-heatmap':
      return buildHeatmapOption(base, topProjects)
    case 'sunburst-structure':
      return buildSunburstOption(base, sorted, metric)
    case 'treemap-share':
      return buildTreemapOption(base, sorted, metric)
    case 'radar-profile':
      return buildRadarOption(base, topProjects.slice(0, 5))
    case 'bubble-quadrant':
      return buildBubbleOption(base, sorted.slice(0, 30))
    case 'trend-line':
      return buildTrendLineOption(base, sorted.slice(0, 8), trendData, timeRange)
    case 'sankey-flow':
      return buildSankeyOption(base, topProjects, metric)
    case 'network-relation':
      return buildNetworkOption(base, sorted.slice(0, 30), metric)
    case 'bump-rank':
      return buildBumpRankOption(base, sorted.slice(0, 8), trendData, timeRange)
    case 'risk-matrix':
      return buildRiskMatrixOption(base, topProjects)
    default:
      return buildRankingBarOption(base, topProjects, metric, metricLabel)
  }
}

export function buildLocalInsights(chart, projects = [], metric = 'health_score') {
  const sorted = sortProjects(projects, metric)
  if (!sorted.length) {
    return ['暂无可分析项目，请调整筛选条件或稍后重试数据加载。']
  }

  const top = sorted[0]
  const second = sorted[1]
  const risky = [...projects].sort((a, b) => b.riskScore - a.riskScore)[0]
  const categories = groupByCategory(projects)
  const leadingCategory = Object.entries(categories)
    .map(([category, items]) => ({
      category,
      label: renderCategory(category),
      count: items.length,
      totalHealth: items.reduce((sum, item) => sum + item.health, 0)
    }))
    .sort((a, b) => b.totalHealth - a.totalHealth)[0]

  const gap = second ? getProjectMetricValue(top, metric) - getProjectMetricValue(second, metric) : 0
  const gapText = second
    ? `${top.shortName} 领先 ${second.shortName} ${formatNumber(gap)}，头部差距需要结合类别结构判断。`
    : `${top.shortName} 是当前筛选条件下的唯一项目。`

  const common = [
    `${top.shortName} 在「${getMetricLabel(metric)}」上排名第一，当前值为 ${formatNumber(getProjectMetricValue(top, metric))}。`,
    gapText,
    leadingCategory
      ? `${leadingCategory.label} 是当前筛选中综合贡献最高的类别，共覆盖 ${leadingCategory.count} 个项目。`
      : '当前筛选没有形成明显类别中心。'
  ]

  if (chart.category === 'risk') {
    common.push(`${risky.shortName} 的风险分最高，主要由健康度、活跃度和波动共同决定。`)
  } else if (chart.category === 'relation') {
    common.push('关系类图表建议先看类别枢纽，再看组织和项目节点的连接强度。')
  } else if (chart.category === 'trend') {
    common.push('趋势类图表会优先拉取 OpenRank 月度序列；接口不可用时保留当前汇总视角。')
  } else if (chart.category === 'structure') {
    common.push('结构类图表适合回答生态是否过度依赖少数类别或少数项目。')
  } else if (chart.category === 'evaluation') {
    common.push('多指标视角更适合选型：关注均衡能力，而不只看单项峰值。')
  }

  return common
}

export function buildReportMarkdown({ chart, projects, metric, filters, insights, aiReport }) {
  const sorted = sortProjects(projects, metric).slice(0, 10)
  const lines = [
    `# ${chart.name} 分析报告`,
    '',
    `- 图表问题：${chart.question}`,
    `- 分析指标：${getMetricLabel(metric)}`,
    `- 时间窗口：${filters.timeRangeLabel}`,
    `- 项目类别：${filters.categoryLabel}`,
    `- Top N：${filters.topN}`,
    '',
    '## 关键洞察',
    ...insights.map(item => `- ${item}`),
    '',
    '## Top 项目',
    '| 排名 | 项目 | 类别 | 健康度 | OpenRank | 活跃度 | 波动 |',
    '|---:|---|---|---:|---:|---:|---:|',
    ...sorted.map((project, index) => (
      `| ${index + 1} | ${project.displayName} | ${project.categoryLabel} | ${formatNumber(project.health)} | ${formatNumber(project.openrank)} | ${formatNumber(project.activity)} | ${formatNumber(project.volatility)} |`
    ))
  ]

  if (aiReport) {
    lines.push('', '## AI 解读', aiReport)
  }

  return `${lines.join('\n')}\n`
}

export function formatNumber(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '0'
  if (Math.abs(n) >= 100) return n.toFixed(1)
  if (Math.abs(n) >= 10) return n.toFixed(2)
  return n.toFixed(3)
}

export function getMonthLimit(timeRange) {
  return timeRangeOptions.find(item => item.value === timeRange)?.months || 12
}

function buildRankingBarOption(base, projects, metric, metricLabel) {
  return {
    ...base,
    grid: { left: 120, right: 28, top: 28, bottom: 34 },
    xAxis: {
      type: 'value',
      name: metricLabel,
      axisLabel: { color: '#9fb2d8' },
      nameTextStyle: { color: '#93c5fd' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)', type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      inverse: true,
      data: projects.map(project => project.displayName),
      axisLabel: { color: '#dbeafe', width: 108, overflow: 'truncate' }
    },
    series: [
      {
        type: 'bar',
        name: metricLabel,
        data: projects.map(project => ({
          value: getProjectMetricValue(project, metric),
          itemStyle: { color: barGradient(project.index) }
        })),
        barWidth: 16,
        label: {
          show: true,
          position: 'right',
          color: '#bfdbfe',
          formatter: params => formatNumber(params.value)
        }
      }
    ]
  }
}

function buildHeatmapOption(base, projects) {
  const dimensions = [
    { key: 'health', label: '健康度' },
    { key: 'openrankNorm', label: '影响力' },
    { key: 'activityNorm', label: '活跃度' },
    { key: 'stability', label: '稳定性' },
    { key: 'riskScore', label: '风险' }
  ]
  const data = []
  projects.forEach((project, projectIndex) => {
    dimensions.forEach((dimension, metricIndex) => {
      data.push([metricIndex, projectIndex, Math.round((project[dimension.key] || 0) * 100)])
    })
  })

  return {
    ...base,
    grid: { left: 120, right: 32, top: 42, bottom: 42 },
    xAxis: {
      type: 'category',
      data: dimensions.map(item => item.label),
      axisLabel: { color: '#c7d2fe' },
      splitArea: { show: true, areaStyle: { color: ['rgba(15, 23, 42, 0.3)', 'rgba(30, 41, 59, 0.16)'] } }
    },
    yAxis: {
      type: 'category',
      data: projects.map(project => project.displayName),
      axisLabel: { color: '#dbeafe', width: 108, overflow: 'truncate' },
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: '#9fb2d8' },
      inRange: { color: ['#172554', '#0ea5e9', '#22c55e'] }
    },
    series: [
      {
        type: 'heatmap',
        data,
        label: {
          show: true,
          color: '#e0f2fe',
          formatter: params => `${params.value[2]}`
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 12,
            shadowColor: 'rgba(56, 189, 248, 0.4)'
          }
        }
      }
    ]
  }
}

function buildSunburstOption(base, projects, metric) {
  const grouped = groupByCategory(projects)
  const data = Object.entries(grouped).map(([category, items]) => ({
    name: renderCategory(category),
    value: items.reduce((sum, item) => sum + getProjectMetricValue(item, metric), 0),
    children: sortProjects(items, metric).slice(0, 12).map(item => ({
      name: item.shortName,
      value: Math.max(getProjectMetricValue(item, metric), 0.01)
    }))
  }))

  return {
    ...base,
    series: [
      {
        type: 'sunburst',
        radius: ['12%', '92%'],
        data,
        sort: null,
        emphasis: { focus: 'ancestor' },
        label: { color: '#e0f2fe', rotate: 'radial', minAngle: 8 },
        levels: [
          {},
          {
            r0: '14%',
            r: '42%',
            itemStyle: { borderWidth: 2, borderColor: '#08111f' },
            label: { rotate: 0 }
          },
          {
            r0: '42%',
            r: '92%',
            itemStyle: { borderWidth: 1, borderColor: '#08111f' }
          }
        ]
      }
    ]
  }
}

function buildTreemapOption(base, projects, metric) {
  const data = Object.entries(groupByCategory(projects)).map(([category, items]) => ({
    name: renderCategory(category),
    children: sortProjects(items, metric).slice(0, 20).map(project => ({
      name: project.shortName,
      value: Math.max(getProjectMetricValue(project, metric), 0.01)
    }))
  }))

  return {
    ...base,
    series: [
      {
        type: 'treemap',
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: { color: '#e0f2fe', formatter: '{b}' },
        upperLabel: { show: true, height: 24, color: '#bfdbfe' },
        itemStyle: {
          borderColor: '#08111f',
          borderWidth: 2,
          gapWidth: 2
        },
        levels: [
          {
            itemStyle: {
              borderColor: 'rgba(148, 163, 184, 0.26)',
              borderWidth: 0,
              gapWidth: 3
            }
          },
          {
            colorSaturation: [0.36, 0.76],
            itemStyle: { gapWidth: 2 }
          }
        ],
        data
      }
    ]
  }
}

function buildRadarOption(base, projects) {
  const indicators = [
    { name: '健康度', key: 'health', max: 1 },
    { name: '影响力', key: 'openrank', max: 1 },
    { name: '活跃度', key: 'activity', max: 1 },
    { name: '稳定性', key: 'stability', max: 1 },
    { name: '风险控制', key: 'riskControl', max: 1 }
  ]

  return {
    ...base,
    legend: {
      top: 0,
      textStyle: { color: '#c7d2fe' },
      data: projects.map(project => project.shortName)
    },
    radar: {
      center: ['50%', '56%'],
      radius: '68%',
      indicator: indicators.map(({ name, max }) => ({ name, max })),
      axisName: { color: '#dbeafe' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.22)' } },
      splitArea: { areaStyle: { color: ['rgba(15, 23, 42, 0.42)', 'rgba(30, 41, 59, 0.22)'] } },
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.28)' } }
    },
    series: [
      {
        type: 'radar',
        data: projects.map((project, index) => ({
          name: project.shortName,
          value: indicators.map(item => project.metricProfile[item.key]),
          areaStyle: { opacity: index === 0 ? 0.24 : 0.12 },
          lineStyle: { width: index === 0 ? 3 : 1.5 }
        }))
      }
    ]
  }
}

function buildBubbleOption(base, projects) {
  return {
    ...base,
    grid: { left: 58, right: 38, top: 34, bottom: 52 },
    xAxis: {
      name: '健康度',
      min: 0,
      max: 1,
      axisLabel: { color: '#9fb2d8' },
      nameTextStyle: { color: '#93c5fd' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)', type: 'dashed' } }
    },
    yAxis: {
      name: '活跃度',
      min: 0,
      max: 1,
      axisLabel: { color: '#9fb2d8' },
      nameTextStyle: { color: '#93c5fd' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)', type: 'dashed' } }
    },
    series: [
      {
        type: 'scatter',
        data: projects.map(project => ({
          name: project.displayName,
          value: [project.health, project.activityNorm, project.openrankNorm, project.categoryLabel],
          symbolSize: Math.max(12, 14 + project.openrankNorm * 46),
          itemStyle: { color: palette[project.index % palette.length], opacity: 0.82 }
        })),
        label: {
          show: true,
          formatter: params => shortProjectName(params.name),
          color: '#dbeafe',
          position: 'top'
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: 'rgba(191, 219, 254, 0.28)', type: 'dashed' },
          data: [{ xAxis: 0.5 }, { yAxis: 0.5 }]
        }
      }
    ]
  }
}

function buildTrendLineOption(base, projects, trendData = {}, timeRange) {
  const months = collectMonths(projects, trendData, timeRange)
  const series = projects.map((project, index) => ({
    type: 'line',
    name: project.shortName,
    smooth: true,
    showSymbol: false,
    emphasis: { focus: 'series' },
    lineStyle: { width: index === 0 ? 3 : 2 },
    data: months.map(month => getTrendValue(project, trendData, month))
  }))

  return {
    ...base,
    legend: { top: 0, textStyle: { color: '#c7d2fe' }, type: 'scroll' },
    grid: { left: 58, right: 32, top: 48, bottom: 42 },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: '#9fb2d8' },
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.28)' } }
    },
    yAxis: {
      type: 'value',
      name: 'OpenRank',
      axisLabel: { color: '#9fb2d8' },
      nameTextStyle: { color: '#93c5fd' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)', type: 'dashed' } }
    },
    series
  }
}

function buildSankeyOption(base, projects, metric) {
  const nodes = new Map()
  const links = []
  const metricNodes = [
    { name: '健康贡献', key: 'health_score' },
    { name: '活跃贡献', key: 'activity_mean_12m' },
    { name: '影响贡献', key: 'openrank_mean_12m' }
  ]

  metricNodes.forEach(node => nodes.set(node.name, { name: node.name, depth: 2 }))

  projects.forEach(project => {
    const categoryName = project.categoryLabel
    const projectName = project.shortName
    nodes.set(categoryName, { name: categoryName, depth: 0 })
    nodes.set(projectName, { name: projectName, depth: 1 })

    links.push({
      source: categoryName,
      target: projectName,
      value: Math.max(getProjectMetricValue(project, metric), 0.01)
    })

    metricNodes.forEach(metricNode => {
      links.push({
        source: projectName,
        target: metricNode.name,
        value: Math.max(Number(project[metricNode.key]) || 0.01, 0.01)
      })
    })
  })

  return {
    ...base,
    series: [
      {
        type: 'sankey',
        nodeWidth: 14,
        nodeGap: 10,
        draggable: false,
        layoutIterations: 20,
        emphasis: { focus: 'adjacency' },
        label: { color: '#dbeafe', fontSize: 11 },
        lineStyle: { color: 'gradient', opacity: 0.28, curveness: 0.45 },
        itemStyle: { borderColor: 'rgba(219, 234, 254, 0.26)', borderWidth: 1 },
        data: Array.from(nodes.values()),
        links
      }
    ]
  }
}

function buildNetworkOption(base, projects, metric) {
  const categories = [{ name: '类别' }, { name: '组织' }, { name: '项目' }]
  const nodes = []
  const links = []
  const seen = new Set()

  const pushNode = (node) => {
    if (seen.has(node.id)) return
    seen.add(node.id)
    nodes.push(node)
  }

  projects.forEach(project => {
    const categoryId = `category:${project.categoryLabel}`
    const orgId = `org:${project.org}`
    const projectId = `project:${project.displayName}`

    pushNode({
      id: categoryId,
      name: project.categoryLabel,
      category: 0,
      symbolSize: 32,
      value: 1,
      itemStyle: { color: '#22c55e' }
    })
    pushNode({
      id: orgId,
      name: project.org,
      category: 1,
      symbolSize: 22,
      value: 1,
      itemStyle: { color: '#38bdf8' }
    })
    pushNode({
      id: projectId,
      name: project.shortName,
      category: 2,
      symbolSize: Math.max(16, 18 + project.openrankNorm * 36),
      value: getProjectMetricValue(project, metric),
      itemStyle: { color: palette[project.index % palette.length] }
    })

    links.push({ source: categoryId, target: projectId, value: project.health })
    links.push({ source: orgId, target: projectId, value: project.openrankNorm })
  })

  return {
    ...base,
    legend: [{ top: 0, data: categories.map(item => item.name), textStyle: { color: '#c7d2fe' } }],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        categories,
        data: nodes,
        links,
        force: {
          repulsion: 140,
          edgeLength: [50, 120],
          gravity: 0.08
        },
        label: { show: true, position: 'right', color: '#dbeafe', fontSize: 11 },
        lineStyle: { color: 'source', opacity: 0.28, width: 1.2 },
        emphasis: { focus: 'adjacency' }
      }
    ]
  }
}

function buildBumpRankOption(base, projects, trendData = {}, timeRange) {
  const months = collectMonths(projects, trendData, timeRange)
  const monthlyRanks = months.map(month => {
    const ranked = projects
      .map(project => ({ key: project.project_key, value: getTrendValue(project, trendData, month) }))
      .sort((a, b) => b.value - a.value)
    return new Map(ranked.map((item, index) => [item.key, index + 1]))
  })

  return {
    ...base,
    legend: { top: 0, textStyle: { color: '#c7d2fe' }, type: 'scroll' },
    grid: { left: 58, right: 32, top: 50, bottom: 42 },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: '#9fb2d8' }
    },
    yAxis: {
      type: 'value',
      inverse: true,
      min: 1,
      max: Math.max(projects.length, 2),
      interval: 1,
      axisLabel: { color: '#9fb2d8', formatter: value => `#${value}` },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.14)', type: 'dashed' } }
    },
    series: projects.map((project, index) => ({
      type: 'line',
      name: project.shortName,
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: index === 0 ? 3 : 2 },
      data: months.map((_, monthIndex) => monthlyRanks[monthIndex].get(project.project_key) || projects.length)
    }))
  }
}

function buildRiskMatrixOption(base, projects) {
  const dimensions = [
    { key: 'riskScore', label: '综合风险' },
    { key: 'volatilityNorm', label: '波动风险' },
    { key: 'healthGap', label: '健康短板' },
    { key: 'activityGap', label: '活跃短板' }
  ]

  const data = []
  projects.forEach((project, projectIndex) => {
    dimensions.forEach((dimension, metricIndex) => {
      const value = dimension.key === 'healthGap'
        ? 1 - project.health
        : dimension.key === 'activityGap'
          ? 1 - project.activityNorm
          : project[dimension.key]
      data.push([metricIndex, projectIndex, Math.round((value || 0) * 100)])
    })
  })

  return {
    ...base,
    grid: { left: 120, right: 32, top: 42, bottom: 42 },
    xAxis: {
      type: 'category',
      data: dimensions.map(item => item.label),
      axisLabel: { color: '#c7d2fe' },
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: projects.map(project => project.displayName),
      axisLabel: { color: '#dbeafe', width: 108, overflow: 'truncate' },
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: '#9fb2d8' },
      inRange: { color: ['#052e16', '#eab308', '#fb7185'] }
    },
    series: [
      {
        type: 'heatmap',
        data,
        label: { show: true, color: '#f8fafc', formatter: params => `${params.value[2]}` }
      }
    ]
  }
}

function collectMonths(projects, trendData, timeRange) {
  const limit = getMonthLimit(timeRange)
  const set = new Set()
  projects.forEach(project => {
    const loadedSeries = trendData?.[project.project_key]
    const series = loadedSeries?.length ? loadedSeries : estimateTrend(project, limit)
    series.forEach(point => set.add(point.month))
  })
  return Array.from(set).sort().slice(-limit)
}

function getTrendValue(project, trendData, month) {
  const loadedSeries = trendData?.[project.project_key]
  const series = loadedSeries?.length ? loadedSeries : estimateTrend(project, 12)
  const point = series.find(item => item.month === month)
  return Number(point?.value ?? point?.count ?? 0)
}

function estimateTrend(project, months) {
  const base = project.openrank || 0
  const amplitude = Math.max(project.volatility || base * 0.08, base * 0.04)
  const now = new Date()

  return Array.from({ length: months }).map((_, index) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (months - index - 1), 1)
    const month = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const wave = Math.sin((index + project.index) * 0.82) * amplitude * 0.38
    const drift = (index - months / 2) * amplitude * 0.035 * (project.health > 0.3 ? 1 : -1)
    return {
      month,
      value: Math.max(0, base + wave + drift)
    }
  })
}

function barGradient(index) {
  const start = palette[index % palette.length]
  const end = palette[(index + 2) % palette.length]
  return {
    type: 'linear',
    x: 0,
    y: 0,
    x2: 1,
    y2: 0,
    colorStops: [
      { offset: 0, color: start },
      { offset: 1, color: end }
    ]
  }
}

function clamp01(value) {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(1, value))
}
