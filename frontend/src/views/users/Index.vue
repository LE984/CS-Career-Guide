<template>
  <div class="bg-gradient-to-r from-white to-purple-100 text-on-surface min-h-screen">
    <!-- Main Content Canvas -->
    <main class="pt-24 pb-12 px-8 max-w-7xl mx-auto">
      <!-- Message Notification -->
      <div v-if="message" :class="['fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg transition-all duration-300 transform translate-y-0 opacity-100', 
        messageType === 'success' ? 'bg-green-500 text-white' : 
        messageType === 'error' ? 'bg-red-500 text-white' : 
        'bg-blue-500 text-white']">
        {{ message }}
      </div>
      <!-- Header Section: Identity & Bio -->
      <header class="mb-12 flex flex-col md:flex-row gap-8 items-start justify-between">
        <div class="flex flex-col gap-6 w-full">
          <div class="flex gap-6 items-center">
            <div class="relative">
              <div class="w-24 h-24 rounded-full overflow-hidden border-4 border-surface-container-lowest shadow-xl cursor-pointer" @click="triggerAvatarUpload">
                <img :src="avatarPreview || user?.avatar || '/avatars/default/default.jpg'" class="w-full h-full object-cover" alt="User Profile"/>
              </div>
              <input ref="avatarInput" type="file" accept="image/*" @change="handleAvatarChange" class="hidden"/>
            </div>
            <div>
              <div class="flex items-center gap-4">
                <h1 class="text-3xl font-extrabold tracking-tight text-primary">{{ user?.username || '用户名' }}</h1>
                <button @click="openEditModal" class="text-secondary text-sm font-bold flex items-center gap-1 hover:gap-2 transition-all p-2 rounded-md">
                  <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 20h9" />
                    <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
                  </svg>
                  编辑资料
                </button>

              </div>
              <div v-if="user?.profile" class="mt-3 text-on-primary-container font-medium">
                {{ user.profile }}
              </div>
              <div class="mt-3 flex flex-wrap gap-4 text-sm text-outline">
                <span class="flex items-center gap-1">学校: {{ user?.school || ' ' }}</span>
                <span class="flex items-center gap-1">专业: {{ user?.major || ' ' }}</span>
                <span class="flex items-center gap-1">学历: {{ user?.education || ' ' }}</span>
                <span class="flex items-center gap-1">邮箱: {{ user?.email || ' ' }}</span>
                <span class="flex items-center gap-1">地址: {{ user?.address || ' ' }}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- Body Section: Left-Right Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Content Area -->
        <div class="lg:col-span-2 space-y-8">
          <!-- Personal Information Section (Self Introduction + Career Recommendations) -->
          <div class="bg-white p-8 rounded-xl border border-gray-200 shadow-md">
            <h2 class="text-2xl font-bold mb-6 text-gray-800">个人信息</h2>
            
            <!-- Self Introduction -->
            <div class="mb-8">
              <h3 class="text-xl font-semibold mb-4 text-gray-700">自我介绍</h3>
              <div v-if="selfIntroduction" class="text-gray-800 leading-relaxed whitespace-pre-line">
                {{ selfIntroduction }}
              </div>
              <div v-else-if="user?.profile" class="text-gray-800 leading-relaxed whitespace-pre-line">
                {{ user.profile }}
              </div>
              <div v-else class="text-gray-500">
                暂无自我介绍内容，请在职业规划的自我介绍页面填写。
              </div>
            </div>
            
            <!-- Career Recommendations (only show if data exists) -->
            <div v-if="recommendations.length > 0">
              <h3 class="text-xl font-semibold mb-4 text-gray-700">职业推荐</h3>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div v-for="(rec, index) in recommendations" :key="index" class="bg-gray-50 p-6 rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="text-sm font-bold text-blue-600">{{ index + 1 }}</span>
                    <h4 class="text-lg font-bold text-gray-800">{{ rec.career }}</h4>
                  </div>
                  <div class="text-sm text-blue-600 mb-3">{{ rec.matchScore }}% 匹配</div>
                  <p class="text-sm text-gray-600">{{ rec.reason }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Mock Interview Review Section -->
          <div class="bg-white p-8 rounded-xl border border-gray-200 shadow-md">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-2xl font-bold text-gray-800">模拟面试复盘</h2>
              <button @click="goToInterview" class="text-blue-600 text-sm font-bold flex items-center gap-1 hover:gap-2 transition-all p-2 rounded-md">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
                </svg>
                开始面试
              </button>
            </div>
            
            <div v-if="loadingReviews" class="text-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
            
            <div v-else-if="interviewReviews.length > 0" class="space-y-4">
              <div 
                v-for="review in interviewReviews" 
                :key="review.id"
                class="bg-gray-50 p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
                @click="viewReviewDetail(review.session_id)"
              >
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm text-gray-500">{{ review.created_at }}</span>
                  <span class="text-xs text-blue-600">{{ review.pair_count }} 条记录</span>
                </div>
                <p class="text-gray-800">{{ review.latest_content }}</p>
              </div>
            </div>
            
            <div v-else class="text-center py-8">
              <div class="text-6xl mb-4">🎯</div>
              <p class="text-gray-500 mb-4">还没有面试复盘记录</p>
              <button @click="goToInterview" class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:opacity-90 transition-all">
                开始模拟面试
              </button>
            </div>
          </div>
        </div>
        
        <!-- Sidebar Section -->
        <div class="lg:col-span-1">
          <!-- Resume Section -->
          <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-md sticky top-24">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-xl font-bold text-gray-800">简历</h2>
              <button @click="goToResume" class="text-blue-600 text-sm font-bold flex items-center gap-1 hover:gap-2 transition-all p-2 rounded-md">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
                </svg>
                编辑
              </button>
            </div>
            
            <div v-if="resume" class="space-y-4">
              <!-- 基本信息 -->
              <div v-if="resume.name || resume.target_position">
                <h3 class="text-sm font-semibold mb-2 text-gray-700">基本信息</h3>
                <div class="space-y-2">
                  <div v-if="resume.name" class="bg-gray-50 p-3 rounded-lg">
                    <span class="text-xs text-gray-500">姓名</span>
                    <p class="font-medium text-sm text-gray-800">{{ resume.name }}</p>
                  </div>
                  <div v-if="resume.target_position" class="bg-gray-50 p-3 rounded-lg">
                    <span class="text-xs text-gray-500">意向岗位</span>
                    <p class="font-medium text-sm text-gray-800">{{ resume.target_position }}</p>
                  </div>
                </div>
              </div>
              
              <!-- 教育背景 -->
              <div v-if="resume.education && resume.education.length > 0">
                <h3 class="text-sm font-semibold mb-2 text-gray-700">教育背景</h3>
                <div class="space-y-2">
                  <div v-for="(edu, index) in resume.education.slice(0, 2)" :key="index" class="bg-gray-50 p-3 rounded-lg">
                    <div>
                      <p class="font-medium text-sm text-gray-800">{{ edu.school }}</p>
                      <p class="text-xs text-gray-500">{{ edu.major }} | {{ edu.degree }}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 实习经历 -->
              <div v-if="resume.experience && resume.experience.length > 0">
                <h3 class="text-sm font-semibold mb-2 text-gray-700">实习经历</h3>
                <div class="space-y-2">
                  <div v-for="(exp, index) in resume.experience.slice(0, 2)" :key="index" class="bg-gray-50 p-3 rounded-lg">
                    <div>
                      <p class="font-medium text-sm text-gray-800">{{ exp.company }}</p>
                      <p class="text-xs text-gray-500">{{ exp.position }}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 专业技能 -->
              <div v-if="resume.skills">
                <h3 class="text-sm font-semibold mb-2 text-gray-700">专业技能</h3>
                <div class="bg-gray-50 p-3 rounded-lg">
                  <p class="text-sm text-gray-800 line-clamp-3">{{ resume.skills }}</p>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-6">
              <div class="text-4xl mb-3">📄</div>
              <p class="text-gray-500 text-sm mb-3">还没有创建简历</p>
              <button @click="goToResume" class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-medium text-sm hover:opacity-90 transition-all">
                立即创建
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 抖音风格的编辑资料弹窗 -->
      <div v-if="showEditModal" class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
        <div class="bg-blue-100 rounded-xl w-full max-w-md p-6 text-gray-900">
          <div class="flex justify-between items-center mb-6">
            <h3 class="text-xl font-bold">编辑资料</h3>
            <button @click="showEditModal = false" class="text-gray-600 hover:text-gray-900">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <!-- 头像上传 -->
          <div class="flex flex-col items-center mb-6">
            <div class="relative mb-2 cursor-pointer" @click="triggerAvatarUpload">
              <div class="w-24 h-24 rounded-full overflow-hidden border-4 border-gray-300">
                <img :src="avatarPreview || user?.avatar || '/avatars/default/default.jpg'" class="w-full h-full object-cover" alt="User Profile"/>
              </div>
            </div>
            <span class="text-gray-600 text-sm">点击修改头像</span>
          </div>
          
          <!-- 编辑表单 -->
          <div class="space-y-4">
            <div>
              <label class="block text-gray-600 text-sm mb-2">名字</label>
              <input v-model="editForm.username" type="text" class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-all text-gray-900" placeholder="请输入用户名">
              <div class="text-right text-gray-600 text-xs mt-1">{{ editForm.username.length }}/20</div>
            </div>
            
            <div>
              <label class="block text-gray-600 text-sm mb-2">简介</label>
              <textarea v-model="editForm.profile" rows="4" class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-all text-gray-900" placeholder="介绍一下你自己"></textarea>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-gray-600 text-sm mb-2">学校</label>
                <input v-model="editForm.school" type="text" class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-all text-gray-900" placeholder="请输入学校名称">
              </div>
              <div>
                <label class="block text-gray-600 text-sm mb-2">专业</label>
                <input v-model="editForm.major" type="text" class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-all text-gray-900" placeholder="请输入专业名称">
              </div>
              <div>
                <label class="block text-gray-600 text-sm mb-2">学历</label>
                <input v-model="editForm.education" type="text" class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-all text-gray-900" placeholder="请输入学历">
              </div>
              <div>
                <label class="block text-gray-600 text-sm mb-2">邮箱</label>
                <input v-model="editForm.email" type="email" class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-all text-gray-900" placeholder="请输入邮箱">
              </div>
              <div class="col-span-2">
                <label class="block text-gray-600 text-sm mb-2">地址</label>
                <input v-model="editForm.address" type="text" class="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-secondary focus:border-secondary transition-all text-gray-900" placeholder="请输入地址">
              </div>
            </div>

          </div>
          
          <!-- 按钮 -->
          <div class="flex gap-4 mt-8">
            <button @click="showEditModal = false" class="flex-1 py-3 bg-white border border-gray-300 rounded-lg font-medium hover:bg-gray-100 transition-all text-gray-900">取消</button>
            <button @click="saveProfile" class="flex-1 py-3 bg-secondary rounded-lg font-medium hover:opacity-90 transition-all text-white">保存</button>
          </div>
        </div>
      </div>
    </main>
  </div>

  <!-- 复盘详情弹窗 -->
  <div v-if="showReviewModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl">
      <div class="flex justify-between items-center p-6 border-b">
        <h3 class="text-lg font-semibold text-gray-800">面试复盘详情</h3>
        <button @click="closeReviewModal" class="text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
      </div>
      <div class="p-6 overflow-y-auto max-h-[calc(80vh-80px)]">
        <div v-if="loadingReviewDetail" class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p class="mt-2 text-gray-500">加载中...</p>
        </div>
        <div v-else-if="currentReview" class="space-y-4">
          <!-- 基本信息 -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 p-3 rounded-lg">
              <p class="text-sm text-gray-500">面试风格</p>
              <p class="font-medium text-gray-800">{{ currentReview.interview_style }}</p>
            </div>
            <div class="bg-gray-50 p-3 rounded-lg">
              <p class="text-sm text-gray-500">综合评分</p>
              <p class="font-medium text-gray-800">{{ currentReview.overall_score }} 分</p>
            </div>
            <div class="bg-gray-50 p-3 rounded-lg">
              <p class="text-sm text-gray-500">面试时长</p>
              <p class="font-medium text-gray-800">{{ currentReview.interview_duration }} 分钟</p>
            </div>
            <div class="bg-gray-50 p-3 rounded-lg">
              <p class="text-sm text-gray-500">问答数量</p>
              <p class="font-medium text-gray-800">{{ currentReview.question_count }} 问 / {{ currentReview.answer_count }} 答</p>
            </div>
          </div>

          <!-- 复盘内容 -->
          <div class="mt-6">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">复盘内容</h4>
            <div class="bg-gray-50 p-4 rounded-lg whitespace-pre-wrap text-gray-800">
              {{ currentReview.review_content }}
            </div>
          </div>

          <!-- 优点 -->
          <div v-if="currentReview.strengths" class="mt-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">优点</h4>
            <div class="bg-green-50 p-4 rounded-lg">
              <ul class="list-disc list-inside text-gray-700">
                <li v-for="(item, index) in currentReview.strengths.split('\n').filter(s => s.trim())" :key="index">{{ item }}</li>
              </ul>
            </div>
          </div>

          <!-- 待改进 -->
          <div v-if="currentReview.weaknesses" class="mt-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">待改进</h4>
            <div class="bg-yellow-50 p-4 rounded-lg">
              <ul class="list-disc list-inside text-gray-700">
                <li v-for="(item, index) in currentReview.weaknesses.split('\n').filter(s => s.trim())" :key="index">{{ item }}</li>
              </ul>
            </div>
          </div>

          <!-- 建议 -->
          <div v-if="currentReview.suggestions" class="mt-4">
            <h4 class="text-sm font-semibold text-gray-700 mb-2">改进建议</h4>
            <div class="bg-blue-50 p-4 rounded-lg">
              <ul class="list-disc list-inside text-gray-700">
                <li v-for="(item, index) in currentReview.suggestions.split('\n').filter(s => s.trim())" :key="index">{{ item }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userAPI, resumeAPI, interviewAPI } from '@/api'

const router = useRouter()

const user = ref(null)
const showEditModal = ref(false)
const avatarInput = ref(null)
const avatarPreview = ref(null)
const uploadingAvatar = ref(false)
const editForm = ref({
  username: '',
  email: '',
  profile: '',
  school: '',
  major: '',
  education: '',
  address: ''
})
const message = ref('')
const messageType = ref('') // success, error, info
const recommendations = ref([])
const selfIntroduction = ref('')
const resume = ref(null)
const interviewReviews = ref([])
const loadingReviews = ref(false)
const showReviewModal = ref(false)
const currentReview = ref(null)
const loadingReviewDetail = ref(false)

onMounted(async () => {
  try {
    const response = await userAPI.getProfile()
    user.value = response
    // 初始化编辑表单
    editForm.value = {
      username: user.value?.username || '',
      email: user.value?.email || '',
      profile: user.value?.profile || '',
      school: user.value?.school || '',
      major: user.value?.major || '',
      education: user.value?.education || '',
      address: user.value?.address || ''
    }
    
    // 加载职业推荐数据
    loadRecommendations()
    
    // 加载自我介绍数据
    loadSelfIntroduction()
    
    // 加载简历数据
    loadResume()
    
    // 加载面试复盘数据
    loadInterviewReviews()
  } catch (err) {
    console.error('获取用户信息失败:', err)
    console.error('错误详情:', err.response?.data || err.message)
  }
})

// 加载简历数据
const loadResume = async () => {
  try {
    const data = await resumeAPI.get()
    resume.value = data
    console.log('Loaded resume:', resume.value)
  } catch (error) {
    console.log('Resume not found or not created yet:', error)
    resume.value = null
  }
}

// 加载职业推荐数据
const loadRecommendations = () => {
  try {
    const careerRecommendationsStr = localStorage.getItem('careerRecommendations')
    if (careerRecommendationsStr) {
      recommendations.value = JSON.parse(careerRecommendationsStr)
      console.log('Loaded career recommendations from localStorage:', recommendations.value)
    } else {
      // 尝试从 aiResponse 中获取推荐数据
      const aiResponseStr = localStorage.getItem('aiResponse')
      if (aiResponseStr) {
        const aiResponse = JSON.parse(aiResponseStr)
        if (aiResponse.recommendations) {
          recommendations.value = aiResponse.recommendations
          console.log('Loaded career recommendations from aiResponse:', recommendations.value)
        }
      }
    }
  } catch (error) {
    console.error('Failed to load career recommendations:', error)
  }
}

// 加载自我介绍数据
const loadSelfIntroduction = () => {
  try {
    const selfIntroductionStr = localStorage.getItem('selfIntroduction')
    if (selfIntroductionStr) {
      const selfIntroData = JSON.parse(selfIntroductionStr)
      // 构建自我介绍文本
      selfIntroduction.value = `姓名: ${selfIntroData.name || ''}\n学校: ${selfIntroData.school || ''}\n性别: ${selfIntroData.gender || ''}\n技能: ${selfIntroData.skills?.join('、') || '无'}\n其他技能: ${selfIntroData.otherSkills || '无'}\n条件自述: ${selfIntroData.selfDescription || '无'}\n职业期望: ${selfIntroData.goal || '无'}`
      console.log('Loaded self introduction from localStorage:', selfIntroduction.value)
    }
  } catch (error) {
    console.error('Failed to load self introduction:', error)
  }
}

// 加载面试复盘数据
const loadInterviewReviews = async () => {
  loadingReviews.value = true
  try {
    const response = await interviewAPI.listReviews()
    if (response.success) {
      interviewReviews.value = response.data
      console.log('Loaded interview reviews:', interviewReviews.value)
    }
  } catch (error) {
    console.error('Failed to load interview reviews:', error)
  } finally {
    loadingReviews.value = false
  }
}



// 打开编辑模态框时，同步用户数据到表单
const openEditModal = () => {
  showEditModal.value = true
  editForm.value = {
    username: user.value?.username || '',
    email: user.value?.email || '',
    self_introduction: user.value?.self_introduction || '',
    school: user.value?.school || '',
    major: user.value?.major || '',
    education: user.value?.education || '',
    address: user.value?.address || ''
  }
}

const triggerAvatarUpload = () => {
  avatarInput.value?.click()
}

const handleAvatarChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 显示预览
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)
  
  // 上传头像
  uploadingAvatar.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', file)
    
    const response = await userAPI.uploadAvatar(formData)
    user.value = response
    // 更新 localStorage 中的用户数据
    localStorage.setItem('user', JSON.stringify(response))
    // 清空预览，显示 user.avatar
    avatarPreview.value = null
    showMessage('头像上传成功', 'success')
  } catch (err) {
    console.error('上传头像失败:', err)
    showMessage('上传头像失败，请重试', 'error')
  } finally {
    uploadingAvatar.value = false
  }
}

const saveProfile = async () => {
  try {
    const response = await userAPI.updateProfile(editForm.value)
    user.value = response
    // 更新 localStorage 中的用户数据
    localStorage.setItem('user', JSON.stringify(response))
    showEditModal.value = false
    showMessage('个人资料更新成功', 'success')
  } catch (err) {
    console.error('更新个人资料失败:', err)
    showMessage('更新失败，请重试', 'error')
  }
}

const showMessage = (msg, type = 'info') => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

const goToResume = () => {
  router.push('/resume')
}

const goToInterview = () => {
  router.push('/interview')
}

const viewReviewDetail = async (sessionId) => {
  console.log('View review detail:', sessionId)
  loadingReviewDetail.value = true
  try {
    const response = await interviewAPI.getReview(sessionId)
    if (response.success) {
      currentReview.value = response.data
      showReviewModal.value = true
    }
  } catch (error) {
    console.error('Failed to load review detail:', error)
  } finally {
    loadingReviewDetail.value = false
  }
}

const closeReviewModal = () => {
  showReviewModal.value = false
  currentReview.value = null
}


</script>
