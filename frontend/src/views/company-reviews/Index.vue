<template>
  <div class="hiring-page">
    <main class="career-container hiring-main">
      <header class="hiring-heading">
        <div><p class="eyebrow">企业与职位</p><h1>发现下一站机会</h1><p class="page-lead">浏览职位、参考企业榜单与前辈经验，为下一步选择多一份了解。</p></div>
        <router-link to="/resume" class="outline-button"><UiIcon name="briefcase" />简历优化<UiIcon name="arrow" /></router-link>
      </header>
      <div class="hiring-tabs" role="tablist" aria-label="企业招聘栏目">
        <button v-for="(tab, index) in tabs" :id="`hiring-tab-${tab.id}`" :key="tab.id" type="button" role="tab" :aria-selected="query.tab === tab.id" :tabindex="query.tab === tab.id ? 0 : -1" aria-controls="hiring-panel" @click="changeTab(tab.id)" @keydown="onTabKey($event, index)">{{ tab.label }}</button>
      </div>
      <div class="hiring-layout" :class="{ 'with-sidebar': query.tab === 'jobs' }">
        <section id="hiring-panel" role="tabpanel" :aria-labelledby="`hiring-tab-${query.tab}`" class="hiring-panel">
          <div v-if="query.tab !== 'safety'" class="list-toolbar"><div><h2>{{ titles[query.tab] }}</h2><p>{{ descriptions[query.tab] }}</p></div><router-link v-if="query.tab === 'advice'" :to="adviceFormLink" class="primary-button"><UiIcon name="message" />分享我的经验</router-link></div>
          <form v-if="query.tab !== 'safety'" class="search-toolbar" role="search" @submit.prevent="submitSearch">
            <div class="search-field"><UiIcon name="search" /><label class="sr-only" for="hiring-search">{{ query.tab === 'advice' ? '搜索建议中的公司或职位' : '搜索职位、公司或地区' }}</label><input id="hiring-search" ref="searchInput" v-model="searchDraft" type="search" maxlength="200" :placeholder="query.tab === 'advice' ? '搜索公司或职位' : '搜索职位、公司、地区或行业'" @input="scheduleSearch" /><button v-if="searchDraft" type="button" class="icon-button" aria-label="清除搜索" @click="clearSearch"><UiIcon name="close" /></button></div>
            <button class="outline-button search-submit" type="submit">搜索</button><label v-if="query.tab === 'advice'" class="sort-field"><span>排序</span><select :value="query.ordering" @change="updateQuery({ ordering: $event.target.value, page: 1 })"><option value="recent">最新提交</option><option value="rating">评分最高</option></select></label>
          </form>
          <section ref="resultsPanel" class="results-panel" tabindex="-1" :aria-busy="currentState?.loading || false" aria-label="栏目内容">
            <template v-if="query.tab === 'jobs' || query.tab === 'advice'">
              <div v-if="currentState.loading" class="loading-state" role="status"><span class="loading-dot"></span>正在加载{{ query.tab === 'jobs' ? '职位' : '建议' }}…</div>
              <div v-else-if="currentState.error" class="feedback error-state" role="alert"><UiIcon name="alert" /><div><h3>暂时未能加载</h3><p>{{ currentState.error }}</p><div class="feedback-actions"><button type="button" class="outline-button" @click="reloadCurrent"><UiIcon name="refresh" />重试</button><button v-if="query.page > 1" type="button" class="text-button" @click="changePage(1)">返回第一页</button></div></div></div>
              <template v-else>
                <p class="result-count" role="status">{{ query.search ? `“${query.search}”的搜索结果` : query.tab === 'jobs' ? '全部职位' : '已分享的经验' }} · 共 {{ currentState.count }} 条</p>
                <div v-if="!currentState.items.length" class="feedback empty-state"><UiIcon :name="query.tab === 'jobs' ? 'briefcase' : 'message'" /><h3>{{ query.search ? '没有找到匹配内容' : query.tab === 'jobs' ? '暂无职位' : '还没有学长学姐的分享' }}</h3><p>{{ query.search ? '尝试其他关键词，或清除搜索查看全部内容。' : '有新的内容后，会展示在这里。' }}</p><button v-if="query.search" type="button" class="outline-button" @click="clearSearch">清除搜索</button><router-link v-else-if="query.tab === 'advice'" :to="adviceFormLink" class="outline-button">分享我的经验</router-link></div>
                <div v-else-if="query.tab === 'jobs'" class="job-list">
                  <article v-for="job in jobs.items" :key="job.id" class="job-card">
                    <div class="job-top"><div><h3>{{ job.position_name || '岗位名称待补充' }}</h3><p class="company-name">{{ job.company_name || '企业名称待补充' }}</p></div><strong class="salary">{{ job.salary_range || '薪资待补充' }}</strong></div>
                    <div class="job-tags"><span v-if="job.address"><UiIcon name="location" />{{ job.address }}</span><span v-if="job.industry">{{ job.industry }}</span><span v-if="job.company_size">{{ job.company_size }}</span></div>
                    <p class="job-description">{{ plainText(job.position_details) || '岗位说明暂未提供，请查看原招聘页面。' }}</p>
                    <div class="job-bottom"><p :title="plainText(job.company_details)">{{ plainText(job.company_details) }}</p><a v-if="externalUrl(job.position_source_url)" :href="externalUrl(job.position_source_url)" target="_blank" rel="noopener noreferrer" class="primary-button" :aria-label="`前往 ${job.position_name || '该岗位'} 招聘页面申请（新窗口）`">立即申请<UiIcon name="external" /></a><span v-else class="unavailable-link">申请链接暂未提供</span></div>
                  </article>
                </div>
                <div v-else class="advice-list">
                  <article v-for="advice in adviceState.items" :key="advice.id" class="advice-card">
                    <div class="advice-top"><div><h3>{{ advice.company }}</h3><p>{{ advice.position }}</p></div><span class="rating"><UiIcon name="star" />{{ advice.rating }}<small>/ 5</small></span></div>
                    <p class="advice-byline"><span>{{ advice.senior_name }} · {{ advice.graduation_year }} 届</span><time :datetime="advice.created_at">{{ displayDate(advice.created_at) }}</time></p>
                    <div v-if="advice.current_company || advice.salary_info" class="job-tags"><span v-if="advice.current_company">现就职：{{ advice.current_company }}</span><span v-if="advice.salary_info">薪资参考：{{ advice.salary_info }}</span></div>
                    <details class="advice-details"><summary><span class="advice-excerpt">{{ advice.advice }}</span><span class="detail-toggle"><span class="when-closed">展开经验</span><span class="when-open">收起经验</span><UiIcon name="down" /></span></summary><p class="full-advice">{{ advice.advice }}</p></details>
                    <div v-if="advice.pros?.length || advice.cons?.length" class="advice-points"><div v-if="advice.pros?.length"><h4>值得关注</h4><ul><li v-for="(item, index) in advice.pros" :key="index">{{ item }}</li></ul></div><div v-if="advice.cons?.length"><h4>需要了解</h4><ul><li v-for="(item, index) in advice.cons" :key="index">{{ item }}</li></ul></div></div>
                  </article>
                </div>
                <PageControls :page="query.page" :page-size="query.pageSize" :total="currentState.count" :busy="currentState.loading" :label="query.tab === 'jobs' ? '职位分页' : '建议分页'" @page="changePage" @size="size => updateQuery({ pageSize: size, page: 1 })" />
              </template>
            </template>
            <template v-else-if="query.tab === 'red' || query.tab === 'black'">
              <p class="ranking-note"><UiIcon :name="query.tab === 'red' ? 'star' : 'shield'" />榜单按现有整理结果展示，作为了解岗位的参考。具体招聘信息请以原招聘页面为准。</p>
              <p class="result-count" role="status">{{ query.search ? '匹配条目' : '榜单条目' }} · 共 {{ rankedItems.length }} 条</p>
              <div v-if="!rankedItems.length" class="feedback empty-state"><h3>没有匹配的榜单条目</h3><button type="button" class="outline-button" @click="clearSearch">清除搜索</button></div>
              <template v-else>
                <div class="ranking-table"><table><caption class="sr-only">{{ titles[query.tab] }}岗位信息</caption><thead><tr><th scope="col">序号</th><th scope="col">岗位与公司</th><th scope="col">地区</th><th scope="col">薪资参考</th><th scope="col">{{ query.tab === 'red' ? '关注理由' : '需核实的情况' }}</th></tr></thead><tbody><tr v-for="item in pagedRankings" :key="item.rank"><td><span class="rank-number" :class="query.tab">{{ String(item.rank).padStart(2, '0') }}</span></td><td><h3>{{ item.position }}</h3><p>{{ item.company }}</p></td><td>{{ item.location }}</td><td class="rank-salary">{{ item.salary || '未提供' }}</td><td class="rank-reason">{{ item.reason }}</td></tr></tbody></table></div>
                <div class="ranking-cards"><article v-for="item in pagedRankings" :key="item.rank" class="ranking-card"><div class="rank-card-top"><span class="rank-number" :class="query.tab">{{ String(item.rank).padStart(2, '0') }}</span><div><h3>{{ item.position }}</h3><p>{{ item.company }}</p></div></div><div class="rank-card-meta"><span><UiIcon name="location" />{{ item.location }}</span><strong>{{ item.salary || '薪资未提供' }}</strong></div><p class="rank-card-reason">{{ item.reason }}</p></article></div>
                <PageControls :page="query.page" :page-size="query.pageSize" :total="rankedItems.length" label="榜单分页" @page="changePage" @size="size => updateQuery({ pageSize: size, page: 1 })" />
              </template>
            </template>
            <template v-else>
              <div class="safety-heading"><span class="section-icon"><UiIcon name="shield" /></span><div><h2>求职安全指南</h2><p>先核实，再决定。遇到异常承诺和收费，给自己留出确认的时间。</p></div></div>
              <div class="safety-topics"><details v-for="(topic, index) in safetyTopics" :key="topic.title" class="safety-topic"><summary><UiIcon :name="topic.icon" /><span><strong>{{ String(index + 1).padStart(2, '0') }} / {{ topic.title }}</strong><small>{{ topic.summary }}</small></span><UiIcon name="down" /></summary><ul><li v-for="point in topic.points" :key="point">{{ point }}</li></ul></details></div>
              <section class="safety-checklist"><h3>遇到疑问时，先做这三件事</h3><ol><li><strong>核实信息</strong><p>通过企业官网、学校就业部门或正规渠道交叉确认。</p></li><li><strong>保留材料</strong><p>保存招聘页面、沟通记录、合同和付款凭据。</p></li><li><strong>及时求助</strong><p>向学校就业部门、当地人社部门咨询；疑似被骗及时报警。</p></li></ol></section>
              <section class="safety-sources"><h3>查看官方提示</h3><a v-for="source in safetySources" :key="source.url" :href="source.url" target="_blank" rel="noopener noreferrer"><span>{{ source.title }}<small>{{ source.publisher }} · {{ source.date }}</small></span><UiIcon name="external" /></a></section>
            </template>
          </section>
        </section>
        <aside v-if="query.tab === 'jobs'" class="hiring-sidebar" aria-label="校园招聘与地区信息">
          <section class="sidebar-panel"><div class="sidebar-heading"><UiIcon name="school" /><h2>湖南高校双选会</h2></div><p class="sidebar-lead">从校园出发，了解学校的招聘安排。</p><p v-if="fairs.loading" role="status" class="sidebar-status">正在加载双选会…</p><div v-else-if="fairs.error" role="alert" class="sidebar-error"><p>{{ fairs.error }}</p><button type="button" class="text-button" @click="loadFairs">重新加载</button></div><p v-else-if="!fairs.items.length" class="sidebar-status">暂无双选会信息</p><ol v-else class="fair-list"><li v-for="fair in fairs.items" :key="fair.id"><div class="fair-school">{{ universityNames[fair.university] || fair.university || '高校' }}</div><a v-if="externalUrl(fair.university_url)" :href="externalUrl(fair.university_url)" target="_blank" rel="noopener noreferrer">{{ fair.name || '查看学校招聘信息' }}<UiIcon name="external" /></a><p v-else>{{ fair.name || '活动信息待补充' }}</p></li></ol><PageControls :page="fairPage" :page-size="6" :total="fairs.count" :busy="fairs.loading" :allow-size="false" label="双选会分页" @page="changeFairPage" /></section>
          <section class="sidebar-panel region-panel"><div class="sidebar-heading"><UiIcon name="location" /><h2>地区招聘资讯</h2></div><p>暂未开启城市定位。你可以在职位搜索中输入城市，查找感兴趣地区的机会。</p><button type="button" class="outline-button" @click="focusCitySearch">按城市查找<UiIcon name="arrow" /></button></section>
          <p class="sidebar-tip">选择机会时，可以一起考虑岗位内容、培养机制与自己的实际需要。</p>
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { computerCareerAPI, jobFairAPI, seniorAdviceAPI } from '@/api'
import UiIcon from '@/components/company-reviews/UiIcon.vue'
import PageControls from '@/components/company-reviews/PageControls.vue'
import { createPageLoader, displayDate, externalUrl, plainText, readBrowseQuery, tabs, text } from '@/features/company-reviews/browse.js'
import { redList, blackList } from '@/features/company-reviews/rankings.js'
import { safetyTopics, safetySources } from '@/features/company-reviews/safety.js'
import { universityNames } from '@/features/company-reviews/universities.js'
import './company-reviews.css'

const route = useRoute(), router = useRouter()
const query = computed(() => readBrowseQuery(route.query))
const searchDraft = ref(query.value.search), searchInput = ref(null), resultsPanel = ref(null)
const adviceFormLink = computed(() => ({ path: '/company-reviews/senior-advice/form', query: { from: route.fullPath } }))
const titles = { jobs: '职位列表', red: '红榜 · 值得关注', black: '黑榜 · 提前了解', advice: '来自前辈的经验' }
const descriptions = { jobs: '按现有招聘记录展示，点击申请查看完整岗位说明。', red: '结合现有榜单，比较你关注的企业与岗位。', black: '了解已有条目中的提示，进一步核实具体招聘情况。', advice: '了解不同岗位的工作体验，也欢迎分享你的经历。' }
const state = () => reactive({ items: [], count: 0, loading: false, error: '' })
const jobs = state(), adviceState = state(), fairs = state(), fairPage = ref(1)
const jobsLoader = createPageLoader(jobs, (params, config) => computerCareerAPI.getComputerCareers(params.page, params.page_size, { search: params.search }, config))
const adviceLoader = createPageLoader(adviceState, (params, config) => seniorAdviceAPI.list(params, config))
const fairsLoader = createPageLoader(fairs, (params, config) => jobFairAPI.getJobFairs(params.page, 6, config))
const currentState = computed(() => query.value.tab === 'jobs' ? jobs : query.value.tab === 'advice' ? adviceState : null)
const rankedItems = computed(() => (query.value.tab === 'red' ? redList : blackList).filter(item => Object.values(item).some(value => text(value).toLowerCase().includes(query.value.search.toLowerCase()))))
const pagedRankings = computed(() => rankedItems.value.slice((query.value.page - 1) * query.value.pageSize, query.value.page * query.value.pageSize))
let searchTimer, fairsLoaded = false, focusAfterLoad = false, reloadSequence = 0
function updateQuery(patch, replace = false) {
  const value = { ...query.value, ...patch }, next = { tab: value.tab }
  if (value.search) next.q = value.search
  if (value.page > 1) next.page = String(value.page)
  if (value.pageSize !== 10) next.size = String(value.pageSize)
  if (value.tab === 'advice' && value.ordering === 'rating') next.sort = 'rating'
  return router[replace ? 'replace' : 'push']({ path: '/company-reviews', query: next })
}
function changeTab(tab) { clearTimeout(searchTimer); focusAfterLoad = false; updateQuery({ tab, page: 1, search: '' }) }
function onTabKey(event, index) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length
  event.currentTarget.parentElement.querySelectorAll('button')[next].focus()
  changeTab(tabs[next].id)
}
function scheduleSearch() { clearTimeout(searchTimer); searchTimer = setTimeout(submitSearch, 350) }
function submitSearch() { clearTimeout(searchTimer); updateQuery({ search: searchDraft.value.trim().slice(0, 200), page: 1 }, true) }
function clearSearch() { searchDraft.value = ''; submitSearch() }
function changePage(page) { focusAfterLoad = true; updateQuery({ page }) }
async function reloadCurrent() {
  const sequence = ++reloadSequence
  const { tab, page, pageSize, search, ordering } = query.value
  if (tab === 'jobs') await jobsLoader.load({ page, page_size: pageSize, search })
  if (tab === 'advice') await adviceLoader.load({ page, page_size: pageSize, search, ordering })
  if (sequence !== reloadSequence) return
  if (focusAfterLoad) { focusAfterLoad = false; await nextTick(); resultsPanel.value?.focus({ preventScroll: true }); resultsPanel.value?.scrollIntoView({ block: 'start', behavior: 'instant' }) }
}
function loadFairs() { fairsLoaded = true; return fairsLoader.load({ page: fairPage.value }) }
function changeFairPage(page) { fairPage.value = page; loadFairs() }
function focusCitySearch() { searchInput.value?.focus(); searchInput.value?.scrollIntoView({ block: 'center' }) }
watch(() => route.fullPath, () => {
  clearTimeout(searchTimer); searchDraft.value = query.value.search
  jobsLoader.cancel(); adviceLoader.cancel()
  if (['red', 'black'].includes(query.value.tab) && query.value.page > Math.max(1, Math.ceil(rankedItems.value.length / query.value.pageSize))) { updateQuery({ page: 1 }, true); return }
  reloadCurrent()
  if (query.value.tab === 'jobs' && !fairsLoaded) loadFairs()
}, { immediate: true })
onBeforeUnmount(() => { reloadSequence++; clearTimeout(searchTimer); jobsLoader.cancel(); adviceLoader.cancel(); fairsLoader.cancel() })
</script>
