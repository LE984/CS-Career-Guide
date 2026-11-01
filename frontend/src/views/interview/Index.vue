<template>
  <div class="interview-page">
    <main class="career-container interview-workspace">
      <header class="interview-heading">
        <div><p class="career-eyebrow">求职准备 / AI 模拟面试</p><h1>{{ isInterviewing ? '专注回答，慢慢把经历讲清楚' : '开始一场模拟面试' }}</h1><p>围绕自己的简历与项目练习表达，结束后查看整场复盘。</p></div>
        <div v-if="isInterviewing" class="interview-controls"><span class="interview-timer">{{ formatTime(remainingTime) }}</span><button class="career-button" @click="pauseInterview">{{ isPaused ? '继续面试' : '暂停面试' }}</button><button class="career-button end-interview" @click="hangupInterview">结束面试</button></div>
        <span v-else class="interview-duration">15 分钟 · 文字 / 语音回答</span>
      </header>
      <div class="interview-layout" :class="{ 'is-running': isInterviewing }">
        <section class="interview-main" aria-label="模拟面试">
          <div v-if="!isInterviewing" class="interview-setup">
            <div class="interview-section-heading"><span class="section-node" aria-hidden="true"></span><div><h2>选择面试风格</h2><p>根据这次想练习的内容选择，开始前可以更改。</p></div></div>
            <div class="interview-style-grid"><button v-for="style in interviewStyleOptions" :key="style.id" type="button" class="interview-style" :class="{ 'is-selected': selectedStyle === style.id }" :aria-pressed="selectedStyle === style.id" @click="selectedStyle = style.id"><span class="style-radio" aria-hidden="true"></span><div><strong>{{ style.title }}</strong><p>{{ style.description }}</p></div><span v-if="selectedStyle === style.id" class="selected-caption">已选择</span></button></div>
            <div class="interview-start"><p>建议先保存简历，面试会结合已有的简历内容展开。</p><button type="button" class="career-button career-button-primary" @click="startInterview">开始面试 →</button></div>
          </div>
          <div v-if="isInterviewing || messages.length" ref="chatRef" class="interview-chat" aria-label="面试对话" aria-live="polite" aria-relevant="additions text">
            <div v-for="(msg,index) in messages" :key="index" class="interview-message" :class="{ 'is-user': msg.type !== 'ai' }">
              <span class="interview-message-avatar">{{ msg.type === 'ai' ? 'AI' : '我' }}</span>
              <div class="interview-message-body"><span class="interview-message-label">{{ msg.type === 'ai' ? '面试官' : '我的回答' }}</span><p v-if="msg.content">{{ msg.content }}</p><span v-else class="interview-thinking" role="status">正在组织问题…</span></div>
            </div>
          </div>
          <div v-if="isInterviewing" class="interview-input">
            <p class="recording-state" role="status"><span :class="{ 'is-recording': isRecording }"></span>{{ isRecording ? (isSpeaking ? '正在识别语音' : '麦克风已开启，等待说话') : '麦克风未开启，可直接输入回答' }}<span v-if="isPaused" class="paused-state">面试已暂停</span></p>
            <label class="sr-only" for="interview-answer">你的面试回答</label>
            <textarea id="interview-answer" ref="inputRef" v-model="inputMessage" placeholder="输入你的回答，也可以点击麦克风使用语音…" :disabled="isLoading" @keydown.enter.prevent="sendMessage"></textarea>
            <div class="interview-input-actions"><span>Enter 发送回答</span><div><button type="button" class="career-button microphone-button" :class="{ 'is-recording': isRecording }" :aria-pressed="isRecording" :aria-label="isRecording ? '关闭麦克风' : '开启麦克风'" @click="toggleRecording"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="9" y="2" width="6" height="13" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/></svg>{{ isRecording ? '关闭语音' : '语音回答' }}</button><button type="button" class="career-button career-button-primary" :disabled="isLoading || !inputMessage.trim()" @click="sendMessage">{{ isLoading ? '回复中…' : '发送回答 →' }}</button></div></div>
          </div>
        </section>
        <aside class="interview-aside"><section><h2>这次，试着把这些讲清楚</h2><ol><li><span>01</span><div><h3>具体做了什么</h3><p>从项目背景开始，说明自己负责的部分。</p></div></li><li><span>02</span><div><h3>为什么这样做</h3><p>解释选择依据，比较考虑过的其他方案。</p></div></li><li><span>03</span><div><h3>结果如何验证</h3><p>说清测试方式和观察结果，不确定的地方如实说明。</p></div></li></ol></section><section class="interview-help"><h2>开始前的小检查</h2><p>已保存最新简历<br />找一个适合说话的环境<br />语音回答时允许麦克风权限</p><router-link to="/resume" class="career-link">查看并完善简历 →</router-link></section><details class="interview-tips"><summary>回答问题的小提示</summary><p>按“背景 → 任务 → 行动 → 结果”组织经历。不会的问题可以说明思路，不需要编造经历和数字。</p></details></aside>
      </div>
    </main>
    <div v-if="showReview" class="interview-review-overlay" role="dialog" aria-modal="true" aria-labelledby="interview-review-title">
      <section class="interview-review-dialog"><header><h2 id="interview-review-title">面试复盘报告</h2><button type="button" class="career-button" aria-label="关闭复盘报告" @click="showReview = false">关闭 ×</button></header><div class="interview-review-body"><div v-if="!reviewContent" class="review-loading" role="status"><span class="loading loading-spinner loading-md"></span>正在生成整场复盘，请稍候…</div><p v-else>{{ reviewContent }}</p></div><footer><button class="career-button career-button-primary" @click="showReview = false">关闭报告</button></footer></section>
    </div>
  </div>
</template>

<script setup>
import { VAD_ASSET_BASE_URL, ENABLE_TTS } from '@/config'
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { userAPI } from '@/api'
import { interviewService } from '@/features/interview'

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

// The page renders normalized interview events; the service owns the implementation.
async function presentInterviewEvent(index, event) {
  const message = messages.value[index]
  if (event.type === 'thinking' || event.type === 'error') {
    message.content = event.content
    await scrollToBottom()
  } else if (event.type === 'chunk' && event.content) {
    message.content = message.content === 'AI正在思考...'
      ? event.content : message.content + event.content
    await scrollToBottom()
  } else if (event.type === 'end') {
    if (event.session_id) sessionId.value = event.session_id
    nextTick(() => inputRef.value?.focus())
  } else if (event.type === 'audio' && ENABLE_TTS && event.audio) {
    handleAudioChunk(event.audio)
  } else if (event.type === 'debug' && event.message?.includes('task-finished')) {
    finishAudio()
  }
}

async function startInterview() {
  isInterviewing.value = true
  isLoading.value = true
  messages.value = []
  remainingTime.value = 900
  await requestAudioPermission()
  initAudioStream()
  startTimer()
  const index = messages.value.length
  messages.value.push({ type: 'ai', content: '' })
  nextTick(() => inputRef.value?.focus())
  try {
    await interviewService.start({
      style: selectedStyle.value, sessionId: sessionId.value
    }, event => presentInterviewEvent(index, event))
  } catch (error) {
    console.error('开始面试失败:', error)
    messages.value.push({ type: 'ai', content: '抱歉，面试服务暂时不可用，请稍后再试。' })
  } finally {
    isLoading.value = false
    nextTick(() => inputRef.value?.focus())
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
  const content = (audioMsg || inputMessage.value).trim()
  if (!content || !isInterviewing.value || isLoading.value) return
  messages.value.push({ type: 'user', content })
  await scrollToBottom()
  if (!audioMsg) inputMessage.value = ''
  isLoading.value = true
  const index = messages.value.length
  messages.value.push({ type: 'ai', content: '' })
  nextTick(() => inputRef.value?.focus())
  try {
    await requestAudioPermission()
    initAudioStream()
    await interviewService.answer({
      answer: content, style: selectedStyle.value, sessionId: sessionId.value
    }, event => presentInterviewEvent(index, event))
  } catch (error) {
    console.error('发送回答失败:', error)
    messages.value.push({ type: 'ai', content: '抱歉，面试服务暂时不可用，请稍后再试。' })
  } finally {
    isLoading.value = false
    nextTick(() => inputRef.value?.focus())
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

async function generateReview() {
  reviewContent.value = ''
  showReview.value = true
  try {
    const review = await interviewService.generateReview({
      messages: messages.value, style: selectedStyle.value, sessionId: sessionId.value
    }, event => {
      if (event.type === 'chunk' && event.content) reviewContent.value += event.content
    })
    reviewContent.value = review.content
    if (!review.skipped) await saveReviewRecord(review.content)
  } catch (error) {
    console.error('生成复盘失败:', error)
    reviewContent.value = `生成复盘时遇到问题：${error.message}\n\n请稍后重试，或检查网络连接。`
  }
}

async function saveReviewRecord(content) {
  try {
    const result = await interviewService.saveReview({
      messages: messages.value, content, style: selectedStyle.value,
      sessionId: sessionId.value, remainingTime: remainingTime.value
    })
    if (!result.success) console.error('保存复盘记录失败:', result.error)
  } catch (error) {
    console.error('保存复盘记录失败:', error)
  }
}

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

    const response = await interviewService.transcribe(formData);

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

const interviewStyleOptions = [
  { id: 'gentle', title: '温和面', description: '以引导和交流为主，适合第一次练习或热身。' },
  { id: 'technical', title: '技术面', description: '围绕项目与技术原理，练习解释方案和取舍。' },
  { id: 'pressure', title: '压力面', description: '面对更直接的追问，练习保持节奏与清楚表达。' },
  { id: 'behavioral', title: '行为面', description: '回顾团队协作、沟通与解决问题的真实经历。' },
]
</script>

<style scoped>
.interview-page {
  padding: 30px 0 40px;
  background: var(--career-bg);
}
.interview-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  margin-bottom: 26px;
}
.interview-heading h1 {
  font-size: 27px;
  font-weight: 600;
  color: var(--career-text);
  margin: 12px 0 8px;
  letter-spacing: -.025em;
}
.interview-heading > div > p:last-child {
  font-size: 14px;
  line-height: 1.8;
  color: var(--career-muted);
}
.interview-controls {
  display: flex;
  align-items: center;
  flex: none;
  gap: 8px;
}
.interview-controls .career-button {
  font-size: 13px;
}
.interview-timer {
  font: 18px ui-monospace, Consolas, monospace;
  color: #344054;
  margin-right: 14px;
  font-variant-numeric: tabular-nums;
}
.end-interview {
  color: #b42318;
  border-color: #f0cfcb;
}
.end-interview:hover {
  background: #fff4f2;
}
.interview-duration {
  font-size: 13px;
  color: var(--career-muted);
  padding-bottom: 4px;
}
.interview-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 24px;
  align-items: start;
}
.interview-main {
  min-width: 0;
  border: 1px solid var(--career-border);
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}
.interview-setup {
  padding: 30px;
}
.interview-section-heading {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.section-node {
  width: 9px;
  height: 9px;
  border: 2px solid var(--career-blue);
  border-radius: 50%;
  margin-top: 7px;
  flex: none;
}
.interview-section-heading h2 {
  font-size: 18px;
  color: #344054;
  font-weight: 600;
}
.interview-section-heading p {
  color: var(--career-muted);
  font-size: 13px;
  margin-top: 7px;
}
.interview-style-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 14px;
  margin-top: 26px;
}
.interview-style {
  display: flex;
  align-items: flex-start;
  text-align: left;
  gap: 12px;
  min-height: 130px;
  border: 1px solid var(--career-border);
  border-radius: 7px;
  padding: 20px 16px;
  background: #fff;
  position: relative;
}
.interview-style:hover {
  border-color: #9bbce3;
}
.interview-style.is-selected {
  border-color: var(--career-blue);
  background: #f4f8ff;
}
.style-radio {
  width: 14px;
  height: 14px;
  border: 1px solid #a8b6c9;
  border-radius: 50%;
  margin-top: 3px;
  flex: none;
}
.is-selected .style-radio {
  border: 4px solid var(--career-blue);
}
.interview-style strong {
  font-size: 15px;
  font-weight: 600;
  color: #344054;
}
.interview-style p {
  margin-top: 9px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--career-muted);
}
.selected-caption {
  position: absolute;
  top: 19px;
  right: 14px;
  color: var(--career-blue);
  font-size: 11px;
}
.interview-start {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-top: 26px;
  padding-top: 24px;
  border-top: 1px solid var(--career-border);
}
.interview-start p {
  color: var(--career-muted);
  font-size: 13px;
  line-height: 1.8;
}
.interview-start button {
  flex: none;
}
.interview-aside {
  display: grid;
  gap: 18px;
}
.interview-aside > section, .interview-tips {
  background: #fff;
  padding: 22px;
  border: 1px solid var(--career-border);
  border-radius: 8px;
}
.interview-aside h2 {
  font-size: 14px;
  font-weight: 600;
  color: #344054;
}
.interview-aside ol {
  display: grid;
  gap: 22px;
  margin-top: 22px;
}
.interview-aside li {
  display: flex;
  gap: 12px;
}
.interview-aside li > span {
  color: #7d9abb;
  font: 11px ui-monospace,Consolas,monospace;
  padding-top: 3px;
}
.interview-aside h3 {
  font-size: 13px;
  color: #344054;
  font-weight: 500;
}
.interview-aside p {
  font-size: 13px;
  line-height: 1.85;
  color: var(--career-muted);
  margin-top: 6px;
}
.interview-help p {
  margin: 15px 0;
  line-height: 2.2;
}
.interview-help a {
  font-size: 13px;
}
.interview-tips summary {
  cursor: pointer;
  font-size: 13px;
  color: #475467;
}
.interview-tips p {
  margin-top: 12px;
}
.is-running .interview-main {
  display: flex;
  flex-direction: column;
  height: max(480px, calc(100vh - 250px));
}
.interview-chat {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 30px;
  scroll-behavior: smooth;
}
.interview-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 26px;
}
.interview-message-avatar {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex: none;
  background: var(--career-blue-soft);
  color: var(--career-blue);
  border: 1px solid #d0e1f7;
  border-radius: 50%;
  font-size: 11px;
}
.interview-message-body {
  min-width: 0;
  flex: 1;
}
.interview-message-label {
  font-size: 12px;
  color: #7a8799;
}
.interview-message-body > p {
  margin-top: 8px;
  font-size: 15px;
  color: #27374d;
  line-height: 1.9;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.is-user .interview-message-avatar {
  background: #f1f4f8;
  color: #586577;
  border-color: #dfe5ec;
}
.is-user .interview-message-body > p {
  background: #f6f8fb;
  border: 1px solid #e3e9f0;
  border-radius: 6px;
  padding: 14px 16px;
  font-size: 14px;
}
.interview-thinking {
  display: block;
  margin-top: 10px;
  font-size: 13px;
  color: var(--career-muted);
}
.interview-input {
  flex: none;
  border-top: 1px solid var(--career-border);
  padding: 16px 22px;
  background: #fff;
}
.recording-state {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: #7a8799;
  margin-bottom: 12px;
}
.recording-state > span:first-child {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #b5c0ce;
}
.recording-state > .is-recording:first-child {
  background: #da4d46;
}
.paused-state {
  margin-left: auto;
  color: #b27916;
}
.interview-input textarea {
  display: block;
  width: 100%;
  min-height: 85px;
  max-height: 180px;
  resize: vertical;
  border: 1px solid #ced8e5;
  border-radius: 5px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.8;
  color: #27374d;
  background: #fff;
}
.interview-input textarea::placeholder {
  color: #95a0b0;
}
.interview-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}
.interview-input-actions > span {
  color: #8a97a8;
  font-size: 12px;
}
.interview-input-actions > div {
  display: flex;
  gap: 8px;
}
.interview-input-actions .career-button {
  min-height: 35px;
  padding: 8px 12px;
  font-size: 13px;
}
.microphone-button.is-recording {
  color: #b42318;
  border-color: #edc7c1;
  background: #fff4f2;
}
.interview-review-overlay {
  position: fixed;
  inset: 0;
  background: #1d293966;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 24px;
}
.interview-review-dialog {
  width: min(780px, 100%);
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 24px 80px #1d293926;
}
.interview-review-dialog > header, .interview-review-dialog > footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid var(--career-border);
}
.interview-review-dialog h2 {
  font-size: 20px;
  color: #344054;
}
.interview-review-body {
  padding: 26px;
  max-height: 60vh;
  overflow-y: auto;
}
.interview-review-body > p {
  white-space: pre-wrap;
  line-height: 1.9;
  font-size: 14px;
}
.interview-review-dialog > footer {
  justify-content: flex-end;
  border-top: 1px solid var(--career-border);
  border-bottom: 0;
}
.review-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 40px 0;
  color: var(--career-muted);
  font-size: 14px;
}
@media (max-width: 1100px) {
  .interview-layout {
    grid-template-columns: minmax(0, 1fr) 250px;
  }
  .interview-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
  }
  .interview-setup {
    padding: 22px;
  }
}
@media (max-width: 760px) {
  .interview-layout {
    grid-template-columns: 1fr;
  }
  .interview-style-grid {
    grid-template-columns: 1fr;
  }
  .interview-start {
    flex-direction: column;
    align-items: flex-start;
  }
  .interview-heading h1 {
    font-size: 25px;
  }
  .is-running .interview-main {
    height: max(500px, calc(100dvh - 240px));
  }
  .interview-chat {
    padding: 20px 16px;
  }
  .interview-input {
    padding: 14px;
  }
  .interview-input-actions > span {
    display: none;
  }
  .interview-input-actions > div {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
