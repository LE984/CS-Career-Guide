<template>
  <div class="fixed bottom-6 right-6 z-50" ref="container">
    <!-- 折叠状态 -->
    <div v-if="!isOpen" class="flex flex-col items-end">
      <div class="relative mb-2 animate-bounce">
        <div class="bg-base-100 text-base-content text-xs px-4 py-2 rounded-2xl shadow-lg border border-base-200 max-w-[120px] text-center">
          有问题戳我
        </div>
        <div class="absolute -bottom-1 right-8 w-3 h-3 bg-base-100 transform rotate-45 border-r border-b border-base-200"></div>
      </div>
      <div 
        ref="modelContainer" 
        class="w-32 h-48 cursor-move relative transition-transform hover:scale-105" 
        @dblclick="isOpen = true"
        @mousedown="startDrag"
        @mousemove="onDrag"
        @mouseup="endDrag"
        @mouseleave="endDrag"
      >
        <!-- 数字人将在这里渲染 -->
      </div>
    </div>
    
    <!-- 展开状态 -->
    <div 
      v-else 
      class="glass-card w-96 max-w-[90vw] overflow-hidden flex flex-col shadow-2xl animate-fade-in-up"
      style="height: 600px; max-height: 80vh;"
    >
      <!-- 头部 -->
      <div 
        class="bg-gradient-to-r from-primary to-accent text-white p-4 flex justify-between items-center cursor-move"
        @mousedown="startDrag"
        @mousemove="onDrag"
        @mouseup="endDrag"
        @mouseleave="endDrag"
      >
        <div class="flex items-center gap-2">
          <div class="p-1.5 bg-white/20 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div>
            <h3 class="font-bold text-sm">AI 智能助手</h3>
            <div class="flex items-center gap-1 mt-0.5">
              <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              <span class="text-xs opacity-90">在线中</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <select v-model="currentMode" class="select select-xs select-ghost text-white bg-white/10 border-none focus:bg-white/20">
              <option value="career" class="text-base-content">职业规划</option>
              <option value="normal" class="text-base-content">闲聊模式</option>
            </select>
          <button @click="isOpen = false" class="btn btn-xs btn-circle btn-ghost text-white hover:bg-white/20">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- 数字人区域 (Mini) -->
      <div class="bg-gradient-to-b from-primary/5 to-transparent h-32 relative shrink-0">
        <div ref="expandedModelContainer" class="w-full h-full absolute inset-0">
          <!-- 数字人将在这里渲染 -->
        </div>
      </div>
      
      <!-- 消息区域 -->
      <div class="flex-1 overflow-hidden relative bg-base-100/50 backdrop-blur-sm">
        <div ref="scrollRef" class="h-full overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-base-300 scrollbar-track-transparent" @scroll="handleScroll">
          <!-- 加载更多指示器 -->
          <div v-if="isLoadingMore" class="flex justify-center py-2">
            <span class="loading loading-spinner loading-xs text-primary"></span>
          </div>
          
          <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-center p-4 opacity-60">
            <div class="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-3 text-primary">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p class="text-sm font-medium">{{ currentMode === 'career' ? '我是您的专属职业规划师' : '我是AI智能助手' }}</p>
            <p class="text-xs mt-1">有什么可以帮您的吗？</p>
          </div>
          
          <template v-else>
            <!-- 按对话回合分组展示消息 -->
            <div v-for="(round, roundIndex) in groupedMessages" :key="roundIndex" class="space-y-4">
              <!-- 公司信息卡片（单独展示） -->
              <div v-if="round.type === 'company'" class="max-w-[90%] bg-white rounded-2xl shadow-md border border-base-200 overflow-hidden mx-auto">
                <div class="p-4">
                  <h4 class="font-bold text-sm text-primary mb-2">{{ round.content.name }}</h4>
                  <div class="text-xs text-base-content/70 space-y-1">
                    <p class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {{ round.content.address }}
                    </p>
                    <p v-if="round.content.scale" class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      {{ round.content.scale }}
                    </p>
                    <p v-if="round.content.industry" class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      {{ round.content.industry }}
                    </p>
                    <p v-if="round.content.salary_range" class="flex items-center gap-1 text-secondary font-medium">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {{ round.content.salary_range }}
                    </p>
                    <p v-if="round.content.job_title" class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      {{ round.content.job_title }}
                    </p>
                  </div>
                </div>
              </div>
              
              <!-- 对话回合 -->
              <div v-else class="space-y-2">
                <!-- 用户消息 -->
                <div class="flex justify-end">
                  <div class="max-w-[85%] p-3 rounded-2xl text-sm shadow-sm relative group bg-primary text-white rounded-tr-none ml-8">
                    <p class="whitespace-pre-wrap leading-relaxed">{{ round.userMessage }}</p>
                    <span class="text-[10px] opacity-50 absolute bottom-1 right-2 text-white">
                      {{ round.timestamp }}
                    </span>
                  </div>
                </div>
                
                <!-- AI消息 -->
                <div class="flex justify-start">
                  <div class="max-w-[85%] p-3 rounded-2xl text-sm shadow-sm relative group bg-white text-base-content rounded-tl-none mr-8 border border-base-200">
                    <p class="whitespace-pre-wrap leading-relaxed">{{ round.aiMessage }}</p>
                    <span class="text-[10px] opacity-50 absolute bottom-1 right-2 text-base-content">
                      {{ round.timestamp }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
        
          </template>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="p-3 bg-white border-t border-base-200">
        <form @submit.prevent="sendMessage" class="flex gap-2 relative">
          <input 
            ref="inputRef"
            v-model="inputMessage" 
            type="text" 
            :placeholder="currentMode === 'career' ? '咨询职业规划问题...' : '输入您的问题...'"
            class="input input-bordered input-sm w-full rounded-full pl-4 pr-10 focus:shadow-glow transition-shadow bg-base-100"
            :disabled="isLoading"
          >
          <button 
            type="submit" 
            class="btn btn-sm btn-circle btn-primary absolute right-1 top-0 bottom-0 my-auto shadow-md hover:scale-105 transition-transform"
            :disabled="isLoading || !inputMessage.trim()"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { apiUrl, AVATAR_MODEL_URL } from '@/config'
import { apiFetch } from '@/api'

const isOpen = ref(false)
const inputMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const isLoadingMore = ref(false)
const scrollRef = ref(null)
const modelContainer = ref(null)
const expandedModelContainer = ref(null)
const hasMoreMessages = ref(true)
const sessionId = ref('')
const container = ref(null)
const currentMode = ref('career') // 默认使用职业规划模式
const inputRef = ref(null)

// 计算属性：按对话回合分组消息
const groupedMessages = computed(() => {
  const groups = []
  let currentRound = null
  
  messages.value.forEach((msg, index) => {
    if (msg.type === 'company') {
      // 公司信息单独分组
      groups.push({
        type: 'company',
        content: msg.content
      })
    } else if (msg.type === 'user') {
      // 开始新的对话回合
      currentRound = {
        userMessage: msg.content,
        aiMessage: '',
        timestamp: msg.timestamp || new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
      }
    } else if (msg.type === 'ai' && currentRound) {
      // 完成对话回合
      currentRound.aiMessage = msg.content
      groups.push(currentRound)
      currentRound = null
    }
  })
  
  return groups
})

// 拖拽相关变量
const isDragging = ref(false)
const startX = ref(0)
const startY = ref(0)

// 旋转相关变量
const isRotating = ref(false)
const rotateStartX = ref(0)
const rotateStartY = ref(0)
const currentRotation = ref({ x: 0, y: 0 })

// 3D scene variables
let scene = null
let camera = null
let renderer = null
let model = null
let animationId = null

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  // 限制消息长度
  const maxMessageLength = 500
  let userMessage = inputMessage.value.trim()
  if (userMessage.length > maxMessageLength) {
    userMessage = userMessage.substring(0, maxMessageLength) + '...'
  }
  
  const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
  
  messages.value.push({
    type: 'user',
    content: userMessage,
    timestamp: timestamp
  })
  await scrollToBottom()
  
  inputMessage.value = ''
  isLoading.value = true
  
  const aiMessageIndex = messages.value.length
  messages.value.push({
    type: 'ai',
    content: 'AI正在思考...',
    timestamp: timestamp
  })
  
  try {
    let message = userMessage
    let mode = 'normal'
    
    if (currentMode.value === 'career') {
      message = userMessage
      mode = 'career'
    } else if (currentMode.value === 'normal') {
      message = userMessage
      mode = 'normal'
    }
    
    console.log('发送API请求:', {
      url: apiUrl('/ai/llm/chat/'),
      mode: mode,
      message: message.substring(0, 50) + '...',
      session_id: sessionId.value
    })
    
    const response = await apiFetch('/ai/llm/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        message: message,
        mode: mode,
        session_id: sessionId.value
      })
    })
    
    console.log('API响应状态:', response.status)
    console.log('API响应状态文本:', response.statusText)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('API请求失败:', errorText)
      throw new Error(`API请求失败: ${response.status} ${response.statusText}`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      const lines = buffer.split('\n\n')
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i]
        if (line.startsWith('data:')) {
          const dataStr = line.substring(5).trim()
          if (!dataStr) continue // 跳过空数据行
          
          try {
            const data = JSON.parse(dataStr)
            
            if (data.type === 'thinking') {
              messages.value[aiMessageIndex].content = data.content
              await scrollToBottom()
            } else if (data.type === 'chunk') {
              if (data.content) { // 只处理非空内容
                if (messages.value[aiMessageIndex].content === 'AI正在思考...') {
                  messages.value[aiMessageIndex].content = data.content
                } else {
                  messages.value[aiMessageIndex].content += data.content
                }
                // 限制AI消息长度
                const maxMessageLength = 1000
                if (messages.value[aiMessageIndex].content.length > maxMessageLength) {
                  messages.value[aiMessageIndex].content = messages.value[aiMessageIndex].content.substring(0, maxMessageLength) + '...'
                }
                await scrollToBottom()
              }

            } else if (data.type === 'companies') {
              // 处理公司信息
              console.log('收到公司信息:', data.data)
              // 对于职业规划模式，公司信息是重要的内容
              if (data.data && data.data.length > 0) {
                // 显示公司信息
                data.data.forEach(company => {
                  messages.value.push({
                    type: 'company',
                    content: company,
                    timestamp: timestamp
                  })
                })
                await scrollToBottom()
              }
            } else if (data.type === 'end') {
              if (data.session_id) {
                sessionId.value = data.session_id
              }
              await saveChatRecord()
            } else if (data.type === 'error') {
              messages.value[aiMessageIndex].content = data.content
              await scrollToBottom()
            }
          } catch (e) {
            console.error('解析SSE数据失败:', e)
            console.error('失败的JSON字符串:', dataStr)
          }
        }
      }
      
      buffer = lines[lines.length - 1]
    }
  } catch (error) {
    console.error('AI回答失败:', error)
    console.error('错误类型:', typeof error)
    console.error('错误堆栈:', error.stack)
    messages.value[aiMessageIndex].content = `抱歉，我暂时无法回答你的问题，请稍后再试。\n错误信息: ${error.message}`
    isLoading.value = false
    await scrollToBottom()
  } finally {
    isLoading.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  }
}

async function saveChatRecord() {
  if (!sessionId.value || messages.value.length < 2) return
  
  const userMsg = messages.value[messages.value.length - 2]
  const aiMsg = messages.value[messages.value.length - 1]
  
  if (userMsg?.type !== 'user' || aiMsg?.type !== 'ai') return
  
  try {
    await apiFetch('/ai/llm/save-chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId.value,
        user_message: userMsg.content,
        assistant_message: aiMsg.content,
        mode: currentMode.value === 'career' ? 'career' : 'normal'
      })
    })
  } catch (error) {
    console.error('保存聊天记录失败:', error)
  }
}

async function loadMoreMessages() {
  return
}

function handleScroll() {
  if (scrollRef.value && scrollRef.value.scrollTop <= 50 && hasMoreMessages.value && !isLoadingMore.value) {
    loadMoreMessages()
  }
}

function startDrag(event) {
  const target = event.target
  if (target.closest('input') || target.closest('button') || target.closest('form') || target.closest('select')) {
    return
  }
  
  if (event.button === 0) {
    isDragging.value = true
    startX.value = event.clientX - container.value.getBoundingClientRect().left
    startY.value = event.clientY - container.value.getBoundingClientRect().top
    event.preventDefault()
  } else if (event.button === 2) {
    isRotating.value = true
    rotateStartX.value = event.clientX
    rotateStartY.value = event.clientY
    event.preventDefault()
  }
}

function onDrag(event) {
  const target = event.target
  if (target.closest('input') || target.closest('button') || target.closest('form') || target.closest('select')) {
    return
  }
  
  if (isDragging.value) {
    const clientX = event.clientX - container.value.getBoundingClientRect().left
    const clientY = event.clientY - container.value.getBoundingClientRect().top
    
    const dx = clientX - startX.value
    const dy = clientY - startY.value
    
    const rect = container.value.getBoundingClientRect()
    container.value.style.left = `${rect.left + dx}px`
    container.value.style.top = `${rect.top + dy}px`
    container.value.style.right = 'auto'
    container.value.style.bottom = 'auto'
  } else if (isRotating.value) {
    const dx = event.clientX - rotateStartX.value
    const dy = event.clientY - rotateStartY.value
    
    currentRotation.value.y += dx * 0.003
    currentRotation.value.x += dy * 0.003
  }
}

function endDrag() {
  isDragging.value = false
  isRotating.value = false
}

function initScene() {
  const currentContainer = isOpen.value ? expandedModelContainer.value : modelContainer.value
  if (!currentContainer) return
  
  scene = new THREE.Scene()
  scene.background = null
  
  camera = new THREE.PerspectiveCamera(45, currentContainer.clientWidth / currentContainer.clientHeight, 0.1, 1000)
  camera.position.z = 5
  
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  // 设置像素比，提高清晰度
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(currentContainer.clientWidth, currentContainer.clientHeight)
  currentContainer.appendChild(renderer.domElement)
  
  const ambientLight = new THREE.AmbientLight(0xffffff, 1.2)
  scene.add(ambientLight)
  
  const directionalLight = new THREE.DirectionalLight(0xffffff, 1.8)
  directionalLight.position.set(1, 1, 1)
  scene.add(directionalLight)
  
  const loader = new GLTFLoader()
  loader.load(AVATAR_MODEL_URL, (gltf) => {
    model = gltf.scene
    scene.add(model)
    
    const isCollapsed = !isOpen.value
    if (isCollapsed) {
      model.position.set(0, -1.8, 0)
      model.scale.set(3, 3, 3)
    } else {
      model.position.set(0, -1.5, 0)
      model.scale.set(3, 3, 3)
    }
    
    animate()
  }, (xhr) => {
    console.log((xhr.loaded / xhr.total * 100) + '% loaded')
  }, (error) => {
    console.error('模型加载失败:', error)
  })
}

function animate() {
  animationId = requestAnimationFrame(animate)
  
  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

function cleanupScene() {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  
  if (renderer) {
    if (modelContainer.value && modelContainer.value.contains(renderer.domElement)) {
      modelContainer.value.removeChild(renderer.domElement)
    } else if (expandedModelContainer.value && expandedModelContainer.value.contains(renderer.domElement)) {
      expandedModelContainer.value.removeChild(renderer.domElement)
    }
    renderer.dispose()
  }
  
  if (scene) {
    scene.traverse((object) => {
      if (object.isMesh) {
        object.geometry.dispose()
        if (object.material.isMaterial) {
          object.material.dispose()
        } else if (Array.isArray(object.material)) {
          object.material.forEach(material => material.dispose())
        }
      }
    })
  }
  
  scene = null
  camera = null
  renderer = null
  model = null
  animationId = null
}

function adjustPosition() {
  if (!container.value) return
  
  const rect = container.value.getBoundingClientRect()
  const windowWidth = window.innerWidth
  const windowHeight = window.innerHeight
  
  let newLeft = rect.left
  let newTop = rect.top
  
  // 检查右侧边界
  if (rect.right > windowWidth) {
    newLeft = windowWidth - rect.width - 24 // 24px margin
  }
  
  // 检查底部边界
  if (rect.bottom > windowHeight) {
    newTop = windowHeight - rect.height - 24 // 24px margin
  }
  
  // 检查左侧边界
  if (newLeft < 24) {
    newLeft = 24 // 24px margin
  }
  
  // 检查顶部边界
  if (newTop < 24) {
    newTop = 24 // 24px margin
  }
  
  // 应用新位置
  container.value.style.left = `${newLeft}px`
  container.value.style.top = `${newTop}px`
  container.value.style.right = 'auto'
  container.value.style.bottom = 'auto'
}

watch(isOpen, (newValue) => {
  if (newValue) {
    cleanupScene()
    setTimeout(() => {
      initScene()
      adjustPosition()
      // 自动聚焦输入框
      nextTick(() => {
        if (inputRef.value) {
          inputRef.value.focus()
        }
      })
    }, 100)
  } else {
    cleanupScene()
    setTimeout(initScene, 100)
  }
})

onMounted(() => {
  container.value = document.querySelector('.fixed.bottom-6.right-6.z-50')
  
  if (modelContainer.value) {
    modelContainer.value.addEventListener('contextmenu', (event) => {
      event.preventDefault()
    })
  }
  
  if (expandedModelContainer.value) {
    expandedModelContainer.value.addEventListener('contextmenu', (event) => {
      event.preventDefault()
    })
  }
  
  setTimeout(initScene, 100)
})

onUnmounted(() => {
  cleanupScene()
})
</script>

<style scoped>
/* 可添加自定义样式 */
.whitespace-pre-wrap {
  white-space: pre-wrap;
  word-break: break-word;
}

.disabled\:bg-gray-400:disabled {
  background-color: #9ca3af;
}
</style>
