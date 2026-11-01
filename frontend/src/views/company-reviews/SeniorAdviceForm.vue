<template>
  <div class="min-h-screen bg-gradient-to-r from-white to-purple-100">
    <main class="pt-24 pb-24 max-w-4xl mx-auto px-4">
      <!-- Page Header -->
      <header class="mb-12 text-center">
        <h1 class="text-4xl font-bold text-primary mb-4">提交学长学姐建议</h1>
        <p class="text-lg text-on-primary-container max-w-2xl mx-auto">
          分享你的职场经验，帮助学弟学妹们做出更明智的职业选择
        </p>
      </header>
      
      <!-- Form Container -->
      <div class="bg-white rounded-2xl shadow-lg p-8">
        <form @submit.prevent="handleSubmit" class="space-y-6">
          <!-- 基本信息 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">公司名称 *</label>
              <input v-model="formData.company" type="text" required 
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">职位名称 *</label>
              <input v-model="formData.position" type="text" required
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">您的姓名 *</label>
              <input v-model="formData.senior_name" type="text" required
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">毕业年份 *</label>
              <input v-model="formData.graduation_year" type="text" required
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                     placeholder="例如：2023">
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-2">当前公司</label>
              <input v-model="formData.current_company" type="text"
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
            </div>
          </div>
          
          <!-- 建议内容 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">详细建议 *</label>
            <textarea v-model="formData.advice" required rows="5"
                      class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"></textarea>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">薪资信息</label>
              <input v-model="formData.salary_info" type="text"
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                     placeholder="例如：1.5-3万·14薪">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">评分 *</label>
              <div class="flex items-center space-x-4">
                <input v-model="formData.rating" type="number" min="1" max="5" step="0.5" required
                       class="w-24 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500">
                <span class="text-gray-500">（1-5分）</span>
              </div>
            </div>
          </div>
          
          <!-- 优缺点 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">优点（用逗号分隔）</label>
            <input v-model="prosInput" type="text"
                   class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                   placeholder="例如：薪资高,福利好,技术氛围好">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">缺点（用逗号分隔）</label>
            <input v-model="consInput" type="text"
                   class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                   placeholder="例如：工作压力较大,加班较多">
          </div>
          
          <!-- 提交按钮 -->
          <div class="flex justify-center">
            <button type="submit" :disabled="isSubmitting"
                    class="px-12 py-4 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {{ isSubmitting ? '提交中...' : '提交建议' }}
            </button>
          </div>
        </form>
        
        <!-- 成功提示 -->
        <div v-if="success" class="mt-8 p-6 bg-green-100 text-green-700 rounded-lg">
          <h3 class="font-bold text-lg mb-2">{{ successMessage }}</h3>
          <p>感谢您的分享！您的建议将在审核通过后显示在企业榜单页面。</p>
          <router-link to="/company-reviews" class="inline-block mt-4 px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors">
            返回企业榜单
          </router-link>
        </div>
        
        <!-- 错误提示 -->
        <div v-if="error" class="mt-8 p-6 bg-red-100 text-red-700 rounded-lg">
          <h3 class="font-bold text-lg mb-2">提交失败</h3>
          <p>{{ errorMessage }}</p>
          <button @click="error = false" class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors">
            重试
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

const router = useRouter()

const formData = ref({
  company: '',
  position: '',
  senior_name: '',
  graduation_year: '',
  current_company: '',
  advice: '',
  salary_info: '',
  pros: [],
  cons: [],
  rating: 4.0
})

const prosInput = ref('')
const consInput = ref('')
const isSubmitting = ref(false)
const success = ref(false)
const successMessage = ref('')
const error = ref(false)
const errorMessage = ref('')

const handleSubmit = async () => {
  // 处理优缺点输入
  formData.value.pros = prosInput.value.split(',').map(item => item.trim()).filter(Boolean)
  formData.value.cons = consInput.value.split(',').map(item => item.trim()).filter(Boolean)
  
  isSubmitting.value = true
  success.value = false
  error.value = false
  
  try {
    const response = await api.post('/ai/senior-advice/', formData.value)
    success.value = true
    successMessage.value = response.data.message
    
    // 重置表单
    formData.value = {
      company: '',
      position: '',
      senior_name: '',
      graduation_year: '',
      current_company: '',
      advice: '',
      salary_info: '',
      pros: [],
      cons: [],
      rating: 4.0
    }
    prosInput.value = ''
    consInput.value = ''
  } catch (err) {
    error.value = true
    errorMessage.value = err.response?.data?.error || err.response?.data?.message || '提交失败，请重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
/* 自定义样式 */
input:focus,
textarea:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2);
}

button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

button:active {
  transform: translateY(0);
}
</style>