<template>
  <footer class="site-footer">
    <div class="career-container footer-grid">
      <div class="md:col-span-1">
        <span class="text-2xl font-black text-indigo-600 mb-8 block">CS Career Guide</span>
        <p class="text-slate-500 font-medium text-sm leading-7 mb-6">© {{ new Date().getFullYear() }} CS Career Guide. Built for the next gen. <br/>专为计算机学子打造的职业成长平台，   赋能每一位开发者的职场梦想。</p>
      </div>
      <div class="flex flex-col gap-6">
        <h5 class="font-black text-slate-900 text-sm uppercase tracking-widest">快速链接</h5>
        <div class="flex flex-col gap-4">
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">关于我们</a>
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">职业路径</a>
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">AI 助手</a>
        </div>
      </div>
      <div class="flex flex-col gap-6">
        <h5 class="font-black text-slate-900 text-sm uppercase tracking-widest">法律合规</h5>
        <div class="flex flex-col gap-4">
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">隐私政策</a>
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">服务条款</a>
        </div>
      </div>
      <div class="flex flex-col gap-6">
        <h5 class="font-black text-slate-900 text-sm uppercase tracking-widest">联系支持</h5>
        <div class="flex flex-col gap-4">
          <a class="text-slate-500 hover:text-indigo-600 font-bold transition-colors text-sm" href="#">联系我们</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer { padding: 48px 0; background: #f0f1eb; border-top: 1px solid var(--career-border); }
.footer-grid { display: grid; grid-template-columns: 2fr repeat(3, 1fr); gap: 64px; }
.footer-grid > div:first-child > span { font-size: 18px; color: var(--career-text); font-weight: 600; margin-bottom: 18px; }
.footer-grid h5 { font-size: 12px; font-weight: 600; letter-spacing: .03em; }
.footer-grid p, .footer-grid a { color: var(--career-muted); font-size: 12px; font-weight: 400; }
.footer-grid a:hover { color: var(--career-text); text-decoration: underline; text-underline-offset: 4px; }
@media (max-width: 760px) {
  .site-footer { padding: 32px 0; }
  .footer-grid { grid-template-columns: repeat(3, 1fr); gap: 30px 20px; }
  .footer-grid > div:first-child { grid-column: 1 / -1; }
}
</style>
