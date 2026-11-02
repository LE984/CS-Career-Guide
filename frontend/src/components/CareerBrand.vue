<template>
  <router-link to="/" class="career-brand" aria-label="CS Career Guide 首页">
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><rect x="1" y="1" width="30" height="30" rx="7" stroke="#b8d3f6"/><path d="m7 23 6-9 6 4 6-10" stroke="#1768c4" stroke-width="1.6"/><circle cx="7" cy="23" r="2" fill="white" stroke="#1768c4" stroke-width="1.5"/><circle cx="13" cy="14" r="2" fill="white" stroke="#1768c4" stroke-width="1.5"/><circle cx="19" cy="18" r="2" fill="white" stroke="#1768c4" stroke-width="1.5"/><circle cx="25" cy="8" r="2" fill="white" stroke="#13867d" stroke-width="1.5"/></svg>
    <span>CS Career Guide<small>计算机大学生职业指南</small></span>
  </router-link>
</template>
<style scoped>
.career-brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #1d2939;
  text-decoration: none;
  flex: none;
}
.career-brand svg {
  width: 32px;
  height: 32px;
  flex: none;
}
.career-brand>span {
  font-size: 16px;
  font-weight: 650;
  line-height: 1.25;
  letter-spacing: -.025em;
}
.career-brand small {
  display: block;
  margin-top: 2px;
  color: #667085;
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 0;
}
</style>
