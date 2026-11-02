<template>
  <div class="home-page">
    <section class="home-hero career-container">
      <div class="hero-copy">
        <p class="home-eyebrow"><span class="status-dot" aria-hidden="true"></span>下一代职业发展平台</p>
        <h1>开启你的 <span>CS</span><br />职业生涯</h1>
        <p class="hero-description">专为计算机学子打造的全栈职业指导平台。从技能对齐到简历优化，从 AI 模拟面试到企业真实红黑榜，助你锁定顶级 Offer。</p>
        <div class="home-actions">
          <router-link to="/career-paths" class="career-button">浏览职业路径 <span aria-hidden="true">→</span></router-link>
          <router-link to="/career-paths/employment/self-introduction" class="career-button career-button-primary">开始测评 <span aria-hidden="true">↗</span></router-link>
        </div>
      </div>
      <div class="hero-visual">
        <img class="hero-illustration" src="@/assets/images/career-journey.svg" alt="细线路径串联简历文档与对话框，描绘从职业探索到面试交流的旅程" width="560" height="440" fetchpriority="high" />
      </div>
    </section>

    <section class="home-modules career-container">
      <header class="section-heading"><div><p class="home-eyebrow">01 / EXPLORE</p><h2>核心赋能模块</h2></div><p>全方位覆盖求职链路，利用数据与 AI 填补信息差，打造沉浸式求职体验。</p></header>
      <div class="module-grid">
        <article class="module-card">
          <div class="module-top"><img src="@/assets/images/路径10.png" alt="路径10" loading="lazy" /><span>01</span></div>
          <h3>职业路径</h3><p>根据技术趋势动态更新的技能树，精准定位前后端、算法、运维等 20+ 细分方向。</p>
          <router-link to="/career-paths" class="module-link">了解更多 <span aria-hidden="true">↗</span></router-link>
        </article>
        <article class="module-card">
          <div class="module-top"><img src="@/assets/images/评价10.png" alt="评价10" loading="lazy" /><span>02</span></div>
          <h3>职业测评</h3><p>多维人格与技术栈匹配度评估，告诉你最适合的赛道。</p>
          <router-link to="/career-paths/employment/self-introduction" class="module-link">开始测评 <span aria-hidden="true">↗</span></router-link>
        </article>
        <article class="module-card">
          <div class="module-top"><img src="@/assets/images/榜单10.png" alt="榜单10" loading="lazy" /><span>03</span></div>
          <h3>企业红黑榜</h3><p>脱敏真实职场评价，避开"坑企"，直达"神仙公司"。</p>
          <router-link to="/company-reviews" class="module-link">查看榜单 <span aria-hidden="true">↗</span></router-link>
        </article>
      </div>
      <article class="interview-feature">
        <div class="interview-feature-copy"><p class="home-eyebrow">Premium AI 模块</p><h3>AI 面试模拟仓</h3><p>深度集成 LangGraph 多智能体工作流，模拟真实技术面试官，提供实时反馈与专业改进建议。</p><router-link to="/interview" class="career-button career-button-primary">立即免费体验 <span aria-hidden="true">↗</span></router-link></div>
        <div class="interview-sample">
          <p class="sample-status"><span class="status-dot" aria-hidden="true"></span>// 正在初始化面试机器人...</p>
          <div class="sample-question"><span>面试官:</span><p>"请解释下 Vue3 的组合式 API 比选项式 API 强在哪里？"</p></div>
          <div class="sample-answer">_等待候选人回答...<span aria-hidden="true">|</span></div>
        </div>
      </article>
    </section>

    <section class="home-advantages career-container">
      <header class="section-heading"><div><p class="home-eyebrow">02 / WHY US</p><h2>为什么选择<br /><span>我们?</span></h2></div><p>我们不仅仅是信息的搬运工，更是你职场跃迁的加速器，用技术力量重塑求职可能。</p></header>
      <div class="advantage-grid">
        <article><img src="@/assets/images/首页1.png" alt="首页1" loading="lazy" @error="handleImageError" /><h4>全栈架构</h4><p>系统化覆盖从底层计算机组成原理到上层云原生应用的所有技能节点。</p></article>
        <article><img src="@/assets/images/首页2.png" alt="首页2" loading="lazy" @error="handleImageError" /><h4>AI 驱动</h4><p>基于最新大模型技术，为你定制个性化的学习路径与改写建议。</p></article>
        <article><img src="@/assets/images/首页3.png" alt="首页3" loading="lazy" @error="handleImageError" /><h4>真实评价</h4><p>拒绝虚假宣传，所有企业点评均经过严格的人工审核与身份核验。</p></article>
      </div>
    </section>

    <section class="home-stack career-container">
      <div><p class="home-eyebrow">03 / BUILT WITH</p><h2>卓越的底层架构</h2><p>我们深知 CS 学子的标准，因此在产品构建上也追求极致的技术美学与性能。</p></div>
      <div class="stack-list"><div><strong>Vue 3</strong><span>前端</span></div><div><strong>Django</strong><span>后端</span></div><div><strong>MySQL</strong><span>数据库</span></div><div><strong>LangGraph</strong><span>AI 多智能体</span></div></div>
    </section>

    <section class="home-cta career-container"><div><p class="home-eyebrow">YOUR NEXT CHAPTER</p><h2>准备好迎接你的第一个<br />顶级 Offer 了吗？</h2><p>加入优秀计算机学子的选择，让你的职业起点更高、更稳、更远。</p></div><router-link to="/career-paths" class="career-button career-button-primary">立即开启免费规划 <span aria-hidden="true">↗</span></router-link></section>
  </div>
</template>

<script setup>
function handleImageError(event) {
  event.target.onerror = null
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyMCAyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIGZpbGw9IiNmNWY1ZjUiLz48cGF0aCBkPSJNMTAgMTVjLTIuNyAwLTUgMi4zLTUgNXMxLjY0IDMgMy4zNiAzYzEuNzIgMCAzLTIgMy00cy0xLjI4LTMtMy0zczMtMi4zIDMtNXoiIGZpbGw9IiM4ODgiLz48L3N2Zz4='
  event.target.alt = '图片加载失败'
}
</script>

<style scoped>
.home-page { color: var(--career-text); }
.home-eyebrow { font-size: 11px; letter-spacing: .14em; color: var(--career-muted); font-weight: 500; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; background: #7b8e5b; flex: none; }
.home-hero { display: grid; grid-template-columns: 1.15fr 1fr; gap: 88px; align-items: center; padding-block: 92px 100px; }
.hero-copy > .home-eyebrow { display: flex; align-items: center; gap: 10px; margin-bottom: 28px; }
.hero-copy h1 { font-size: clamp(44px, 5.6vw, 76px); line-height: 1.22; letter-spacing: -.06em; font-weight: 500; }
.hero-copy h1 span { font-family: Georgia, 'Times New Roman', serif; font-weight: 400; font-style: italic; color: #657453; }
.hero-description { max-width: 470px; color: var(--career-muted); font-size: 15px; line-height: 2; margin: 26px 0 34px; }
.home-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.home-actions .career-button { min-height: 48px; gap: 26px; }
.hero-visual { min-width: 0; }
.hero-illustration { display: block; width: 100%; height: auto; max-width: 560px; margin-inline: auto; }
.home-modules, .home-advantages { padding-block: 64px 80px; border-top: 1px solid var(--career-border); }
.section-heading { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: 20px 40px; margin-bottom: 38px; }
.section-heading h2, .home-stack h2 { font-size: 32px; line-height: 1.4; margin-top: 12px; }
.section-heading > p { max-width: 100%; flex-shrink: 0; white-space: nowrap; color: var(--career-muted); font-size: 14px; line-height: 1.9; }
.module-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--career-border); border-radius: 6px; overflow: hidden; }
.module-card { padding: 30px; background: #fff; display: flex; flex-direction: column; transition: background .2s; }
.module-card:hover { background: #f5f6f0; }
.module-card + .module-card { border-left: 1px solid var(--career-border); }
.module-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.module-top img { width: 46px; height: 46px; object-fit: cover; border-radius: 5px; }
.module-top > span { font-size: 11px; color: #858a7f; font-variant-numeric: tabular-nums; }
.module-card h3 { font-size: 22px; margin-bottom: 14px; }
.module-card > p { font-size: 14px; line-height: 1.9; color: var(--career-muted); }
.module-link { display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 30px; font-size: 13px; color: var(--career-text); }
.module-link span { font-size: 20px; }
.interview-feature { margin-top: 24px; padding: 42px; display: grid; grid-template-columns: 1fr 1fr; gap: 70px; align-items: center; background: #edf0e5; border: 1px solid #dde2d2; border-radius: 6px; }
.interview-feature h3 { font-size: 30px; margin: 12px 0 16px; }
.interview-feature-copy > p:not(.home-eyebrow) { font-size: 14px; color: #64705b; line-height: 1.9; margin-bottom: 26px; }
.interview-sample { background: #fafbf7; border: 1px solid #d6ddca; border-radius: 5px; padding: 26px; font-size: 13px; }
.sample-status { font-family: ui-monospace, monospace; color: #738164; font-size: 11px; display: flex; gap: 9px; align-items: center; padding-bottom: 20px; border-bottom: 1px solid #e3e7db; }
.sample-question { padding: 22px 0; line-height: 1.9; }
.sample-question > span { color: #79866c; font-size: 11px; display: block; margin-bottom: 8px; }
.sample-answer { color: #7c8474; font-size: 12px; display: flex; justify-content: space-between; border-top: 1px solid #e3e7db; padding-top: 18px; }
.home-advantages { border-top: 0; padding-top: 24px; }
.advantage-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 54px; }
.advantage-grid article { border-top: 1px solid var(--career-border); padding-top: 26px; }
.advantage-grid img { width: 44px; height: 44px; object-fit: cover; border-radius: 5px; margin-bottom: 22px; }
.advantage-grid h4 { font-size: 20px; margin-bottom: 12px; }
.advantage-grid p, .home-stack > div > p:last-child { font-size: 14px; line-height: 1.9; color: var(--career-muted); }
.home-stack { padding-block: 48px 64px; border-top: 1px solid var(--career-border); display: grid; grid-template-columns: 1fr 1.2fr; gap: 70px; align-items: center; }
.home-stack h2 { font-size: 26px; margin-bottom: 14px; }
.stack-list { display: grid; grid-template-columns: repeat(4, 1fr); gap: 22px; }
.stack-list div { display: flex; flex-direction: column; gap: 12px; }
.stack-list strong { font-size: 20px; font-weight: 500; letter-spacing: -.04em; }
.stack-list span { font-size: 11px; color: var(--career-muted); }
.home-cta { border-top: 1px solid var(--career-border); padding-block: 64px 80px; display: flex; justify-content: space-between; align-items: center; gap: 32px; }
.home-cta h2 { font-size: 36px; line-height: 1.5; margin: 16px 0; }
.home-cta > div > p:last-child { font-size: 14px; color: var(--career-muted); }
.home-cta > a { flex: none; gap: 24px; }
@media (max-width: 1050px) {
  .home-hero { gap: 40px; padding-block: 64px; }
  .module-card { padding: 24px; }
  .interview-feature { gap: 30px; padding: 30px; }
  .home-stack { grid-template-columns: 1fr; gap: 32px; }
}
@media (max-width: 760px) {
  .home-hero { grid-template-columns: 1fr; gap: 36px; padding-block: 44px; }
  .hero-copy h1 { font-size: clamp(42px, 10vw, 64px); }
  .hero-description { font-size: 14px; margin: 22px 0 26px; }
  .hero-illustration { max-width: 440px; }
  .section-heading { align-items: flex-start; flex-direction: column; gap: 18px; margin-bottom: 28px; }
  .section-heading h2 { font-size: 28px; }
  .section-heading > p { white-space: normal; }
  .home-modules, .home-advantages { padding-block: 40px; }
  .module-grid, .interview-feature, .advantage-grid { grid-template-columns: 1fr; }
  .module-card + .module-card { border-left: 0; border-top: 1px solid var(--career-border); }
  .module-top { margin-bottom: 20px; }
  .interview-feature { padding: 24px; gap: 28px; }
  .interview-sample { padding: 20px; }
  .advantage-grid { gap: 30px; }
  .stack-list { grid-template-columns: repeat(2, 1fr); gap: 26px; }
  .home-cta { flex-direction: column; align-items: flex-start; padding-block: 40px 52px; }
  .home-cta h2 { font-size: 28px; }
}
</style>
