<template>
  <main class="career-container platform-workspace">
    <header><p class="career-eyebrow">课程项目 / 功能开发</p><h1>{{ title }}</h1><p>{{ description }}</p><span class="stage-label">开发骨架 · 功能待实现</span></header>
    <nav aria-label="课程模块"><router-link v-for="item in modules" :key="item.path" :to="'/career-platform/'+item.path">{{ item.title }}</router-link></nav>
    <section class="platform-panel"><slot /></section>
  </main>
</template>
<script setup>
defineProps({ title:String, description:String })
const modules=[{path:'catalog',title:'岗位与题库'},{path:'resume',title:'简历优化'},{path:'practice',title:'岗位题库练习'},{path:'records',title:'练习记录'},{path:'evaluation',title:'评估与调优（管理员）'}]
</script>
<style>
.platform-workspace { padding-top:32px; padding-bottom:48px; }
.platform-workspace h1 { font-size:27px; color:var(--career-text); margin:12px 0; }
.platform-workspace header > p:last-of-type { color:var(--career-muted); font-size:14px; line-height:1.8; }
.stage-label { display:inline-block; padding:5px 10px; margin-top:14px; background:#fff8e8; color:#8a5a16; border:1px solid #eadab7; border-radius:4px; font-size:12px; }
.platform-workspace nav { display:flex; flex-wrap:wrap; gap:18px; margin:26px 0; padding-bottom:16px; border-bottom:1px solid var(--career-border); font-size:14px; }
.platform-workspace nav .router-link-active { color:var(--career-blue); font-weight:600; }
.platform-panel { padding:24px; border:1px solid var(--career-border); border-radius:8px; background:white; }
.platform-form { display:grid; gap:16px; max-width:760px; }
.platform-form label { display:grid; gap:8px; font-size:13px; color:#475467; }
.platform-form input,.platform-form textarea,.platform-form select { width:100%; padding:10px 12px; border:1px solid #ced8e5; border-radius:5px; background:white; }
.platform-form textarea { min-height:140px; }
.platform-actions { display:flex; flex-wrap:wrap; gap:12px; }
.platform-status { padding:18px; margin:20px 0; background:#f6f8fb; color:#62748b; font-size:13px; line-height:1.9; }
.platform-result { border-top:1px solid var(--career-border); margin-top:24px; padding-top:20px; color:#62748b; font-size:13px; }
.platform-result h2 { color:#344054; font-size:16px; margin-bottom:10px; }
</style>
