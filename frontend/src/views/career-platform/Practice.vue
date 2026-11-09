<template>
  <main class="career-container retrieval-demo">
    <header class="demo-header">
      <div><p class="demo-eyebrow">岗位题库练习 / 文本检索</p><h1>让每一道题，都有据可查。</h1>
      <p class="demo-intro">选择岗位和知识点，观察题目如何筛选、排序，再查看原始参考要点。</p></div>
      <span class="demo-badge">演示版 · 自编虚构题</span>
    </header>
    <nav class="demo-nav" aria-label="课程模块">
      <router-link to="/career-platform/catalog">岗位与题库</router-link>
      <span aria-current="page">文本检索演示</span>
      <router-link to="/interview">自由模拟面试 →</router-link>
    </nav>
    <aside class="demo-notice">当前仅演示题目检索。材料为专门编写的虚构示例，不是正式题库；不调用大模型、不保存回答或练习记录。</aside>
    <div class="demo-layout">
      <section class="demo-controls" aria-labelledby="filter-title">
        <h2 id="filter-title">检索条件</h2>
        <form @submit.prevent="search">
          <label>岗位方向<select v-model="form.role"><option>Java后端</option><option>Python后端</option></select></label>
          <label>知识点<input v-model="form.topic" list="demo-topics" placeholder="留空表示不限" maxlength="100" /></label>
          <datalist id="demo-topics"><option value="集合"/><option value="并发"/><option value="数据库"/></datalist>
          <label>难度<select v-model="form.difficulty"><option value="easy">基础 · easy</option><option value="medium">进阶 · medium</option><option value="hard">深入 · hard</option></select></label>
          <label>查询文本<input v-model="form.query" maxlength="500" placeholder="如 ArrayList、顺序、遍历" /></label>
          <label>返回数量<select v-model.number="form.top_k"><option :value="1">1 道</option><option :value="3">3 道</option><option :value="5">5 道</option></select></label>
          <button class="demo-primary" :disabled="busy">{{ busy ? '正在检索…' : '检索候选题' }}</button>
        </form>
        <div class="demo-scenarios"><h3>试一试</h3>
          <button type="button" :disabled="busy" @click="preset('basic')">集合基础题 <span>↗</span></button>
          <button type="button" :disabled="busy" @click="preset('rank')">ArrayList 排序 <span>↗</span></button>
          <button type="button" :disabled="busy" @click="preset('empty')">不存在的知识点 <span>↗</span></button>
        </div>
        <p class="demo-policy">候选材料中包含 pending 和 restricted 示例，用于观察许可过滤；这两类题不会出现在结果中。</p>
      </section>
      <section class="demo-results" aria-labelledby="results-title" :aria-busy="busy">
        <div class="demo-results-heading"><h2 id="results-title">候选题目</h2><span v-if="response">{{ response.count }} 道匹配</span></div>
        <p class="demo-status" :class="{ 'demo-error': error }" role="status">{{ status }}</p>
        <p v-if="submitted" class="demo-query">本次条件：{{ submitted.role }} / {{ submitted.topic || '全部知识点' }} / {{ submitted.difficulty }} · {{ submitted.query || '仅筛选' }}</p>
        <div v-if="response && !response.results.length" class="demo-empty"><h3>没有符合条件的题目</h3><p>试试其他知识点，或清空查询文本扩大范围。这里不会补入不相关题目。</p></div>
        <article v-for="(item, index) in response?.results || []" :key="item.question_id" class="demo-question">
          <div class="demo-question-meta"><span>候选 {{ index + 1 }} · 演示题</span><span>文本匹配 {{ item.score.toFixed(3) }}</span></div>
          <h3>{{ item.question }}</h3>
          <div class="demo-points"><h4>参考要点</h4><ul><li v-for="point in item.key_points" :key="point">{{ point }}</li></ul></div>
          <p class="demo-source">来源：{{ item.evidence.find(e => e.field_path === 'source')?.quote }}</p>
          <details><summary>查看来源证据</summary><p class="demo-id">题目 ID：{{ item.question_id }}</p><dl v-for="(evidence, i) in item.evidence" :key="i"><dt>{{ evidence.field_path }}</dt><dd>{{ evidence.quote }}</dd></dl></details>
        </article>
        <p class="demo-footnote">匹配值只用于比较文本相关程度，不是答案正确率或能力评分。同分按题目 ID 稳定排序。</p>
      </section>
    </div>
  </main>
</template>
<script setup>
import { ref, reactive, onUnmounted } from 'vue'
import client from '@/api'
const form = reactive({role:'Java后端',topic:'集合',difficulty:'easy',query:'集合',top_k:5})
const busy = ref(false), response = ref(null), submitted = ref(null), error = ref(false)
const status = ref('选择条件后开始检索，或点击左侧示例。')
const controller = new AbortController()
onUnmounted(() => controller.abort())
async function search() {
  if (busy.value) return
  busy.value = true; error.value = false; response.value = null
  const conditions = {...form}
  submitted.value = conditions
  status.value = '正在筛选并排序候选题目…'
  try {
    const result = await client.post('/career-platform/questions/demo-retrieve/', conditions, {signal:controller.signal})
    if (controller.signal.aborted) return
    if (result.is_demo !== true || !Array.isArray(result.results)) throw new Error('invalid demo response')
    response.value = result
    status.value = result.count ? `检索完成，返回 ${result.count} 道有来源的演示题。` : '检索完成，没有匹配结果。'
  } catch (failure) {
    if (controller.signal.aborted) return
    error.value = true
    status.value = failure.response?.status === 400 ? '条件无效，请检查输入后重试。' : '检索暂时不可用，请稍后重试。'
  } finally { if (!controller.signal.aborted) busy.value = false }
}
function preset(kind) {
  Object.assign(form, {role:'Java后端',topic:kind === 'empty' ? '不存在的知识点' : '集合',difficulty:'easy',query:kind === 'rank' ? 'ArrayList' : '集合',top_k:5})
  search()
}
</script>
<style scoped>
.retrieval-demo{padding-top:40px;padding-bottom:64px;color:#293b34;max-width:1200px}
.demo-header{display:flex;justify-content:space-between;gap:24px;align-items:flex-start}.demo-eyebrow{font-size:12px;letter-spacing:.12em;color:#60796b}.demo-header h1{font-family:'Noto Serif SC','Songti SC',SimSun,serif;font-size:34px;line-height:1.45;margin:12px 0}.demo-intro{font-size:14px;color:#68766e;line-height:1.9}.demo-badge{white-space:nowrap;border:1px solid #d5c5a0;background:#faf6ea;color:#80672f;border-radius:6px;padding:8px 12px;font-size:12px;margin-top:8px}.demo-nav{display:flex;flex-wrap:wrap;gap:24px;padding:24px 0 16px;border-bottom:1px solid #dce3dc;font-size:13px}.demo-nav span{color:#286347;font-weight:600}.demo-notice{background:#edf3ed;border-left:3px solid #527c60;padding:14px 18px;font-size:13px;line-height:1.9;margin:24px 0}.demo-layout{display:grid;grid-template-columns:280px minmax(0,1fr);gap:40px;align-items:start}.demo-controls{background:#fff;border:1px solid #dce3dc;border-radius:12px;padding:24px}.demo-controls h2,.demo-results h2{font-size:18px;font-weight:600;margin:0 0 20px}.demo-controls form{display:grid;gap:16px}.demo-controls label{display:grid;gap:8px;font-size:12px;color:#53675b}.demo-controls input,.demo-controls select{width:100%;min-width:0;border:1px solid #ccd8ce;border-radius:6px;background:#fff;padding:10px;font-size:14px;color:#293b34}.demo-primary{border-radius:6px;padding:12px;background:#365e45;color:#fff;font-size:14px;margin-top:4px}.demo-primary:disabled{opacity:.6}.demo-scenarios{border-top:1px solid #e3e9e3;margin-top:24px;padding-top:18px}.demo-scenarios h3{font-size:12px;color:#6c7b70;margin:0 0 8px}.demo-scenarios button{display:flex;justify-content:space-between;width:100%;text-align:left;padding:10px 0;font-size:13px;color:#365e45}.demo-policy{font-size:12px;line-height:1.9;color:#7a8178;margin-top:18px}.demo-results-heading{display:flex;justify-content:space-between;align-items:baseline}.demo-results-heading h2{margin-bottom:12px}.demo-results-heading span{font-size:12px;color:#60796b}.demo-status{font-size:13px;color:#4e6955;padding:12px 0;line-height:1.8}.demo-error{color:#a33d32}.demo-query{font-size:12px;color:#788179;margin-bottom:18px;overflow-wrap:anywhere}.demo-question{padding:24px 0;border-top:1px solid #dce3dc}.demo-question-meta{display:flex;justify-content:space-between;gap:12px;color:#718273;font-size:11px}.demo-question h3{font-size:20px;line-height:1.65;font-weight:600;margin:12px 0 20px}.demo-points{padding:16px 20px;background:#f2f5ef;border-radius:8px}.demo-points h4{font-size:12px;color:#667e6a;margin:0 0 10px}.demo-points ul{list-style:disc;padding-left:18px;font-size:14px;line-height:1.9}.demo-source{font-size:11px;color:#7a8178;line-height:1.8;margin:16px 0 12px}.demo-question summary{font-size:12px;cursor:pointer;color:#365e45}.demo-question details{overflow-wrap:anywhere}.demo-id{font:11px monospace;color:#788179;margin-top:16px}.demo-question dl{margin-top:14px}.demo-question dt{font:11px monospace;color:#66836d}.demo-question dd{font-size:12px;line-height:1.8;margin-top:4px}.demo-footnote{border-top:1px solid #dce3dc;padding-top:18px;font-size:11px;line-height:1.8;color:#788179}.demo-empty{padding:50px 24px;background:#f2f5ef;border-radius:10px;margin:16px 0 24px}.demo-empty h3{font-size:20px;margin-bottom:12px}.demo-empty p{font-size:13px;color:#6c7b70;line-height:1.8}button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible,a:focus-visible{outline:2px solid #527c60;outline-offset:4px}
@media(max-width:760px){.retrieval-demo{padding-top:24px}.demo-header{flex-direction:column;gap:8px}.demo-header h1{font-size:27px}.demo-layout{grid-template-columns:1fr;gap:28px}.demo-controls{padding:20px}.demo-controls form{grid-template-columns:1fr 1fr}.demo-primary{grid-column:1/-1}.demo-badge{margin-top:0}.demo-question h3{font-size:18px}.demo-nav{gap:16px}}
@media(max-width:380px){.demo-controls form{grid-template-columns:1fr}}
</style>
