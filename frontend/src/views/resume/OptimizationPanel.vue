<template>
  <section class="optimization-panel" aria-labelledby="optimization-title">
    <div class="optimization-heading"><div><p class="career-eyebrow">求职准备 / 岗位对照</p><h2 id="optimization-title">对照目标岗位，打磨真实经历。</h2><p>先在编辑区保存简历，再填写目标岗位要求。分析不会自动覆盖原稿。</p></div><span class="availability">分析服务开发中</span></div>
    <div class="optimization-layout"><form @submit.prevent="analyze"><label for="resume-target-jd">目标岗位 JD</label><textarea id="resume-target-jd" v-model="jd" maxlength="20000" rows="9" required placeholder="粘贴岗位职责与任职要求，后续将基于已保存的简历进行分析。" /><p class="optimization-note">当前简历优化后端尚未完成。可以填写 JD，但暂时无法生成或应用建议。</p><button class="career-button career-button-primary" :disabled="busy||!jd.trim()">{{ busy?'正在检查服务…':'尝试分析已保存简历' }}</button><p v-if="status" class="optimization-status" role="status">{{ status }}</p></form><aside><h3>有依据，才值得修改</h3><ul><li>对照技能要求，区分已有证据与待补足项。</li><li>建议应附原文、改写理由和来源证据。</li><li>由你预览、编辑并确认，不凭空增加经历与成果。</li></ul><p>已有的简历编辑、保存与 PDF 导出不受影响。当前不提供手填建议 ID 的应用入口，也不会展示固定“优化成功”。</p></aside></div>
  </section>
</template>
<script setup>
import { ref } from 'vue'
import { resumeAPI } from '@/api'
import { platformAPI } from '@/features/career-platform'
import { newRequestId } from '@/features/career-platform/api.js'
const jd=ref(''),busy=ref(false),status=ref('')
async function analyze(){
  if(busy.value||!jd.value.trim())return
  busy.value=true;status.value=''
  try{
    const response=await resumeAPI.get(),saved=response?.data??response
    if(!Number.isInteger(saved?.edit_revision)){status.value='请先在编辑区保存简历，再尝试分析。';return}
    await platformAPI.analyze({jd_text:jd.value.trim(),resume_revision:saved.edit_revision,request_id:newRequestId()})
    status.value='已收到分析响应；建议预览和确认应用仍待接入，原简历未在本页修改。'
  }catch(error){status.value=error.response?.status===501?'简历分析服务尚未实现。JD已保留在本页，原简历未修改。':error.response?.status===404?'尚未找到已保存简历，请先在编辑区保存。':error.response?.status===409?'已保存简历版本发生变化，请保存后重新分析。':'分析未完成，请检查登录和网络后重试；原简历未修改。'}
  finally{busy.value=false}
}
</script>
<style scoped>
.optimization-panel{padding:28px;background:#fff;border:1px solid var(--career-border);border-radius:12px;margin:24px 0}.optimization-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.optimization-heading h2{font-size:24px;font-weight:600;margin:12px 0}.optimization-heading p,.optimization-note{color:var(--career-muted);font-size:14px;line-height:1.8}.availability{font-size:12px;color:#80672f;background:#faf6ea;border:1px solid #d5c5a0;padding:6px 10px;white-space:nowrap;border-radius:5px}.optimization-layout{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:36px;margin-top:28px}.optimization-layout label{display:block;margin-bottom:10px;font-size:14px}.optimization-layout textarea{width:100%;padding:16px;border:1px solid #ccd8ce;border-radius:8px;font:inherit;line-height:1.8;resize:vertical}.optimization-note{font-size:12px;margin:12px 0 18px}.optimization-layout aside{padding:24px;background:#f1f5ee;border-radius:8px;color:#5f7163;line-height:1.9}.optimization-layout h3{font-size:18px;font-weight:600;color:#365e45;margin-bottom:14px}.optimization-layout ul{list-style:disc;padding-left:20px}.optimization-layout li{margin-bottom:12px}.optimization-layout aside p{font-size:12px;margin-top:22px}.optimization-status{padding:14px;background:#edf3ed;margin-top:18px;overflow-wrap:anywhere}.optimization-panel :is(textarea,button):focus-visible{outline:2px solid #527c60;outline-offset:4px}@media(max-width:760px){.optimization-panel{padding:20px}.optimization-heading{flex-direction:column}.optimization-layout{grid-template-columns:1fr;gap:20px}.optimization-heading h2{font-size:22px}}
</style>
