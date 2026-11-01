// Project the existing /resumes/my/ schema into read-only sections.
const text = value => typeof value === 'string' ? value.trim() : ''
export function resumePreview(data) {
  const resume = data && typeof data === 'object' ? data : {}
  const sections = []
  for (const [key, title] of [['self_evaluation', '个人自评'], ['skills', '专业技能']]) {
    if (text(resume[key])) sections.push({ title, items: [{ title: '', meta: '', description: text(resume[key]), url: '' }] })
  }
  for (const [key, title, heading, detail] of [
    ['education', '教育背景', 'school', 'major'],
    ['experience', '实习与工作经历', 'company', 'position'],
    ['projects', '项目经历', 'name', 'role'],
    ['certificates', '证书认证', 'name', 'issuer'],
    ['awards', '获奖经历', 'name', 'issuer'],
  ]) {
    const items = (Array.isArray(resume[key]) ? resume[key] : []).filter(item => item && typeof item === 'object').map(item => ({
      title: text(item[heading]),
      meta: [text(item[detail]), text(item.period)].filter(Boolean).join(' · '),
      description: text(item.description),
      url: key === 'projects' ? text(item.url) : '',
    })).filter(item => item.title || item.meta || item.description || item.url)
    if (items.length) sections.push({ title, items })
  }
  const result = {
    name: text(resume.name), target: text(resume.target_position),
    contacts: ['phone', 'email', 'address'].map(key => text(resume[key])).filter(Boolean), sections,
  }
  return { ...result, empty: !result.name && !result.target && !result.contacts.length && !sections.length }
}
