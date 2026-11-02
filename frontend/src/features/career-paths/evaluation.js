import { normalizeIntroduction, textFields } from './self-introduction.js'

// 保留原有职业名称；同一分类中的重复条目仅展示一次。
export const careerCategories = [
  {
    "id": "backend",
    "label": "后端开发",
    "roles": [
      "Java",
      "C++",
      "PHP",
      "Golang",
      "Python",
      "Node.js",
      "Rust",
      "C#工程师",
      "全栈开发",
      "安全工程师",
      "游戏后端",
      "游戏前端",
      "区块链",
      "信息技术岗",
      ".NET",
      "Delphi",
      "GIS工程师",
      "VB",
      "Perl",
      "Ruby",
      "Erlang",
      "后端工程师",
      "语音视频图形开发"
    ]
  },
  {
    "id": "ai",
    "label": "人工智能",
    "roles": [
      "算法工程师",
      "深度学习",
      "自然语言处理",
      "机器学习",
      "计算机视觉",
      "语音识别",
      "推荐算法",
      "数据挖掘"
    ]
  },
  {
    "id": "frontend",
    "label": "前端开发",
    "roles": [
      "Web前端",
      "前端工程师",
      "游戏前端",
      "H5开发",
      "React/Vue",
      "小程序开发"
    ]
  },
  {
    "id": "client",
    "label": "客户端开发",
    "roles": [
      "安卓 (Android)",
      "iOS开发",
      "Flutter开发",
      "Unity3D",
      "游戏客户端"
    ]
  },
  {
    "id": "data",
    "label": "数据",
    "roles": [
      "数据分析师",
      "大数据开发",
      "数据仓库 (ETL)",
      "数据架构师"
    ]
  },
  {
    "id": "operations",
    "label": "运维",
    "roles": [
      "运维工程师",
      "网络工程师",
      "安全运维",
      "SRE 工程师",
      "DBA (数据库管理)"
    ]
  },
  {
    "id": "testing",
    "label": "测试",
    "roles": [
      "测试工程师",
      "自动化测试",
      "性能测试",
      "测试开发 (TestDev)"
    ]
  },
  {
    "id": "engineering",
    "label": "研发工程师",
    "roles": [
      "嵌入式软件开发",
      "嵌入式硬件开发",
      "固件开发",
      "FPGA/芯片设计"
    ]
  },
  {
    "id": "support",
    "label": "销售技术支持",
    "roles": [
      "售前技术工程师",
      "客户成功",
      "售后技术支持",
      "技术支持经理"
    ]
  }
]

const text = value => typeof value === 'string' ? value.trim() : ''
const record = value => value && typeof value === 'object' && !Array.isArray(value)
const list = value => [...new Set((Array.isArray(value) ? value : [value]).map(text).filter(Boolean))]

export function normalizeMatchScore(value) {
  if (typeof value !== 'number' && typeof value !== 'string') return null
  const raw = typeof value === 'string' ? value.trim().replace(/[%％]$/, '').trim() : String(value)
  if (!/^\d+(?:\.\d+)?$/.test(raw)) return null
  const score = Number(raw)
  return Number.isFinite(score) && score >= 0 && score <= 100 ? Math.round(score * 10) / 10 : null
}

export function normalizeRecommendations(value) {
  if (!Array.isArray(value)) return []
  const seen = new Set()
  return value.flatMap(item => {
    if (!record(item)) return []
    const career = text(item.career) || text(item.职业) || text(item.title)
    if (!career || seen.has(career)) return []
    seen.add(career)
    return [{
      career,
      matchScore: normalizeMatchScore(item.matchScore ?? item.匹配度),
      reason: text(item.reason) || text(item.推荐理由) || list(item.reasons).join('；'),
    }]
  })
}

export function normalizeCareerAnalysis(value) {
  const source = record(value) ? value : {}
  const careers = Array.isArray(source.careers) ? source.careers.flatMap(item => {
    if (!record(item)) return []
    const title = text(item.title) || text(item.career) || text(item.职业)
    if (!title) return []
    return [{
      title,
      matchScore: normalizeMatchScore(item.matchScore ?? item.匹配度),
      reasons: list(item.reasons || item.reason || item.推荐理由),
      skills: list(item.skills || item.skillsMatch || item.技能匹配),
      weakestPoint: text(item.weakestPoint),
      marketDemand: text(item.marketDemand),
      salaryRange: text(item.salaryRange),
      nextSteps: list(item.nextStep || item.suggestions || item.improvement || item.发展建议),
    }]
  }) : []
  const plan = record(source.actionPlan) ? source.actionPlan : {}
  return {
    overall: text(source.overall), careers,
    actionPlan: ['short', 'medium', 'long'].flatMap((key, index) => {
      const items = list(plan[key])
      return items.length ? [{ label: ['近期行动', '中期提升', '长期发展'][index], items }] : []
    }),
  }
}

export function hasIntroduction(value) {
  if (!record(value)) return false
  const form = normalizeIntroduction(value)
  return textFields.some(key => form[key].trim()) || form.skills.length > 0
}

// 只能使用用户明确选择的目标，不从推荐列表中隐式选取第一项。
export function selectedCareerName(value) {
  return Array.isArray(value) ? text(value[0]) : ''
}

export function readEvaluationState(storage) {
  const issues = []
  function read(key) {
    try {
      const raw = storage.getItem(key)
      return raw ? JSON.parse(raw) : null
    } catch {
      issues.push(key)
      return null
    }
  }
  const introduction = read('selfIntroduction')
  const analysis = normalizeCareerAnalysis(read('careerAnalysis'))
  let recommendations = normalizeRecommendations(read('careerRecommendations'))
  if (!recommendations.length) recommendations = normalizeRecommendations(analysis.careers)
  const validCareers = new Set([...careerCategories.flatMap(group => group.roles), ...recommendations.map(item => item.career)])
  const savedSelection = selectedCareerName(read('selectedCareers'))
  return {
    hasIntroduction: hasIntroduction(introduction),
    recommendations, analysis,
    selectedCareer: validCareers.has(savedSelection) ? savedSelection : '',
    issues,
  }
}

export function filterCareerCategories(query, category = 'all') {
  const search = text(query).toLocaleLowerCase()
  return careerCategories.filter(group => category === 'all' || category === group.id).map(group => ({
    ...group,
    roles: !search || group.label.toLocaleLowerCase().includes(search)
      ? group.roles : group.roles.filter(role => role.toLocaleLowerCase().includes(search)),
  })).filter(group => group.roles.length)
}

export function saveCareerSelection(storage, sessionToken, career) {
  try {
    if (!sessionToken || storage.getItem('token') !== sessionToken) return 'session-changed'
    storage.setItem('selectedCareers', JSON.stringify(career ? [career] : []))
    return 'saved'
  } catch {
    return 'unavailable'
  }
}
