<template>
  <div class="font-body text-on-surface antialiased min-h-screen bg-gradient-to-r from-white to-purple-100">
    <main class="pt-32 pb-24 px-6 max-w-5xl mx-auto">
    <!-- Header Section -->
    <header class="mb-16">
    <h1 class="font-headline text-5xl font-extrabold tracking-tight text-primary mb-4">填写个人自述</h1>
    <p class="text-on-primary-container text-lg max-w-2xl leading-relaxed">
                    通过多维度的自我评估，我们将为您构建精准的职业画像，助力您在计算机科学领域发现最适合的发展路径。
                </p>
    </header>
    <form class="space-y-12">
    <!-- Section 1: Basic Information (Bento Style) -->
    <section class="grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-100 rounded-xl">
      <div class="md:col-span-2 bg-surface-container-lowest p-8 rounded-xl tonal-shift hover:shadow-sm">
        <h2 class="text-label-md font-bold uppercase tracking-widest text-secondary mb-6 flex items-center gap-2">
          <span class="material-symbols-outlined text-sm">person</span> 基本信息
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="block text-sm font-medium text-on-surface-variant">姓名</label>
            <input class="w-full bg-surface-container-low border-none focus:ring-0 focus:border-b-2 focus:border-secondary transition-all p-3 rounded-lg placeholder:text-outline-variant" placeholder="请输入您的真实姓名" type="text" v-model="formData.name"/>
          </div>
          <div class="space-y-1">
            <label class="block text-sm font-medium text-on-surface-variant">就读学校</label>
            <input class="w-full bg-surface-container-low border-none focus:ring-0 focus:border-b-2 focus:border-secondary transition-all p-3 rounded-lg placeholder:text-outline-variant" placeholder="例如：长沙理工大学" type="text" v-model="formData.school"/>
          </div>
          <div class="space-y-1">
            <label class="block text-sm font-medium text-on-surface-variant">专业</label>
            <input class="w-full bg-surface-container-low border-none focus:ring-0 focus:border-b-2 focus:border-secondary transition-all p-3 rounded-lg placeholder:text-outline-variant" placeholder="例如：计算机科学与技术" type="text" v-model="formData.major"/>
          </div>
          <div class="space-y-1">
            <label class="block text-sm font-medium text-on-surface-variant">年级</label>
            <input class="w-full bg-surface-container-low border-none focus:ring-0 focus:border-b-2 focus:border-secondary transition-all p-3 rounded-lg placeholder:text-outline-variant" placeholder="例如：大三" type="text" v-model="formData.grade"/>
          </div>
        </div>
      </div>
      <div class="bg-surface-container-lowest p-8 rounded-xl tonal-shift flex flex-col justify-center">
        <label class="block text-sm font-medium text-on-surface-variant mb-6">性别</label>
        <div class="flex gap-4">
          <label class="flex-1 cursor-pointer group">
            <input class="hidden peer" name="gender" type="radio" v-model="formData.gender" value="男"/>
            <div class="text-center py-4 rounded-xl border border-transparent bg-surface-container-low peer-checked:bg-secondary peer-checked:text-on-secondary transition-all group-hover:bg-primary-fixed">
                男
            </div>
          </label>
          <label class="flex-1 cursor-pointer group">
            <input class="hidden peer" name="gender" type="radio" v-model="formData.gender" value="女"/>
            <div class="text-center py-4 rounded-xl border border-transparent bg-surface-container-low peer-checked:bg-secondary peer-checked:text-on-secondary transition-all group-hover:bg-primary-fixed">
                女
            </div>
          </label>
        </div>
      </div>
    </section>
    <!-- Section 2: Skill Matrix -->
    <section class="bg-surface-container-low p-8 md:p-12 rounded-xl bg-slate-100">
      <h2 class="font-headline text-2xl font-bold mb-8 text-primary">技能模块评估</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
      <!-- Tech Skills -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-on-primary-container flex items-center gap-2">
          技术技能
        </h3>
        <div class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'Python 开发'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">Python 开发</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'PostgreSQL 数据库'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">PostgreSQL 数据库</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'RESTfulAPI设计'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">RESTfulAPI设计</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'并发 / 异步编程'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">并发 / 异步编程</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'Linux 使用与脚本'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">Linux 使用与脚本</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'Git / 版本管理'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">Git / 版本管理</span>
          </label>
        </div>
      </div>
      <!-- Data Science -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-on-primary-container flex items-center gap-2">
          数据科学
        </h3>
        <div class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'数据分析'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">数据分析(Pandas)</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'机器学习'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">机器学习(有无监督)</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'深度学习框架'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">深度学习框架</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'NLP'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">NLP(LLM)</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'CV(图像处理)'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">CV(图像处理)</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'数据可视化(Plotly)'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">数据可视化(Plotly)</span>
          </label>
        </div>
      </div>
      <!-- Core Skills -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-on-primary-container flex items-center gap-2">
          基础技能
        </h3>
        <div class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'基本电脑操作'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">电脑操作基础系统使用</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'效率管理'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">Office文档与数据处理</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'效率管理工具:任务管理'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">效率管理工具:任务管理</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'英文资料阅读能力'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">英文资料阅读能力</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'安全意识意识'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">安全意识</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'学习与问题解决能力'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">学习与问题拆解能力</span>
          </label>
        </div>
      </div>
      <!-- Academic Knowledge -->
      <div class="space-y-4">
        <h3 class="text-sm font-bold text-on-primary-container flex items-center gap-2">
          专业知识
        </h3>
        <div class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'线性代数与矩阵运算'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">线性代数</span>
          </label>                    
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'概率论与统计推断'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">概率论</span>
          </label>
          <!-- Remaining 6 for total of 18 (Distributed for layout balance) -->
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'离散数学'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">离散数学</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'数据结构'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">数据结构</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'算法设计'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">算法设计</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer group">
            <input class="w-5 h-5 rounded border-outline-variant text-secondary focus:ring-secondary/20" type="checkbox" v-model="formData.skills" :value="'计算机网络'"/>
            <span class="text-on-surface-variant group-hover:text-primary transition-colors">计算机网络</span>
          </label>
        </div>
      </div>
      </div>
    </section>
    <!-- Section 3: Subjective Self-Description -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-8 bg-slate-100 rounded-xl">
    <div class="space-y-8">
    <div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm">
    <label class="block text-sm font-bold text-on-primary-container mb-4 flex items-center gap-2">
      其他技能或项目经历
    </label>
    <textarea class="w-full bg-surface-container-low border-none focus:ring-2 focus:ring-secondary/10 rounded-xl p-4 text-on-surface resize-none" placeholder="请描述您掌握的其他技能，如：Docker, AWS, 特定项目经验等..." rows="7" v-model="formData.otherSkills"></textarea>
    </div>
    <div class="bg-surface-container-lowest  pb-8 px-8 rounded-xl shadow-sm">
    <label class="block text-sm font-bold text-on-primary-container mb-4 flex items-center gap-2">
      目标职业
    </label>
    <input class="w-full bg-surface-container-low border-none focus:ring-0 focus:border-b-2 focus:border-secondary transition-all p-4 rounded-xl placeholder:text-outline-variant" placeholder="例如：全栈工程师 / 算法科学家" type="text" v-model="formData.goal"/>
    </div>
    </div>
    <div class="bg-surface-container-lowest p-8 rounded-xl shadow-sm flex flex-col">
    <label class="block text-sm font-bold text-on-primary-container mb-4 flex items-center gap-2">
      条件自述
    </label>
    <textarea class="w-full flex-grow bg-surface-container-low border-none focus:ring-2 focus:ring-secondary/10 rounded-xl p-4 text-on-surface resize-none" placeholder="请描述您的用户性格、学习能力、职业偏好等。这有助于我们为您推荐更符合个人特质的发展方向..." rows="10" v-model="formData.selfDescription"></textarea>
    </div>
    </section>
    <!-- Action Section -->
    <footer class="flex justify-center pt-4">
      <button class="group relative overflow-hidden bg-secondary text-on-secondary px-12 py-5 rounded-xl font-headline font-bold text-lg shadow-[0_10px_30px_rgba(70,72,212,0.3)] hover:shadow-[0_15px_40px_rgba(70,72,212,0.4)] transition-all active:scale-95" type="submit" @click="nextToAssessment" :disabled="loading">
        <span class="relative z-10 flex items-center gap-3">
          {{ loading ? '保存中...' : '下一步：开始测评' }}         
        </span>
        <div class="absolute inset-0 bg-gradient-to-r from-secondary to-secondary-container opacity-0 group-hover:opacity-100 transition-opacity"></div>
      </button>
    </footer>
    </form>
    </main>
    <!-- Decorative Sidebar Element -->
      <aside class="hidden xl:block fixed right-12 top-1/2 -translate-y-1/2 w-64 space-y-6">
      <div class="bg-primary-container p-6 rounded-2xl border border-outline-variant/10">
        <h4 class="text-tertiary-fixed font-headline font-bold mb-3 flex items-center gap-2">
          Tips:
        </h4>
        <p class="text-on-primary-container text-xs leading-relaxed">
          您的自我介绍将帮助我们构建精准的职业画像。请尽量详尽地描述您的技能、经验与职业目标，AI将基于此为您推荐最匹配的岗位。
        </p>
      </div>
      <div class="relative h-48 rounded-2xl overflow-hidden group">

        <img class="absolute inset-0 w-full h-full  transition-all duration-700" data-alt="Modern high-tech workspace with multiple monitors displaying code and clean minimalist desk at sunset with warm ambient lighting" src="@/assets/images/自我介绍.png"/>
        <div class="absolute inset-0 bg-secondary/20 mix-blend-multiply"></div>
          <div class="absolute bottom-4 left-4 text-on-secondary">
          <p class="text-[10px] uppercase tracking-widest font-bold opacity-80">Tech Career</p>
          <p class="font-headline font-black">NAVIGATOR</p>
          </div>  
      </div>
      </aside>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api, { aiAPI, userAPI } from '@/api'

const router = useRouter()
const loading = ref(false)
const error = ref('')

// 从localStorage加载数据，如果没有则使用默认值
const loadFormData = () => {
  try {
    const savedData = localStorage.getItem('selfIntroduction')
    if (savedData) {
      const parsedData = JSON.parse(savedData)
      // 确保所有必要的字段都存在
      return {
        name: parsedData.name || '',
        school: parsedData.school || '',
        major: parsedData.major || '',
        grade: parsedData.grade || '',
        gender: parsedData.gender || '',
        skills: Array.isArray(parsedData.skills) ? parsedData.skills : [],
        otherSkills: parsedData.otherSkills || '',
        selfDescription: parsedData.selfDescription || '',
        goal: parsedData.goal || ''
      }
    }
  } catch (error) {
  }
  // 返回默认值
  return {
    name: '',
    school: '',
    major: '',
    grade: '',
    gender: '',
    skills: [],
    otherSkills: '',
    selfDescription: '',
    goal: ''
  }
}

const formData = ref(loadFormData())

// 页面加载时从localStorage恢复数据
onMounted(() => {
  formData.value = loadFormData()
})



// 生成自我介绍内容的哈希值，用于缓存键
function generateCacheKey(selfIntroductionText) {
  let hash = 0
  for (let i = 0; i < selfIntroductionText.length; i++) {
    const char = selfIntroductionText.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return 'career_rec_cache_' + Math.abs(hash).toString(36)
}

// 检查是否有有效的缓存
function getCachedRecommendation(selfIntroductionText) {
  try {
    const cacheKey = generateCacheKey(selfIntroductionText)
    const cachedData = localStorage.getItem(cacheKey)
    
    if (cachedData) {
      const parsed = JSON.parse(cachedData)
      // 检查缓存是否过期（有效期24小时）
      const now = Date.now()
      if (parsed.expireTime && parsed.expireTime > now) {
        return parsed.data
      } else {
        localStorage.removeItem(cacheKey)
      }
    }
  } catch (error) {
  }
  return null
}

// 保存缓存
function setCachedRecommendation(selfIntroductionText, data) {
  try {
    const cacheKey = generateCacheKey(selfIntroductionText)
    const expireTime = Date.now() + (24 * 60 * 60 * 1000) // 24小时
    
    const cacheData = {
      data: data,
      expireTime: expireTime,
      cachedAt: Date.now()
    }
    
    localStorage.setItem(cacheKey, JSON.stringify(cacheData))
  } catch (error) {
  }
}

async function nextToAssessment() {
  loading.value = true
  error.value = ''
  try {
    // 保存自我介绍到localStorage
    localStorage.setItem('selfIntroduction', JSON.stringify(formData.value))
    
    const userData = {
      name: formData.value.name || '',
      gender: formData.value.gender || '',
      school: formData.value.school || '',
      major: formData.value.major || '',
      grade: formData.value.grade || '',
      skills: formData.value.skills.join(',') || '',
      other_skills: formData.value.otherSkills || '',
      self_introduction: formData.value.selfDescription || '',
      career_goal: formData.value.goal || ''
    }
    
    await userAPI.updateProfile(userData)

    // 构建用户自我介绍文本（包含专业和年级信息，供大模型识别）
    const selfIntroductionText = `姓名: ${formData.value.name || ''}\n学校: ${formData.value.school || ''}\n专业: ${formData.value.major || ''}\n年级: ${formData.value.grade || ''}\n性别: ${formData.value.gender || ''}\n技能: ${formData.value.skills.join('、') || '无'}\n其他技能: ${formData.value.otherSkills || '无'}\n条件自述: ${formData.value.selfDescription || '无'}\n职业期望: ${formData.value.goal || '无'}`
    

    
    // ========== 检查缓存 ==========
    const cachedData = getCachedRecommendation(selfIntroductionText)
    
    if (cachedData) {
      // 使用缓存结果（瞬间显示）
      const recommendations = cachedData.recommendations
      
      // 存储推荐结果到localStorage
      localStorage.setItem('careerRecommendations', JSON.stringify(recommendations))
      
      // 存储原始分析
      if (cachedData.raw_analysis) {
        localStorage.setItem('careerRecommendationRaw', cachedData.raw_analysis)
      }
      
      // 存储会话ID
      if (cachedData.session_id) {
        localStorage.setItem('careerRecommendationSessionId', cachedData.session_id)
      }
      
      // 跳转到测评页面
      loading.value = false
      router.push('/career-evaluation')
      return
    }
    
    // ========== 没有缓存，调用API ==========
    
    try {
      // 使用aiAPI.careerRecommendation方法
      const responseData = await aiAPI.careerRecommendation(selfIntroductionText)
      
      if (!responseData.success) {
        error.value = `职业推荐失败: ${responseData.error}`
        loading.value = false
        return
      }
      
      // 解析后端返回的推荐结果（支持新旧两种格式）
      let cards = []
      let accordion = null
      
      // 新格式：包含 cards 和 accordion
      if (responseData.cards && Array.isArray(responseData.cards)) {
        cards = responseData.cards
        accordion = responseData.accordion || null
      } else if (responseData.recommendations && Array.isArray(responseData.recommendations)) {
        // 旧格式：兼容之前的 recommendations 数组（同时支持accordion字段）
        cards = responseData.recommendations.map(rec => ({
          career: rec.career,
          matchScore: rec.matchScore,
          reason: rec.reason
        }))
        accordion = responseData.accordion || null
      } else {
        error.value = '推荐结果格式错误'
        loading.value = false
        return
      }
      
      // 验证推荐结果格式
      if (!Array.isArray(cards) || cards.length === 0) {
        error.value = '推荐结果为空或格式错误'
        loading.value = false
        return
      }
      
      // 存储卡片数据到localStorage（用于卡片展示）
      localStorage.setItem('careerRecommendations', JSON.stringify(cards))
      
      // 存储手风琴数据到localStorage（用于详细分析展示）
      if (accordion) {
        localStorage.setItem('careerAnalysis', JSON.stringify(accordion))
      }
      
      // 存储大模型的原始响应到localStorage
      if (responseData.raw_analysis) {
        localStorage.setItem('careerRecommendationRaw', responseData.raw_analysis)
      } else if (responseData.recommendations) {
        localStorage.setItem('careerRecommendationRaw', JSON.stringify(responseData.recommendations))
      } else {
        localStorage.setItem('careerRecommendationRaw', '')
      }
      
      // 存储会话ID到localStorage
      if (responseData.session_id) {
        localStorage.setItem('careerRecommendationSessionId', responseData.session_id)
      }
      
      // ========== 保存到缓存 ==========
      const cacheData = {
        recommendations: cards,
        raw_analysis: responseData.raw_analysis || '',
        session_id: responseData.session_id || '',
        match_score: responseData.match_score || 0
      }
      setCachedRecommendation(selfIntroductionText, cacheData)
      
    } catch (apiError) {
      error.value = `调用职业推荐API失败: ${apiError.message}`
      loading.value = false
      return
    }
    
    // 跳转到测评页面
    router.push('/career-evaluation')
  } catch (err) {
    router.push('/career-evaluation')
  } finally {
    loading.value = false
  }
}

// Lifecycle hooks
onMounted(() => {
  formData.value = loadFormData()
})

onUnmounted(() => {
  // Clean up
})
</script>
