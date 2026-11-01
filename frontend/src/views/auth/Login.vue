<template>
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden bg-base-200">
    <!-- Background Elements -->
    <div class="absolute inset-0 bg-gradient-to-r from-white to-purple-100 dark:from-gray-900 dark:to-gray-800 pointer-events-none"></div>
    <div class="absolute top-[-10%] right-[-5%] w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-pulse-slow pointer-events-none"></div>
    <div class="absolute bottom-[-10%] left-[-5%] w-96 h-96 bg-accent/20 rounded-full blur-3xl animate-pulse-slow delay-1000 pointer-events-none"></div>

    <div class="w-full max-w-md p-8 glass-card relative z-10 animate-fade-in-up">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent mb-2">欢迎回来</h1>
        <p class="text-base-content/60">登录您的账户以继续</p>
      </div>
      
      <form @submit.prevent="login" class="space-y-6">
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">用户名</span>
          </label>
          <input
            v-model="form.username"
            type="text"
            class="input input-bordered w-full bg-white/50 dark:bg-gray-800/50 focus:bg-white dark:focus:bg-gray-800 transition-colors"
            placeholder="请输入用户名"
            required
          />
        </div>
        
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">密码</span>
          </label>
          <input
            v-model="form.password"
            type="password"
            class="input input-bordered w-full bg-white/50 dark:bg-gray-800/50 focus:bg-white dark:focus:bg-gray-800 transition-colors"
            placeholder="请输入密码"
            required
          />
          <label class="label">
            <a href="#" class="label-text-alt link link-hover text-primary">忘记密码?</a>
          </label>
        </div>

        <button
          type="submit"
          class="btn btn-primary w-full rounded-full shadow-glow hover:shadow-lg transition-all duration-300"
          :disabled="loading"
        >
          <span v-if="loading" class="loading loading-spinner loading-sm"></span>
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <div class="text-center text-sm">
          <span class="text-base-content/70">还没有账号？</span>
          <router-link :to="{ path: '/register', query: { redirect: safeRedirect(route.query.redirect) } }" class="link link-primary font-medium ml-1">立即注册</router-link>
        </div>
      </form>
      
      <div v-if="error" class="mt-6 p-4 rounded-lg bg-red-50 text-red-600 border border-red-100 flex items-center gap-2 animate-shake">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authAPI } from '@/api'
import { clearSession, safeRedirect } from '@/auth/session.js'

const router = useRouter()
const route = useRoute()
const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)
const error = ref('')

const login = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await authAPI.login(form.value)
    clearSession()
    // 设置新用户信息
    localStorage.setItem('token', response.token)
    localStorage.setItem('user', JSON.stringify(response.user))
    const redirect = safeRedirect(route.query.redirect)
    await router.replace(router.resolve(redirect).matched.length ? redirect : '/')
  } catch (err) {
    if (err.response) {
      error.value = err.response.data?.non_field_errors?.[0] || '登录失败，请检查用户名和密码'
    } else {
      error.value = '网络错误，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>
