<template>
  <div class="min-h-screen bg-gradient-to-r from-white to-purple-100 text-on-surface antialiased">
    <main class="pt-24 min-h-screen flex flex-col">
      <!-- Interview Header Section -->
      <header class="bg-surface-container-low px-8 py-6">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="flex items-center gap-4">
            <div class="h-12 w-12 bg-secondary rounded-xl flex items-center justify-center text-on-secondary shadow-lg shadow-secondary/20 overflow-hidden">
              <img src="../../assets/images/面试.png" alt="面试" class="w-full h-full object-cover"/>
            </div>
            <div>
              <h1 class="text-2xl font-extrabold tracking-tight text-primary-container">模拟面试</h1>
              <p class="text-sm text-on-primary-container font-medium">L3 级别职级自测 • 实时语义分析已开启</p>
            </div>
          </div>
          <div v-if="isInterviewing" class="flex items-center gap-6">
            <div class="flex items-center gap-3 bg-surface-container-lowest px-4 py-2 rounded-full shadow-sm">
              <span class="material-symbols-outlined text-secondary animate-pulse" style="font-variation-settings: 'FILL' 1;">timer</span>
              <span class="font-mono text-lg font-bold text-primary-container">{{ formatTime(remainingTime) }}</span>
            </div>
            <div class="flex gap-2">
              <button class="px-5 py-2.5 rounded-xl bg-amber-500 text-white font-semibold shadow-lg shadow-amber-500/20 hover:opacity-90 transition-all active:scale-95" @click="pauseInterview">
                {{ isPaused ? '继续面试' : '暂停面试' }}
              </button>
              <button class="px-5 py-2.5 rounded-xl bg-error text-on-error font-semibold shadow-lg shadow-error/20 hover:opacity-90 transition-all active:scale-95" @click="hangupInterview">
                结束面试
              </button>
            </div>
          </div>
        </div>
      </header>
      <!-- Main Content Area: Asymmetric Layout -->
      <section class="flex-grow grid grid-cols-12 gap-0">
        <!-- Left Sidebar: Progress (Progressive Disclosure) -->
        <aside class="col-span-12 lg:col-span-2 bg-surface border-r border-slate-200/15 p-6 space-y-8">
          <div>
            <h3 class="text-xl font-bold uppercase tracking-widest text-on-primary-container mb-4">面试流程</h3>
            <div class="space-y-4 text-sm text-on-surface-variant">
              <div class="bg-surface-container-low p-4 rounded-lg">
                <h4 class="font-semibold text-primary-container mb-3">典型面试流程环节</h4>
                <ol class="space-y-3">
                  <li>
                    <span class="font-medium text-secondary">1. 面试前准备：</span>
                    <span>筛选简历、了解岗位职责与公司业务。建议提前10分钟到达，整理仪容并确认准备情况。</span>
                  </li>
                  <li>
                    <span class="font-medium text-secondary">2. 开场与自我介绍：</span>
                    <span>通常2-3分钟，包含教育背景、工作经历、突出能力。</span>
                  </li>
                  <li>
                    <span class="font-medium text-secondary">3. 核心提问环节：</span>
                    <ul class="mt-2 space-y-2 pl-4">
                      <li>○ 行为面试 (Behavioral Interview)：使用STAR原则（情境、任务、行动、结果）描述过往经历，体现行为模式。</li>
                      <li>○ 专业技能问答：针对岗位要求进行技术或业务能力考核。</li>
                      <li>○ 经典问题：包括动机（为什么选我们）、优缺点、未来规划等。</li>
                    </ul>
                  </li>
                  <li>
                    <span class="font-medium text-secondary">4. 求职者提问 (Q&A)：</span>
                    <span>针对公司文化、团队情况、岗位细节提问，展示积极性。</span>
                  </li>
                  <li>
                    <span class="font-medium text-secondary">5. 面试结束与后续：</span>
                    <span>通常1-2周内收到结果通知。</span>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </aside>
        <!-- Center: Main Chat Window -->
        <div class="col-span-12 lg:col-span-7 bg-surface-container-lowest flex flex-col">
          <div ref="chatRef" class="h-[600px] overflow-y-auto p-8 space-y-8 border-2 border-surface-variant rounded-2xl mb-6">
             <!-- Interviewer Type Selection (New Section) -->
            <div v-if="!isInterviewing" class="mb-8 p-6 bg-surface-container-low rounded-3xl border border-slate-200/15 shadow-sm">
              <div class="flex items-center gap-3 mb-6">
                <div class="h-8 w-8 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary">
                  <span class="material-symbols-outlined text-xl"></span>
                </div>
                <h2 class="text-lg font-bold text-primary-container">选择面试风格</h2>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <!-- Gentle -->
                <button 
                  class="flex items-start gap-4 p-4 rounded-2xl bg-white border-2 border-transparent hover:border-secondary/30 transition-all text-left group"
                  @click="selectedStyle = 'gentle'"
                  :class="selectedStyle === 'gentle' ? 'border-2 border-secondary shadow-md shadow-secondary/5' : ''"
                >
                  <div class="h-10 w-10 rounded-xl bg-green-50 text-green-600 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined">favorite</span>
                  </div>
                  <div>
                    <div class="flex items-center justify-between">
                      <p class="font-bold text-primary-container text-sm">温和面</p>
                      <span v-if="selectedStyle === 'gentle'" class="text-[10px] bg-secondary text-on-secondary px-1.5 py-0.5 rounded-full uppercase font-bold tracking-tighter">Selected</span>
                    </div>
                    <p class="text-xs text-on-primary-container mt-1">语气友好亲切，侧重引导与交流，适合舒缓紧张感。</p>
                  </div>
                </button>
                <!-- Technical -->
                <button 
                  class="flex items-start gap-4 p-4 rounded-2xl bg-white border-2 border-transparent hover:border-secondary/30 transition-all text-left group"
                  @click="selectedStyle = 'technical'"
                  :class="selectedStyle === 'technical' ? 'border-2 border-secondary shadow-md shadow-secondary/5' : ''"
                >
                  <div class="h-10 w-10 rounded-xl bg-secondary/10 text-secondary flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">code</span>
                  </div>
                  <div>
                    <div class="flex items-center justify-between">
                      <p class="font-bold text-primary-container text-sm">技术面</p>
                      <span v-if="selectedStyle === 'technical'" class="text-[10px] bg-secondary text-on-secondary px-1.5 py-0.5 rounded-full uppercase font-bold tracking-tighter">Selected</span>
                    </div>
                    <p class="text-xs text-on-primary-container mt-1">极致理性的硬核技术深挖，针对底层原理进行连环追问。</p>
                  </div>
                </button>
                <!-- Stress -->
                <button 
                  class="flex items-start gap-4 p-4 rounded-2xl bg-white border-2 border-transparent hover:border-error/30 transition-all text-left group"
                  @click="selectedStyle = 'pressure'"
                  :class="selectedStyle === 'pressure' ? 'border-2 border-error shadow-md shadow-error/5' : ''"
                >
                  <div class="h-10 w-10 rounded-xl bg-error/5 text-error flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined">bolt</span>
                  </div>
                  <div>
                    <div class="flex items-center justify-between">
                      <p class="font-bold text-primary-container text-sm">压力面</p>
                      <span v-if="selectedStyle === 'pressure'" class="text-[10px] bg-secondary text-on-secondary px-1.5 py-0.5 rounded-full uppercase font-bold tracking-tighter">Selected</span>
                    </div>
                    <p class="text-xs text-on-primary-container mt-1">快速、尖锐甚至质疑式的提问，考察极高压力下的心态表现。</p>
                  </div>
                </button>
                <!-- Behavioral -->
                <button 
                  class="flex items-start gap-4 p-4 rounded-2xl bg-white border-2 border-transparent hover:border-amber-500/30 transition-all text-left group"
                  @click="selectedStyle = 'behavioral'"
                  :class="selectedStyle === 'behavioral' ? 'border-2 border-amber-500 shadow-md shadow-amber-500/5' : ''"
                >
                  <div class="h-10 w-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                    <span class="material-symbols-outlined">groups</span>
                  </div>
                  <div>
                    <div class="flex items-center justify-between">
                      <p class="font-bold text-primary-container text-sm">行为面</p>
                      <span v-if="selectedStyle === 'behavioral'" class="text-[10px] bg-secondary text-on-secondary px-1.5 py-0.5 rounded-full uppercase font-bold tracking-tighter">Selected</span>
                    </div>
                    <p class="text-xs text-on-primary-container mt-1">关注过往经历中的决策、冲突处理及团队协作等软技能。</p>
                  </div>
                </button>
              </div>
              <div class="mt-6 flex justify-center">
                <button 
                  @click="startInterview" 
                  class="px-8 py-3 rounded-xl bg-secondary text-on-secondary font-bold hover:opacity-90 transition-all active:scale-95 shadow-lg shadow-secondary/20"
                >
                  <span>开始面试</span>
                </button>
              </div>
            </div>
            

            
            <!-- AI Message -->
            <div v-if="messages.length > 0" class="space-y-8">
              <div v-for="(msg, index) in messages" :key="index" class="flex gap-4 items-start max-w-2xl" :class="msg.type === 'ai' ? '' : 'flex-row-reverse ml-auto'">
                <template v-if="msg.type === 'ai'">
                  <div class="h-10 w-10 rounded-full bg-primary-container flex-shrink-0 flex items-center justify-center shadow-md overflow-hidden">
                    <img alt="AI面试官头像" class="h-full w-full object-cover" src="@/assets/images/面试官头像.jpg"/>
                  </div>
                </template>
                <template v-else>
                  <div class="h-10 w-10 rounded-full bg-primary-fixed flex-shrink-0 flex items-center justify-center border-2 border-white shadow-md overflow-hidden">
                    <img alt="用户头像" class="h-full w-full object-cover" :src="user?.avatar || '/avatars/default/default.jpg'"/>
                  </div>
                </template>
                <div :class="msg.type === 'ai' ? 'bg-surface-container-low p-6 rounded-2xl rounded-tl-none shadow-sm' : 'bg-secondary text-on-secondary p-6 rounded-2xl rounded-tr-none shadow-xl shadow-secondary/10'">
                  <div v-if="msg.type === 'ai'" class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 rounded-full bg-secondary/10 text-secondary text-[10px] font-bold uppercase">
                      {{ selectedStyle === 'pressure' ? '压力型人格' : selectedStyle === 'technical' ? '技术型人格' : selectedStyle === 'gentle' ? '温和型人格' : '行为型人格' }}
                    </span>
                  </div>
                  <p class="leading-relaxed font-medium">{{ msg.content }}</p>
                  
                </div>
              </div>
              
              
            </div>
            
            <!-- 空状态 -->
            <div v-else class="h-full flex flex-col items-center justify-center text-center opacity-60 py-12">
              <div class="w-24 h-24 bg-base-200 rounded-full flex items-center justify-center mb-4 transition-transform ">
                <span class="material-symbols-outlined text-8xl text-base-content/50">Action</span>
              </div>
              <p class="text-lg font-medium">准备好开始面试了吗？</p>
              <p class="text-sm mt-2">选择面试风格并点击开始按钮</p>
            </div>
          </div>
          <!-- Input Zone -->
          <div v-if="isInterviewing" class="p-1 border-t border-slate-200/10">
            <div class="relative group">
              <textarea 
                ref="inputRef"
                v-model="inputMessage"
                class="w-full h-full rounded-2xl p-6 pr-32 focus:ring-0 focus:border-secondary transition-all resize-none min-h-[90px] text-white text-base placeholder:text-white text-base backdrop-blur-sm bg-black/30"
                placeholder="在此输入或语音录入你的回答..."
                :disabled="isLoading"
                @keydown.enter.prevent="sendMessage"
              ></textarea>
              <div class="absolute bottom-4 right-4 flex gap-2 items-end">
                <div v-if="isRecording" class="flex flex-col items-center mr-2">
                  <div class="text-xs text-white/70 mb-1">
                    {{ isSpeaking ? '🎤 录音中' : '👂 监听中' }}
                  </div>
                  <div v-if="isSpeaking" class="flex gap-0.5">
                    <div 
                      v-for="i in 5" 
                      :key="i"
                      class="w-1 bg-error rounded-full transition-all"
                      :style="{ 
                        height: `${Math.max(4, audioLevel * 20 + Math.random() * 8)}px`,
                        opacity: audioLevel > 0 ? 0.6 + Math.random() * 0.4 : 0.3
                      }"
                    ></div>
                  </div>
                  <div v-if="isSpeaking && recordingDuration > 0" class="text-xs text-white/50">
                    {{ (recordingDuration / 1000).toFixed(1) }}s
                  </div>
                </div>
                <button 
                  class="h-12 w-12 rounded-xl flex items-center justify-center transition-all active:scale-90 relative cursor-pointer"
                  :class="[
                    isSpeaking ? 'bg-error text-on-error animate-pulse' : 
                    isRecording ? 'bg-secondary text-on-secondary' : 
                    'bg-surface-container-highest text-on-surface hover:bg-surface-variant'
                  ]"
                  :disabled="!isInterviewing"
                  @click="toggleRecording"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    class="w-6 h-6"
                  >
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="23" />
                    <line x1="8" y1="23" x2="16" y2="23" />
                  </svg>
                  <div 
                    v-if="isSpeaking" 
                    class="absolute -top-1 -right-1 w-3 h-3 bg-error rounded-full animate-ping"
                  ></div>
                </button>
                <button 
                  class="h-12 w-12 rounded-xl bg-surface-container-highest text-on-surface hover:bg-surface-variant flex items-center justify-center transition-all active:scale-90"
                  :disabled="isLoading || !inputMessage.trim()"
                  @click="sendMessage"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    class="w-6 h-6"
                  >
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                </button>
              </div>
            </div>
            <div class="mt-4 flex justify-between items-center text-[11px] font-bold text-on-primary-container uppercase tracking-widest px-2">
              <span>畅所欲言</span>
              <span class="text-secondary">AI 正在实时听取...</span>
            </div>
          </div>
        </div>
        <!-- Right Sidebar: Feedback Panel -->
        <aside class="col-span-12 lg:col-span-3 bg-surface p-8 border-l border-slate-200/15 overflow-y-auto">
          <h3 class="text-sm font-extrabold text-primary-container mb-6 flex items-center gap-2">
            面试要点
          </h3>
          <div class="space-y-6">
            <!-- Feedback Card 1 -->
            <div class="bg-surface-container-lowest p-5 rounded-2xl shadow-sm border-l-4 border-error">
              <div class="flex items-center gap-2 text-error mb-2">
                <span class="material-symbols-outlined text-sm">warning</span>
                <span class="text-xs font-bold uppercase tracking-tighter">语气提示</span>
              </div>
              <p class="text-sm font-bold text-on-surface mb-1">语气不紧张</p>
              <p class="text-xs text-on-primary-container leading-relaxed">建议在谈到技术细节时适当停顿，保持语速适中。</p>
            </div>
            <!-- Feedback Card 2 -->
            <div class="bg-surface-container-lowest p-5 rounded-2xl shadow-sm border-l-4 border-secondary">
              <div class="flex items-center gap-2 text-secondary mb-2">
                <span class="material-symbols-outlined text-sm">key</span>
                <span class="text-xs font-bold uppercase tracking-tighter">关键词命中</span>
              </div>
              <p class="text-sm font-bold text-on-surface mb-1">项目关键词：高性能</p>
              <p class="text-xs text-on-primary-container leading-relaxed">成功捕捉到“高并发”、“消息队列”、“削峰填谷”等核心指标。</p>
            </div>
            <!-- Feedback Card 3 -->
            <div class="bg-surface-container-lowest p-5 rounded-2xl shadow-sm border-l-4 border-tertiary-fixed-dim">
              <div class="flex items-center gap-2 text-on-tertiary-container mb-2">
                <span class="material-symbols-outlined text-sm">verified</span>
                <span class="text-xs font-bold uppercase tracking-tighter">逻辑评估</span>
              </div>
              <p class="text-sm font-bold text-on-surface mb-1">逻辑清晰</p>
              <p class="text-xs text-on-primary-container leading-relaxed">采用 STAR 法则进行描述，问题背景和结果产出定义明确。</p>
            </div>
            <!-- Tech Callout -->
            <div class="bg-primary-container p-6 rounded-2xl text-tertiary-fixed relative overflow-hidden group mt-12">
              <h4 class="text-xs font-bold uppercase tracking-widest text-on-primary-container mb-4">面试小贴士</h4>
              <p class="text-sm font-medium leading-relaxed italic">
                "回答问题时，不仅要讲方案，更要讲清楚方案对比的演进过程（Why not A? Why B?）。"
              </p>
            </div>
          </div>
        </aside>
      </section>
    </main>
    
    <!-- 面试复盘弹窗 -->
    <div v-if="showReview" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div class="bg-base-100 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-hidden animate-scale-up">
        <div class="p-6 border-b border-base-200 flex justify-between items-center bg-base-100/50">
          <h3 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">面试复盘报告</h3>
          <button @click="showReview = false" class="btn btn-circle btn-sm btn-ghost">
          </button>
        </div>
        <div class="p-8 overflow-y-auto max-h-[60vh] bg-base-100">
          <div v-if="!reviewContent" class="flex flex-col items-center justify-center py-12">
            <span class="loading loading-spinner loading-lg text-primary mb-4"></span>
            <span class="text-base-content/60 font-medium">正在生成复盘报告，请稍候...</span>
          </div>
          <div v-else class="prose prose-sm md:prose-base max-w-none">
            <div class="whitespace-pre-wrap leading-relaxed text-base-content/80">{{ reviewContent }}</div>
          </div>
        </div>
        <div class="p-6 border-t border-base-200 bg-base-200/30 flex justify-end">
          <button @click="showReview = false" class="btn btn-primary px-8 rounded-full shadow-glow">
            关闭报告
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { VAD_ASSET_BASE_URL, ENABLE_TTS } from '@/config'
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import api, { aiAPI, userAPI, apiFetch } from '@/api'

const router = useRouter()

const user = ref(null)

const isLoggedIn = computed(() => {
  return !!localStorage.getItem('token')
})

const updateUserFromLocalStorage = () => {
  const userStr = localStorage.getItem('user')
  const userData = userStr ? JSON.parse(userStr) : null
  user.value = userData
}

const syncUserProfile = async () => {
  if (isLoggedIn.value) {
    try {
      const response = await userAPI.getProfile()
      user.value = response
      localStorage.setItem('user', JSON.stringify(response))
    } catch (err) {
      console.error('同步用户信息失败:', err)
    }
  }
}

let mediaSource = null
let sourceBuffer = null
let audioPlayer = new Audio()
let audioQueue = []
let isUpdating = false
let isAudioInitialized = false
let deferredAudioChunks = []
let hasAudioPermission = false
let audioPlaybackContext = null

const requestAudioPermission = async () => {
  console.log('[AUDIO] 请求音频播放权限')
  
  if (hasAudioPermission) {
    console.log('[AUDIO] 已拥有音频播放权限')
    return true
  }

  try {
    if (audioPlaybackContext) {
      audioPlaybackContext.close()
    }
    audioPlaybackContext = new (window.AudioContext || window.webkitAudioContext)()
    await audioPlaybackContext.resume()
    console.log('[AUDIO] 通过 AudioContext 获取权限成功')
    hasAudioPermission = true
    return true
  } catch (e) {
    console.warn('[AUDIO] AudioContext 获取权限失败:', e)
  }

  try {
    audioPlayer.volume = 0
    await audioPlayer.play()
    audioPlayer.pause()
    audioPlayer.volume = 0.8
    console.log('[AUDIO] 通过静音播放获取权限成功')
    hasAudioPermission = true
    return true
  } catch (e) {
    console.warn('[AUDIO] 静音播放获取权限失败:', e)
    hasAudioPermission = false
    return false
  }
}

const initAudioStream = () => {
  console.log('[AUDIO] 初始化音频流')
  
  audioQueue = []
  deferredAudioChunks = []
  isUpdating = false
  isAudioInitialized = false

  if (mediaSource) {
    try {
      URL.revokeObjectURL(audioPlayer.src)
      console.log('[AUDIO] 已清理旧资源')
    } catch (e) {
      console.warn('[AUDIO] 清理旧资源失败:', e)
    }
  }

  mediaSource = new MediaSource()
  audioPlayer.src = URL.createObjectURL(mediaSource)
  audioPlayer.volume = 0.8

  const onUpdateEnd = () => {
    console.log('[AUDIO] SourceBuffer updateend 事件触发')
    isUpdating = false
    processQueue()
  }

  const onSourceBufferError = (e) => {
    console.error('[AUDIO] SourceBuffer 错误:', e)
    isUpdating = false
  }

  const onSourceBufferAbort = () => {
    console.warn('[AUDIO] SourceBuffer 被中止')
    isUpdating = false
  }

  const onSourceOpen = () => {
    console.log('[AUDIO] MediaSource sourceopen 事件触发')
    mediaSource.removeEventListener('sourceopen', onSourceOpen)
    
    try {
      const codecs = ['audio/mpeg', 'audio/mp3', 'audio/mp4; codecs="mp3"']
      let success = false
      
      for (const codec of codecs) {
        try {
          sourceBuffer = mediaSource.addSourceBuffer(codec)
          console.log(`[AUDIO] 成功创建 SourceBuffer, codec: ${codec}`)
          success = true
          break
        } catch (e) {
          console.log(`[AUDIO] 尝试 codec ${codec} 失败:`, e)
        }
      }
      
      if (!success) {
        console.error('[AUDIO] 无法创建 SourceBuffer，所有codec都失败')
        return
      }

      sourceBuffer.addEventListener('updateend', onUpdateEnd)
      sourceBuffer.addEventListener('error', onSourceBufferError)
      sourceBuffer.addEventListener('abort', onSourceBufferAbort)

      isAudioInitialized = true
      
      if (deferredAudioChunks.length > 0) {
        console.log(`[AUDIO] 处理延迟的 ${deferredAudioChunks.length} 个音频块`)
        audioQueue.push(...deferredAudioChunks)
        deferredAudioChunks = []
        processQueue()
      }
    } catch (e) {
      console.error("[AUDIO] MSE AddSourceBuffer Error:", e)
    }
  }

  mediaSource.addEventListener('sourceopen', onSourceOpen)

  mediaSource.addEventListener('error', (e) => {
    console.error('[AUDIO] MediaSource 错误:', e)
  })

  mediaSource.addEventListener('close', () => {
    console.log('[AUDIO] MediaSource 已关闭')
  })

  audioPlayer.addEventListener('error', (e) => {
    console.error('[AUDIO] Audio 元素错误:', e)
  })

  audioPlayer.addEventListener('playing', () => {
    console.log('[AUDIO] 开始播放')
  })

  audioPlayer.addEventListener('pause', () => {
    console.log('[AUDIO] 暂停播放')
  })
}

const processQueue = () => {
  if (isUpdating || audioQueue.length === 0 || !sourceBuffer || sourceBuffer.updating) {
    return
  }

  isUpdating = true
  const chunk = audioQueue.shift()
  console.log(`[AUDIO] 处理音频块，大小: ${chunk.length} bytes, 队列剩余: ${audioQueue.length}`)
  
  try {
    sourceBuffer.appendBuffer(chunk)
    console.log('[AUDIO] 音频块已写入 SourceBuffer')
  } catch (e) {
    console.error("[AUDIO] SourceBuffer Append Error:", e)
    isUpdating = false
  }
}

const handleAudioChunk = (base64Data) => {
  console.log(`[AUDIO] 收到音频数据，base64长度: ${base64Data?.length || 0}`)
  
  if (!base64Data || !base64Data.trim()) {
    console.warn('[AUDIO] 收到空的音频数据')
    return
  }

  try {
    const binaryString = atob(base64Data)
    const len = binaryString.length
    console.log(`[AUDIO] Base64解码完成，二进制长度: ${len}`)
    
    const bytes = new Uint8Array(len)
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }

    if (!isAudioInitialized) {
      console.log('[AUDIO] 音频尚未初始化，缓存音频块')
      deferredAudioChunks.push(bytes)
    } else {
      audioQueue.push(bytes)
      
      if (audioQueue.length === 1) {
        const tryPlay = async () => {
          try {
            await audioPlayer.play()
            console.log('[AUDIO] 收到第一个音频块，开始播放')
          } catch (e) {
            console.warn('[AUDIO] 播放失败，尝试获取权限:', e)
            
            await requestAudioPermission()
            
            try {
              await audioPlayer.play()
              console.log('[AUDIO] 获取权限后播放成功')
            } catch (e2) {
              console.error('[AUDIO] 获取权限后播放仍然失败:', e2)
            }
          }
        }
        
        tryPlay()
      }
      
      processQueue()
    }
  } catch (e) {
    console.error("[AUDIO] Base64 Decode Error:", e)
  }
}

const finishAudio = () => {
  console.log('[AUDIO FINISH] 音频传输完成')
  if (sourceBuffer && mediaSource && !mediaSource.readyState === 'closed') {
    try {
      sourceBuffer.abort()
      mediaSource.endOfStream()
      console.log('[AUDIO] 已调用 endOfStream')
    } catch (e) {
      console.warn('[AUDIO] endOfStream 失败:', e)
    }
  }
}

const stopAIAudio = () => {
  console.log('[AUDIO] 用户开始说话，停止AI语音播放')
  
  try {
    audioPlayer.pause()
    console.log('[AUDIO] 暂停audioPlayer')
  } catch (e) {
    console.warn('[AUDIO] 暂停audioPlayer失败:', e)
  }
  
  try {
    if (sourceBuffer) {
      sourceBuffer.abort()
      console.log('[AUDIO] 中止SourceBuffer')
    }
  } catch (e) {
    console.warn('[AUDIO] 中止SourceBuffer失败:', e)
  }
  
  try {
    if (mediaSource && mediaSource.readyState !== 'closed') {
      mediaSource.endOfStream()
      console.log('[AUDIO] 调用endOfStream')
    }
  } catch (e) {
    console.warn('[AUDIO] endOfStream失败:', e)
  }
  
  audioQueue = []
  deferredAudioChunks = []
  isAudioInitialized = false
  isUpdating = false
  
  console.log('[AUDIO] AI语音已停止，音频队列已清空')
}

const initAudio = () => {
  initAudioStream()
}

const ensureAudioPlayback = () => {
  if (audioPlayer.paused && isAudioInitialized) {
    audioPlayer.play().then(() => {
      console.log('[AUDIO] 用户交互后恢复播放')
    }).catch(e => {
      console.error('[AUDIO] 恢复播放失败:', e)
    })
  }
}

onUnmounted(() => {
  console.log('[AUDIO] 组件卸载，清理音频资源')
  audioPlayer.pause()
  audioPlayer.src = ''
  if (mediaSource) {
    try {
      mediaSource.endOfStream()
    } catch (e) {
      console.warn('[AUDIO] endOfStream on unmount:', e)
    }
  }
  audioQueue = []
  deferredAudioChunks = []
})

// 面试设置
const interviewStyles = [
  { label: '温和面', value: 'gentle' },
  { label: '压力面', value: 'pressure' },
  { label: '技术面', value: 'technical' },
  { label: '行为面', value: 'behavioral' }
]

const selectedStyle = ref('technical')
const isInterviewing = ref(false)
const isLoading = ref(false)
const inputMessage = ref('')
const messages = ref([])
const chatRef = ref(null)
const inputRef = ref(null)
const remainingTime = ref(900) // 15分钟
const sessionId = ref('')
const showReview = ref(false)
const reviewContent = ref('')

// 语音合成由 VITE_ENABLE_TTS 控制；后端需同时设置 ENABLE_TTS。

// 语音识别相关
const isSpeaking = ref(false)
const isRecording = ref(false)
const isSending = ref(false)
const audioLevel = ref(0)
const recordingDuration = ref(0)
let vadInstance = null
let audioContext = null
let analyser = null
let dataArray = null
let animationFrameId = null

// 面试计时相关
const isPaused = ref(false)
let timer = null

// 格式化时间
const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// 获取用户简历信息
const getUserResume = () => {
  try {
    const resumeStr = localStorage.getItem('resume')
    if (!resumeStr) {
      console.log('[RESUME] 未找到简历数据')
      return null
    }
    
    const resume = JSON.parse(resumeStr)
    
    // 构建简历提示词
    let resumePrompt = ''
    
    if (resume.name) {
      resumePrompt += `姓名：${resume.name}\n`
    }
    if (resume.target_position) {
      resumePrompt += `意向岗位：${resume.target_position}\n`
    }
    if (resume.self_evaluation) {
      resumePrompt += `个人自评：${resume.self_evaluation}\n`
    }
    if (resume.skills) {
      resumePrompt += `专业技能：${resume.skills}\n`
    }
    if (resume.education && resume.education.length > 0) {
      resumePrompt += `教育背景：\n`
      resume.education.forEach(edu => {
        if (edu.school) {
          resumePrompt += `  - ${edu.school} ${edu.major || ''} ${edu.degree || ''} ${edu.period || ''}\n`
        }
      })
    }
    if (resume.experience && resume.experience.length > 0) {
      resumePrompt += `实习经历：\n`
      resume.experience.forEach(exp => {
        if (exp.company) {
          resumePrompt += `  - ${exp.company} ${exp.position || ''} ${exp.period || ''}\n`
          if (exp.description) {
            resumePrompt += `    ${exp.description}\n`
          }
        }
      })
    }
    if (resume.projects && resume.projects.length > 0) {
      resumePrompt += `项目经验：\n`
      resume.projects.forEach(project => {
        if (project.name) {
          resumePrompt += `  - ${project.name} ${project.role || ''} ${project.period || ''}\n`
          if (project.description) {
            resumePrompt += `    ${project.description}\n`
          }
        }
      })
    }
    if (resume.certificates && resume.certificates.length > 0) {
      resumePrompt += `证书认证：\n`
      resume.certificates.forEach(cert => {
        if (cert.name) {
          resumePrompt += `  - ${cert.name} ${cert.issuer || ''} ${cert.period || ''}\n`
        }
      })
    }
    
    return resumePrompt.trim() || null
  } catch (error) {
    console.error('[RESUME] 解析简历数据失败:', error)
    return null
  }
}

// 方法
async function startInterview() {
  console.log('开始面试按钮被点击，调用startInterview函数')
  
  isInterviewing.value = true
  isLoading.value = true
  messages.value = []
  remainingTime.value = 900 // 15分钟
  
  // 请求音频播放权限（在用户交互中立即调用）
  await requestAudioPermission()
  
  // 初始化音频流
  initAudioStream()
  console.log('音频流已初始化')
  
  // 开始计时
  startTimer()
  console.log('计时已开始')
  
  // 获取用户简历
  const resumePrompt = getUserResume()
  console.log('[RESUME] 简历提示词:', resumePrompt ? '已加载' : '未找到')
  
  // 添加AI消息占位符
  const aiMessageIndex = messages.value.length
  messages.value.push({
    type: 'ai',
    content: ''
  })
  
  // 自动聚焦输入框
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
    }
  })
  
  try {
    // 使用更新后的aiAPI.chatStream方法
    const promptType = selectedStyle.value === 'pressure' ? 'pressure_interview' : 'interview'
    
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('请求超时')), 15000)
    })
    
    // 构建包含简历的提示词
    let interviewPrompt = `【面试模式】你是一位${getStyleDescription(selectedStyle.value)}面试官。请开始一场15分钟的面试。`
    
    if (resumePrompt) {
      interviewPrompt += `

【面试者简历信息】
${resumePrompt}

请根据以上简历信息，提出针对性的面试问题。`
    }
    
    interviewPrompt += `

要求：
1. 首先进行简短的自我介绍（说明你是面试官，面试风格）
2. 然后提出第一个面试问题
3. 在整个面试过程中，你只需要扮演面试官角色
4. 根据用户的回答，提出下一个相关问题
5. 保持${selectedStyle.value === 'pressure' ? '压力面试' : selectedStyle.value === 'technical' ? '技术面试' : selectedStyle.value === 'behavioral' ? '行为面试' : '温和友好'}的风格

现在开始面试。`
    
    const responsePromise = aiAPI.chatStream(
      interviewPrompt,
      promptType,
      selectedStyle.value,
      sessionId.value
    )
    
    const response = await Promise.race([responsePromise, timeoutPromise])
    
    if (!response.ok) {
      throw new Error('API请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let receivedData = false
    let startTime = Date.now()
    
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      receivedData = true
      startTime = Date.now()
      
      buffer += decoder.decode(value, { stream: true })
      
      // 处理SSE格式的数据
      const lines = buffer.split('\n\n')
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i]
        if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim()
          if (!dataStr) continue // 跳过空数据行

          // 处理后端的结束标记
          if (dataStr === '[DONE]') {
            console.log('[SSE] 数据流结束')
            break  // 或 continue，根据逻辑决定
          }
          
          try {
            const data = JSON.parse(dataStr)
            
            if (data.type === 'thinking') {
              messages.value[aiMessageIndex].content = data.content
              await scrollToBottom()
            } else if (data.type === 'chunk') {
              if (data.content) {
                if (messages.value[aiMessageIndex].content === 'AI正在思考...') {
                  messages.value[aiMessageIndex].content = data.content
                } else {
                  messages.value[aiMessageIndex].content += data.content
                }
                await scrollToBottom()
              }
            } else if (data.type === 'end') {
              if (data.session_id) {
                sessionId.value = data.session_id
              }
              nextTick(() => {
                if (inputRef.value) {
                  inputRef.value.focus()
                }
              })
            } else if (data.type === 'error') {
              messages.value[aiMessageIndex].content = data.content
              await scrollToBottom()
            } else if (data.type === 'debug') {
              console.log('[TTS DEBUG]', data.message)
              if (data.message && data.message.includes('task-finished')) {
                finishAudio()
              }
            } else if (data.type === 'audio') {
              if (ENABLE_TTS) {
                console.log('[TTS AUDIO] Received audio chunk:', data.audio ? `(${data.audio.length} bytes)` : 'empty')
                if (data.audio) {
                  handleAudioChunk(data.audio)
                }
              } else {
                console.log('[TTS AUDIO] 语音合成已禁用，跳过音频处理')
              }
            }
          } catch (e) {
            console.error('解析SSE数据失败:', e, 'Data:', dataStr)
          }
        }
      }
      
      buffer = lines[lines.length - 1]
    }
    
    if (!receivedData) {
      throw new Error('未收到任何数据')
    }
  } catch (error) {
    console.error('开始面试失败:', error)
    messages.value.push({
      type: 'ai',
      content: '抱歉，面试服务暂时不可用，请稍后再试。'
    })
  } finally {
    isLoading.value = false
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.focus()
      }
    })
  }
}

function hangupInterview() {
  if (confirm('确定要结束面试吗？')) {
    endInterview()
  }
}

function pauseInterview() {
  isPaused.value = !isPaused.value
}

async function sendMessage(event, audioMsg = null) {
  let content
  if (audioMsg) {
    content = audioMsg.trim()
  } else {
    content = inputMessage.value.trim()
  }
  
  if (!content || !isInterviewing.value || isLoading.value) return
  
  messages.value.push({
    type: 'user',
    content: content
  })
  await scrollToBottom()
  
  const userMessage = content
  if (!audioMsg) {
    inputMessage.value = ''
  }
  isLoading.value = true
  
  // 添加AI消息占位符
  const aiMessageIndex = messages.value.length
  messages.value.push({
    type: 'ai',
    content: ''
  })
  
  // 自动聚焦输入框
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
    }
  })
  
  try {
    // 请求音频播放权限（在用户交互中立即调用）
    await requestAudioPermission()
    
    // 重新初始化音频流以准备接收新的语音数据
    initAudioStream()
    console.log('[AUDIO] 重新初始化音频流')
    
    // 使用更新后的aiAPI.chatStream方法
    const promptType = selectedStyle.value === 'pressure' ? 'pressure_interview' : 'interview'
    const response = await aiAPI.chatStream(
      `【面试模式】用户的回答是："${userMessage}"

作为${getStyleDescription(selectedStyle.value)}面试官，请：
1. 简要评价用户的回答（可选）
2. 提出下一个面试问题

注意：你只需扮演面试官角色，不要查询任何数据库信息。`,
      promptType,
      selectedStyle.value,
      sessionId.value
    )
    
    if (!response.ok) {
      throw new Error('API请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      // 处理SSE格式的数据
      const lines = buffer.split('\n\n')
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i]
        if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim()
          if (!dataStr) continue // 跳过空数据行
          
          // 添加对 [DONE] 的处理
          if (dataStr === '[DONE]') {
            console.log('[SSE] 数据流结束')
            continue  // 或 break，根据逻辑决定
          }

          try {
            const data = JSON.parse(dataStr)
            
            if (data.type === 'thinking') {
              // 显示思考状态
              messages.value[aiMessageIndex].content = data.content
              await scrollToBottom()
            } else if (data.type === 'chunk') {
              // 更新AI消息内容
              if (data.content) {
                if (messages.value[aiMessageIndex].content === 'AI正在思考...') {
                  messages.value[aiMessageIndex].content = data.content
                } else {
                  messages.value[aiMessageIndex].content += data.content
                }
                await scrollToBottom()
              }
            } else if (data.type === 'end') {
              // 保存sessionId
              if (data.session_id) {
                sessionId.value = data.session_id
              }
              // AI消息结束后聚焦输入框
              nextTick(() => {
                if (inputRef.value) {
                  inputRef.value.focus()
                }
              })
            } else if (data.type === 'error') {
              // 显示错误消息
              messages.value[aiMessageIndex].content = data.content
              await scrollToBottom()
            } else if (data.type === 'audio') {
              // 处理音频数据
              if (ENABLE_TTS) {
                console.log('[TTS AUDIO] Received audio chunk:', data.audio ? `(${data.audio.length} bytes)` : 'empty')
                if (data.audio) {
                  handleAudioChunk(data.audio)
                }
              } else {
                console.log('[TTS AUDIO] 语音合成已禁用，跳过音频处理')
              }
            }
          } catch (e) {
            console.error('解析SSE数据失败:', e, 'Data:', dataStr)
          }
        }
      }
      
      // 保留未处理的部分
      buffer = lines[lines.length - 1]
    }
  } catch (error) {
    console.error('发送回答失败:', error)
    messages.value.push({
      type: 'ai',
      content: '抱歉，面试服务暂时不可用，请稍后再试。'
    })
  } finally {
    isLoading.value = false
    // 加载完成后聚焦输入框
    nextTick(() => {
      if (inputRef.value) {
        inputRef.value.focus()
      }
    })
  }
}

function startTimer() {
  timer = setInterval(() => {
    if (!isPaused.value && remainingTime.value > 0) {
      remainingTime.value--
    } else if (remainingTime.value <= 0) {
      endInterview()
    }
  }, 1000)
}

async function endInterview() {
  clearInterval(timer)
  isInterviewing.value = false

  // 添加结束消息
  messages.value.push({
    type: 'ai',
    content: '面试结束，感谢你的参与！正在生成面试复盘...'
  })
  await scrollToBottom()

  try {
    // 生成面试复盘
    await generateReview()
  } catch (error) {
    console.error('生成复盘时发生错误:', error)
    // 即使发生错误，也显示复盘弹窗
    reviewContent.value = '生成复盘时发生错误，请稍后重试。'
    showReview.value = true
  }
}

async function generateReview() 
{
  // 构建对话记录
  const conversation = messages.value
    .filter(msg => msg.content && !msg.content.includes('正在生成面试复盘'))
    .map(msg => `${msg.type === 'ai' ? '面试官' : '面试者'}：${msg.content}`)
    .join('\n')

  // 检查是否有足够的对话内容
  if (conversation.trim().length < 50) {
    reviewContent.value = '面试对话内容不足，无法生成复盘报告。请确保面试过程中有足够的交流。'
    showReview.value = true
    return
  }

  try {
    // 使用完整的会话ID，确保记忆功能正常工作
    const requestSessionId = sessionId.value || 'default_session'
    const response = await aiAPI.chatStream(
      `【面试复盘模式】请对以下面试过程进行复盘，并提供改进建议。

面试风格：${getStyleDescription(selectedStyle.value)}

对话记录：
${conversation}

请提供以下内容：
1. 面试表现总结（整体评价）
2. 回答的优点
3. 需要改进的地方
4. 具体改进建议
5. 下次面试的准备建议`,
      'interview_review',
      selectedStyle.value,
      requestSessionId
    )

    if (!response.ok) {
      throw new Error(`API请求失败，状态码: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    reviewContent.value = ''
    showReview.value = true

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n\n')
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim()
          if (dataStr) {
            // 跳过 [DONE] 标记
            if (dataStr === '[DONE]') {
              console.log('[REVIEW] SSE流结束')
              continue
            }
            try {
              const data = JSON.parse(dataStr)
              if (data.type === 'chunk') {
                if (data.content) {
                  reviewContent.value += data.content
                }
              }
            } catch (e) {
              console.warn('[REVIEW] 忽略非JSON数据:', dataStr)
            }
          }
        }
      }

      buffer = lines[lines.length - 1]
    }

    // 检查是否生成了复盘内容
    if (!reviewContent.value || reviewContent.value.trim().length === 0) {
      throw new Error('未获取到复盘内容')
    }
    
    // 保存复盘记录到后端
    await saveReviewRecord(reviewContent.value)
  } catch (error) {
    console.error('生成复盘失败:', error)
    reviewContent.value = `生成复盘时遇到问题：${error.message}\n\n请稍后重试，或检查网络连接。`
    showReview.value = true
  }
}

async function saveReviewRecord(reviewContent) {
  try {
    const interviewMsgs = messages.value.filter(m => m.content && !m.content.includes('正在生成面试复盘'))
    const questionCount = interviewMsgs.filter(m => m.type === 'ai').length
    const answerCount = interviewMsgs.filter(m => m.type === 'user').length
    
    // 计算面试时长：总时长900秒 - 剩余时间 = 已用时间
    const totalDuration = 900 // 15分钟 = 900秒
    const usedSeconds = totalDuration - remainingTime.value
    const interviewDurationMinutes = Math.floor(usedSeconds / 60)
    
    const data = {
      session_id: sessionId.value || 'default_session',
      review_content: reviewContent,
      interview_style: selectedStyle.value || 'gentle',
      interview_duration: interviewDurationMinutes,
      question_count: questionCount,
      answer_count: answerCount
    }
    
    const token = localStorage.getItem('token')
    console.log('[REVIEW] 保存复盘记录 - session_id:', sessionId.value, 'token:', token ? '存在' : '不存在')
    
    const response = await apiFetch('/ai/interview/save_review/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
    
    console.log('[REVIEW] 响应状态:', response.status)
    const result = await response.json()
    if (result.success) {
      console.log('复盘记录保存成功:', result.review_id)
    } else {
      console.error('保存复盘记录失败:', result.error)
    }
  } catch (error) {
    console.error('保存复盘记录失败:', error)
  }
}

function getStyleDescription(style) {
  const descriptions = {
    gentle: '温和友好的',
    pressure: '压力型',
    technical: '技术导向的',
    behavioral: '行为面试' 
  }
  return descriptions[style] || '专业的'
}

// 语音识别相关函数
const startRecording = async () => {
  const baseUrl = VAD_ASSET_BASE_URL;
  try {
    const { MicVAD } = await import('@ricky0123/vad-web');
    
    vadInstance = await MicVAD.new({
      baseAssetPath: baseUrl,
      onSpeechStart: () => {
        isSpeaking.value = true;
        recordingDuration.value = 0;
        startDurationTimer();
        console.log('🎤 检测到语音开始！');
        
        stopAIAudio();
      },
      onSpeechEnd: (audio) => {
        isSpeaking.value = false;
        stopDurationTimer();
        console.log(`🎤 检测到语音结束！`);
        console.log(`   - 录制时长: ${recordingDuration.value}ms`);
        console.log(`   - 音频样本数: ${audio.length}`);
        console.log(`   - 估算时长: ${(audio.length / 16000).toFixed(2)}秒`);
        
        if (audio.length > 0) {
          const pcm16 = float32ToInt16(audio);
          sendToBackend(pcm16);
        } else {
          console.log(`⚠️  音频数据为空，跳过发送`);
        }
      },
      onAudioProcessed: (audio) => {
        updateAudioLevel(audio);
      },
      ortConfig: (ort) => {
        ort.env.wasm.wasmPaths = baseUrl;
        ort.env.logLevel = "error";
      },
      positiveSpeechThreshold: 0.8,
      negativeSpeechThreshold: 0.65,
      minSpeechFrames: 5,
      redemptionFrames: 5,
      preSpeechPadFrames: 10,
      postSpeechPadFrames: 20,
    });

    await vadInstance.start();
    console.log('✅ VAD 初始化成功并开始监听');
    console.log('📝 检测配置:');
    console.log('   - 正阈值: 0.5 (检测到语音)');
    console.log('   - 负阈值: 0.35 (停止检测)');
    console.log('   - 最小语音帧数: 3');
    console.log('   - 前置填充: 10帧');
    console.log('   - 后置填充: 20帧');
    
    checkMicrophoneStatus();
  } catch (e) {
    console.error("❌ VAD 初始化失败:", e);
    console.error("   - 错误详情:", e.message);
  }
};

const checkMicrophoneStatus = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const tracks = stream.getAudioTracks();
    
    if (tracks.length > 0) {
      const track = tracks[0];
      console.log('🎧 麦克风状态:');
      console.log('   - 设备名称:', track.label || '未知设备');
      console.log('   - 启用状态:', track.enabled);
      console.log('   - 静音状态:', track.muted);
      
      const constraints = track.getConstraints();
      console.log('   - 采样率:', constraints.sampleRate || '默认');
      
      if (track.muted) {
        console.warn('⚠️  警告：麦克风当前处于静音状态！请取消静音后再试。');
        alert('麦克风当前处于静音状态，请先取消静音后再尝试语音输入。');
      }
      
      tracks.forEach(t => t.stop());
    } else {
      console.log('⚠️  未找到音频轨道');
    }
  } catch (error) {
    console.error('❌ 麦克风访问失败:', error.message);
    console.error('   - 可能原因: 权限未授权 / 无可用设备');
  }
};

let durationTimer = null;

const startDurationTimer = () => {
  durationTimer = setInterval(() => {
    recordingDuration.value += 100;
  }, 100);
};

const stopDurationTimer = () => {
  if (durationTimer) {
    clearInterval(durationTimer);
    durationTimer = null;
  }
};

const updateAudioLevel = (audioData) => {
  if (!audioData || audioData.length === 0) return;
  
  let sum = 0;
  for (let i = 0; i < audioData.length; i++) {
    sum += Math.abs(audioData[i]);
  }
  const avg = sum / audioData.length;
  audioLevel.value = Math.min(avg * 10, 1);
};

const float32ToInt16 = (float32Array) => {
  const buffer = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    let s = Math.max(-1, Math.min(1, float32Array[i]));
    buffer[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return buffer.buffer;
};

const sendToBackend = async (arrayBuffer) => {
  try {
    isSending.value = true;
    console.log(`📤 开始发送音频到后端...`);
    console.log(`📊 音频数据大小: ${arrayBuffer.byteLength} 字节`);
    console.log(`📊 音频时长估算: ${(arrayBuffer.byteLength / 32000).toFixed(2)} 秒`);
    
    const formData = new FormData();
    formData.append('audio', new Blob([arrayBuffer], { type: 'audio/pcm; sample_rate=16000' }));
    
    console.log(`🔌 正在连接后端接口: /asr/speech-to-text/`);
    const startTime = Date.now();
    
    const response = await api.post('/asr/speech-to-text/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    const responseTime = Date.now() - startTime;
    console.log(`⏱️  后端响应时间: ${responseTime}ms`);
    
    if (response.result === 'success' && response.text) {
      console.log(`✅ 语音识别成功!`);
      console.log(`📝 识别结果: "${response.text}"`);
      await sendMessage(null, response.text);
    } else if (response.result === 'success' && !response.text) {
      console.log(`⚠️  语音识别完成，但未识别到内容`);
    } else {
      console.error(`❌ 语音识别失败: ${response.result || response.error || '未知错误'}`);
    }
  } catch (error) {
    console.error(`❌ 发送音频失败:`);
    console.error(`   - 错误类型: ${error.name}`);
    console.error(`   - 错误信息: ${error.message}`);
    console.error(`   - 错误堆栈:`, error);
  } finally {
    isSending.value = false;
    audioLevel.value = 0;
  }
};

const toggleRecording = () => {
  if (!vadInstance) {
    console.log('🔴 首次点击，初始化VAD...');
    startRecording();
    isRecording.value = true;
    return;
  }
  
  if (isRecording.value) {
    try {
      if (typeof vadInstance.stop === 'function') {
        vadInstance.stop();
      } else if (typeof vadInstance.destroy === 'function') {
        vadInstance.destroy();
      }
      console.log('⏹️  停止VAD监听');
    } catch (e) {
      console.warn('⚠️  停止VAD失败:', e.message);
    }
    
    vadInstance = null;
    isRecording.value = false;
    isSpeaking.value = false;
    stopDurationTimer();
    audioLevel.value = 0;
    console.log('⏹️  关闭语音识别');
  } else {
    console.log('▶️  重新初始化VAD...');
    startRecording();
    isRecording.value = true;
    console.log('▶️  打开语音识别');
  }
};


async function scrollToBottom() {
  await nextTick()
  if (chatRef.value) {
    chatRef.value.scrollTop = chatRef.value.scrollHeight
  }
}

// 生命周期
onMounted(() => {
  updateUserFromLocalStorage()
  syncUserProfile()
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
  if (vadInstance) {
    vadInstance.destroy()
    vadInstance = null
  }
})
</script>

<style scoped>
.glass-panel {
  backdrop-filter: blur(20px);
  background-color: rgba(247, 249, 251, 0.7);
}

/* 可添加自定义样式 */
</style>
