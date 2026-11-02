<template>
  <div class="direction-page">
    <main class="career-container direction-main">
      <header class="page-heading">
        <div><p class="eyebrow">规划报告 / 职业方向</p><h1>选择你的职业方向</h1><p class="page-lead">结合推荐与个人兴趣，选择一个目标岗位，生成你的职业规划报告。</p></div>
        <router-link class="edit-intro" to="/career-paths/employment/self-introduction"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15v5Z" /></svg>编辑自我介绍</router-link>
      </header>
      <ol class="journey" aria-label="规划步骤">
        <li><router-link to="/career-paths/employment/self-introduction"><span>01</span>了解个人背景</router-link></li>
        <li class="current" aria-current="step"><span>02</span>选择职业方向</li>
        <li><span>03</span>生成规划报告</li>
      </ol>
      <p v-if="notice" class="read-notice" role="status">{{ notice }}</p>
      <section class="recommend-section" aria-labelledby="recommend-title">
        <div class="section-heading"><div><p class="eyebrow">从适合你的方向开始</p><h2 id="recommend-title">职业推荐</h2></div><span v-if="recommendations.length" class="subtle-badge">AI 定制推荐</span></div>
        <template v-if="recommendations.length">
          <p class="section-description">基于已保存的测评结果，选择你想进一步了解的方向。</p>
          <div class="recommend-grid">
            <article v-for="(rec, index) in recommendations" :key="rec.career" class="recommend-card" :class="{ selected: selectedCareer === rec.career }">
              <div class="recommend-top"><img src="@/assets/images/推荐1.png" alt="" class="recommend-icon" /><span v-if="rec.matchScore !== null" class="match-score"><strong>{{ rec.matchScore }}<small>%</small></strong><span>匹配度</span></span><span v-else class="no-score">匹配度未提供</span></div>
              <h3>{{ rec.career }}</h3>
              <p :id="`recommend-reason-${index}`" class="recommend-reason" :class="{ collapsed: rec.reason.length > 60 && !expandedReasons[rec.career] }">{{ rec.reason || '暂未提供推荐理由。' }}</p>
              <button v-if="rec.reason.length > 60" type="button" class="text-button reason-toggle" :aria-expanded="Boolean(expandedReasons[rec.career])" :aria-controls="`recommend-reason-${index}`" @click="expandedReasons[rec.career] = !expandedReasons[rec.career]">{{ expandedReasons[rec.career] ? '收起理由' : '展开理由' }}</button>
              <button type="button" class="recommend-select" :aria-label="`选择推荐方向：${rec.career}`" :aria-pressed="selectedCareer === rec.career" :disabled="loading" @click="selectCareer(rec.career)">{{ selectedCareer === rec.career ? '已选择此方向' : '选择此方向' }}<svg viewBox="0 0 24 24" aria-hidden="true"><path v-if="selectedCareer === rec.career" d="m5 12 4 4L19 6" /><path v-else d="M4 12h16m-6-6 6 6-6 6" /></svg></button>
            </article>
          </div>
          <p v-if="recommendations.length > 1" class="mobile-scroll-hint">左右滑动，查看其他推荐方向</p>
        </template>
        <div v-else class="recommend-empty">
          <svg class="empty-icon" viewBox="0 0 48 48" aria-hidden="true"><rect x="10" y="5" width="28" height="38" rx="5" /><path d="M17 15h14M17 22h14M17 29h8m6 5 2 2 5-5" /></svg>
          <div><h3>{{ profileReady ? '还没有可用的职业推荐' : '从了解自己开始' }}</h3><p>完成自我介绍测评后，这里会展示推荐方向。你也可以先浏览下方岗位。</p></div>
          <router-link class="outline-link" to="/career-paths/employment/self-introduction">{{ profileReady ? '重新进行测评' : '填写自我介绍' }}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6" /></svg></router-link>
        </div>
        <div v-if="hasAnalysis" class="analysis-panel">
          <button class="analysis-toggle" type="button" :aria-expanded="analysisOpen" aria-controls="career-analysis" @click="analysisOpen = !analysisOpen"><span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l4 4v14H6zM14 3v5h5M9 12h7M9 16h5" /></svg>职业分析</span><span>{{ analysisOpen ? '收起分析' : '展开分析' }}<svg :class="{ rotated: analysisOpen }" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></span></button>
          <div v-if="analysisOpen" id="career-analysis" class="analysis-content">
            <div v-if="analysis.overall" class="analysis-overview"><h3>总体分析</h3><p>{{ analysis.overall }}</p></div>
            <details v-for="(career, index) in analysis.careers" :key="`${career.title}-${index}`" class="analysis-career">
              <summary><strong>{{ career.title }}</strong><span v-if="career.matchScore !== null">{{ career.matchScore }}% 匹配</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></summary>
              <dl class="analysis-fields">
                <div v-if="career.reasons.length"><dt>推荐理由</dt><dd><ul><li v-for="reason in career.reasons" :key="reason">{{ reason }}</li></ul></dd></div>
                <div v-if="career.skills.length"><dt>技能匹配</dt><dd class="skill-tags"><span v-for="skill in career.skills" :key="skill">{{ skill }}</span></dd></div>
                <div v-if="career.weakestPoint"><dt>待补足的能力</dt><dd>{{ career.weakestPoint }}</dd></div>
                <div v-if="career.marketDemand"><dt>市场热度</dt><dd>{{ career.marketDemand }}</dd></div>
                <div v-if="career.salaryRange"><dt>起薪范围</dt><dd>{{ career.salaryRange }}</dd></div>
                <div v-if="career.nextSteps.length"><dt>下一步建议</dt><dd><ul><li v-for="step in career.nextSteps" :key="step">{{ step }}</li></ul></dd></div>
              </dl>
            </details>
            <div v-if="analysis.actionPlan.length" class="action-plan"><section v-for="phase in analysis.actionPlan" :key="phase.label"><h3>{{ phase.label }}</h3><ul><li v-for="item in phase.items" :key="item">{{ item }}</li></ul></section></div>
          </div>
        </div>
        <p v-else-if="recommendations.length" class="analysis-unavailable">本次推荐暂未提供详细分析。</p>
      </section>
      <section id="career-catalog" class="catalog-section" aria-labelledby="catalog-title">
        <div class="catalog-heading">
          <div class="catalog-title"><img src="@/assets/images/职业大类.png" alt="" /><div><h2 id="catalog-title">全职业图谱</h2><p>{{ careerCategories.length }} 个领域 · {{ roleCount }} 个岗位，每次选择一个目标岗位</p></div></div>
          <div class="search-box"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg><label class="sr-only" for="career-search">搜索岗位或领域</label><input id="career-search" v-model="searchQuery" type="search" placeholder="搜索岗位，如 Python、前端、数据" @input="activeCategory = 'all'" /></div>
        </div>
        <div class="category-filters" role="group" aria-label="按职业领域筛选"><button type="button" :aria-pressed="activeCategory === 'all'" @click="activeCategory = 'all'">全部领域</button><button v-for="category in careerCategories" :key="category.id" type="button" :aria-pressed="activeCategory === category.id" @click="activeCategory = category.id">{{ category.label }}</button></div>
        <p class="filter-status" role="status">{{ searchQuery.trim() ? `找到 ${filteredRoleCount} 个匹配岗位` : activeCategory === 'all' ? '展开领域查看岗位，或使用搜索快速查找' : `本领域共 ${filteredRoleCount} 个岗位` }}</p>
        <div v-if="filteredCategories.length" class="category-list">
          <details v-for="category in filteredCategories" :key="category.id" class="career-category" :open="Boolean(expandedGroups[category.id])" @toggle="expandedGroups[category.id] = $event.target.open">
            <summary><span class="category-marker" aria-hidden="true"></span><h3>{{ category.label }}</h3><span class="category-count">{{ category.roles.length }} 项</span><span v-if="category.roles.includes(selectedCareer)" class="category-selected">已选</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg></summary>
            <div class="role-grid" role="group" :aria-label="`${category.label}岗位`"><button v-for="role in category.roles" :key="role" type="button" class="career-choice" :class="{ selected: selectedCareer === role }" :aria-pressed="selectedCareer === role" :disabled="loading" @click="selectCareer(role)"><span>{{ role }}</span><svg v-if="selectedCareer === role" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg><span v-else class="choice-circle" aria-hidden="true"></span></button></div>
          </details>
        </div>
        <div v-else class="search-empty"><h3>没有找到匹配岗位</h3><p>试试更短的关键词，或查看全部职业领域。</p><button type="button" class="text-button" @click="resetSearch">清除筛选</button></div>
      </section>
      <p v-if="!profileReady" class="profile-reminder">生成报告前，请先<router-link to="/career-paths/employment/self-introduction">完善自我介绍</router-link>，让规划与你的背景相关。</p>
      <p v-if="error" ref="errorPanel" class="page-error" role="alert" tabindex="-1">{{ error }}</p>
      <div class="selection-bar" :aria-busy="loading">
        <div class="selection-summary" aria-live="polite"><span class="selection-caption">目标岗位 · 单选</span><div><strong :title="selectedCareer">{{ selectedCareer || '请选择一个岗位' }}</strong><button v-if="selectedCareer" class="clear-selection" type="button" :disabled="loading" aria-label="清除已选岗位" @click="selectCareer('')"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 7 10 10M17 7 7 17" /></svg></button></div></div>
        <button class="generate-button" type="button" :disabled="!canGenerate" @click="goToCareerPlan"><span>{{ loading ? '正在打开报告…' : '生成规划报告' }}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6" /></svg></button>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { isNavigationFailure, useRouter } from 'vue-router'
import { careerCategories, filterCareerCategories, normalizeCareerAnalysis, readEvaluationState, saveCareerSelection } from '@/features/career-paths/evaluation.js'

const router = useRouter()
const recommendations = ref([])
const analysis = ref(normalizeCareerAnalysis(null))
const profileReady = ref(false)
const selectedCareer = ref('')
const searchQuery = ref('')
const activeCategory = ref('all')
const expandedGroups = ref({})
const expandedReasons = ref({})
const analysisOpen = ref(false)
const loading = ref(false)
const sessionValid = ref(false)
const notice = ref('')
const error = ref('')
const errorPanel = ref(null)
let sessionToken = ''
const roleCount = new Set(careerCategories.flatMap(category => category.roles)).size
const filteredCategories = computed(() => filterCareerCategories(searchQuery.value, activeCategory.value))
const filteredRoleCount = computed(() => new Set(filteredCategories.value.flatMap(category => category.roles)).size)
const hasAnalysis = computed(() => Boolean(analysis.value.overall || analysis.value.careers.length || analysis.value.actionPlan.length))
const canGenerate = computed(() => Boolean(selectedCareer.value && profileReady.value && sessionValid.value && !loading.value))
watch([searchQuery, activeCategory], () => {
  expandedGroups.value = Object.fromEntries(filteredCategories.value.map(category => [category.id, Boolean(searchQuery.value.trim()) || activeCategory.value !== 'all']))
})
function resetSearch() { searchQuery.value = ''; activeCategory.value = 'all' }
function loadSavedState() {
  try {
    const state = readEvaluationState(localStorage)
    recommendations.value = state.recommendations
    analysis.value = state.analysis
    selectedCareer.value = state.selectedCareer
    profileReady.value = state.hasIntroduction
    notice.value = state.issues.length ? '部分保存的资料无法读取。你可以重新完成自我介绍测评，或重新选择目标岗位。' : ''
  } catch { notice.value = '暂时无法读取本地资料，请检查浏览器存储设置。' }
}
function onStorageChange(event) {
  if (event.key === 'token' || event.key === null) {
    sessionValid.value = false
    selectedCareer.value = ''
    recommendations.value = []
    analysis.value = normalizeCareerAnalysis(null)
    profileReady.value = false
    error.value = '登录状态已变化，请重新登录后继续。'
  } else if (sessionValid.value && ['selfIntroduction', 'careerRecommendations', 'careerAnalysis', 'selectedCareers'].includes(event.key)) loadSavedState()
}
onMounted(() => {
  try { sessionToken = localStorage.getItem('token') || ''; sessionValid.value = Boolean(sessionToken) }
  catch { error.value = '无法读取登录状态，请检查浏览器存储设置。' }
  loadSavedState()
  window.addEventListener('storage', onStorageChange)
})
onBeforeUnmount(() => window.removeEventListener('storage', onStorageChange))
function persistSelection() {
  let status = 'unavailable'
  try { status = saveCareerSelection(localStorage, sessionToken, selectedCareer.value) } catch { /* 浏览器可能直接拒绝访问 localStorage。 */ }
  if (status === 'session-changed') { sessionValid.value = false; error.value = '登录状态已变化，请重新登录后继续。' }
  else if (status === 'unavailable') error.value = '未能保存所选岗位，请检查浏览器存储权限或可用空间后重试。'
  return status === 'saved'
}
function selectCareer(career) {
  if (loading.value) return
  selectedCareer.value = selectedCareer.value === career ? '' : career
  error.value = ''
  persistSelection()
}
async function goToCareerPlan() {
  if (!canGenerate.value) return
  loading.value = true
  error.value = ''
  try {
    if (!persistSelection()) return
    if (!readEvaluationState(localStorage).hasIntroduction) { profileReady.value = false; error.value = '请先完善自我介绍，再生成职业规划报告。'; return }
    const failure = await router.push('/career-plan')
    if (isNavigationFailure(failure)) error.value = '未能打开报告页面，请稍后重试。'
  } catch { error.value = '未能打开报告页面，请检查网络和浏览器存储设置后重试。' }
  finally { loading.value = false; if (error.value) { await nextTick(); errorPanel.value?.focus() } }
}
</script>

<style scoped>
.direction-page { color: var(--career-text); background: var(--career-bg); }
.direction-main { padding-block: 48px; }
.direction-page svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; flex-shrink: 0; }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; }
.eyebrow { font-size: 11px; letter-spacing: .08em; color: var(--career-muted); }
.page-heading h1 { margin-top: 10px; font-size: clamp(28px, 3vw, 38px); line-height: 1.35; }
.page-lead { margin-top: 14px; color: var(--career-muted); font-size: 14px; line-height: 1.9; text-wrap: pretty; }
.edit-intro { display: inline-flex; gap: 8px; align-items: center; min-height: 44px; font-size: 13px; flex-shrink: 0; }
.edit-intro:hover { color: #526349; }
.journey { display: flex; gap: 32px; align-items: center; padding-block: 26px; margin-bottom: 30px; border-bottom: 1px solid var(--career-border); color: var(--career-muted); font-size: 12px; }
.journey li, .journey a { display: flex; gap: 8px; align-items: center; }
.journey li > span, .journey a > span { display: grid; place-items: center; width: 25px; height: 25px; border: 1px solid var(--career-border); border-radius: 50%; font-size: 10px; }
.journey .current { color: var(--career-text); font-weight: 600; }
.journey .current > span { color: #fff; background: #526349; border-color: #526349; }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.section-heading h2, .catalog-title h2 { font-size: 22px; line-height: 1.5; }
.section-heading .eyebrow { margin-bottom: 6px; }
.subtle-badge { background: #eaf0e0; color: #526349; border-radius: 20px; font-size: 11px; padding: 5px 12px; }
.section-description { color: var(--career-muted); font-size: 13px; margin-block: 10px 20px; }
.recommend-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
.recommend-card { display: flex; flex-direction: column; align-items: flex-start; min-width: 0; padding: 24px; border: 1px solid var(--career-border); border-radius: 16px; background: #fff; }
.recommend-card.selected { background: #f0f4e9; border-color: #82956d; }
.recommend-top { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 18px; gap: 12px; }
.recommend-icon { width: 32px; height: 32px; border-radius: 8px; object-fit: cover; }
.match-score { display: flex; align-items: baseline; gap: 8px; color: #526349; }
.match-score strong { font-size: 25px; font-weight: 500; font-variant-numeric: tabular-nums; }
.match-score small { font-size: 12px; margin-left: 2px; }
.match-score > span, .no-score { font-size: 11px; color: var(--career-muted); }
.recommend-card h3 { font-size: 18px; overflow-wrap: anywhere; line-height: 1.5; }
.recommend-reason { font-size: 13px; line-height: 1.85; color: var(--career-muted); margin-block: 10px 14px; overflow-wrap: anywhere; white-space: pre-line; }
.recommend-reason.collapsed { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.text-button { color: #526349; font-size: 12px; min-height: 36px; text-decoration: underline; text-underline-offset: 4px; }
.reason-toggle { margin-top: -10px; margin-bottom: 10px; }
.recommend-select { display: flex; justify-content: space-between; align-items: center; gap: 10px; width: 100%; min-height: 44px; border-top: 1px solid var(--career-border); padding-top: 12px; margin-top: auto; font-size: 13px; color: #43563a; text-align: left; }
.recommend-select[aria-pressed='true'] { font-weight: 600; }
.recommend-select:hover { color: #1e3519; }
.mobile-scroll-hint { display: none; }
.recommend-empty { display: flex; align-items: center; gap: 20px; background: #f0f2eb; border: 1px solid #e0e5d7; border-radius: 16px; padding: 26px; margin-top: 20px; }
.recommend-empty .empty-icon { width: 42px; height: 42px; color: #748763; }
.recommend-empty > div { flex: 1; }
.recommend-empty h3 { font-size: 17px; }
.recommend-empty p { color: var(--career-muted); font-size: 13px; line-height: 1.8; margin-top: 6px; }
.outline-link { display: inline-flex; gap: 10px; align-items: center; border: 1px solid #b8c2ac; border-radius: 8px; background: #fff; padding: 10px 14px; font-size: 13px; flex-shrink: 0; }
.analysis-panel { border: 1px solid var(--career-border); border-radius: 12px; margin-top: 18px; background: #fff; overflow: hidden; }
.analysis-toggle { display: flex; align-items: center; justify-content: space-between; gap: 16px; width: 100%; padding: 16px 20px; min-height: 56px; font-size: 13px; text-align: left; }
.analysis-toggle > span { display: inline-flex; align-items: center; gap: 9px; }
.analysis-toggle > span:last-child { color: var(--career-muted); font-size: 12px; }
.analysis-toggle .rotated { transform: rotate(180deg); }
.analysis-content { padding: 24px; border-top: 1px solid var(--career-border); }
.analysis-content p, .analysis-content dd, .analysis-content li { color: var(--career-muted); font-size: 13px; line-height: 1.9; white-space: pre-line; overflow-wrap: anywhere; }
.analysis-content h3, .analysis-content dt { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.analysis-overview { margin-bottom: 22px; }
.analysis-career { border-top: 1px solid var(--career-border); }
.analysis-career summary { display: flex; align-items: center; gap: 12px; min-height: 56px; padding-block: 12px; cursor: pointer; list-style: none; }
.analysis-career summary strong { flex: 1; font-size: 14px; font-weight: 500; }
.analysis-career summary > span { color: #526349; font-size: 12px; }
.analysis-career[open] summary > svg { transform: rotate(180deg); }
.analysis-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px; padding-bottom: 24px; }
.analysis-fields ul, .action-plan ul { padding-left: 18px; list-style: disc; }
.skill-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.skill-tags span { display: inline-block; padding: 3px 8px; background: #f2f4ed; border-radius: 5px; font-size: 12px; }
.action-plan { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; border-top: 1px solid var(--career-border); padding-top: 22px; }
.analysis-unavailable { color: var(--career-muted); font-size: 11px; margin-top: 14px; }
.catalog-section { margin-top: 40px; scroll-margin-top: 116px; }
.catalog-heading { display: flex; justify-content: space-between; align-items: center; gap: 24px; margin-bottom: 22px; }
.catalog-title { display: flex; align-items: center; gap: 12px; }
.catalog-title img { width: 36px; height: 36px; object-fit: cover; border-radius: 8px; }
.catalog-title p { color: var(--career-muted); font-size: 12px; margin-top: 4px; }
.search-box { display: flex; align-items: center; gap: 10px; width: 340px; max-width: 100%; border: 1px solid #d5dacd; border-radius: 9px; padding: 0 12px; min-height: 46px; background: #fff; }
.search-box svg { color: #7a8471; width: 18px; height: 18px; }
.search-box:focus-within { outline: 2px solid #687c53; outline-offset: 2px; }
.search-box input { width: 100%; min-width: 0; min-height: 44px; font-size: 13px; border: 0; outline: none; background: transparent; }
.search-box input:focus-visible { outline: none; }
.search-box input::placeholder { color: #737a6b; opacity: 1; }
.category-filters { display: flex; flex-wrap: wrap; gap: 8px; }
.category-filters button { padding: 9px 13px; min-height: 40px; border: 1px solid var(--career-border); border-radius: 8px; color: var(--career-muted); background: #fff; font-size: 12px; white-space: nowrap; }
.category-filters button[aria-pressed='true'] { border-color: #526349; color: #fff; background: #526349; }
.filter-status { font-size: 12px; color: var(--career-muted); margin-block: 16px 12px; }
.category-list { border: 1px solid var(--career-border); border-radius: 16px; overflow: hidden; background: #fff; }
.career-category + .career-category { border-top: 1px solid var(--career-border); }
.career-category summary { display: flex; align-items: center; gap: 12px; padding: 18px 22px; min-height: 62px; cursor: pointer; list-style: none; }
.career-category summary:hover { background: #fafbf7; }
.direction-page summary::-webkit-details-marker { display: none; }
.category-marker { width: 7px; height: 7px; background: #b3bda7; border-radius: 50%; }
.career-category summary h3 { font-size: 14px; font-weight: 500; flex: 1; }
.category-count { color: var(--career-muted); font-size: 12px; }
.category-selected { color: #526349; background: #edf2e4; padding: 2px 7px; border-radius: 4px; font-size: 11px; }
.career-category[open] summary > svg { transform: rotate(180deg); }
.role-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; padding: 0 22px 22px; }
.career-choice { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 46px; padding: 10px 12px; border: 1px solid #e2e6da; border-radius: 8px; background: #fcfcfa; text-align: left; font-size: 13px; overflow-wrap: anywhere; scroll-margin-block: 130px 110px; }
.career-choice:hover { border-color: #b4c1a5; background: #f4f7ee; }
.career-choice.selected { background: #edf3e3; border-color: #82956d; color: #3d5430; }
.career-choice svg { width: 17px; height: 17px; }
.choice-circle { width: 15px; height: 15px; border: 1px solid #c7cebd; border-radius: 50%; flex-shrink: 0; }
.search-empty { padding: 40px 24px; border: 1px dashed #d4dacb; border-radius: 16px; text-align: center; }
.search-empty h3 { font-size: 17px; }
.search-empty p { color: var(--career-muted); font-size: 13px; margin-block: 8px; }
.profile-reminder { font-size: 12px; color: var(--career-muted); margin-top: 22px; }
.profile-reminder a { color: #526349; text-decoration: underline; text-underline-offset: 3px; }
.read-notice, .page-error { border: 1px solid #decdb5; border-radius: 10px; padding: 14px 18px; background: #faf6ee; color: #785931; font-size: 13px; margin-block: 18px; scroll-margin-block: 120px 120px; }
.selection-bar { position: sticky; bottom: 16px; z-index: 30; display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-top: 24px; padding: 14px 20px; border: 1px solid #cfd8c3; border-radius: 12px; background: #fff; box-shadow: 0 4px 24px #2738200a; }
.selection-summary { min-width: 0; flex: 1; }
.selection-caption { font-size: 11px; color: var(--career-muted); }
.selection-summary > div { display: flex; gap: 8px; align-items: center; min-height: 26px; }
.selection-summary strong { font-size: 15px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.clear-selection { display: grid; place-items: center; width: 28px; height: 28px; flex-shrink: 0; border-radius: 50%; color: var(--career-muted); }
.clear-selection:hover { background: #f0f3e9; }
.clear-selection svg { width: 17px; height: 17px; }
.generate-button { display: inline-flex; align-items: center; justify-content: center; gap: 12px; min-height: 46px; border-radius: 8px; background: #333f32; color: #fff; padding: 11px 22px; font-size: 14px; flex-shrink: 0; }
.generate-button:hover:enabled { background: #202b20; }
.generate-button:disabled { background: #e7eadf; color: #727a69; cursor: not-allowed; }
.direction-page button:disabled { cursor: not-allowed; }
@media (max-width: 1000px) { .role-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } .catalog-heading { flex-wrap: wrap; } .recommend-card { padding: 20px; } }
@media (max-width: 760px) {
  .direction-main { width: calc(100% - 32px); padding-block: 28px 32px; }
  .page-heading { display: block; }
  .page-lead { font-size: 13px; margin-top: 10px; }
  .edit-intro { font-size: 12px; margin-top: 12px; min-height: 36px; }
  .edit-intro svg { width: 16px; height: 16px; }
  .journey { gap: 10px; justify-content: space-between; padding-block: 20px; margin-bottom: 24px; font-size: 10px; }
  .journey li, .journey a { gap: 5px; }
  .journey li > span, .journey a > span { width: 21px; height: 21px; font-size: 9px; }
  .section-heading h2, .catalog-title h2 { font-size: 20px; }
  .section-heading .eyebrow { display: none; }
  .section-description { margin-top: 8px; font-size: 12px; }
  .recommend-grid { display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory; padding: 2px 2px 10px; align-items: flex-start; }
  .recommend-card { flex: 0 0 calc(100% - 24px); scroll-snap-align: start; padding: 18px; }
  .recommend-top { margin-bottom: 10px; }
  .recommend-icon { width: 28px; height: 28px; }
  .recommend-card h3 { font-size: 17px; }
  .recommend-reason { font-size: 12px; margin-block: 8px 10px; }
  .recommend-select { min-height: 42px; padding-top: 10px; font-size: 12px; }
  .match-score strong { font-size: 23px; }
  .mobile-scroll-hint { display: block; color: var(--career-muted); font-size: 10px; margin-top: 1px; }
  .recommend-empty { padding: 20px; gap: 14px; flex-wrap: wrap; margin-top: 14px; }
  .recommend-empty .empty-icon { width: 32px; height: 32px; }
  .recommend-empty > div { flex-basis: calc(100% - 48px); }
  .recommend-empty h3 { font-size: 16px; }
  .recommend-empty p { font-size: 12px; }
  .outline-link { margin-left: 46px; font-size: 12px; }
  .analysis-toggle { padding: 14px 16px; }
  .analysis-content { padding: 18px; }
  .analysis-fields, .action-plan { grid-template-columns: minmax(0, 1fr); gap: 18px; }
  .catalog-section { margin-top: 30px; }
  .catalog-heading { gap: 18px; margin-bottom: 16px; }
  .catalog-title img { width: 30px; height: 30px; }
  .catalog-title p { font-size: 11px; }
  .search-box { width: 100%; }
  .search-box input { font-size: 16px; }
  .category-filters { flex-wrap: nowrap; overflow-x: auto; padding-block: 3px; }
  .category-filters button { padding-inline: 12px; min-height: 40px; }
  .filter-status { font-size: 11px; }
  .career-category summary { padding: 16px; gap: 9px; min-height: 58px; }
  .career-category summary h3 { font-size: 13px; }
  .role-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); padding: 0 14px 16px; gap: 8px; }
  .career-choice { font-size: 12px; padding: 10px; gap: 8px; }
  .selection-bar { bottom: 0; margin-top: 18px; gap: 10px; padding: 11px 12px calc(11px + env(safe-area-inset-bottom)); border-radius: 12px 12px 0 0; }
  .selection-caption { font-size: 10px; }
  .selection-summary strong { font-size: 13px; }
  .generate-button { font-size: 12px; gap: 8px; padding-inline: 12px; }
  .generate-button svg { width: 16px; height: 16px; }
}
</style>
