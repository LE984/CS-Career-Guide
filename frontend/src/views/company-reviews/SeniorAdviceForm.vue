<template>
  <div class="hiring-page advice-form-page"><main class="career-container advice-form-main">
    <router-link :to="returnTo" class="back-link"><UiIcon class="back-arrow" name="arrow" />返回学长学姐建议</router-link>
    <header class="hiring-heading"><div><p class="eyebrow">分享经验</p><h1>把你的经历，留给下一位</h1><p class="page-lead">分享具体的工作体验与建议，帮助学弟学妹了解岗位。标有 * 的项目为必填。</p></div></header>
    <section v-if="success" ref="successPanel" tabindex="-1" class="feedback success-panel" role="status"><UiIcon name="check" /><h2>{{ successMessage }}</h2><p>感谢你的分享。审核通过后，这条建议会显示在列表中。</p><router-link :to="returnTo" class="primary-button">返回建议列表<UiIcon name="arrow" /></router-link></section>
    <form v-else ref="formElement" class="advice-form" @submit.prevent="handleSubmit">
      <fieldset :disabled="isSubmitting"><legend>基本信息</legend><div class="form-grid">
        <div v-for="field in basicFields" :key="field.key" class="form-field" :class="{ wide: field.key === 'current_company' }"><label :for="`advice-${field.key}`">{{ fieldLabels[field.key] }}<span v-if="field.required" aria-hidden="true"> *</span><small v-else>选填</small></label><input :id="`advice-${field.key}`" v-model="formData[field.key]" :name="field.key" type="text" :required="field.required" :maxlength="field.max" :pattern="field.key === 'graduation_year' ? '[0-9]{4}' : undefined" :inputmode="field.key === 'graduation_year' ? 'numeric' : 'text'" :placeholder="field.key === 'graduation_year' ? '例如：2025' : undefined" :aria-invalid="Boolean(errors[field.key])" :aria-describedby="errors[field.key] ? `error-${field.key}` : undefined" @input="clearFieldError(field.key)" /><p v-if="errors[field.key]" :id="`error-${field.key}`" class="field-error">{{ errors[field.key] }}</p></div>
      </div></fieldset>
      <fieldset :disabled="isSubmitting"><legend>你的工作体验</legend><div class="form-grid">
        <div class="form-field wide"><label for="advice-advice">详细建议 <span aria-hidden="true">*</span></label><textarea id="advice-advice" v-model="formData.advice" name="advice" required rows="6" placeholder="可以分享工作内容、团队培养，以及应聘前值得了解的情况。" :aria-invalid="Boolean(errors.advice)" :aria-describedby="errors.advice ? 'error-advice' : undefined" @input="clearFieldError('advice')"></textarea><p v-if="errors.advice" id="error-advice" class="field-error">{{ errors.advice }}</p></div>
        <div class="form-field"><label for="advice-salary_info">薪资信息 <small>选填</small></label><input id="advice-salary_info" v-model="formData.salary_info" name="salary_info" maxlength="100" placeholder="例如：12–18K · 13 薪" :aria-invalid="Boolean(errors.salary_info)" :aria-describedby="errors.salary_info ? 'error-salary_info' : undefined" @input="clearFieldError('salary_info')" /><p v-if="errors.salary_info" id="error-salary_info" class="field-error">{{ errors.salary_info }}</p></div>
        <div class="form-field"><label for="advice-rating">整体评分 <span aria-hidden="true">*</span></label><div class="rating-field"><input id="advice-rating" v-model.number="formData.rating" name="rating" type="number" required min="1" max="5" step="0.5" :aria-invalid="Boolean(errors.rating)" :aria-describedby="errors.rating ? 'rating-help error-rating' : 'rating-help'" @input="clearFieldError('rating')" /><span id="rating-help">1–5 分</span></div><p v-if="errors.rating" id="error-rating" class="field-error">{{ errors.rating }}</p></div>
        <div class="form-field"><label for="advice-pros">值得关注 <small>选填</small></label><input id="advice-pros" v-model="prosInput" name="pros" placeholder="例如：导师指导，技术交流" :aria-invalid="Boolean(errors.pros)" :aria-describedby="errors.pros ? 'points-help error-pros' : 'points-help'" @input="clearFieldError('pros')" /><p v-if="errors.pros" id="error-pros" class="field-error">{{ errors.pros }}</p></div>
        <div class="form-field"><label for="advice-cons">需要了解 <small>选填</small></label><input id="advice-cons" v-model="consInput" name="cons" placeholder="例如：项目节奏，轮班安排" :aria-invalid="Boolean(errors.cons)" :aria-describedby="errors.cons ? 'points-help error-cons' : 'points-help'" @input="clearFieldError('cons')" /><p v-if="errors.cons" id="error-cons" class="field-error">{{ errors.cons }}</p></div>
        <p id="points-help" class="form-help wide">多个要点可用中文或英文逗号分隔。</p>
      </div></fieldset>
      <div v-if="error" ref="errorPanel" class="feedback error-state" role="alert" tabindex="-1"><UiIcon name="alert" /><div><h3>提交未完成</h3><p>{{ error }}</p><ul v-if="Object.keys(errors).length"><li v-for="(message, field) in errors" :key="field"><a :href="`#advice-${field}`" @click.prevent="focusField(field)">{{ fieldLabels[field] }}：{{ message }}</a></li></ul></div></div>
      <div class="form-actions"><p>提交后需审核，姓名与毕业年份将随建议展示。</p><button type="submit" class="primary-button" :disabled="isSubmitting">{{ isSubmitting ? '正在提交…' : error ? '重新提交' : '提交建议' }}<UiIcon name="arrow" /></button></div>
    </form>
  </main></div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRoute } from 'vue-router'
import { seniorAdviceAPI } from '@/api'
import UiIcon from '@/components/company-reviews/UiIcon.vue'
import { errorMessage, fieldErrors, fieldLabels, splitPoints } from '@/features/company-reviews/browse.js'
import './company-reviews.css'
const route = useRoute()
const returnTo = computed(() => {
  const raw = typeof route.query.from === 'string' ? route.query.from : ''
  try { const target = new URL(raw, 'https://local.invalid'); return target.origin === 'https://local.invalid' && target.pathname === '/company-reviews' ? target.pathname + target.search : '/company-reviews?tab=advice' } catch { return '/company-reviews?tab=advice' }
})
const basicFields = [{ key: 'company', required: true, max: 255 }, { key: 'position', required: true, max: 255 }, { key: 'senior_name', required: true, max: 100 }, { key: 'graduation_year', required: true, max: 4 }, { key: 'current_company', required: false, max: 255 }]
const formData = ref({ company: '', position: '', senior_name: '', graduation_year: '', current_company: '', advice: '', salary_info: '', rating: 4 })
const prosInput = ref(''), consInput = ref(''), isSubmitting = ref(false), success = ref(false), successMessage = ref(''), error = ref(''), errors = ref({})
const formElement = ref(null), errorPanel = ref(null), successPanel = ref(null)
function clearFieldError(field) { delete errors.value[field] }
function focusField(field) { formElement.value?.querySelector(`[name="${field}"]`)?.focus() }
async function handleSubmit() {
  if (isSubmitting.value) return
  isSubmitting.value = true; error.value = ''; errors.value = {}
  try {
    const response = await seniorAdviceAPI.submit({ ...formData.value, pros: splitPoints(prosInput.value), cons: splitPoints(consInput.value) })
    if (!response?.success) throw { response: { status: 400, data: response } }
    successMessage.value = response.message || '建议提交成功，等待审核。'
    success.value = true
    await nextTick(); successPanel.value?.focus()
  } catch (failure) {
    errors.value = fieldErrors(failure); error.value = errorMessage(failure)
    await nextTick(); errorPanel.value?.focus()
  } finally { isSubmitting.value = false }
}
</script>

<style scoped>
.advice-form-main { max-width: 860px; padding-block: 32px 64px; }
.back-link { display: inline-flex; align-items: center; gap: 8px; color: var(--career-muted); font-size: 13px; min-height: 44px; margin-bottom: 24px; }
.back-arrow { transform: rotate(180deg); width: 16px; }
.advice-form { background: white; border: 1px solid var(--career-border); padding: 32px; border-radius: 16px; }
fieldset + fieldset { margin-top: 32px; border-top: 1px solid var(--career-border); padding-top: 26px; }
legend { font-size: 18px; font-weight: 600; margin-bottom: 22px; }
.form-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 22px; }
.wide { grid-column: 1 / -1; }
.form-field { min-width: 0; }
.form-field label { display: block; font-size: 13px; margin-bottom: 9px; }
.form-field label span { color: #9b653e; }
.form-field label small { color: var(--career-muted); font-size: 11px; margin-left: 6px; }
input, textarea { width: 100%; min-height: 46px; border: 1px solid #d6dccf; border-radius: 8px; background: #fff; padding: 11px 13px; font-size: 14px; line-height: 1.7; }
textarea { resize: vertical; }
[aria-invalid='true'] { border-color: #b57850; }
.field-error { color: #a15b36; font-size: 12px; margin-top: 7px; }
.rating-field { display: flex; align-items: center; gap: 12px; }
.rating-field input { width: 100px; }
.rating-field span, .form-help { font-size: 12px; color: var(--career-muted); }
.form-actions { display: flex; gap: 24px; justify-content: space-between; align-items: center; margin-top: 28px; border-top: 1px solid var(--career-border); padding-top: 22px; }
.form-actions p { font-size: 12px; color: var(--career-muted); line-height: 1.8; }
.error-state { margin-top: 24px; scroll-margin-block: 130px 50px; }
.error-state ul { list-style: disc; padding-left: 18px; font-size: 12px; margin-top: 8px; }
.error-state a { text-decoration: underline; text-underline-offset: 3px; }
.success-panel { text-align: center; scroll-margin-top: 130px; }
.success-panel > svg { width: 34px; height: 34px; margin: 0 auto 18px; color: #607b4b; }
.success-panel .primary-button { margin-top: 24px; }
@media(max-width:760px) { .advice-form-main { width: calc(100% - 32px); padding-block: 20px 40px; } .advice-form { padding: 22px 18px; } .form-grid { grid-template-columns: minmax(0,1fr); gap: 20px; } input, textarea { font-size: 16px; } .form-actions { align-items: stretch; flex-direction: column; gap: 16px; } }
</style>
