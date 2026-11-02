<template>
  <div class="intro-page">
    <div class="career-container intro-main">
      <header class="intro-header">
        <router-link to="/career-paths" class="back-link">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6M8 12h12" /></svg>
          返回职业路径
        </router-link>
        <p class="intro-eyebrow">个人背景 / 自我介绍</p>
        <h1>填写个人自述</h1>
        <p class="intro-lead">通过多维度的自我评估，我们将为您构建精准的职业画像，助力您在计算机科学领域发现最适合的发展路径。</p>
        <nav class="intro-steps" aria-label="填写章节">
          <a v-for="(section, index) in sections" :key="section.id" :href="`#intro-${section.id}`" @click.prevent="goToSection(section.id)">
            <span class="step-number" :class="{ complete: section.complete }">
              <svg v-if="section.complete" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
              <template v-else>0{{ index + 1 }}</template>
            </span>
            {{ section.title }}
          </a>
        </nav>
      </header>

      <div class="intro-layout">
        <form class="intro-form" @submit.prevent="nextToAssessment" @focusin="revealFocusedField" :aria-busy="loading">
          <fieldset class="form-fields" :disabled="loading">
            <legend class="sr-only">个人自述</legend>
            <section id="intro-basics" class="intro-panel" aria-labelledby="basics-title">
              <div class="section-heading">
                <span class="section-number">01</span>
                <div><h2 id="basics-title">基本信息与职业目标</h2><p>从你的学习背景开始，告诉我们你想前往的方向。</p></div>
              </div>
              <div class="basic-grid">
                <div class="field"><label for="intro-name">姓名</label><input id="intro-name" v-model="formData.name" autocomplete="name" placeholder="请输入您的姓名" type="text" /></div>
                <div class="field"><label for="intro-school">就读学校</label><input id="intro-school" v-model="formData.school" placeholder="例如：长沙理工大学" type="text" /></div>
                <div class="field"><label for="intro-major">专业</label><input id="intro-major" v-model="formData.major" placeholder="例如：计算机科学与技术" type="text" /></div>
                <div class="field"><label for="intro-grade">年级</label><input id="intro-grade" v-model="formData.grade" placeholder="例如：大三" type="text" /></div>
                <fieldset class="gender-field">
                  <legend>性别 <span class="optional">选填</span></legend>
                  <div class="gender-options">
                    <label v-for="gender in ['男', '女']" :key="gender" :class="{ selected: formData.gender === gender }"><input v-model="formData.gender" name="gender" type="radio" :value="gender" /><span>{{ gender }}</span></label>
                  </div>
                </fieldset>
                <div class="field"><label for="intro-goal">目标职业</label><input id="intro-goal" v-model="formData.goal" placeholder="例如：全栈工程师 / 算法科学家" type="text" /></div>
              </div>
            </section>

            <section id="intro-skills" class="intro-panel" aria-labelledby="skills-title">
              <div class="section-heading">
                <span class="section-number">02</span>
                <div><h2 id="skills-title">技能模块评估</h2><p>选择你已经接触或掌握的技能，可以多选。</p></div>
                <span class="selection-count" aria-live="polite">已选 {{ formData.skills.length }} 项</span>
              </div>
              <div class="skills-grid">
                <details v-for="group in skillGroups" :key="group.id" class="skill-group" :open="expandedGroups[group.id]" @toggle="expandedGroups[group.id] = $event.target.open">
                  <summary><span><strong>{{ group.title }}</strong><small>{{ group.description }}</small></span><span class="group-count">{{ selectedInGroup(group) }}/{{ group.items.length }}</span><svg class="chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></summary>
                  <div class="skill-options">
                    <label v-for="skill in group.items" :key="skill.value" :class="{ selected: formData.skills.includes(skill.value) }"><input v-model="formData.skills" type="checkbox" :value="skill.value" /><span>{{ skill.label }}</span></label>
                  </div>
                </details>
              </div>
            </section>

            <section id="intro-experience" class="intro-panel" aria-labelledby="experience-title">
              <div class="section-heading">
                <span class="section-number">03</span>
                <div><h2 id="experience-title">经历与个人偏好</h2><p>不必写成正式简历，具体的经历会让推荐更有参考价值。</p></div>
              </div>
              <div class="writing-grid">
                <div class="field">
                  <label for="intro-other-skills">其他技能或项目经历</label>
                  <p id="experience-hint" class="field-hint">可以写：做过什么、使用的技术、你的职责与成果。</p>
                  <textarea id="intro-other-skills" v-model="formData.otherSkills" aria-describedby="experience-hint" rows="7" placeholder="例如：使用 Vue 与 Django 完成校园活动平台，负责前端页面与接口联调。也可以补充 Docker、AWS 等其他技能。"></textarea>
                  <span class="character-count">{{ formData.otherSkills.length }} 字</span>
                </div>
                <div class="field">
                  <label for="intro-description">个人特点与职业偏好</label>
                  <p id="preference-hint" class="field-hint">可以写：性格、学习方式、喜欢的工作内容与环境。</p>
                  <textarea id="intro-description" v-model="formData.selfDescription" aria-describedby="preference-hint" rows="7" placeholder="例如：喜欢拆解问题，愿意持续学习；希望参与有实际用户的产品开发，偏好协作清晰的团队。"></textarea>
                  <span class="character-count">{{ formData.selfDescription.length }} 字</span>
                </div>
              </div>
            </section>
          </fieldset>

          <div v-if="error" ref="errorPanel" class="form-error" role="alert" tabindex="-1">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v6m0 3h.01" /></svg>
            <p>{{ error }}</p>
          </div>
          <div class="intro-actions">
            <div class="action-status"><span>已填写 <strong>{{ progress.completed }}</strong> / {{ progress.total }} 项</span><small role="status">{{ draftMessage }}</small></div>
            <div class="action-buttons">
              <button class="draft-button" type="button" :disabled="loading" @click="saveDraftNow">保存草稿</button>
              <button class="submit-button" type="submit" :disabled="loading"><svg v-if="loading" class="loading-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9" /></svg><span>{{ loading ? loadingLabel : '下一步：开始测评' }}</span><svg v-if="!loading" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6" /></svg></button>
            </div>
          </div>
        </form>

        <aside class="intro-sidebar" aria-label="填写进度与提示">
          <div class="sidebar-content">
            <section class="progress-panel">
              <p class="sidebar-eyebrow">YOUR NEXT CHAPTER</p>
              <h2>让方向更清晰一点</h2>
              <div class="progress-heading"><span>填写进度</span><strong>{{ progress.percent }}<small>%</small></strong></div>
              <progress :value="progress.completed" :max="progress.total" aria-label="填写进度"></progress>
              <ul><li v-for="section in sections" :key="section.id"><span>{{ section.title }}</span><span :class="{ 'section-done': section.complete }">{{ section.complete ? '已填写' : '待补充' }}</span></li></ul>
              <p class="progress-note">按实际情况填写即可，进度仅供参考，不影响继续测评。</p>
            </section>
            <section class="tips-panel">
              <h2><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6m-5 3h4M8 14a6 6 0 1 1 8 0c-1 1-1 2-1 2H9s0-1-1-2Z" /></svg>填写小提示</h2>
              <p>您的自我介绍将帮助我们构建精准的职业画像。请尽量详尽地描述您的技能、经验与职业目标，AI 将基于此为您推荐最匹配的岗位。</p>
              <p class="privacy-note">草稿保存在当前浏览器，退出登录时清除。</p>
            </section>
            <figure class="intro-image"><img src="@/assets/images/自我介绍.png" alt="桌面上的工作与规划资料" /><figcaption><span>Tech Career</span><strong>NAVIGATOR</strong></figcaption></figure>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { aiAPI, userAPI } from '@/api'
import { skillGroups, normalizeIntroduction, introductionProgress, introductionProfile, introductionText, saveIntroductionDraft } from '@/features/career-paths/self-introduction.js'

const router = useRouter()
const formData = ref(normalizeIntroduction())
const loading = ref(false)
const loadingLabel = ref('正在保存资料…')
const error = ref('')
const errorPanel = ref(null)
const draftState = ref('idle')
const expandedGroups = ref(Object.fromEntries(skillGroups.map(group => [group.id, true])))
let sessionToken = ''
let saveTimer
let stopWatching
let mobileQuery
let active = true
const progress = computed(() => introductionProgress(formData.value))
const hasText = key => Boolean(formData.value[key].trim())
const sections = computed(() => [
  { id: 'basics', title: '基本信息', complete: ['name', 'school', 'major', 'grade', 'goal'].every(hasText) },
  { id: 'skills', title: '技能评估', complete: formData.value.skills.length > 0 },
  { id: 'experience', title: '经历与偏好', complete: ['otherSkills', 'selfDescription'].every(hasText) },
])
const draftMessage = computed(() => ({ idle: '填写后自动保存草稿', restored: '已恢复本地草稿', pending: '草稿保存中…', saved: '草稿已保存到此浏览器', unavailable: '草稿未保存，请检查浏览器存储设置', 'session-changed': '登录状态已变化，请重新登录' }[draftState.value]))
const selectedInGroup = group => group.items.filter(skill => formData.value.skills.includes(skill.value)).length

function saveDraftNow() {
  clearTimeout(saveTimer)
  saveTimer = undefined
  draftState.value = saveIntroductionDraft(localStorage, sessionToken, formData.value)
}
function flushDraft() { if (saveTimer !== undefined) saveDraftNow() }
function goToSection(id) {
  document.getElementById(`intro-${id}`)?.scrollIntoView({ block: 'start', behavior: 'instant' })
}
function revealFocusedField(event) {
  const field = event.target
  if (!mobileQuery?.matches || !field.matches('input, textarea, summary')) return
  const bounds = field.getBoundingClientRect()
  const actions = field.closest('form').querySelector('.intro-actions').getBoundingClientRect()
  if (bounds.bottom > actions.top - 16 || bounds.top < 110) field.scrollIntoView({ block: 'center', behavior: 'instant' })
}
function setGroupLayout() {
  expandedGroups.value = Object.fromEntries(skillGroups.map((group, index) => [group.id, !mobileQuery.matches || index === 0 || selectedInGroup(group) > 0]))
}
onMounted(() => {
  try {
    sessionToken = localStorage.getItem('token') || ''
    const saved = localStorage.getItem('selfIntroduction')
    if (saved && sessionToken) {
      formData.value = normalizeIntroduction(JSON.parse(saved))
      draftState.value = 'restored'
    }
  } catch { draftState.value = 'unavailable' }
  mobileQuery = window.matchMedia('(max-width: 760px)')
  setGroupLayout()
  mobileQuery.addEventListener('change', setGroupLayout)
  stopWatching = watch(formData, () => {
    draftState.value = 'pending'
    clearTimeout(saveTimer)
    saveTimer = setTimeout(saveDraftNow, 600)
  }, { deep: true, flush: 'sync' })
  window.addEventListener('pagehide', flushDraft)
})
onBeforeUnmount(() => {
  active = false
  stopWatching?.()
  flushDraft()
  mobileQuery?.removeEventListener('change', setGroupLayout)
  window.removeEventListener('pagehide', flushDraft)
})

// 保留现有推荐文本哈希及 24 小时缓存约定。
function generateCacheKey(text) {
  let hash = 0
  for (let i = 0; i < text.length; i++) hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0
  return 'career_rec_cache_' + Math.abs(hash).toString(36)
}
function validCards(cards) {
  return Array.isArray(cards) && cards.length > 0 && cards.every(card => card && typeof card.career === 'string' && card.career.trim())
}
function getCachedRecommendation(text) {
  try {
    const cached = JSON.parse(localStorage.getItem(generateCacheKey(text)))
    if (cached?.expireTime > Date.now() && validCards(cached.data?.recommendations)) return cached.data
  } catch { /* 缓存损坏不阻止重新请求。 */ }
  return null
}
function setCachedRecommendation(text, data) {
  try { localStorage.setItem(generateCacheKey(text), JSON.stringify({ data, expireTime: Date.now() + 86400000, cachedAt: Date.now() })) }
  catch { /* 结果已保存时，缓存写入失败不阻止继续。 */ }
}
function storeResults(data) {
  localStorage.setItem('careerRecommendations', JSON.stringify(data.recommendations))
  if (data.accordion) localStorage.setItem('careerAnalysis', JSON.stringify(data.accordion))
  else localStorage.removeItem('careerAnalysis')
  localStorage.setItem('careerRecommendationRaw', data.raw_analysis || '')
  if (data.session_id) localStorage.setItem('careerRecommendationSessionId', data.session_id)
  else localStorage.removeItem('careerRecommendationSessionId')
}
function sessionIsCurrent() { return active && sessionToken && localStorage.getItem('token') === sessionToken }
async function nextToAssessment() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  loadingLabel.value = '正在保存资料…'
  let phase = 'profile'
  try {
    if (!sessionIsCurrent()) throw new Error('登录状态已变化，请重新登录后再继续。')
    saveDraftNow()
    const snapshot = normalizeIntroduction(formData.value)
    await userAPI.updateProfile(introductionProfile(snapshot))
    if (!sessionIsCurrent()) return
    const text = introductionText(snapshot)
    phase = 'recommendation'
    loadingLabel.value = '正在生成推荐…'
    let data = getCachedRecommendation(text)
    if (!data) {
      const response = await aiAPI.careerRecommendation(text)
      if (!sessionIsCurrent()) return
      if (!response?.success) throw new Error('暂时无法生成职业推荐，请稍后重试。已填写的内容仍保留。')
      const cards = Array.isArray(response.cards) ? response.cards : Array.isArray(response.recommendations) ? response.recommendations.map(rec => ({ career: rec?.career, matchScore: rec?.matchScore, reason: rec?.reason })) : []
      if (!validCards(cards)) throw new Error('本次未返回有效的职业推荐，请重试或补充个人自述。')
      data = { recommendations: cards, accordion: response.accordion || null, raw_analysis: response.raw_analysis || (response.recommendations ? JSON.stringify(response.recommendations) : ''), session_id: response.session_id || '', match_score: response.match_score || 0 }
    }
    phase = 'storage'
    storeResults(data)
    setCachedRecommendation(text, data)
    phase = 'navigation'
    await router.push('/career-evaluation')
  } catch (err) {
    if (!active) return
    if (phase === 'profile') error.value = '资料保存失败，请检查网络或登录状态后重试。已填写的内容仍保留。'
    else if (phase === 'storage') error.value = '推荐已生成，但浏览器未能保存结果。请检查存储权限或可用空间后重试。'
    else if (phase === 'navigation') error.value = '未能打开测评页面，请检查网络后重试。'
    else error.value = err.response || err.code ? '职业推荐请求失败，请检查网络后重试。已填写的内容仍保留。' : err.message || '暂时无法生成推荐，请稍后重试。'
    await nextTick()
    errorPanel.value?.focus()
  } finally { loading.value = false }
}
</script>

<style scoped>
.intro-page { color: var(--career-text); background: var(--career-bg); }
.intro-main { padding-block: 36px 64px; }
.intro-header { max-width: 880px; margin-bottom: 30px; }
.intro-page svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; flex-shrink: 0; }
.back-link { display: inline-flex; align-items: center; gap: 8px; color: var(--career-muted); font-size: 13px; min-height: 36px; margin-bottom: 26px; }
.back-link:hover { color: var(--career-text); }
.intro-eyebrow { font-size: 12px; color: var(--career-muted); letter-spacing: .08em; margin-bottom: 10px; }
.intro-header h1 { font-size: clamp(30px, 3.2vw, 42px); line-height: 1.3; }
.intro-lead { font-size: 15px; line-height: 1.9; color: var(--career-muted); max-width: 760px; margin-top: 14px; text-wrap: pretty; }
.intro-steps { display: flex; gap: 32px; margin-top: 26px; }
.intro-steps a { display: flex; align-items: center; gap: 9px; min-height: 44px; font-size: 13px; }
.step-number { display: grid; place-items: center; width: 28px; height: 28px; border: 1px solid var(--career-border); border-radius: 50%; font-size: 11px; color: var(--career-muted); }
.step-number.complete { background: #e8edde; border-color: #e8edde; color: #526349; }
.step-number svg { width: 16px; height: 16px; }
.intro-layout { display: grid; grid-template-columns: minmax(0, 1fr) 256px; gap: 32px; align-items: start; }
.intro-form, .form-fields { min-width: 0; }
.form-fields { display: grid; gap: 24px; margin: 0; padding: 0; border: 0; }
.intro-panel { background: #fff; border: 1px solid var(--career-border); border-radius: 16px; padding: 30px; scroll-margin-top: 105px; }
.section-heading { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 24px; }
.section-number { font-size: 12px; padding-top: 5px; color: #7c8475; font-variant-numeric: tabular-nums; }
.section-heading h2 { font-size: 19px; line-height: 1.5; }
.section-heading p { font-size: 13px; color: var(--career-muted); margin-top: 5px; line-height: 1.7; }
.basic-grid, .writing-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px 24px; }
.field { display: flex; flex-direction: column; min-width: 0; }
.field > label, .gender-field legend { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.field input, .field textarea { display: block; width: 100%; min-width: 0; border: 1px solid #dfe2d7; border-radius: 8px; background: #fcfcfa; padding: 12px 13px; font-size: 14px; line-height: 1.6; color: var(--career-text); scroll-margin-block: 110px 150px; }
.field input { min-height: 46px; }
.field textarea { min-height: 200px; resize: vertical; flex: 1; }
.field input::placeholder, .field textarea::placeholder { color: #757d6e; opacity: 1; }
.field input:focus, .field textarea:focus { border-color: #687c53; background: #fff; }
.gender-field { min-width: 0; margin: 0; padding: 0; border: 0; }
.optional { font-weight: 400; color: var(--career-muted); margin-left: 6px; font-size: 11px; }
.gender-options { display: flex; gap: 8px; }
.gender-options label { display: flex; align-items: center; justify-content: center; gap: 7px; min-height: 47px; padding: 8px 11px; border: 1px solid var(--career-border); border-radius: 8px; font-size: 13px; cursor: pointer; }
.gender-options label.selected { border-color: #9aa98b; background: #f1f4ec; }
.intro-page input[type='checkbox'], .intro-page input[type='radio'] { accent-color: #526349; width: 17px; height: 17px; flex-shrink: 0; }
.selection-count { margin-left: auto; flex-shrink: 0; border-radius: 20px; padding: 4px 10px; font-size: 12px; color: #526349; background: #eff2e9; }
.skills-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-items: start; }
.skill-group { border: 1px solid var(--career-border); border-radius: 12px; overflow: hidden; }
.skill-group summary { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 16px; list-style: none; }
.skill-group summary::-webkit-details-marker { display: none; }
.skill-group summary strong { display: block; font-weight: 600; font-size: 14px; }
.skill-group summary small { display: block; font-size: 11px; color: var(--career-muted); margin-top: 3px; }
.group-count { margin-left: auto; font-size: 11px; color: var(--career-muted); }
.chevron { width: 16px !important; height: 16px !important; }
.skill-group[open] .chevron { transform: rotate(180deg); }
.skill-options { display: grid; padding: 0 8px 8px; }
.skill-options label { display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 8px; border-radius: 6px; font-size: 13px; cursor: pointer; }
.skill-options label:hover { background: #f7f8f3; }
.skill-options label.selected { background: #eef2e7; }
.field-hint { min-height: 44px; margin-bottom: 10px; font-size: 12px; line-height: 1.8; color: var(--career-muted); }
.character-count { text-align: right; font-size: 11px; color: var(--career-muted); margin-top: 7px; }
.intro-actions { position: relative; z-index: 20; display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px 20px; margin-top: 24px; border: 1px solid #d8ddcf; border-radius: 12px; background: #fff; box-shadow: 0 5px 24px #2935220a; }
.action-status { font-size: 12px; }
.action-status strong { font-weight: 600; color: #526349; }
.action-status small { display: block; font-size: 11px; color: var(--career-muted); margin-top: 3px; }
.action-buttons { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.action-buttons button { min-height: 46px; border-radius: 8px; font-size: 13px; padding: 11px 16px; }
.draft-button { border: 1px solid var(--career-border); background: #fff; }
.draft-button:hover { background: #f7f8f3; }
.submit-button { display: inline-flex; align-items: center; justify-content: center; gap: 10px; color: #fff; background: var(--career-blue); }
.submit-button:hover { background: var(--career-blue-dark); }
.action-buttons button:disabled { opacity: .65; cursor: wait; }
.form-error { display: flex; align-items: flex-start; gap: 10px; border: 1px solid #e4c7bd; background: #fcf5f2; color: #8c4432; padding: 16px; margin-top: 24px; border-radius: 12px; font-size: 14px; scroll-margin-block: 110px 150px; }
.sidebar-content { position: sticky; top: 112px; display: grid; gap: 20px; }
.intro-sidebar { align-self: stretch; }
.progress-panel { background: #eef1e7; border: 1px solid #e0e5d6; padding: 24px; border-radius: 16px; }
.sidebar-eyebrow { font-size: 9px; letter-spacing: .14em; color: #6c795f; margin-bottom: 12px; }
.progress-panel h2 { font-size: 18px; }
.progress-heading { display: flex; justify-content: space-between; align-items: baseline; margin-top: 24px; font-size: 12px; color: #58664d; }
.progress-heading strong { font-size: 28px; font-weight: 500; }
.progress-heading small { font-size: 13px; margin-left: 2px; }
progress { display: block; width: 100%; height: 5px; appearance: none; border: 0; background: #dce2d2; border-radius: 5px; margin: 10px 0 18px; overflow: hidden; }
progress::-webkit-progress-bar { background: #dce2d2; }
progress::-webkit-progress-value { background: #697e55; border-radius: 5px; }
progress::-moz-progress-bar { background: #697e55; }
.progress-panel ul { display: grid; gap: 12px; font-size: 12px; }
.progress-panel li { display: flex; justify-content: space-between; }
.progress-panel li > span:last-child { color: #727a68; font-size: 11px; }
.progress-panel li > .section-done { color: #415836; }
.progress-note { font-size: 11px; color: #68735f; line-height: 1.9; margin-top: 22px; padding-top: 16px; border-top: 1px solid #dbe2d1; }
.tips-panel { padding: 4px 8px; }
.tips-panel h2 { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-bottom: 12px; }
.tips-panel p { color: var(--career-muted); font-size: 12px; line-height: 1.9; }
.tips-panel .privacy-note { margin-top: 14px; font-size: 11px; }
.intro-image { position: relative; border-radius: 16px; overflow: hidden; height: 160px; }
.intro-image img { width: 100%; height: 100%; object-fit: cover; }
.intro-image figcaption { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: flex-end; padding: 18px; color: #fff; background: linear-gradient(transparent 25%, #152018b3); }
.intro-image figcaption span { text-transform: uppercase; letter-spacing: .14em; font-size: 9px; }
.intro-image figcaption strong { font-size: 15px; letter-spacing: .04em; }
.loading-icon { animation: intro-spin 1s linear infinite; }
@keyframes intro-spin { to { transform: rotate(360deg); } }
@media (max-width: 1100px) { .intro-layout { grid-template-columns: minmax(0, 1fr); } .intro-sidebar { display: none; } }
@media (max-width: 760px) {
  .intro-main { width: calc(100% - 32px); padding-block: 24px 32px; }
  .back-link { margin-bottom: 22px; }
  .intro-lead { font-size: 14px; }
  .intro-steps { justify-content: space-between; gap: 8px; margin-top: 20px; }
  .intro-steps a { font-size: 12px; gap: 6px; }
  .intro-panel { padding: 22px 18px; }
  .form-fields { gap: 18px; }
  .section-heading { flex-wrap: wrap; gap: 9px; margin-bottom: 20px; }
  .section-heading > div { flex: 1; min-width: 0; }
  .section-heading h2 { font-size: 18px; }
  .section-heading p { font-size: 12px; }
  .selection-count { margin-left: 26px; }
  .basic-grid, .writing-grid, .skills-grid { grid-template-columns: minmax(0, 1fr); gap: 18px; }
  .field input, .field textarea { font-size: 16px; }
  .field textarea { min-height: 200px; }
  .field-hint { min-height: 0; }
  .gender-options label { flex: 1; padding-inline: 8px; }
  .intro-actions { position: sticky; bottom: 0; padding: 12px 12px calc(12px + env(safe-area-inset-bottom)); flex-direction: column; align-items: stretch; gap: 10px; margin-top: 18px; border-radius: 12px 12px 0 0; }
  .action-status { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .action-status small { margin: 0; font-size: 10px; text-align: right; }
  .action-buttons { gap: 10px; }
  .action-buttons .submit-button { flex: 1; padding-inline: 10px; }
  .action-buttons button { font-size: 13px; }
}
@media (prefers-reduced-motion: reduce) { .loading-icon { animation: none; } }
</style>
