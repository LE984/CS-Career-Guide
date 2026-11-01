<template>
  <div class="bg-[#0f1115] text-white min-h-screen selection:bg-secondary selection:text-white">
    <main class="pt-32 pb-24 px-8 max-w-7xl mx-auto">
      <!-- Hero Header -->
      <header class="mb-20 text-center">
        <div class="inline-block px-4 py-1.5 mb-6 rounded-full border border-white/10 bg-white/5 text-[10px] font-bold uppercase tracking-[0.3em] text-slate-400">
          Professional Navigation System
        </div>
        <h1 class="text-6xl md:text-8xl font-extrabold tracking-tighter text-white mb-6">
          未来 <span class="text-transparent bg-clip-text bg-gradient-to-r from-secondary to-tertiary-fixed-dim">职业路径</span>
        </h1>
        <p class="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
          为计算机科学精英定制。通过多维度的路径分析与艺术化的资源呈现，助力你在数字浪潮中精准定位，构建巅峰职业蓝图。
        </p>
      </header>
      <!-- Poster Grid Layout -->
      <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
        <!-- Section 1: Employment (The Main Poster) -->
        <section class="md:col-span-12 relative h-[600px] rounded-[2rem] overflow-hidden group mb-6">
          <img alt="职业路径就业" class="absolute inset-0 w-full h-full object-cover scale-105 group-hover:scale-100 transition-transform duration-1000" src="../../assets/images/职业路径就业.png"/>
          <div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent"></div>
          <div class="absolute inset-0 bg-gradient-to-r from-black/80 via-transparent to-transparent"></div>
          <div class="relative z-10 h-full p-12 flex flex-col justify-end">
            <div class="flex items-center gap-3 mb-6">
              <span class="w-12 h-0.5 bg-secondary"></span>
              <span class="text-xs font-bold uppercase tracking-[0.4em] text-secondary">The Major Path</span>
            </div>
            <div class="relative mb-8">
              <div class="flex">
                <h2 class="text-7xl md:text-9xl font-black tracking-tighter leading-none mb-4 opacity-90">
                  互联网
                </h2>
                <h2 class="text-7xl md:text-9xl font-black tracking-tighter leading-none mb-4 opacity-90 text-gray-100">
                  就业
                </h2>
              </div>
              <div class="flex flex-wrap gap-4 text-sm font-bold uppercase tracking-widest text-slate-300">
                <span class="flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-green-400"></span> TOP TIER COMPANIES</span>
                <span class="flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-blue-400"></span> HIGH SALARY PACKAGES</span>
                <span class="flex items-center gap-2"><span class="w-1.5 h-1.5 rounded-full bg-purple-400"></span> TECH LEADERSHIP</span>
              </div>
            </div>
            <div class="flex flex-col md:flex-row md:items-end justify-between gap-8">
              <p class="max-w-xl text-slate-300 text-lg leading-relaxed">
                探索顶尖技术岗位的入职路径。从算法工程师到架构师，我们为您整理了行业最前沿的技能栈要求与职业成长阶梯。这里是开启职业生涯的第一步
              </p>
              <router-link to="/career-paths/employment/self-introduction" class="group relative overflow-hidden bg-secondary text-on-secondary px-12 py-5 rounded-xl font-headline font-bold text-lg shadow-[0_10px_30px_rgba(70,72,212,0.3)] hover:shadow-[0_15px_40px_rgba(70,72,212,0.4)] transition-all active:scale-95 flex items-center gap-3">
                <span class="material-symbols-outlined">Just do it</span>
                <span class="relative z-10 flex items-center gap-3">
                  开始"自我评价"评估
                </span>
                <div class="absolute inset-0 bg-gradient-to-r from-secondary to-secondary-container opacity-0 group-hover:opacity-100 transition-opacity"></div>
              </router-link>
            </div>
          </div>
          <!-- Overlay Value Props -->
          <div class="absolute top-12 right-12 text-right hidden lg:block">
            <div class="mb-4">
              <div class="text-4xl font-black">100+</div>
              <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Cooperating Enterprises</div>
            </div>
            <div>
              <div class="text-4xl font-black">98%</div>
              <div class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Match Accuracy</div>
            </div>
          </div>
        </section>
        <!-- Section 2: Civil Service -->
        <section class="md:col-span-6 lg:col-span-3 poster-card group relative h-[500px] rounded-[2rem] overflow-hidden bg-[#1a1c23] border border-white/5">
          <div class="inset-0 bg-gradient-to-br from-red-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div class="p-8 h-full flex flex-col">
            <div class="mb-auto">
              <div class="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mb-8 border border-red-500/20 overflow-hidden">
                <img src="@/assets/images/考公.png" alt="考公" class="w-full h-full object-cover"/>
              </div>
              <h3 class="text-xs font-bold uppercase tracking-[0.3em] text-red-500 mb-2">Governmental Service</h3>
              <h2 class="text-3xl font-extrabold text-gray-100 mb-4">考公板块</h2>
              <p class="text-slate-400 text-sm leading-relaxed mb-6">
                "Serve the People" — 解读计算机类专业在国家及地方公务员考试中的岗位分布与竞争态势。
              </p>
              <div class="flex flex-wrap gap-2">
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-red-500/20 hover:text-red-400 transition-colors cursor-pointer">招录简章</span>
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-red-500/20 hover:text-red-400 transition-colors cursor-pointer">历年分数线</span>
              </div>
            </div>
            <div class="mt-8 flex items-center justify-between">
              <span class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Learn More</span>
              <router-link to="/career-paths/civil_service" class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-red-500 transition-colors">
                <span class="material-symbols-outlined text-sm">click</span>
              </router-link>
            </div>
          </div>
        </section>
        <!-- Section 3: Graduate Entrance -->
        <section class="md:col-span-6 lg:col-span-3 poster-card group relative h-[500px] rounded-[2rem] overflow-hidden bg-[#1a1c23] border border-white/5">
          <div class="inset-0 bg-gradient-to-br from-blue-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div class="p-8 h-full flex flex-col">
            <div class="mb-auto">
              <div class="w-16 h-16 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-8 border border-blue-500/20 overflow-hidden">
                <img src="@/assets/images/考研.png" alt="考研" class="w-full h-full object-cover"/>
              </div>
              <h3 class="text-xs font-bold uppercase tracking-[0.3em] text-blue-500 mb-2">Master the Future</h3>
              <h2 class="text-3xl font-extrabold text-gray-100 mb-4">考研板块</h2>
              <p class="text-slate-400 text-sm leading-relaxed mb-6">
                深度解析CS学硕与专硕的研招趋势，提供院校专业排名与科研方向指南。
              </p>
              <div class="flex flex-wrap gap-2">
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-blue-500/20 hover:text-blue-400 transition-colors cursor-pointer">院校库</span>
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-blue-500/20 hover:text-blue-400 transition-colors cursor-pointer">导师导航</span>
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-blue-500/20 hover:text-blue-400 transition-colors cursor-pointer">真题库</span>
              </div>
            </div>
            <div class="mt-8 flex items-center justify-between">
              <span class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Learn More</span>
              <router-link to="/career-paths/postgraduate" class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-blue-500 transition-colors">
                <span class="material-symbols-outlined text-sm">click</span>
              </router-link>
            </div>
          </div>
        </section>
        <!-- Section 4: Military -->
        <section class="md:col-span-6 lg:col-span-3 poster-card group relative h-[500px] rounded-[2rem] overflow-hidden bg-[#1a1c23] border border-white/5">
          <div class="inset-0 bg-gradient-to-br from-green-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div class="p-8 h-full flex flex-col">
            <div class="mb-auto">
              <div class="w-16 h-16 rounded-2xl bg-green-500/10 flex items-center justify-center mb-8 border border-green-500/20 overflow-hidden">
                <img src="@/assets/images/入伍.png" alt="入伍" class="w-full h-full object-cover"/>
              </div>
              <h3 class="text-xs font-bold uppercase tracking-[0.3em] text-green-500 mb-2">Duty &amp; Honor</h3>
              <h2 class="text-3xl font-extrabold text-gray-100 mb-4">入伍板块</h2>
              <p class="text-slate-400 text-sm leading-relaxed mb-6">
                针对技术人才的强军计划，介绍计算机专业在国防现代化中的战略地位及入伍优待政策。
              </p>
              <div class="flex flex-wrap gap-2">
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-green-500/20 hover:text-green-400 transition-colors cursor-pointer">直招士官</span>
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-green-500/20 hover:text-green-400 transition-colors cursor-pointer">优待政策</span>
              </div>
            </div>
            <div class="mt-8 flex items-center justify-between">
              <span class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Learn More</span>
              <router-link to="/career-paths/military" class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-green-500 transition-colors">
                <span class="material-symbols-outlined text-sm">click</span>
              </router-link>
            </div>
          </div>
        </section>
        <!-- Section 5: Entrepreneurship -->
        <section class="md:col-span-6 lg:col-span-3 poster-card group relative h-[500px] rounded-[2rem] overflow-hidden bg-[#1a1c23] border border-white/5">
          <div class="inset-0 bg-gradient-to-br from-purple-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <div class="p-8 h-full flex flex-col">
            <div class="mb-auto">
              <div class="w-16 h-16 rounded-2xl bg-purple-500/10 flex items-center justify-center mb-8 border border-purple-500/20 overflow-hidden">
                <img src="@/assets/images/创业.png" alt="创业" class="w-full h-full object-cover"/>
              </div>
              <h3 class="text-xs font-bold uppercase tracking-[0.3em] text-purple-500 mb-2">Build The New</h3>
              <h2 class="text-3xl font-extrabold text-gray-100 mb-4">创业板块</h2>
              <p class="text-slate-400 text-sm leading-relaxed mb-6">
                对接科技创业孵化器，提供从项目打磨到投融资对接的专业资源，助力技术转化为商业价值。
              </p>
              <div class="flex flex-wrap gap-2">
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-purple-500/20 hover:text-purple-400 transition-colors cursor-pointer">融资指南</span>
                <span class="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold text-slate-400 hover:bg-purple-500/20 hover:text-purple-400 transition-colors cursor-pointer">办公空间</span>
              </div>
            </div>
            <div class="mt-8 flex items-center justify-between">
              <span class="text-[10px] font-bold uppercase tracking-widest text-slate-500">Learn More</span>
              <router-link to="/career-paths/entrepreneurship" class="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-purple-500 transition-colors">
                <span class="material-symbols-outlined text-sm">click</span>
              </router-link>
            </div>
          </div>
        </section>
      </div>
      <!-- Career Insights Callout -->
      <div class="mt-10 rounded-[2.5rem] p-12 relative overflow-hidden" style="background-image: url('../../assets/images/就业.png'); background-size: cover; background-position: center;">
        <div class="absolute inset-0 bg-black/10"></div>
        
        <div class="flex flex-col md:flex-row items-center gap-12 relative z-10">
          <div class="w-full md:w-1/3 aspect-video rounded-3xl overflow-hidden grayscale hover:grayscale-0 transition-all duration-700 shadow-2xl">
            <img alt="就业" class="w-full h-full object-cover" src="@/assets/images/就业.jpg"/>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-6">
              <span class="text-xs font-black uppercase tracking-[0.5em] text-white">Editor's Perspective</span>
            </div>
            <p class="text-2xl font-medium text-white leading-relaxed italic mb-8">
              "预测职业路径的最佳方式是亲手创造它。在代码与系统的世界里，每一行逻辑都是你职业大厦的基石。"
            </p>
            <div class="flex flex-wrap gap-4">
              <a href="https://www.ccf.org.cn/" target="_blank" class="flex justify-center items-center bg-white text-black px-8 py-3 rounded-full text-xs font-bold uppercase tracking-widest hover:bg-secondary hover:text-white transition-all inline-block text-center">
                阅读行业周报
              </a>
              <a href="https://www.ieee.org/" target="_blank" class="flex justify-center items-center text-white border border-white px-8 py-3 rounded-full text-xs font-bold uppercase tracking-widest flex items-center gap-2 hover:bg-white hover:text-black transition-all inline-flex">  
                查看更多建议
                <span class="material-symbols-outlined text-sm">north_east</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </main>
    <!-- Floating  -->    
    <footer class="border-t border-white/5 py-12 px-8">
      <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
        <span class="text-slate-500 text-xs font-bold uppercase tracking-widest">© 2026 CS Career Guide. Built for the next gen.</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()
</script>

<style scoped>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.glass-effect {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.text-glow {
  text-shadow: 0 0 20px rgba(255,255,255,0.4);
}

.poster-card {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.poster-card:hover {
  transform: translateY(-8px);
}
</style>
