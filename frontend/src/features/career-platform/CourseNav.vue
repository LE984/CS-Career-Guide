<template>
  <nav class="course-nav" aria-label="课程模块">
    <router-link v-for="item in modules" :key="item.path" :to="'/career-platform/' + item.path" active-class="course-nav-active">{{ item.title }}</router-link>
  </nav>
</template>
<script setup>
const modules = [
  { path: 'catalog', title: '岗位与题库' },
  { path: 'resume', title: '简历优化' },
  { path: 'practice', title: '岗位题库练习' },
  { path: 'records', title: '练习记录' },
  { path: 'evaluation', title: '评估与调优（管理员）' },
]
</script>
<style>
.course-nav { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 28px; padding-bottom:20px; border-bottom:1px solid var(--career-border); font-size:14px; line-height:1.5; }
.course-nav a { display:block; padding:10px 14px; border:1px solid transparent; border-radius:6px; color:var(--career-muted); font-weight:500; text-decoration:none; transition:background-color 140ms ease,color 140ms ease,border-color 140ms ease; }
.course-nav a:hover { background:#f0f1eb; color:var(--career-text); }
.course-nav a.course-nav-active { background:#edf3ed; border-color:#ccd8ce; color:#365e45; }
.course-nav a:focus-visible { outline:2px solid #527c60; outline-offset:3px; }
.course-content-enter { animation:course-content-in 160ms ease-out; }
@keyframes course-content-in { from { opacity:.65; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }
@media(max-width:760px) { .course-nav { gap:6px; margin-bottom:24px; padding-bottom:16px; } .course-nav a { padding:9px 10px; font-size:13px; } }
@media(prefers-reduced-motion:reduce) { .course-nav a { transition:none; } .course-content-enter { animation:none; } }
</style>
