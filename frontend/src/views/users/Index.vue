<template>
  <div class="account-page">
    <main class="career-container account-main">
      <header class="account-heading"><div><p class="career-eyebrow">个人中心</p><h1>把每一次准备，留在这里</h1><p>整理个人资料、查看简历，回顾你的面试练习。</p></div><router-link to="/interview" class="account-button primary"><WorkspaceIcon name="message" />开始模拟面试<WorkspaceIcon name="arrow" /></router-link></header>
      <p v-if="message" class="account-notice" :class="messageType" :role="messageType === 'error' ? 'alert' : 'status'">{{ message }}</p>
      <div v-if="profileLoading" class="account-state" role="status">正在加载个人资料…</div>
      <div v-else-if="profileError" class="account-state error" role="alert"><WorkspaceIcon name="alert" /><p>{{ profileError }}</p><button class="account-button" @click="loadProfile">重新加载</button></div>
      <template v-else>
        <section class="identity-card" aria-label="个人资料">
          <button type="button" class="account-avatar" :disabled="uploadingAvatar" aria-label="上传个人头像" @click="triggerAvatarUpload"><WorkspaceAvatar :src="avatarPreview || user?.avatar" /><span><WorkspaceIcon name="edit" /></span></button>
          <input ref="avatarInput" type="file" accept="image/*" aria-label="选择个人头像文件" class="sr-only" tabindex="-1" @change="handleAvatarChange" />
          <div class="identity-body"><div class="identity-title"><h2>{{ user?.username || '我的账号' }}</h2><button type="button" class="account-button" @click="openEditModal"><WorkspaceIcon name="edit" />编辑资料</button></div><p class="identity-bio">{{ user?.profile || '写下你的专业方向与兴趣，让个人资料更完整。' }}</p><dl class="identity-facts"><div v-for="field in identityFields" :key="field.key"><dt>{{ field.label }}</dt><dd>{{ user?.[field.key] || '未填写' }}</dd></div></dl><p v-if="uploadingAvatar" class="account-help" role="status">正在上传头像…</p></div>
        </section>
        <div class="account-layout">
          <div class="account-primary">
            <section class="account-panel"><div class="account-panel-heading"><div><span class="account-kicker">关于我</span><h2>个人信息</h2></div><router-link to="/career-paths/employment/self-introduction" class="account-text-link">完善自我介绍<WorkspaceIcon name="arrow" /></router-link></div>
              <div class="introduction-content"><h3>自我介绍</h3><p v-if="selfIntroduction || user?.profile" class="introduction-text">{{ selfIntroduction || user.profile }}</p><div v-else class="account-empty compact"><WorkspaceIcon name="user" /><p>还没有自我介绍，先记录你的经历与职业目标。</p><router-link to="/career-paths/employment/self-introduction" class="account-text-link">填写自我介绍<WorkspaceIcon name="arrow" /></router-link></div></div>
              <div class="account-recommendations"><div class="subsection-heading"><h3>职业推荐</h3><router-link to="/career-evaluation" class="account-text-link">查看规划<WorkspaceIcon name="arrow" /></router-link></div><div v-if="recommendations.length" class="recommendation-grid"><article v-for="(rec,index) in recommendations" :key="rec.career"><span class="recommendation-index">{{ String(index + 1).padStart(2,'0') }}</span><h4>{{ rec.career }}</h4><p v-if="rec.matchScore !== null" class="recommendation-score">{{ rec.matchScore }}% 匹配</p><p>{{ rec.reason }}</p></article></div><p v-else class="account-help">当前浏览器中还没有测评推荐。完成自我介绍后，可前往规划报告查看。</p></div>
            </section>
            <section class="account-panel" aria-labelledby="account-reviews-title"><div class="account-panel-heading"><div><span class="account-kicker">练习与成长</span><h2 id="account-reviews-title">模拟面试复盘</h2></div><span v-if="!loadingReviews && !reviewsError" class="account-count">{{ interviewReviews.length }} 次记录</span></div>
              <p v-if="loadingReviews" class="account-state" role="status">正在读取面试复盘…</p><div v-else-if="reviewsError" class="account-state error" role="alert"><WorkspaceIcon name="alert" /><p>{{ reviewsError }}</p><button type="button" class="account-button" @click="loadInterviewReviews">重新加载</button></div>
              <template v-else-if="interviewReviews.length"><div class="review-list"><button v-for="review in pagedReviews" :key="review.id || review.session_id" type="button" class="review-item" @click="viewReviewDetail(review.session_id)"><span class="review-symbol"><WorkspaceIcon name="message" /></span><span class="review-summary"><span class="review-meta"><time :datetime="review.created_at">{{ displayDate(review.created_at) }}</time><span>{{ review.pair_count }} 条记录</span></span><span class="review-excerpt">{{ review.latest_content || '查看本次面试的复盘详情' }}</span><span class="review-open">查看复盘</span></span><WorkspaceIcon name="arrow" /></button></div><nav v-if="reviewPages > 1" class="account-pagination" aria-label="复盘记录分页"><span>第 {{ reviewPage }} / {{ reviewPages }} 页</span><div><button type="button" class="account-button" :disabled="reviewPage === 1" @click="reviewPage--">上一页</button><button type="button" class="account-button" :disabled="reviewPage >= reviewPages" @click="reviewPage++">下一页</button></div></nav></template>
              <div v-else class="account-empty"><WorkspaceIcon name="message" /><h3>第一场练习，从这里开始</h3><p>完成模拟面试后，可在这里回顾复盘内容。</p><button type="button" class="account-button" @click="goToInterview">开始模拟面试<WorkspaceIcon name="arrow" /></button></div>
            </section>
          </div>
          <aside class="account-sidebar" aria-label="简历与快捷入口"><section class="account-panel resume-summary"><div class="account-panel-heading"><div><span class="account-kicker">求职准备</span><h2>我的简历</h2></div><WorkspaceIcon name="file" /></div><p v-if="resumeLoading" class="account-help" role="status">正在加载简历…</p><div v-else-if="resumeError" class="account-state error" role="alert"><p>{{ resumeError }}</p><button type="button" class="account-button" @click="loadResume">重新加载</button></div><template v-else-if="resume"><div class="resume-identity"><h3>{{ resume.name || '我的简历' }}</h3><p>{{ resume.target_position || '意向岗位待补充' }}</p></div><div v-if="resume.education?.length" class="resume-summary-section"><h4><WorkspaceIcon name="school" />教育背景</h4><div v-for="(edu,index) in resume.education.slice(0,2)" :key="index"><strong>{{ edu.school }}</strong><p>{{ [edu.major,edu.degree].filter(Boolean).join(' · ') }}</p></div></div><div v-if="resume.experience?.length" class="resume-summary-section"><h4><WorkspaceIcon name="briefcase" />实习经历</h4><div v-for="(exp,index) in resume.experience.slice(0,2)" :key="index"><strong>{{ exp.company }}</strong><p>{{ exp.position }}</p></div></div><div v-if="resume.skills" class="resume-summary-section"><h4><WorkspaceIcon name="code" />专业技能</h4><p class="skill-excerpt">{{ resume.skills }}</p></div><button type="button" class="account-button full" @click="goToResume"><WorkspaceIcon name="edit" />编辑简历<WorkspaceIcon name="arrow" /></button></template><div v-else class="account-empty compact"><WorkspaceIcon name="file" /><h3>整理你的第一份简历</h3><p>把教育、项目和实习经历汇集在一起。</p><button type="button" class="account-button full" @click="goToResume">创建简历<WorkspaceIcon name="arrow" /></button></div></section><section class="account-next-step"><WorkspaceIcon name="compass" /><h3>准备好，向下一步出发</h3><p>完善简历后，继续了解企业与职位，找到值得深入了解的机会。</p><router-link to="/company-reviews" class="account-text-link">浏览企业与职位<WorkspaceIcon name="arrow" /></router-link></section></aside>
        </div>
      </template>
    </main>
    <WorkspaceDialog :open="showEditModal" :busy="savingProfile" title="编辑资料" title-id="profile-edit-title" caption="让个人资料更完整" @close="showEditModal = false"><form id="profile-edit-form" class="profile-edit-form" @submit.prevent="saveProfile"><div class="edit-avatar-row"><button type="button" class="account-avatar" :disabled="uploadingAvatar" aria-label="更换个人头像" @click="triggerAvatarUpload"><WorkspaceAvatar :src="avatarPreview || user?.avatar" /><span><WorkspaceIcon name="edit" /></span></button><div><strong>个人头像</strong><p>{{ uploadingAvatar ? '正在上传…' : '点击头像可选择图片，头像会单独保存。' }}</p></div></div><div class="profile-field"><label for="profile-username">用户名</label><input id="profile-username" v-model="editForm.username" autocomplete="username" required /></div><div class="profile-field"><label for="profile-bio">简介</label><textarea id="profile-bio" v-model="editForm.profile" rows="3" placeholder="介绍你的方向、兴趣或当前目标"></textarea></div><div class="profile-field-grid"><div v-for="field in identityFields" :key="field.key" class="profile-field" :class="{wide:field.key === 'address'}"><label :for="`profile-${field.key}`">{{ field.label }}</label><input :id="`profile-${field.key}`" v-model="editForm[field.key]" :type="field.key === 'email' ? 'email' : 'text'" /></div></div><p v-if="profileSaveError" role="alert" class="account-notice error">{{ profileSaveError }}</p></form><template #footer><button type="button" class="account-button" :disabled="savingProfile" @click="showEditModal = false">取消</button><button type="submit" form="profile-edit-form" class="account-button primary" :disabled="savingProfile">{{ savingProfile ? '正在保存…' : '保存资料' }}<WorkspaceIcon name="check" /></button></template></WorkspaceDialog>
    <WorkspaceDialog :open="showReviewModal" title="面试复盘详情" title-id="account-review-title" caption="回顾这次练习" @close="closeReviewModal"><p v-if="loadingReviewDetail" class="account-state" role="status">正在加载复盘…</p><div v-else-if="reviewDetailError" class="account-state error" role="alert"><p>{{ reviewDetailError }}</p><button type="button" class="account-button" @click="viewReviewDetail(reviewSession)">重新加载</button></div><div v-else-if="currentReview" class="account-review-detail"><dl class="review-metrics"><div><dt>面试风格</dt><dd>{{ styleNames[currentReview.interview_style] || currentReview.interview_style || '未提供' }}</dd></div><div><dt>综合评分</dt><dd>{{ currentReview.overall_score == null ? '未提供' : `${currentReview.overall_score} 分` }}</dd></div><div><dt>面试时长</dt><dd>{{ currentReview.interview_duration == null ? '未提供' : `${currentReview.interview_duration} 分钟` }}</dd></div><div><dt>问答数量</dt><dd>{{ currentReview.question_count ?? '—' }} 问 / {{ currentReview.answer_count ?? '—' }} 答</dd></div></dl><section><h3>复盘内容</h3><p class="review-full-content">{{ currentReview.review_content }}</p></section><section v-for="field in reviewFields.filter(field => currentReview[field.key])" :key="field.key" class="review-detail-section"><h3>{{ field.label }}</h3><ul><li v-for="(line,index) in lines(currentReview[field.key])" :key="index">{{ line }}</li></ul></section></div><template #footer><button type="button" class="account-button primary" @click="closeReviewModal">完成阅读<WorkspaceIcon name="check" /></button></template></WorkspaceDialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { userAPI, resumeAPI, interviewAPI } from '@/api'
import WorkspaceIcon from '@/components/WorkspaceIcon.vue'
import WorkspaceAvatar from '@/components/WorkspaceAvatar.vue'
import WorkspaceDialog from '@/components/WorkspaceDialog.vue'
import { normalizeRecommendations } from '@/features/career-paths/evaluation.js'
import { normalizeIntroduction } from '@/features/career-paths/self-introduction.js'
const router = useRouter()
const user = ref(null), avatarInput = ref(null), avatarPreview = ref(null), uploadingAvatar = ref(false)
const profileLoading = ref(true), profileError = ref(''), profileSaveError = ref(''), savingProfile = ref(false)
const showEditModal = ref(false), editForm = ref({}), message = ref(''), messageType = ref('')
const recommendations = ref([]), selfIntroduction = ref(''), resume = ref(null), resumeLoading = ref(false), resumeError = ref('')
const interviewReviews = ref([]), loadingReviews = ref(false), reviewsError = ref(''), reviewPage = ref(1)
const showReviewModal = ref(false), currentReview = ref(null), loadingReviewDetail = ref(false), reviewDetailError = ref(''), reviewSession = ref('')
const identityFields = [{key:'school',label:'学校'},{key:'major',label:'专业'},{key:'education',label:'学历'},{key:'email',label:'邮箱'},{key:'address',label:'地址'}]
const styleNames = {gentle:'温和面',technical:'技术面',pressure:'压力面',behavioral:'行为面'}
const reviewFields = [{key:'strengths',label:'优点'},{key:'weaknesses',label:'待改进'},{key:'suggestions',label:'改进建议'}]
const pagedReviews = computed(() => interviewReviews.value.slice((reviewPage.value-1)*6,reviewPage.value*6))
const reviewPages = computed(() => Math.max(1,Math.ceil(interviewReviews.value.length/6)))
let messageTimer, detailSequence = 0
const lines = value => Array.isArray(value) ? value : String(value || '').split('\n').filter(line => line.trim())
function displayDate(value) { const date = new Date(value); return !value || Number.isNaN(date.getTime()) ? '日期未提供' : new Intl.DateTimeFormat('zh-CN',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(date) }
function requestError(error, action) { const status = error?.response?.status; if (status === 401) return '登录已过期，请重新登录。'; if (status === 403) return '当前账号没有访问权限。'; if (!status) return `${action}失败，请检查网络后重试。`; return `${action}失败（HTTP ${status}），请稍后重试。` }
function showMessage(text,type='info') { clearTimeout(messageTimer); message.value=text; messageType.value=type; messageTimer=setTimeout(()=>{message.value=''},5000) }
async function loadProfile() {
  profileLoading.value=true; profileError.value=''
  try { user.value=await userAPI.getProfile(); loadRecommendations(); loadSelfIntroduction(); loadResume(); loadInterviewReviews() }
  catch(error) { profileError.value=requestError(error,'读取个人资料') }
  finally { profileLoading.value=false }
}
async function loadResume() {
  resumeLoading.value=true; resumeError.value=''
  try { resume.value=await resumeAPI.get() }
  catch(error) { resume.value=null; if(error?.response?.status!==404)resumeError.value=requestError(error,'读取简历') }
  finally { resumeLoading.value=false }
}
function loadRecommendations() {
  try { const existing=localStorage.getItem('careerRecommendations'); recommendations.value=normalizeRecommendations(existing ? JSON.parse(existing) : JSON.parse(localStorage.getItem('aiResponse') || '{}').recommendations) }
  catch { recommendations.value=[] }
}
function loadSelfIntroduction() {
  try { const raw=localStorage.getItem('selfIntroduction'); if(!raw)return; const data=normalizeIntroduction(JSON.parse(raw)); const values=[['姓名',data.name],['学校',data.school],['性别',data.gender],['技能',data.skills.join('、')],['其他技能',data.otherSkills],['条件自述',data.selfDescription],['职业期望',data.goal]]; selfIntroduction.value=values.filter(([,value])=>typeof value==='string'&&value.trim()).map(([label,value])=>`${label}：${value}`).join('\n') }
  catch { selfIntroduction.value='' }
}
async function loadInterviewReviews() {
  loadingReviews.value=true; reviewsError.value=''
  try { const response=await interviewAPI.listReviews(); if(!response.success||!Array.isArray(response.data))throw new Error('Invalid response'); interviewReviews.value=response.data; reviewPage.value=1 }
  catch(error) { reviewsError.value=requestError(error,'读取面试复盘') }
  finally { loadingReviews.value=false }
}
function openEditModal() { editForm.value={username:user.value?.username||'',profile:user.value?.profile||'',...Object.fromEntries(identityFields.map(field=>[field.key,user.value?.[field.key]||'']))}; profileSaveError.value=''; showEditModal.value=true }
function triggerAvatarUpload() { if(!uploadingAvatar.value)avatarInput.value?.click() }
async function handleAvatarChange(event) {
  const file=event.target.files[0]; if(!file)return
  uploadingAvatar.value=true
  const reader=new FileReader(); reader.onload=e=>{if(uploadingAvatar.value)avatarPreview.value=e.target.result}; reader.readAsDataURL(file)
  try { const data=new FormData(); data.append('avatar',file); const response=await userAPI.uploadAvatar(data); user.value=response; try {localStorage.setItem('user',JSON.stringify(response))}catch{}; showMessage('头像上传成功','success') }
  catch(error) {showMessage(requestError(error,'上传头像'),'error')}
  finally {uploadingAvatar.value=false; avatarPreview.value=null; event.target.value=''}
}
async function saveProfile() {
  if(savingProfile.value)return
  savingProfile.value=true; profileSaveError.value=''
  try { const response=await userAPI.updateProfile(editForm.value); user.value=response; try{localStorage.setItem('user',JSON.stringify(response))}catch{}; showEditModal.value=false; showMessage('个人资料更新成功','success') }
  catch(error) {const fields=error?.response?.data; const details=fields&&typeof fields==='object'?Object.values(fields).flat().filter(value=>typeof value==='string').join('；'):''; profileSaveError.value=error?.response?.status===400&&details?details:requestError(error,'保存资料')}
  finally {savingProfile.value=false}
}
function goToResume(){router.push('/resume')}
function goToInterview(){router.push('/interview')}
async function viewReviewDetail(sessionId) {
  const sequence=++detailSequence; reviewSession.value=sessionId; loadingReviewDetail.value=true; reviewDetailError.value=''; currentReview.value=null; showReviewModal.value=true
  try {const response=await interviewAPI.getReview(sessionId); if(sequence!==detailSequence)return; if(!response.success||!response.data)throw new Error('Invalid response'); currentReview.value=response.data}
  catch(error){if(sequence===detailSequence)reviewDetailError.value=requestError(error,'读取复盘详情')}
  finally{if(sequence===detailSequence)loadingReviewDetail.value=false}
}
function closeReviewModal(){detailSequence++; showReviewModal.value=false; currentReview.value=null}
onMounted(loadProfile)
onBeforeUnmount(()=>{clearTimeout(messageTimer);detailSequence++})
</script>

<style scoped>
.account-page { background: var(--career-bg); color: var(--career-text); }
.account-main { padding-block: 44px 64px; }
.account-heading { display: flex; justify-content: space-between; align-items: center; gap: 24px; margin-bottom: 30px; }
.account-heading h1 { font-size: clamp(28px,3vw,38px); line-height: 1.4; margin: 9px 0 12px; }
.account-heading > div > p:last-child { color: var(--career-muted); font-size: 14px; }
.account-button { display: inline-flex; justify-content: center; align-items: center; gap: 8px; min-height: 44px; padding: 10px 16px; background: white; border: 1px solid #d6ddcd; color: #43543a; border-radius: 9px; font-size: 13px; line-height: 1.6; flex-shrink: 0; }
.account-button:hover { background: #f0f3e9; border-color: #aabb99; }
.account-button.primary { background: #333f32; border-color: #333f32; color: white; }
.account-button.primary:hover { background: #202b20; }
.account-button:disabled { opacity: .5; cursor: not-allowed; }
.account-button.full { width: 100%; margin-top: 24px; }
.account-text-link { display: inline-flex; align-items: center; gap: 7px; min-height: 40px; color: #526349; font-size: 12px; }
.account-text-link:hover { text-decoration: underline; text-underline-offset: 4px; }
.account-text-link svg { width: 16px; height: 16px; }
.account-notice { padding: 14px 18px; margin-bottom: 20px; border: 1px solid #d6e0ca; border-radius: 10px; background: #f0f4e9; color: #43543a; font-size: 13px; }
.account-notice.error { background: #fff8f1; color: #8d5737; border-color: #e6d2bd; }
.identity-card { display: flex; gap: 28px; padding: 30px; border: 1px solid var(--career-border); border-radius: 18px; background: white; margin-bottom: 28px; align-items: flex-start; }
.account-avatar { position: relative; width: 92px; height: 92px; flex-shrink: 0; border: 1px solid #dae2d0; border-radius: 22px; background: #eff3e8; }
.account-avatar img { width: 100%; height: 100%; object-fit: cover; border-radius: inherit; }
.account-avatar > span:not(.workspace-avatar-content) { position: absolute; display: grid; place-items: center; width: 28px; height: 28px; bottom: -5px; right: -5px; background: #526349; border: 3px solid white; color: white; border-radius: 9px; }
.account-avatar svg { width: 12px; height: 12px; }
.identity-body { flex: 1; min-width: 0; }
.identity-title { display: flex; gap: 20px; align-items: center; justify-content: space-between; }
.identity-title h2 { font-size: 25px; overflow-wrap: anywhere; }
.identity-bio { color: var(--career-muted); font-size: 13px; line-height: 1.85; margin-top: 8px; overflow-wrap: anywhere; white-space: pre-line; }
.identity-facts { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 18px 24px; border-top: 1px solid #edf0e7; padding-top: 18px; margin-top: 20px; }
.identity-facts dt { font-size: 11px; color: #818a76; margin-bottom: 4px; }
.identity-facts dd { font-size: 13px; color: #4d5845; overflow-wrap: anywhere; }
.account-layout { display: grid; grid-template-columns: minmax(0,1fr) 320px; align-items: start; gap: 28px; }
.account-primary { display: grid; gap: 24px; min-width: 0; }
.account-panel { background: white; border: 1px solid var(--career-border); padding: 28px; border-radius: 18px; min-width: 0; }
.account-panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 24px; }
.account-kicker { display: block; color: #818a76; font-size: 11px; margin-bottom: 6px; }
.account-panel h2 { font-size: 22px; }
.account-panel h3, .account-next-step h3 { font-size: 15px; }
.introduction-content > h3 { margin-bottom: 12px; }
.introduction-text { color: var(--career-muted); font-size: 13px; line-height: 1.9; white-space: pre-line; overflow-wrap: anywhere; }
.account-recommendations { border-top: 1px solid #e9ece3; margin-top: 24px; padding-top: 20px; }
.subsection-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.recommendation-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 12px; }
.recommendation-grid article { background: #f5f8ef; border: 1px solid #e4eadc; padding: 18px; border-radius: 12px; min-width: 0; }
.recommendation-index { font-size: 11px; color: #839574; }
.recommendation-grid h4 { font-size: 15px; margin-top: 8px; overflow-wrap: anywhere; }
.recommendation-grid p { color: var(--career-muted); font-size: 12px; margin-top: 10px; line-height: 1.85; overflow-wrap: anywhere; }
.recommendation-grid .recommendation-score { color: #526349; font-size: 11px; }
.account-help { color: var(--career-muted); font-size: 12px; line-height: 1.9; }
.account-count { color: #657657; background: #f0f3e9; border-radius: 7px; padding: 5px 10px; font-size: 12px; white-space: nowrap; }
.review-list { border-top: 1px solid #e9ece3; }
.review-item { display: flex; width: 100%; align-items: flex-start; gap: 14px; padding: 22px 0; border-bottom: 1px solid #e9ece3; text-align: left; }
.review-item:hover .review-open { text-decoration: underline; text-underline-offset: 4px; }
.review-symbol { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 11px; background: #f1f5e9; color: #667d51; flex-shrink: 0; }
.review-summary { flex: 1; min-width: 0; }
.review-meta { display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 11px; color: #7a8471; }
.review-excerpt { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; font-size: 13px; line-height: 1.85; margin-block: 8px; overflow-wrap: anywhere; }
.review-open { font-size: 11px; color: #667d51; }
.review-item > svg { margin-top: 12px; color: #738663; width: 16px; height: 16px; }
.account-pagination { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 20px; color: var(--career-muted); font-size: 12px; }
.account-pagination > div { display: flex; gap: 8px; }
.account-pagination .account-button { padding-inline: 12px; font-size: 12px; }
.account-sidebar { display: grid; gap: 20px; position: sticky; top: calc(var(--career-nav-height) + 24px); }
.account-sidebar .account-panel { padding: 24px; }
.account-sidebar .account-panel h2 { font-size: 20px; }
.resume-identity { background: #f3f6ed; border-radius: 12px; padding: 18px; }
.resume-identity p { margin-top: 5px; color: #66765a; font-size: 12px; }
.resume-summary-section { margin-top: 22px; }
.resume-summary-section h4 { display: flex; gap: 8px; align-items: center; font-size: 13px; margin-bottom: 12px; }
.resume-summary-section h4 svg { width: 16px; height: 16px; color: #758966; }
.resume-summary-section > div + div { margin-top: 12px; }
.resume-summary-section strong { font-size: 12px; font-weight: 500; }
.resume-summary-section p { color: var(--career-muted); font-size: 12px; line-height: 1.9; overflow-wrap: anywhere; }
.skill-excerpt { display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
.account-next-step { background: #eff3e6; padding: 24px; border: 1px solid #e0e6d7; border-radius: 16px; }
.account-next-step > svg { color: #6b8258; margin-bottom: 15px; width: 24px; height: 24px; }
.account-next-step p { font-size: 12px; line-height: 1.9; color: var(--career-muted); margin-block: 10px; }
.account-state { display: flex; flex-direction: column; gap: 14px; align-items: center; padding: 32px 18px; text-align: center; font-size: 13px; color: var(--career-muted); }
.account-state.error { border-radius: 12px; background: #fffaf4; color: #8d623e; }
.account-empty { padding: 26px 14px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.account-empty > svg { color: #82966f; width: 30px; height: 30px; }
.account-empty p { color: var(--career-muted); font-size: 13px; line-height: 1.8; }
.account-empty.compact { padding: 16px 0; align-items: flex-start; text-align: left; }
.account-empty .account-button { margin-top: 6px; }
.edit-avatar-row { display: flex; align-items: center; gap: 20px; margin-bottom: 26px; }
.edit-avatar-row .account-avatar { width: 68px; height: 68px; border-radius: 16px; }
.edit-avatar-row strong { font-size: 14px; font-weight: 500; }
.edit-avatar-row p { font-size: 12px; line-height: 1.8; color: var(--career-muted); margin-top: 6px; }
.profile-field { margin-bottom: 20px; min-width: 0; }
.profile-field label { display: block; font-size: 13px; color: #515e46; margin-bottom: 8px; }
.profile-field :is(input,textarea) { width: 100%; min-height: 46px; padding: 11px 13px; border: 1px solid #d4ddc9; border-radius: 8px; background: #fcfdf9; font-size: 14px; line-height: 1.8; }
.profile-field textarea { resize: vertical; }
.profile-field-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 0 20px; }
.profile-field.wide { grid-column: 1/-1; }
.review-metrics { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 12px; margin-bottom: 26px; }
.review-metrics > div { padding: 16px; background: #f1f5e9; border-radius: 10px; }
.review-metrics dt { font-size: 11px; color: #76846a; }
.review-metrics dd { margin-top: 5px; font-size: 15px; color: #43543a; }
.account-review-detail h3 { font-size: 16px; margin-bottom: 12px; }
.review-full-content { white-space: pre-wrap; line-height: 1.9; font-size: 14px; color: var(--career-muted); overflow-wrap: anywhere; }
.review-detail-section { margin-top: 24px; padding-top: 20px; border-top: 1px solid #e5eadd; }
.review-detail-section ul { list-style: disc; padding-left: 20px; color: var(--career-muted); font-size: 13px; line-height: 1.9; }
@media(max-width:1100px) { .account-layout { grid-template-columns: minmax(0,1fr) 280px; gap: 20px; } .recommendation-grid { grid-template-columns: 1fr; } .account-panel { padding: 24px; } }
@media(max-width:900px) { .account-layout { grid-template-columns: 1fr; } .account-sidebar { position: static; grid-template-columns: repeat(2,minmax(0,1fr)); align-items: start; } }
@media(max-width:760px) {
 .account-main { width: calc(100% - 32px); padding-block: 28px 40px; }
 .account-heading { flex-direction: column; align-items: flex-start; gap: 18px; }
 .account-heading > div > p:last-child { font-size: 13px; }
 .identity-card { padding: 22px 18px; gap: 16px; flex-wrap: wrap; }
 .account-avatar { width: 68px; height: 68px; border-radius: 17px; }
 .identity-body { flex-basis: 100%; }
 .identity-title { align-items: flex-start; }
 .identity-title h2 { font-size: 23px; }
 .identity-title .account-button { font-size: 12px; padding-inline: 12px; }
 .identity-facts { grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16px; }
 .identity-facts > div:last-child { grid-column: 1/-1; }
 .account-layout { gap: 22px; }
 .account-sidebar { grid-template-columns: 1fr; }
 .account-panel, .account-sidebar .account-panel { padding: 22px 18px; }
 .account-panel-heading { gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
 .account-panel h2 { font-size: 20px; }
 .review-item { gap: 10px; }
 .review-symbol { width: 32px; height: 32px; border-radius: 8px; }
 .review-symbol svg { width: 16px; height: 16px; }
 .review-item > svg { display: none; }
 .profile-field-grid { grid-template-columns: 1fr; }
 .profile-field :is(input,textarea) { font-size: 16px; }
 .account-pagination { gap: 8px; }
 .account-pagination .account-button { padding-inline: 10px; }
}
</style>
