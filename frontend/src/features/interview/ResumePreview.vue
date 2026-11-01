<template>
  <div class="resume-reader">
    <div class="reader-tools"><span>已保存的简历</span><button type="button" class="career-button" :disabled="loading" @click="loadResume">刷新简历</button></div>
    <div v-if="loading" class="reader-state" role="status">正在读取简历…</div>
    <div v-else-if="error" class="reader-state" role="alert"><h3>暂时无法读取简历</h3><p>{{ error }}</p><button type="button" class="career-button" @click="loadResume">重试</button></div>
    <div v-else-if="!resume || resume.empty" class="reader-state"><h3>还没有已保存的简历</h3><p>先在简历页填写并保存，再回到这里刷新。<br />你可以继续本场面试。</p><router-link to="/resume" target="_blank" rel="noopener noreferrer" class="career-link">在新页面完善简历 ↗</router-link></div>
    <article v-else class="resume-document" aria-label="已保存的简历内容">
      <header><h3>{{ resume.name || '我的简历' }}</h3><p v-if="resume.target" class="resume-target">{{ resume.target }}</p><ul v-if="resume.contacts.length" class="resume-contacts"><li v-for="(contact,index) in resume.contacts" :key="index">{{ contact }}</li></ul></header>
      <section v-for="section in resume.sections" :key="section.title"><h4>{{ section.title }}</h4><div v-for="(item,index) in section.items" :key="index" class="resume-entry"><h5 v-if="item.title">{{ item.title }}</h5><p v-if="item.meta" class="entry-meta">{{ item.meta }}</p><p v-if="item.description" class="entry-description">{{ item.description }}</p><p v-if="item.url" class="entry-url">{{ item.url }}</p></div></section>
      <footer><router-link to="/resume" target="_blank" rel="noopener noreferrer" class="career-link">在新页面编辑简历 ↗</router-link><p>保存修改后，点击上方“刷新简历”。</p></footer>
    </article>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { resumeAPI } from '@/api'
import { resumePreview } from './resume-preview.js'
const loading = ref(true), error = ref(''), resume = ref(null)
let controller = null
async function loadResume() {
  controller?.abort()
  const request = new AbortController()
  controller = request
  loading.value = true; error.value = ''; resume.value = null
  try {
    const data = await resumeAPI.get({ signal: request.signal })
    if (!request.signal.aborted) resume.value = resumePreview(data)
  } catch (failure) {
    if (request.signal.aborted) return
    if (failure.response?.status !== 404) error.value = '请检查网络后重试，当前面试不会中断。'
  } finally {
    if (controller === request && !request.signal.aborted) loading.value = false
  }
}
onMounted(loadResume)
onUnmounted(() => controller?.abort())
</script>

<style scoped>
.reader-tools { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 22px; font-size: 11px; color: #7a8799; border-bottom: 1px solid #e3e9f0; }
.reader-tools button, .reader-state button { min-height: 30px; padding: 5px 10px; font-size: 12px; }
.reader-state { padding: 48px 24px; text-align: center; font-size: 13px; color: #66788e; line-height: 1.9; }
.reader-state h3 { font-size: 14px; font-weight: 500; color: #344054; }
.reader-state p { margin: 12px 0 20px; }
.reader-state a { font-size: 12px; }
.resume-document { margin: 18px 16px 24px; padding: 26px 20px; background: #fff; border: 1px solid #e3e9f0; border-radius: 4px; color: #344054; overflow-wrap: anywhere; }
.resume-document > header { padding-bottom: 22px; border-bottom: 2px solid #d4e2f3; }
.resume-document h3 { font-size: 23px; font-weight: 600; letter-spacing: -.02em; }
.resume-target { margin-top: 8px; font-size: 14px; color: #346591; }
.resume-contacts { display: grid; gap: 5px; margin-top: 14px; font-size: 11px; color: #7a8799; }
.resume-document section { margin-top: 25px; }
.resume-document h4 { font-size: 13px; font-weight: 600; color: #346591; padding-bottom: 8px; border-bottom: 1px solid #e3e9f0; }
.resume-entry { margin-top: 13px; }
.resume-entry h5 { font-size: 13px; font-weight: 600; line-height: 1.8; }
.entry-meta, .entry-url { margin-top: 3px; font-size: 11px; line-height: 1.8; color: #7a8799; }
.entry-description { margin-top: 6px; white-space: pre-wrap; font-size: 12px; line-height: 1.95; }
.resume-document footer { margin-top: 30px; padding-top: 16px; border-top: 1px solid #e3e9f0; font-size: 11px; line-height: 1.9; color: #7a8799; }
.resume-document footer p { margin-top: 7px; }
</style>
