<template>
  <div class="bg-gradient-to-r from-white to-purple-100 font-body text-on-surface min-h-screen">
    <main class="pt-24 pb-64">
      <!--Category Navigation -->
      <section class="max-w-7xl mx-auto px-8 mb-10">
        <div class="flex flex-col items-center justify-center gap-6">
          <div class="text-center">
            <h2 class="font-headline text-6xl font-extrabold text-on-background">全职业图谱</h2> 
            <p class="text-on-primary-container mt-2">深度解析核心领域，           选择您的目标岗位</p>
          </div>
        </div>
      </section>
      <!-- AI Recommendation Section -->
      <section class="max-w-7xl mx-auto px-8 mb-16">
        <div class="recommendation-gradient rounded-[2.5rem] p-10 editorial-shadow overflow-hidden relative">
          <div class="absolute top-0 right-0 w-1/3 h-full opacity-10 pointer-events-none">
            <svg class="w-full h-full fill-current text-secondary" viewbox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
              <circle cx="200" cy="200" fill="none" r="150" stroke="currentColor" stroke-width="2"></circle>
              <circle cx="200" cy="200" fill="none" r="100" stroke="currentColor" stroke-width="1"></circle>
            </svg>
          </div>
          <div class="relative z-10">
            <div class="flex items-center gap-3 mb-6">
              <span class="bg-secondary text-on-secondary px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">AI 定制推荐</span>
              <h2 class="text-white text-2xl font-bold font-headline">根据您的个人画像，以下方向最适合您</h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <!-- Dynamic Recommendations -->
              <div v-for="(rec, index) in recommendations" :key="index" class="bg-white/10 backdrop-blur-md border border-white/10 p-6 rounded-3xl group hover:bg-white/15 transition-all">
                <div class="flex justify-between items-start mb-4">
                  <div class="w-10 h-10 bg-secondary rounded-xl flex items-center justify-center text-white overflow-hidden">
                    <img src="../../assets/images/推荐1.png" alt="推荐1" class="w-full h-full object-cover"/>
                  </div>
                  <span class="text-secondary font-bold text-xl">{{ rec.matchScore }}% 匹配</span>
                </div>
                <h3 class="text-white text-xl font-bold mb-2">{{ rec.career }}</h3>
                <p class="text-slate-300 text-sm leading-relaxed mb-4">{{ rec.reason || '基于您的背景和技能推荐' }}</p>
              </div>
            </div>
            <!-- 大模型分析结果手风琴组件 -->
            <div class="mt-8">
              <div class="accordion">
                <div class="flex items-center justify-between">
                  <h3 class="text-white text-lg font-bold flex items-center gap-2">
                    大模型职业分析
                  </h3>
                  <span class="material-symbols-outlined text-white transition-transform cursor-pointer" :class="{ 'rotate-180': isAccordionOpen }" @click="toggleAccordion">
                    更多
                  </span>
                </div>
                <div v-if="isAccordionOpen" class="mt-4 bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 text-white">
                  <div v-if="careerAnalysis" class="space-y-4 markdown-content" v-html="renderedCareerAnalysis"></div>
                  <div v-else class="text-slate-400">
                    暂无分析结果，请先完成自我介绍。
                  </div>
                  <div></div>
                  
                  <div class="text-white text-xl text-left pt-4 mt-4">下一步：查看职业生涯规划报告</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- Major Categories Grid -->
      <section class="max-w-7xl mx-auto px-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <!-- 1. Backend -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">后端开发</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Java</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">C++</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">PHP</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Golang</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Python</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Node.js</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Rust</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">C#工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">全栈开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">安全工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">游戏后端</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">游戏前端</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon"> ✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">区块链</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">信息技术岗</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">.NET</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Delphi</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">GIS工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">VB</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Perl</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Ruby</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Erlang</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">后端工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">语音视频图形开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 2. AI -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">人工智能</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">算法工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">深度学习</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">自然语言处理</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">机器学习</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">计算机视觉</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">语音识别</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">推荐算法</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">数据挖掘</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 3. Frontend -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">前端开发</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Web前端</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">前端工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">游戏前端</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">游戏前端</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">H5开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">React/Vue</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">小程序开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 4. Client -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">客户端开发</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">安卓 (Android)</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">iOS开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Flutter开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">Unity3D</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">游戏客户端</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 5. Data -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">数据</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">数据分析师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">大数据开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">数据仓库 (ETL)</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">数据架构师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 6. DevOps -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">运维</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">运维工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">网络工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">安全运维</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">SRE 工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">DBA (数据库管理)</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 7. Testing -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">测试</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">测试工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">自动化测试</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">性能测试</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">测试开发 (TestDev)</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 8. R&D -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">研发工程师</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">嵌入式软件开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">嵌入式硬件开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">固件开发</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">FPGA/芯片设计</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
          <!-- 9. Tech Support -->
          <div class="bg-white p-6 rounded-3xl border border-slate-200/60 shadow-lg flex flex-col h-[400px]">
            <div class="flex items-center gap-3 mb-5 flex-shrink-0">
              <div class="w-10 h-10 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center overflow-hidden">
                <img src="../../assets/images/职业大类.png" alt="职业大类" class="w-full h-full object-cover"/>
              </div>
              <h3 class="font-headline text-xl font-bold">销售技术支持</h3>
            </div>
            <div class="space-y-1.5 overflow-y-auto role-scroll pr-2 flex-grow">
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">售前技术工程师</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">客户成功</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">售后技术支持</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
              <button class="role-item w-full p-3 bg-slate-50 rounded-xl flex items-center justify-between border border-transparent transition-all hover:bg-indigo-50 group" @click="toggleSelection($event)">
                <span class="font-medium text-sm">技术支持经理</span>
                <span class="material-symbols-outlined text-indigo-600 text-sm hidden check-icon">✓</span>
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
    <!-- Selection Summary Bar -->
    <div class="fixed bottom-6 left-1/2 -translate-x-1/2 w-[calc(100%-8rem)] max-w-4xl z-50 bg-indigo-600/95 dark:bg-indigo-900/95 backdrop-blur-2xl border border-white/20 rounded-3xl shadow-2xl p-5 editorial-shadow">
      <div class="flex flex-col md:flex-row items-center justify-between gap-5">
        <div class="flex items-center gap-5 w-full md:w-auto min-w-0">
          <div class="flex items-center gap-3 whitespace-nowrap text-white">
            <span class="font-bold text-lg tracking-tight">选择目标岗位，查看职业生涯规划报告</span>
          </div>
          <div class="flex-grow flex gap-3 overflow-x-auto py-1 no-scrollbar items-center">
            <!-- Dynamic Selection Labels -->
            <div class="flex gap-2" v-if="selectedCareers.length > 0">
              <span v-for="career in selectedCareers" :key="career" class="bg-white/20 text-white backdrop-blur-sm px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2 border border-white/30 shadow-sm whitespace-nowrap">
                {{ career }} <span class="material-symbols-outlined text-sm cursor-pointer hover:bg-white/20 rounded-full" @click="removeSelection(career)">✓</span>
              </span>
            </div>
            <span v-else class="text-indigo-100/60 text-sm italic ml-2 shrink-0">点击卡片选择职业...</span>
          </div>
        </div>
        <button @click="goToCareerPlan" class="w-full md:w-auto px-10 py-4 bg-white text-indigo-600 rounded-2xl font-black text-base hover:bg-indigo-50 transition-all flex items-center justify-center gap-1 shadow-xl transform active:scale-95 whitespace-nowrap">
          生成职业规划报告
          <span class="material-symbols-outlined text-sm">launch</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'

const router = useRouter()
const recommendations = ref([])
const isAccordionOpen = ref(false)
const careerAnalysis = ref(null)
const selectedCareers = ref([]) 
// 将职业分析数据转换为Markdown格式
const careerAnalysisMarkdown = computed(() => {
  if (!careerAnalysis.value) return ''
  
  let markdown = ''
  
  // 总体职业分析
  markdown += `# 总体职业分析

${careerAnalysis.value.overall}

`
  
  // 三个职业分析
  markdown += `# 职业推荐分析

`
  
  careerAnalysis.value.careers.forEach((career, index) => {
    markdown += `## ${index + 1}. ${career.title}

`
    
    // 匹配度（支持数字和字符串格式）
    if (career.matchScore) {
      const matchScoreStr = typeof career.matchScore === 'number' ? `${career.matchScore}%` : career.matchScore
      markdown += `- **匹配度**：${matchScoreStr}

`
    }
    
    // 推荐理由
    markdown += `### 推荐理由
`
    if (career.reasons && career.reasons.length > 0) {
      career.reasons.forEach(reason => {
        markdown += `- ${reason}
`
      })
    } else if (career.reason) {
      markdown += `- ${career.reason}
`
    } else {
      markdown += `- 暂无推荐理由
`
    }
    markdown += `
`
    
    // 技能匹配
    markdown += `### 技能匹配
`
    if (career.skills && career.skills.length > 0) {
      career.skills.forEach(skill => {
        markdown += `- ${skill}
`
      })
    } else if (career.skillsMatch && career.skillsMatch.length > 0) {
      career.skillsMatch.forEach(skill => {
        markdown += `- ${skill}
`
      })
    } else {
      markdown += `- 暂无技能匹配数据
`
    }
    markdown += `
`
    
    // 当前最大短板（新字段）
    if (career.weakestPoint) {
      markdown += `### 当前最大短板

${career.weakestPoint}

`
    }
    
    // 市场热度（新字段）
    if (career.marketDemand) {
      markdown += `### 市场热度

${career.marketDemand}

`
    }
    
    // 起薪范围（新字段）
    if (career.salaryRange) {
      markdown += `### 起薪范围

${career.salaryRange}

`
    }
    
    // 下一步建议（新字段，支持数组和字符串格式）
    if (career.nextStep) {
      markdown += `### 下一步建议
`
      if (Array.isArray(career.nextStep)) {
        career.nextStep.forEach((step, stepIndex) => {
          markdown += `${stepIndex + 1}. ${step}
`
        })
      } else {
        markdown += `${career.nextStep}
`
      }
      markdown += `
`
    } else if (career.suggestions && career.suggestions.length > 0) {
      markdown += `### 发展建议
`
      career.suggestions.forEach(suggestion => {
        markdown += `- ${suggestion}
`
      })
      markdown += `
`
    } else if (career.improvement) {
      markdown += `### 发展建议

${career.improvement}

`
    }
  })
  
  return markdown
})

// 渲染Markdown为HTML
const renderedCareerAnalysis = computed(() => {
  return marked(careerAnalysisMarkdown.value)
})

// 从大模型分析结果加载推荐数据
function loadRecommendations() {
  try {
    // 优先从localStorage读取cards数据（包含正确的matchScore和reason）
    const careerRecommendationsStr = localStorage.getItem('careerRecommendations')
    if (careerRecommendationsStr) {
      const careerRecommendations = JSON.parse(careerRecommendationsStr)
      console.log('Loaded careerRecommendations:', careerRecommendations)
      if (Array.isArray(careerRecommendations) && careerRecommendations.length > 0) {
        recommendations.value = careerRecommendations.map(rec => ({
          career: rec.career || rec.职业,
          matchScore: rec.matchScore || rec.匹配度,
          reason: rec.reason || rec.推荐理由 || '基于您的背景和技能推荐'
        }))
        console.log('Loaded recommendations from careerRecommendations:', recommendations.value)
        return
      }
    }
    
    // 如果没有cards数据，尝试从careerAnalysis中获取（用于手风琴展示的详细数据）
    if (careerAnalysis.value && careerAnalysis.value.careers) {
      recommendations.value = careerAnalysis.value.careers.map(career => ({
        career: career.title,
        matchScore: career.matchScore || (career.marketDemand === '高' ? 85 : career.marketDemand === '中高' ? 75 : 65),
        reason: career.reasons[0] || '基于您的背景和技能推荐'
      }))
      console.log('Loaded recommendations from career analysis:', recommendations.value)
    } else {
      // 使用默认推荐数据
      recommendations.value = [
        {
          career: "Python",
          matchScore: 92,
          reason: "用户熟练掌握Python开发，并具备Git、计算机网络、数据结构等后端核心基础，且已完成两个大模型应用项目，高度契合Python后端岗位需求。"
        },
        {
          career: "自然语言处理",
          matchScore: 88,
          reason: "用户具备大模型应用项目实战经验，叠加Python、线性代数、离散数学和英文阅读能力，构成NLP工程师的核心能力三角。"
        },
        {
          career: "大数据开发工程师",
          matchScore: 85,
          reason: "用户Python与数据结构基础扎实，大模型项目隐含ETL与批处理经验，线性代数支撑特征工程，符合大数据开发岗位技术画像。"
        }
      ]
      console.log('Using default recommendations:', recommendations.value)
    }
  } catch (error) {
    console.error('Failed to load recommendations:', error)
  }
}

// 从localStorage加载大模型分析结果
function loadCareerAnalysis() {
  try {
    // 从localStorage读取大模型分析结果
    const careerAnalysisStr = localStorage.getItem('careerAnalysis')
    if (careerAnalysisStr) {
      careerAnalysis.value = JSON.parse(careerAnalysisStr)
      console.log('Loaded career analysis from localStorage:', careerAnalysis.value)
    } else {
      // 尝试读取职业推荐数据
      const careerRecommendationsStr = localStorage.getItem('careerRecommendations')
      if (careerRecommendationsStr) {
        const careerRecommendations = JSON.parse(careerRecommendationsStr)
        console.log('Loaded careerRecommendations for analysis:', careerRecommendations)
        // 解析职业推荐数据，提取职业分析数据
        if (Array.isArray(careerRecommendations)) {
          careerAnalysis.value = {
            overall: '基于您的技能和背景，我们为您推荐以下职业方向。您具备扎实的计算机基础素养和良好的工程实践潜力，在Python后端开发、人工智能（特别是自然语言处理方向）、数据相关开发（如大数据开发/数据工程师）三大路径上具有高度适配性和快速成长潜力。',
            careers: careerRecommendations.map((rec, index) => ({
              title: rec.career || rec.职业,
              matchScore: `${rec.matchScore || rec.匹配度}%`,
              reasons: [rec.reason || rec.推荐理由 || '基于您的背景和技能推荐'],
              skills: rec.skillsMatch || rec.技能匹配 || [],
              suggestions: [rec.improvement || rec.发展建议 || '根据您的技能和背景，建议您进一步提升相关技能。']
            })),
            actionPlan: {
              short: '完成1个FastAPI+PostgreSQL+Vue的AI工具后台，部署至云服务器；同步整理NLP项目技术文档，发布至GitHub并撰写技术复盘博客。',
              medium: '使用PySpark重写项目中的数据预处理模块，对比Pandas性能差异；在Hugging Face Model Hub复现1个开源NLP模型，完成本地微调+API封装。',
              long: '精修简历，按三个方向定制版本；参加技术面试模拟；主动联系本地科技企业实习内推，发挥地域+Python+NLP复合优势。'
            }
          }
          console.log('Loaded career analysis from careerRecommendations:', careerAnalysis.value)
        } else {
          careerAnalysis.value = null
          console.log('No recommendations found in careerRecommendations')
        }
      } else {
        careerAnalysis.value = null
        console.log('No career analysis found in localStorage')
      }
    }
  } catch (error) {
    console.error('Failed to load career analysis:', error)
    careerAnalysis.value = null
  }
}

// 切换手风琴状态
function toggleAccordion() {
  isAccordionOpen.value = !isAccordionOpen.value
}

// 根据职业类型返回对应的图标
function getIconForCareer(career) {
  const careerLower = career.toLowerCase()
  if (careerLower.includes('后端') || careerLower.includes('java') || careerLower.includes('go') || careerLower.includes('python') || careerLower.includes('c++')) {
    return 'database'
  } else if (careerLower.includes('ai') || careerLower.includes('算法') || careerLower.includes('机器学习') || careerLower.includes('深度学习') || careerLower.includes('人工智能')) {
    return 'smart_toy'
  } else if (careerLower.includes('前端') || careerLower.includes('web') || careerLower.includes('react') || careerLower.includes('vue')) {
    return 'web'
  } else if (careerLower.includes('移动') || careerLower.includes('android') || careerLower.includes('ios') || careerLower.includes('flutter')) {
    return 'smartphone'
  } else if (careerLower.includes('数据') || careerLower.includes('分析') || careerLower.includes('大数据')) {
    return 'analytics'
  } else if (careerLower.includes('运维') || careerLower.includes('devops') || careerLower.includes('sre') || careerLower.includes('云')) {
    return 'cloud_sync'
  } else if (careerLower.includes('测试') || careerLower.includes('qa')) {
    return 'bug_report'
  } else if (careerLower.includes('嵌入式') || careerLower.includes('硬件') || careerLower.includes('芯片')) {
    return 'settings_input_component'
  } else if (careerLower.includes('销售') || careerLower.includes('支持') || careerLower.includes('客户')) {
    return 'support_agent'
  } else if (careerLower.includes('安全')) {
    return 'security'
  } else {
    return 'work'
  }
}

// 切换选择状态（单选模式）
function toggleSelection(event) {
  const button = event.currentTarget
  const careerName = button.querySelector('span:first-child').textContent.trim()
  
  if (button.classList.contains('selected')) {
    // 取消选择
    button.classList.remove('selected')
    const checkIcon = button.querySelector('.check-icon')
    if (checkIcon) {
      checkIcon.classList.add('hidden')
    }
    // 从数组中移除
    const index = selectedCareers.value.indexOf(careerName)
    if (index > -1) {
      selectedCareers.value.splice(index, 1)
    }
  } else {
    // 单选模式：先取消所有已选中的职业
    if (selectedCareers.value.length > 0) {
      const buttons = document.querySelectorAll('.role-item')
      buttons.forEach(btn => {
        const btnCareerName = btn.querySelector('span:first-child').textContent.trim()
        if (btn.classList.contains('selected') && btnCareerName !== careerName) {
          btn.classList.remove('selected')
          const checkIcon = btn.querySelector('.check-icon')
          if (checkIcon) {
            checkIcon.classList.add('hidden')
          }
        }
      })
      // 清空数组
      selectedCareers.value = []
    }
    
    // 选择新职业
    button.classList.add('selected')
    const checkIcon = button.querySelector('.check-icon')
    if (checkIcon) {
      checkIcon.classList.remove('hidden')
    }
    // 添加到数组
    selectedCareers.value.push(careerName)
  }
  
  console.log('Selected careers:', selectedCareers.value)
}

// 移除选择
function removeSelection(itemName) {
  // 从数组中移除
  const index = selectedCareers.value.indexOf(itemName)
  if (index > -1) {
    selectedCareers.value.splice(index, 1)
  }
  
  // 更新按钮状态
  const buttons = document.querySelectorAll('.role-item')
  buttons.forEach(button => {
    const careerName = button.querySelector('span:first-child').textContent.trim()
    if (careerName === itemName) {
      button.classList.remove('selected')
      const checkIcon = button.querySelector('.check-icon')
      if (checkIcon) {
        checkIcon.classList.add('hidden')
      }
    }
  })
  
  console.log('Removed selection:', itemName)
  console.log('Selected careers:', selectedCareers.value)
}

// 跳转到职业规划页面
function goToCareerPlan() {
  // 保存选择的职业到 localStorage 缓存中
  localStorage.setItem('selectedCareers', JSON.stringify(selectedCareers.value))
  
  // 跳转到职业规划页面
  router.push('/career-plan')
}

onMounted(() => {
  // 页面加载时的初始化逻辑
  loadCareerAnalysis()
  loadRecommendations()
})

onUnmounted(() => {
  // 页面卸载时的清理逻辑
})
</script>

<style scoped>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.glass-effect {
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.editorial-shadow {
  box-shadow: 0 20px 40px rgba(25, 28, 30, 0.06);
}

.strong-shadow {
  box-shadow: 0 10px 30px -5px rgba(70, 72, 212, 0.2), 0 8px 10px -6px rgba(70, 72, 212, 0.1);
}

.recommendation-gradient {
  background: linear-gradient(135deg, #111c2d 0%, #2d3133 100%);
}

.role-scroll::-webkit-scrollbar {
  width: 4px;
}

.role-scroll::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 10px;
}

.role-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

.role-scroll::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.role-item.selected {
  background-color: rgba(70, 72, 212, 0.1);
  border-color: #4648d4;
  color: #4648d4;
}

.role-item.selected .check-icon {
  display: block;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.rotate-180 {
  transform: rotate(180deg);
  transition: transform 0.3s ease;
}

.accordion {
  transition: all 0.3s ease;
}

/* Markdown内容样式 */
.markdown-content {
  line-height: 1.6;
  color: #93c5fd;
}

/* 使用深度选择器确保样式应用到v-html渲染的内容 */
.markdown-content ::v-deep h1 {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
  color: #38bdf8 !important;
}

.markdown-content ::v-deep h2 {
  font-size: 1.25rem;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: #38bdf8 !important;
}

.markdown-content ::v-deep h3 {
  font-size: 1.1rem;
  font-weight: bold;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  color: #38bdf8 !important;
}

.markdown-content ::v-deep p {
  margin-bottom: 1rem;
  color: #93c5fd !important;
}

.markdown-content ::v-deep ul {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.markdown-content ::v-deep li {
  margin-bottom: 0.5rem;
  color: #93c5fd !important;
}

.markdown-content ::v-deep strong {
  color: #38bdf8 !important;
  font-weight: bold;
}

.markdown-content ::v-deep a {
  color: #60a5fa !important;
  text-decoration: underline;
}

.markdown-content ::v-deep a:hover {
  color: #3b82f6 !important;
}

/* 确保所有Markdown内容都使用浅色 */
.markdown-content ::v-deep * {
  color: #93c5fd !important;
}

.markdown-content ::v-deep h1,
.markdown-content ::v-deep h2,
.markdown-content ::v-deep h3,
.markdown-content ::v-deep h4,
.markdown-content ::v-deep h5,
.markdown-content ::v-deep h6 {
  color: #38bdf8 !important;
}

.markdown-content ::v-deep strong {
  color: #38bdf8 !important;
}
</style>
