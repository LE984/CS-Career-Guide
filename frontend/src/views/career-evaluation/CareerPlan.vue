﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 p-6 md:p-10">
    <div class="max-w-6xl mx-auto space-y-6">
      <header class="bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-xl shadow-purple-500/5">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 class="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">职业生涯规划报告</h1>
            <div class="flex flex-wrap items-center gap-3 mt-3">
              <p class="text-slate-300 text-lg">目标职业：<span class="text-cyan-400 font-medium">{{ targetJob || '未选择' }}</span></p>
              <span v-if="cacheHit" class="inline-flex items-center gap-1 px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full text-green-400 text-sm">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                缓存命中
              </span>
            </div>
          </div>
          <router-link 
            to="/company-reviews" 
            class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-cyan-600 transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-blue-500/30 hover:-translate-y-0.5"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
            </svg>
            查看企业榜单
          </router-link>
        </div>
      </header>

      <div v-if="loading" class="bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 flex items-center justify-center shadow-lg">
        <div class="flex items-center gap-3">
          <div class="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          <span class="text-slate-200">正在生成报告，请稍候...</span>
        </div>
      </div>
      <div v-else-if="error" class="bg-red-950/30 border border-red-800/50 rounded-2xl p-6 text-red-200">{{ error }}</div>

      <template v-else>
        <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <article class="bg-slate-900/60 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-lg hover:shadow-xl hover:shadow-purple-500/10 transition-all duration-300">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <h2 class="text-xl font-bold text-white">人才画像与匹配</h2>
            </div>
            <p class="text-slate-300 mb-3 leading-relaxed">{{ report.profile?.talent_portrait }}</p>
            <p class="text-slate-300 leading-relaxed">{{ report.profile?.personality_job_fit }}</p>
            <div class="mt-5">
              <h3 class="font-semibold text-cyan-400 mb-3 flex items-center gap-2">
                <span class="w-2 h-2 bg-cyan-400 rounded-full"></span>优势
              </h3>
              <ul class="list-disc ml-5 text-slate-300 space-y-2">
                <li v-for="(item, idx) in report.profile?.strengths || []" :key="`s-${idx}`" class="hover:text-slate-100 transition-colors">{{ item }}</li>
              </ul>
            </div>
            <div class="mt-5">
              <h3 class="font-semibold text-orange-400 mb-3 flex items-center gap-2">
                <span class="w-2 h-2 bg-orange-400 rounded-full"></span>短板
              </h3>
              <ul class="list-disc ml-5 text-slate-300 space-y-2">
                <li v-for="(item, idx) in report.profile?.weaknesses || []" :key="`w-${idx}`" class="hover:text-slate-100 transition-colors">{{ item }}</li>
              </ul>
            </div>
          </article>

          <article class="bg-slate-900/60 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-lg hover:shadow-xl hover:shadow-blue-500/10 transition-all duration-300">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <h2 class="text-xl font-bold text-white">市场与城市建议</h2>
            </div>
            <div class="flex items-center gap-2 mb-4">
              <span class="text-slate-400">市场热度：</span>
              <span class="px-3 py-1 bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 rounded-full text-amber-400 text-sm font-medium">{{ report.market?.market_heat }}</span>
            </div>
            <h3 class="font-semibold text-blue-400 mb-3 flex items-center gap-2">
              <span class="w-2 h-2 bg-blue-400 rounded-full"></span>薪资成长预测
            </h3>
            <ul class="list-disc ml-5 text-slate-300 space-y-2">
              <li v-for="(item, idx) in report.market?.salary_growth_forecast || []" :key="`pay-${idx}`" class="hover:text-slate-100 transition-colors">
                <span class="text-cyan-300">{{ item.year }}</span>：{{ item.range }}（{{ item.condition }}）
              </li>
            </ul>
            <h3 class="font-semibold text-green-400 mt-5 mb-3 flex items-center gap-2">
              <span class="w-2 h-2 bg-green-400 rounded-full"></span>城市建议
            </h3>
            <ul class="list-disc ml-5 text-slate-300 space-y-2">
              <li v-for="(item, idx) in report.market?.city_suggestions || []" :key="`city-${idx}`" class="hover:text-slate-100 transition-colors">
                <span class="text-purple-300 font-medium">{{ item.city }}</span>（<span class="text-yellow-400">{{ item.fit_score }}</span>分）：{{ item.reason }}
              </li>
            </ul>
          </article>
        </section>

        <section class="bg-slate-900/60 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-lg">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-12 h-12 bg-gradient-to-br from-cyan-500 to-purple-500 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
              </svg>
            </div>
            <h2 class="text-2xl font-bold text-white">至毕业成长路线 & 学习路径</h2>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 class="font-semibold text-cyan-400 mb-4 flex items-center gap-2">
                <span class="w-2 h-2 bg-cyan-400 rounded-full"></span>成长路线
              </h3>
              <ul class="space-y-4">
                <li v-for="(item, idx) in report.growth_plan?.to_graduation_roadmap || []" :key="`road-${idx}`" class="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 hover:border-cyan-500/50 transition-all duration-300">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs font-bold rounded-full">{{ item.phase }}</span>
                    <span class="font-semibold text-white">{{ item.goal }}</span>
                  </div>
                  <ul class="list-disc ml-5 text-slate-300 space-y-1">
                    <li v-for="(a, i2) in item.actions || []" :key="`a-${idx}-${i2}`" class="text-sm">{{ a }}</li>
                  </ul>
                </li>
              </ul>
            </div>
            <div>
              <h3 class="font-semibold text-purple-400 mb-4 flex items-center gap-2">
                <span class="w-2 h-2 bg-purple-400 rounded-full"></span>学习路径
              </h3>
              <ul class="space-y-4">
                <li v-for="(item, idx) in report.growth_plan?.learning_path || []" :key="`learn-${idx}`" class="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 hover:border-purple-500/50 transition-all duration-300">
                  <div class="font-semibold text-white mb-2">{{ item.stage }}</div>
                  <div class="flex flex-wrap gap-2 mb-2">
                    <span v-for="(topic, tIdx) in item.topics || []" :key="`t-${idx}-${tIdx}`" class="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded-full">{{ topic }}</span>
                  </div>
                  <div class="text-slate-400 text-sm">
                    <span class="text-slate-500">项目：</span>{{ (item.projects || []).join('、') || '暂无' }}
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <article class="bg-slate-900/60 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-lg hover:shadow-xl hover:shadow-green-500/10 transition-all duration-300">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                </svg>
              </div>
              <h2 class="text-xl font-bold text-white">求职策略与风险提醒</h2>
            </div>
            <h3 class="font-semibold text-green-400 mb-3 flex items-center gap-2">
              <span class="w-2 h-2 bg-green-400 rounded-full"></span>求职策略
            </h3>
            <ul class="list-disc ml-5 text-slate-300 space-y-2">
              <li v-for="(item, idx) in report.strategy?.job_hunting_strategy || []" :key="`st-${idx}`" class="hover:text-slate-100 transition-colors">{{ item }}</li>
            </ul>
            <h3 class="font-semibold text-red-400 mt-5 mb-3 flex items-center gap-2">
              <span class="w-2 h-2 bg-red-400 rounded-full"></span>风险提醒
            </h3>
            <ul class="list-disc ml-5 text-slate-300 space-y-2">
              <li v-for="(item, idx) in report.strategy?.risk_alerts || []" :key="`r-${idx}`" class="hover:text-slate-100 transition-colors">{{ item }}</li>
            </ul>
          </article>

          <article class="bg-slate-900/60 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-lg hover:shadow-xl hover:shadow-amber-500/10 transition-all duration-300">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
              </div>
              <h2 class="text-xl font-bold text-white">计划生成</h2>
            </div>
            <h3 class="font-semibold text-amber-400 mb-3 flex items-center gap-2">
              <span class="w-2 h-2 bg-amber-400 rounded-full"></span>周计划
            </h3>
            <div class="bg-slate-800/50 rounded-lg p-3 mb-3">
              <span class="text-slate-400 text-sm">重点：</span>
              <span class="text-amber-300 font-medium">{{ report.weekly_plan?.focus || '未设置' }}</span>
            </div>
            <ul class="list-disc ml-5 text-slate-300 space-y-2">
              <li v-for="(item, idx) in report.weekly_plan?.schedule || []" :key="`week-${idx}`" class="hover:text-slate-100 transition-colors">
                <span class="text-cyan-300">{{ item.day }}</span>：{{ item.task }}（<span class="text-amber-400">{{ item.hours }}h</span>）
              </li>
            </ul>
            <h3 class="font-semibold text-orange-400 mt-5 mb-3 flex items-center gap-2">
              <span class="w-2 h-2 bg-orange-400 rounded-full"></span>月计划
            </h3>
            <div class="bg-slate-800/50 rounded-lg p-3 mb-2">
              <span class="text-slate-400 text-sm">主题：</span>
              <span class="text-orange-300 font-medium">{{ report.monthly_plan?.theme || '未设置' }}</span>
            </div>
            <ul class="list-disc ml-5 text-slate-300 space-y-2">
              <li v-for="(item, idx) in report.monthly_plan?.targets || []" :key="`month-${idx}`" class="hover:text-slate-100 transition-colors">{{ item }}</li>
            </ul>
          </article>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { aiAPI } from '@/api'

const loading = ref(true)
const error = ref('')
const report = ref({})
const targetJob = ref('')
const cacheHit = ref(false)

function getUserProfileFromLocalStorage() {
  const raw = localStorage.getItem('selfIntroduction')
  if (!raw) return null
  const data = JSON.parse(raw)
  return {
    major: data.major || '',
    education: '本科',
    skills: data.skills || [],
    personality: data.selfDescription || '',
    graduation_year: new Date().getFullYear() + 1,
    school: data.school || '',
    grade: data.grade || '',
    self_introduction: data.selfDescription || '',
    career_goal: data.goal || ''
  }
}

function getTargetJobFromLocalStorage() {
  const selected = localStorage.getItem('selectedCareers')
  if (selected) {
    const careers = JSON.parse(selected)
    if (Array.isArray(careers) && careers.length > 0) return careers[0]
  }

  const rec = localStorage.getItem('careerRecommendations')
  if (rec) {
    const recommendations = JSON.parse(rec)
    if (Array.isArray(recommendations) && recommendations.length > 0) {
      return recommendations[0].career
    }
  }
  return ''
}

function generateCacheKey(userProfile, targetJob) {
  const profileStr = JSON.stringify({
    major: userProfile.major,
    education: userProfile.education,
    skills: userProfile.skills.sort(),
    personality: userProfile.personality,
    school: userProfile.school,
    grade: userProfile.grade,
    self_introduction: userProfile.self_introduction,
    career_goal: userProfile.career_goal
  })
  const combined = `${targetJob}_${profileStr}`
  try {
    return btoa(encodeURIComponent(combined)).replace(/[+/=]/g, (c) => ({'+':'-', '/':'_', '=':''}[c]))
  } catch (e) {
    console.warn('btoa failed, using alternative method:', e)
    return Array.from(new TextEncoder().encode(combined))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
  }
}

function getCachedReport(cacheKey) {
  try {
    const cachedData = localStorage.getItem(`careerReport_${cacheKey}`)
    if (cachedData) {
      const parsed = JSON.parse(cachedData)
      if (parsed.expireTime && parsed.expireTime > Date.now()) {
        return parsed.report
      }
    }
  } catch (e) {
    console.error('读取缓存失败:', e)
  }
  return null
}

function setCachedReport(cacheKey, reportData) {
  try {
    const cachedData = {
      report: reportData,
      expireTime: Date.now() + 7 * 24 * 60 * 60 * 1000
    }
    localStorage.setItem(`careerReport_${cacheKey}`, JSON.stringify(cachedData))
  } catch (e) {
    console.error('写入缓存失败:', e)
  }
}

onMounted(async () => {
  try {
    const userProfile = getUserProfileFromLocalStorage()
    targetJob.value = getTargetJobFromLocalStorage()

    if (!userProfile || !targetJob.value) {
      error.value = '缺少用户资料或目标职业，请先完成第一阶段测评。'
      loading.value = false
      return
    }

    const cacheKey = generateCacheKey(userProfile, targetJob.value)
    const cachedReport = getCachedReport(cacheKey)

    if (cachedReport) {
      cacheHit.value = true
      report.value = cachedReport
      console.log('缓存命中，直接使用缓存数据')
    } else {
      const resp = await aiAPI.careerReport(userProfile, targetJob.value)
      if (!resp.success) {
        throw new Error(resp.error || '职业报告生成失败')
      }

      report.value = resp.data || {}
      setCachedReport(cacheKey, report.value)
    }

    localStorage.setItem('careerReport', JSON.stringify(report.value))
  } catch (e) {
    error.value = e.message || '生成职业报告失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

article {
  transition: all 0.3s ease;
}

article:hover {
  transform: translateY(-2px);
}

ul {
  list-style-position: outside;
}

ul li::marker {
  color: #60a5fa;
}

.list-disc li::marker {
  color: #60a5fa;
}

h1, h2, h3, h4, h5, h6 {
  font-weight: 700;
  letter-spacing: -0.02em;
}

h2 {
  font-size: 1.25rem;
}

h3 {
  font-size: 1rem;
}

.bg-clip-text {
  -webkit-background-clip: text;
  background-clip: text;
}

.backdrop-blur-sm {
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
}

.shadow-xl {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
}

section {
  animation: fadeInUp 0.6s ease-out forwards;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

section:nth-child(2) { animation-delay: 0.1s; }
section:nth-child(3) { animation-delay: 0.2s; }
section:nth-child(4) { animation-delay: 0.3s; }
section:nth-child(5) { animation-delay: 0.4s; }
section:nth-child(6) { animation-delay: 0.5s; }
</style>

