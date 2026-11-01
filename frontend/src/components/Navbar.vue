<template>
  <nav class="fixed top-0 w-full z-50 bg-white/70 backdrop-blur-2xl border-b border-slate-200/50 shadow-sm font-manrope antialiased h-16 flex items-center justify-between px-8 max-w-full">
    <div class="flex items-center gap-10">
      <router-link to="/" class="text-xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">CS Career Guide</router-link>
      <div class="hidden md:flex gap-8">
        <router-link to="/career-paths" :class="getNavClass('/career-paths')">职业路径</router-link>
        <router-link to="/career-paths/employment/self-introduction" :class="getNavClass('/career-paths/employment/self-introduction')">自我介绍</router-link>
        <router-link to="/career-evaluation" :class="getNavClass('/career-evaluation')">规划报告</router-link>
        <router-link to="/company-reviews" :class="getNavClass('/company-reviews')">企业榜单</router-link>
        <router-link to="/resume" :class="getNavClass('/resume')">简历管理</router-link>
        <router-link to="/interview" :class="getNavClass('/interview')">AI 面试</router-link> 
      </div>
    </div>
    <div class="flex items-center gap-4">

      <div class="flex gap-2 ml-2">
        <template v-if="!isLoggedIn">
          <router-link to="/login" class="px-5 py-2 text-sm font-bold text-slate-700 hover:bg-slate-100 rounded-xl transition-all">登录</router-link>
          <router-link to="/register" class="px-5 py-2 text-sm font-bold bg-secondary text-white rounded-2xl active:scale-95 transition-all shadow-md shadow-indigo-200">注册</router-link>
        </template>
        <template v-else>
          <div class="dropdown dropdown-end">
            <label tabindex="0" class="flex items-center gap-2 px-2 py-2 text-sm font-bold text-slate-700 hover:bg-slate-100 rounded-xl transition-all">
              <div class="w-10 h-10 rounded-full overflow-hidden border-2 border-slate-200">
                <img :src="user?.avatar || '/avatars/default/default.jpg'" class="w-full h-full object-cover" alt="User Avatar"/>
              </div>
            </label>
            <div tabindex="0" class="dropdown-content mt-3 z-[1] shadow bg-white rounded-xl w-32 border border-slate-200 overflow-hidden flex flex-col right-0">
              <router-link to="/users" class="hover:bg-slate-50 py-2 px-3 border-b border-slate-100 text-sm font-medium text-slate-700 flex justify-center items-center">个人中心</router-link>
              <a @click="logout" class="hover:bg-slate-50 py-2 px-3 text-sm font-medium text-red-500 cursor-pointer flex justify-center items-center">登出</a>
            </div>
          </div>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api, { authAPI, userAPI } from '@/api'
import { clearSession, getToken, isPublicPath } from '@/auth/session.js'

const router = useRouter()
const route = useRoute()
const user = ref(null)

const isLoggedIn = computed(() => {
  return !isPublicPath(route.path) && !!getToken()
})

// 从 localStorage 更新用户数据
const updateUserFromLocalStorage = () => {
  const userStr = localStorage.getItem('user')
  const userData = userStr ? JSON.parse(userStr) : null
  user.value = userData
}

// 主动同步用户信息
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

// 监听路由变化，每次路由切换时同步用户信息
import { watch } from 'vue'
watch(() => route.path, () => {
  if (isLoggedIn.value) {
    syncUserProfile()
  }
})

// 监听 localStorage 变化
const handleStorageChange = (event) => {
  if (event.key === 'user') {
    updateUserFromLocalStorage()
  }
}

onMounted(() => {
  updateUserFromLocalStorage()
  // 监听 localStorage 变化
  window.addEventListener('storage', handleStorageChange)
  // 页面加载时主动同步一次
  syncUserProfile()
})

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange)
})

const getNavClass = (path) => {
  const isActive = route.path === path || (path === '/career-paths' && route.path.startsWith('/career-paths/') && !route.path.includes('/self-introduction'))
  return {
    'text-indigo-600 font-bold border-b-2 border-indigo-600 transition-colors py-1': isActive,
    'text-slate-500 hover:text-indigo-600 font-medium transition-colors py-1': !isActive
  }
}

const logout = async () => {
  try {
    await authAPI.logout()
  } catch (err) {
    console.error('登出失败:', err)
  } finally {
    clearSession()
    router.replace('/login')
  }
}
</script>
