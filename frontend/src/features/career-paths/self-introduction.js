export const skillGroups = [
  { id: 'technical', title: '技术技能', description: '开发语言与工程实践', items: [
    { value: 'Python 开发', label: 'Python 开发' },
    { value: 'PostgreSQL 数据库', label: 'PostgreSQL 数据库' },
    { value: 'RESTfulAPI设计', label: 'RESTful API 设计' },
    { value: '并发 / 异步编程', label: '并发 / 异步编程' },
    { value: 'Linux 使用与脚本', label: 'Linux 使用与脚本' },
    { value: 'Git / 版本管理', label: 'Git / 版本管理' },
  ] },
  { id: 'data', title: '数据科学', description: '数据分析与人工智能', items: [
    { value: '数据分析', label: '数据分析（Pandas）' },
    { value: '机器学习', label: '机器学习（有 / 无监督）' },
    { value: '深度学习框架', label: '深度学习框架' },
    { value: 'NLP', label: 'NLP（LLM）' },
    { value: 'CV(图像处理)', label: 'CV（图像处理）' },
    { value: '数据可视化(Plotly)', label: '数据可视化（Plotly）' },
  ] },
  { id: 'foundation', title: '基础技能', description: '日常工具与学习能力', items: [
    { value: '基本电脑操作', label: '电脑操作与系统使用' },
    { value: '效率管理', label: 'Office 文档与数据处理' },
    { value: '效率管理工具:任务管理', label: '效率工具与任务管理' },
    { value: '英文资料阅读能力', label: '英文资料阅读能力' },
    { value: '安全意识意识', label: '安全意识' },
    { value: '学习与问题解决能力', label: '学习与问题解决能力' },
  ] },
  { id: 'academic', title: '专业知识', description: '数学基础与计算机核心课程', items: [
    { value: '线性代数与矩阵运算', label: '线性代数' },
    { value: '概率论与统计推断', label: '概率论' },
    { value: '离散数学', label: '离散数学' },
    { value: '数据结构', label: '数据结构' },
    { value: '算法设计', label: '算法设计' },
    { value: '计算机网络', label: '计算机网络' },
  ] },
]

// 保持原有字段与技能 value，旧草稿及推荐接口仍可直接使用。
export const textFields = ['name', 'school', 'major', 'grade', 'gender', 'goal', 'otherSkills', 'selfDescription']

export function normalizeIntroduction(value) {
  const source = value && typeof value === 'object' && !Array.isArray(value) ? value : {}
  const result = Object.fromEntries(textFields.map(key => [key, typeof source[key] === 'string' ? source[key] : '']))
  result.gender = ['男', '女'].includes(result.gender) ? result.gender : ''
  result.skills = Array.isArray(source.skills)
    ? [...new Set(source.skills.filter(skill => typeof skill === 'string' && skill.trim()))]
    : []
  return result
}

export function introductionProgress(form) {
  const completed = textFields.filter(key => form[key].trim()).length + Number(form.skills.length > 0)
  return { completed, total: textFields.length + 1, percent: Math.round(completed / (textFields.length + 1) * 100) }
}

export function introductionProfile(form) {
  return {
    name: form.name, gender: form.gender || null, school: form.school,
    major: form.major, grade: form.grade, skills: form.skills.join(','),
    other_skills: form.otherSkills, self_introduction: form.selfDescription, career_goal: form.goal,
  }
}

export function introductionText(form) {
  return `姓名: ${form.name}\n学校: ${form.school}\n专业: ${form.major}\n年级: ${form.grade}\n性别: ${form.gender}\n技能: ${form.skills.join('、') || '无'}\n其他技能: ${form.otherSkills || '无'}\n条件自述: ${form.selfDescription || '无'}\n职业期望: ${form.goal || '无'}`
}

// 退出/切换账号后，不允许延迟保存重新写入已清除的个人资料。
export function saveIntroductionDraft(storage, sessionToken, form) {
  try {
    if (!sessionToken || storage.getItem('token') !== sessionToken) return 'session-changed'
    storage.setItem('selfIntroduction', JSON.stringify(normalizeIntroduction(form)))
    return 'saved'
  } catch {
    return 'unavailable'
  }
}
