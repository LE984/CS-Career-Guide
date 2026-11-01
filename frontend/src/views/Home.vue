<template>
  <div class="w-full bg-gradient-to-r from-white to-purple-100">
    
    <!-- Hero Section -->
    <section class="relative min-h-[850px] flex items-center overflow-hidden px-8 py-20 bg-white">
      <!-- Abstract Background Elements -->
      <div class="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-bl from-indigo-50/50 to-purple-50/30 -z-10 rounded-bl-[100px]"></div>
      <div class="absolute top-40 right-40 w-72 h-72 bg-indigo-400/10 rounded-full blur-[100px] -z-10 animate-pulse-glow"></div>
      <div class="absolute bottom-20 left-20 w-96 h-96 bg-purple-400/10 rounded-full blur-[120px] -z-10 animate-pulse-glow" style="animation-delay: -4s;"></div>
      <!-- Tech Decor -->
      <div class="absolute top-20 left-1/4 w-2 h-2 bg-indigo-200 rounded-full animate-ping"></div>
      <div class="absolute bottom-40 right-1/3 w-3 h-3 bg-purple-200 rounded-full animate-pulse"></div>
      <div class="max-w-7xl mx-auto editorial-grid w-full relative z-10">
        <div class="col-span-12 lg:col-span-7 flex flex-col justify-center">
          <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-extrabold mb-8 w-fit border border-indigo-100/50">
            <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;"></span>
            下一代职业发展平台
          </div>
          <h1 class="font-headline text-6xl md:text-8xl font-black text-slate-900 leading-[1.1] mb-8 tracking-tight">
            开启你的 <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-500">CS</span> <br/>职业生涯
          </h1>
          <p class="text-xl text-slate-600 max-w-xl mb-12 leading-relaxed font-medium">
            专为计算机学子打造的全栈职业指导平台。从技能对齐到简历优化，从 AI 模拟面试到企业真实红黑榜，助你锁定顶级 Offer。
          </p>
          <div class="flex flex-wrap gap-5">
            <button @click="navigateToCareerEvaluation" class="px-10 py-5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-3xl font-bold text-lg shadow-xl shadow-indigo-200 hover:translate-y-[-4px] active:scale-95 transition-all flex items-center gap-2">
              开始测评 <span class="material-symbols-outlined"></span>
            </button>
            <button @click="navigateToCareerPaths" class="px-10 py-5 bg-white text-slate-900 rounded-3xl font-bold text-lg border-2 border-slate-100 hover:border-indigo-100 hover:bg-indigo-50/30 transition-all flex items-center gap-2">
              浏览职业路径 <span class="material-symbols-outlined"></span>
            </button>
          </div>
        </div>
        <div class="col-span-12 lg:col-span-5 relative hidden lg:flex items-center justify-center">
          <div class="relative w-full max-w-[500px]">
            <div class="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 to-purple-500/20 rounded-[3rem] blur-3xl -z-10 scale-110"></div>
            <div class="bg-white/40 backdrop-blur-xl p-8 rounded-[3.5rem] soft-shadow border border-white/50 hero-img-animated transition-transform duration-700">
              <img alt="Technology Hub" class="rounded-[2.5rem] w-full h-[450px] object-cover shadow-2xl" src="@/assets/images/indexpicture1.jpg"/>
              <div class="mt-8 space-y-4">
                <div class="h-2.5 w-1/4 bg-indigo-600/30 rounded-full"></div>
                <div class="h-2.5 w-full bg-slate-100 rounded-full"></div>
                <div class="h-2.5 w-3/4 bg-slate-100 rounded-full"></div>
              </div>
            </div>
            <!-- Decorative Floating Elements -->
            <div class="absolute -top-10 -left-10 w-24 h-24 bg-white/80 backdrop-blur-md rounded-3xl shadow-xl flex items-center justify-center border border-white animate-bounce" style="animation-duration: 4s;">
              <img 
                src="@/assets/images/首页0.png" 
                alt="首页0" 
                class="w-full h-full object-cover rounded-2xl"
                @error="handleImageError"
              />
            </div>
            
          </div>
        </div>
      </div>
    </section>
    
    <!-- Core Modules Showcase (Bento Grid) -->
    <section class="py-32 px-8 bg-slate-50/50 relative overflow-hidden">
      <div class="max-w-7xl mx-auto">
        <div class="text-center mb-20">
          <h2 class="font-headline text-5xl font-black text-slate-900 mb-6">核心赋能模块</h2>
          <p class="text-slate-500 text-lg max-w-2xl mx-auto font-medium">全方位覆盖求职链路，利用数据与 AI 填补信息差，打造沉浸式求职体验。</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <!-- Module Card 1 -->
          <div class="md:col-span-2 bg-white p-10 rounded-[2.5rem] soft-shadow border border-slate-100 tech-glow-card transition-all duration-500 group cursor-pointer">
            <div class="w-16 h-16 bg-indigo-50 rounded-3xl flex items-center justify-center mb-8 group-hover:bg-indigo-600 group-hover:text-white transition-all duration-300 overflow-hidden">
              <img src="@/assets/images/路径10.png" alt="路径10" class="w-full h-full object-cover"/>
            </div>
            <h3 class="text-3xl font-black mb-4 text-slate-900">职业路径</h3>
            <p class="text-slate-500 text-lg mb-8 leading-relaxed">根据技术趋势动态更新的技能树，精准定位前后端、算法、运维等 20+ 细分方向。</p>
            <div class="flex items-center text-indigo-600 font-bold group-hover:gap-2 transition-all" @click="navigateToCareerPaths">
              了解更多 
            </div>
          </div>
          <!-- Module Card 2 -->
          <div class="bg-white p-10 rounded-[2.5rem] soft-shadow border border-slate-100 tech-glow-card transition-all duration-500 group cursor-pointer">
            <div class="w-16 h-16 bg-purple-50 rounded-3xl flex items-center justify-center mb-8 group-hover:bg-purple-600 transition-all duration-300 overflow-hidden">
              <img src="@/assets/images/评价10.png" alt="评价10" class="w-full h-full object-cover"/>
            </div>
            <h3 class="text-2xl font-black mb-4 text-slate-900">职业测评</h3>
            <p class="text-slate-500 leading-relaxed">多维人格与技术栈匹配度评估，告诉你最适合的赛道。</p>
            <div class="flex items-center text-indigo-600 font-bold group-hover:gap-2 transition-all mt-4" @click="navigateToCareerEvaluation">
              开始测评 
            </div>
          </div>
          <!-- Module Card 3 -->
          <div class="bg-white p-10 rounded-[2.5rem] soft-shadow border border-slate-100 tech-glow-card transition-all duration-500 group cursor-pointer">
            <div class="w-16 h-16 bg-cyan-50 rounded-3xl flex items-center justify-center mb-8 group-hover:bg-cyan-500 transition-all duration-300 overflow-hidden">
              <img src="@/assets/images/榜单10.png" alt="榜单10" class="w-full h-full object-cover"/>
            </div>
            <h3 class="text-2xl font-black mb-4 text-slate-900">企业红黑榜</h3>
            <p class="text-slate-500 leading-relaxed">脱敏真实职场评价，避开"坑企"，直达"神仙公司"。</p>
            <div class="mt-4 flex gap-2">
              <span class="px-2 py-0.5 bg-green-50 text-green-600 text-[10px] font-black rounded-lg border border-green-100 uppercase tracking-tighter">推荐</span>
              <span class="px-2 py-0.5 bg-red-50 text-red-600 text-[10px] font-black rounded-lg border border-red-100 uppercase tracking-tighter">预警</span>
            </div>
            <div class="flex items-center text-indigo-600 font-bold group-hover:gap-2 transition-all mt-4" @click="navigateToCompanyReviews">
              查看榜单 
            </div>
          </div>
          <!-- Module Card 4 -->
          <div class="md:col-span-4 bg-indigo-950 p-10 md:p-16 rounded-[3rem] relative overflow-hidden group shadow-2xl transition-all duration-500 hover:shadow-indigo-500/20">
            <!-- Glassmorphism Overlay -->
            <div class="absolute -right-20 -bottom-20 w-96 h-96 bg-indigo-500/20 rounded-full blur-[100px]"></div>
            <div class="absolute -left-20 -top-20 w-80 h-80 bg-purple-500/10 rounded-full blur-[100px]"></div>
            <div class="relative z-10 grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div class="inline-block px-4 py-1.5 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full text-[10px] text-white font-black mb-6 tracking-widest uppercase">Premium AI 模块</div>
                <h3 class="text-white text-4xl md:text-5xl font-black mb-6 leading-tight">AI 面试模拟仓</h3>
                <p class="text-indigo-200/80 text-xl mb-10 leading-relaxed">深度集成 LangGraph 多智能体工作流，模拟真实技术面试官，提供实时反馈与专业改进建议。</p>
                <button @click="navigateToInterview" class="px-10 py-5 bg-white text-indigo-900 rounded-[2rem] font-black text-lg hover:bg-indigo-50 active:scale-95 transition-all shadow-xl shadow-indigo-900/40">立即免费体验</button>
              </div>
              <div class="hidden md:block">
                <div class="bg-white/5 backdrop-blur-md border border-white/10 p-8 rounded-[2.5rem] font-mono text-sm text-indigo-100/90 shadow-2xl">
                  <p class="text-indigo-400 mb-4 flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                    // 正在初始化面试机器人...
                  </p>
                  <div class="space-y-4">
                    <div class="flex gap-3">
                      <span class="text-purple-400 font-bold shrink-0">面试官:</span>
                      <p class="italic">"请解释下 Vue3 的组合式 API 比选项式 API 强在哪里？"</p>
                    </div>
                    <div class="p-4 bg-white/5 rounded-2xl border border-white/5">
                      <p class="text-indigo-300/60 mb-3">_等待候选人回答...</p>
                      <div class="w-full bg-indigo-900/50 h-2 rounded-full overflow-hidden">
                        <div class="w-2/3 h-full bg-gradient-to-r from-indigo-500 to-purple-500 animate-[loading_2s_ease-in-out_infinite]"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Platform Advantages -->
    <section class="py-32 px-8 bg-white overflow-hidden relative">
      <div class="max-w-7xl mx-auto editorial-grid relative">
        <div class="col-span-12 lg:col-span-4 flex flex-col justify-center">
          <h2 class="font-headline text-5xl font-black mb-8 text-slate-900 leading-tight">为什么选择 <br/><span class="text-indigo-600">我们?</span></h2>
          <p class="text-slate-500 text-lg font-medium leading-relaxed">我们不仅仅是信息的搬运工，更是你职场跃迁的加速器，用技术力量重塑求职可能。</p>
        </div>
        <div class="col-span-12 lg:col-span-8 grid grid-cols-1 md:grid-cols-3 gap-10">
          <div class="space-y-6 p-8 rounded-[2.5rem] hover:bg-slate-50 transition-all border border-transparent hover:border-slate-100 tech-glow-card cursor-default">
            <div class="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center group-hover:scale-110 transition-transform overflow-hidden">
              <img src="@/assets/images/首页1.png" alt="首页1" class="w-full h-full object-cover" @error="handleImageError"/>
            </div>
            <h4 class="text-2xl font-black text-slate-900">全栈架构</h4>
            <p class="text-slate-500 leading-relaxed font-medium">系统化覆盖从底层计算机组成原理到上层云原生应用的所有技能节点。</p>
          </div>
          <div class="space-y-6 p-8 rounded-[2.5rem] hover:bg-slate-50 transition-all border border-transparent hover:border-slate-100 tech-glow-card cursor-default">
            <div class="w-16 h-16 rounded-2xl bg-purple-50 flex items-center justify-center group-hover:scale-110 transition-transform overflow-hidden">
              <img src="@/assets/images/首页2.png" alt="首页2" class="w-full h-full object-cover" @error="handleImageError"/>
            </div>
            <h4 class="text-2xl font-black text-slate-900">AI 驱动</h4>
            <p class="text-slate-500 leading-relaxed font-medium">基于最新大模型技术，为你定制个性化的学习路径与改写建议。</p>
          </div>
          <div class="space-y-6 p-8 rounded-[2.5rem] hover:bg-slate-50 transition-all border border-transparent hover:border-slate-100 tech-glow-card cursor-default">
            <div class="w-16 h-16 rounded-2xl bg-cyan-50 flex items-center justify-center group-hover:scale-110 transition-transform overflow-hidden">
              <img src="@/assets/images/首页3.png" alt="首页3" class="w-full h-full object-cover" @error="handleImageError"/>
            </div>
            <h4 class="text-2xl font-black text-slate-900">真实评价</h4>
            <p class="text-slate-500 leading-relaxed font-medium">拒绝虚假宣传，所有企业点评均经过严格的人工审核与身份核验。</p>
          </div>
        </div>
      </div>
    </section>
    
    <!-- Technology Stack Section -->
    <section class="py-24 px-8 border-t border-slate-100 bg-slate-50/30">
      <div class="max-w-7xl mx-auto">
        <div class="flex flex-col lg:flex-row items-center justify-between gap-16">
          <div class="max-w-md text-center lg:text-left">
            <h2 class="font-headline text-4xl font-black text-slate-900 mb-6">卓越的底层架构</h2>
            <p class="text-slate-500 font-medium">我们深知 CS 学子的标准，因此在产品构建上也追求极致的技术美学与性能。</p>
          </div>
          <div class="flex flex-wrap gap-16 justify-center opacity-60 grayscale hover:grayscale-0 transition-all duration-700">
            <div class="flex flex-col items-center gap-3">
              <span class="text-3xl font-black text-slate-900">Vue 3</span>
              <span class="text-[10px] uppercase tracking-[0.2em] font-black text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">前端</span>
            </div>
            <div class="flex flex-col items-center gap-3">
              <span class="text-3xl font-black text-slate-900">Django</span>
              <span class="text-[10px] uppercase tracking-[0.2em] font-black text-purple-600 bg-purple-50 px-3 py-1 rounded-full">后端</span>
            </div>
            <div class="flex flex-col items-center gap-3">
              <span class="text-3xl font-black text-slate-900">MySQL</span>
              <span class="text-[10px] uppercase tracking-[0.2em] font-black text-cyan-600 bg-cyan-50 px-3 py-1 rounded-full">数据库</span>
            </div>
            <div class="flex flex-col items-center gap-3">
              <span class="text-3xl font-black text-slate-900">LangGraph</span>
              <span class="text-[10px] uppercase tracking-[0.2em] font-black text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">AI 多智能体</span>
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- CTA Section -->
    <section class="py-24 px-8 relative">
      <div class="max-w-6xl mx-auto bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 rounded-[3.5rem] p-16 md:p-24 text-center text-white relative overflow-hidden shadow-2xl shadow-indigo-200">
        <!-- Dynamic Background Effects -->
        <div class="absolute top-0 right-0 w-[40rem] h-[40rem] bg-white/10 rounded-full blur-[120px] -mr-64 -mt-64 animate-pulse-glow"></div>
        <div class="absolute bottom-0 left-0 w-[30rem] h-[30rem] bg-purple-400/20 rounded-full blur-[100px] -ml-48 -mb-48 animate-pulse-glow" style="animation-delay: -2s;"></div>
        <div class="relative z-10">
          <h2 class="font-headline text-5xl md:text-6xl font-black mb-8 tracking-tight">准备好迎接你的第一个<br/>顶级 Offer 了吗？</h2>
          <p class="text-xl text-indigo-100/90 mb-14 max-w-2xl mx-auto font-medium leading-relaxed">加入优秀计算机学子的选择，让你的职业起点更高、更稳、更远。</p>
          <button @click="navigateToCareerPaths" class="px-14 py-6 bg-white text-indigo-700 rounded-[2rem] font-black text-xl hover:bg-indigo-50 hover:-translate-y-1 active:scale-95 transition-all shadow-2xl shadow-black/20 flex items-center gap-4 mx-auto group">
            立即开启免费规划 <span class="material-symbols-outlined text-2xl group-hover:translate-x-2 transition-transform"></span>
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function navigateToCareerPaths() {
  router.push('/career-paths')
}

function navigateToCareerEvaluation() {
  // 先跳转到自我介绍页面，默认使用就业路径
  router.push('/career-paths/employment/self-introduction')
}

function navigateToCompanyReviews() {
  router.push('/company-reviews')
}

function navigateToInterview() {
  router.push('/interview')
}

function navigateToAI() {
  // 这里可以导航到AI聊天页面
  router.push('/ai-chat')
}

function handleImageError(event) {
  // 处理图片加载失败的情况
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyMCAyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIGZpbGw9IiNmNWY1ZjUiLz48cGF0aCBkPSJNMTAgMTVjLTIuNyAwLTUgMi4zLTUgNXMxLjY0IDMgMy4zNiAzYzEuNzIgMCAzLTIgMy00cy0xLjI4LTMtMy0zczMtMi4zIDMtNXoiIGZpbGw9IiM4ODgiLz48L3N2Zz4='
  event.target.alt = '图片加载失败'
}
</script>

<style scoped>
.editorial-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 2.5rem;
}

.soft-shadow {
  box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.15);
}

@keyframes float-hero {
  0%, 100% { transform: translateY(0) rotate(2deg); }
  50% { transform: translateY(-20px) rotate(4deg); }
}

.hero-img-animated {
  animation: float-hero 6s ease-in-out infinite;
}

.tech-glow-card:hover {
  box-shadow: 0 20px 40px -15px rgba(99, 102, 241, 0.3);
  border-color: rgba(99, 102, 241, 0.3);
  transform: translateY(-8px) scale(1.02);
}

.binary-blueprint-bg {
  background-image: radial-gradient(#6366f110 1px, transparent 1px);
  background-size: 30px 30px;
}

@keyframes loading {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(150%); }
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

.animate-pulse-glow {
  animation: pulse-glow 8s ease-in-out infinite;
}
</style>
