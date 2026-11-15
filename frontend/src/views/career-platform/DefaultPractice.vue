<template>
  <section class="default-practice" aria-labelledby="default-bank-title">
    <div class="bank-heading"><div><p class="eyebrow">无需配置 · 即刻开始</p><h2 id="default-bank-title">先用一组基础题热身</h2></div><span class="bank-label">内置自练 · 9 道题</span></div>
    <p class="bank-note">{{ defaultQuestionSource }}。回答仅保留在本页，不调用模型、不保存历史；参考要点不是自动评分。</p>
    <div class="set-grid"><button v-for="set in defaultQuestionSets" :key="set.id" type="button" class="set-card" :class="{active:activeSet.id===set.id}" :aria-pressed="activeSet.id===set.id" @click="choose(set)"><span>{{ set.questions.length }} 道基础题</span><strong>{{ set.title }}</strong><small>{{ set.description }}</small></button></div>
    <div class="local-workspace"><nav aria-label="内置题目"><button v-for="(q,index) in activeSet.questions" :key="q.id" type="button" :class="{active:activeId===q.id}" :aria-current="activeId===q.id?'true':undefined" @click="activeId=q.id"><span>{{ index+1 }}. {{ q.question }}</span><small>{{ drafts[q.id]?.trim()?'已填写':'待练习' }}</small></button></nav>
      <article><p class="eyebrow">{{ activeSet.title }} / 本地自练</p><h3>{{ current.question }}</h3><label for="default-answer">先写下你的回答</label><textarea id="default-answer" v-model="drafts[current.id]" maxlength="20000" rows="6" placeholder="不必急着看答案，先尝试用自己的话解释。" /><div class="local-actions"><span>{{ (drafts[current.id]||'').length }} / 20000 字</span><button type="button" class="career-button" :aria-expanded="!!revealed[current.id]" @click="revealed[current.id]=!revealed[current.id]">{{ revealed[current.id]?'收起参考要点':'查看参考要点' }}</button></div><section v-if="revealed[current.id]" class="reference"><h4>对照要点，自己复盘</h4><ul><li v-for="point in current.key_points" :key="point">{{ point }}</li></ul><p>来源：{{ defaultQuestionSource }}</p></section></article>
    </div>
  </section>
</template>
<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { defaultQuestionSets, defaultQuestionSource } from './default-questions.js'
const activeSet=ref(defaultQuestionSets[0]),activeId=ref(activeSet.value.questions[0].id)
const drafts=reactive({}),revealed=reactive({})
const current=computed(()=>activeSet.value.questions.find(q=>q.id===activeId.value))
function choose(set){activeSet.value=set;activeId.value=set.questions[0].id}
const hasDrafts=()=>Object.values(drafts).some(v=>v?.trim())
function beforeUnload(event){if(hasDrafts()){event.preventDefault();event.returnValue=''}}
onMounted(()=>window.addEventListener('beforeunload',beforeUnload))
onBeforeUnmount(()=>window.removeEventListener('beforeunload',beforeUnload))
onBeforeRouteLeave(()=>!hasDrafts()||window.confirm('内置自练回答尚未保存，离开后会丢失。确定离开？'))
</script>
<style scoped>
.default-practice{padding:26px;border:1px solid #dce3dc;background:#fff;border-radius:12px;margin-bottom:32px}.bank-heading{display:flex;justify-content:space-between;align-items:center;gap:16px}.eyebrow{font-size:12px;color:#718273;letter-spacing:.06em}.bank-heading h2{font-size:20px;margin:8px 0}.bank-label{font-size:12px;color:#52745b;background:#edf3e9;padding:5px 10px;border-radius:5px}.bank-note{font-size:12px;color:#788179;margin:12px 0 20px}.set-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.set-card{text-align:left;padding:18px;border:1px solid #dce3dc;border-radius:8px;display:grid;gap:7px;color:#526757}.set-card.active{background:#edf3e9;border-color:#7b9b7f}.set-card span,.set-card small{font-size:12px}.set-card strong{font-size:16px;color:#293b34}.local-workspace{display:grid;grid-template-columns:240px minmax(0,1fr);gap:28px;border-top:1px solid #dce3dc;margin-top:24px;padding-top:24px}.local-workspace nav{display:grid;align-content:start;gap:8px}.local-workspace nav button{display:grid;gap:5px;text-align:left;padding:12px;border-radius:6px;color:#69776b;font-size:13px}.local-workspace nav button.active{background:#f1f5ee;color:#365e45}.local-workspace small{font-size:11px;color:#788179}.local-workspace article{min-width:0}.local-workspace h3{font-size:20px;line-height:1.7;margin:12px 0 20px}.local-workspace label{display:block;font-size:13px;margin-bottom:8px}.local-workspace textarea{width:100%;padding:16px;border:1px solid #ccd8ce;border-radius:8px;font:inherit;resize:vertical;line-height:1.9}.local-actions{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:12px}.local-actions>span{font-size:12px;color:#788179}.reference{padding:20px;background:#eef4e9;border-radius:8px;margin-top:18px}.reference h4{font-weight:600;margin-bottom:10px}.reference ul{list-style:disc;padding-left:20px}.reference li{margin:7px 0}.reference p{font-size:12px;color:#718273;margin-top:14px}.default-practice :is(button,textarea):focus-visible{outline:2px solid #527c60;outline-offset:3px}.default-practice :is(p,h3,li){overflow-wrap:anywhere}@media(max-width:760px){.set-grid{grid-template-columns:1fr}.local-workspace{grid-template-columns:1fr}.local-workspace nav{grid-template-columns:repeat(3,minmax(0,1fr))}.bank-heading{align-items:flex-start;flex-direction:column}.default-practice{padding:18px}}@media(max-width:400px){.local-workspace nav{grid-template-columns:1fr}.local-actions{align-items:stretch;flex-direction:column}}
</style>
