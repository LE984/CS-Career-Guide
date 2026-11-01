<template>
  <header class="site-header">
    <nav class="career-container site-nav" aria-label="主导航">
      <CareerBrand />
      <div class="site-nav-links">
        <router-link v-for="item in navigation" :key="item.path" :to="item.path" class="site-nav-link" :class="{ 'is-active': isNavActive(item) }" :aria-current="isNavActive(item) ? 'page' : undefined">{{ item.label }}</router-link>
      </div>
      <div class="site-account">
        <template v-if="!isLoggedIn"><router-link to="/login" class="site-login">登录</router-link><router-link to="/register" class="career-button career-button-primary">创建账号</router-link></template>
        <details v-else ref="userMenu" class="site-user-menu">
          <summary class="site-user-trigger">
            <img v-if="user?.avatar" :src="user.avatar" class="site-avatar" alt="" />
            <span v-else class="site-avatar site-avatar-fallback">{{ (user?.username || '我').slice(0, 1) }}</span>
            <span class="site-username">{{ user?.username || '我的账号' }}</span>
            <svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="m4 6 4 4 4-4" stroke="currentColor" stroke-width="1.5"/></svg>
          </summary>
          <div class="site-user-panel"><router-link to="/users">个人中心</router-link><router-link to="/career-paths/employment/self-introduction">填写个人背景</router-link><button type="button" @click="logout">退出登录</button></div>
        </details>
      </div>
    </nav>
  </header>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authAPI, userAPI } from '@/api'
import { clearSession, getToken, isPublicPath } from '@/auth/session.js'
import CareerBrand from './CareerBrand.vue'
const router = useRouter()
const route = useRoute()
const user = ref(null)
const userMenu = ref(null)
const isLoggedIn = computed(() => !isPublicPath(route.path) && !!getToken())
const navigation = [
  { path: '/career-paths', label: '职业路径' },
  { path: '/career-evaluation', label: '背景与规划' },
  { path: '/company-reviews', label: '企业与职位' },
  { path: '/resume', label: '简历' },
  { path: '/interview', label: 'AI 面试' },
    { path: '/career-platform/catalog', label: '课程功能' },
]
const isNavActive = item => item.path === '/career-evaluation'
  ? ['/career-evaluation', '/career-plan'].includes(route.path) || route.path.endsWith('/self-introduction')
  : route.path.startsWith(item.path) && !route.path.endsWith('/self-introduction')
const updateUserFromLocalStorage = () => {
  try { user.value = JSON.parse(localStorage.getItem('user') || 'null') }
  catch { user.value = null }
}
const syncUserProfile = async () => {
  if (!isLoggedIn.value) return
  try {
    const response = await userAPI.getProfile()
    user.value = response
    localStorage.setItem('user', JSON.stringify(response))
  } catch (err) { console.error('同步用户信息失败:', err) }
}
watch(() => route.path, () => {
  if (userMenu.value) userMenu.value.open = false
  updateUserFromLocalStorage()
  syncUserProfile()
})
const handleStorageChange = event => { if (event.key === 'user') updateUserFromLocalStorage() }
onMounted(() => {
  updateUserFromLocalStorage()
  window.addEventListener('storage', handleStorageChange)
  syncUserProfile()
})
onUnmounted(() => window.removeEventListener('storage', handleStorageChange))
const logout = async () => {
  try { await authAPI.logout() }
  catch (err) { console.error('登出失败:', err) }
  finally { clearSession(); router.replace('/login') }
}
</script>
<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: #fff;
  border-bottom: 1px solid var(--career-border);
}
.site-nav {
  display: flex;
  align-items: center;
  gap: 36px;
  min-height: var(--career-nav-height);
}
.site-nav-links {
  display: flex;
  align-self: stretch;
  gap: 22px;
}
.site-nav-link {
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 2px;
  font-size: 14px;
  color: #586577;
  white-space: nowrap;
  text-decoration: none;
}
.site-nav-link:hover,.site-nav-link.is-active {
  color: var(--career-blue);
}
.site-nav-link.is-active {
  font-weight: 600;
}
.site-nav-link.is-active::after {
  content: '';
  position: absolute;
  height: 2px;
  background: var(--career-blue);
  bottom: -1px;
  inset-inline: 0;
}
.site-account {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 16px;
  flex: none;
}
.site-account .career-button {
  min-height: 34px;
  padding: 7px 12px;
  font-size: 13px;
}
.site-login {
  font-size: 14px;
  color: #475467;
}
.site-user-menu {
  position: relative;
}
.site-user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  list-style: none;
  border-radius: 6px;
  padding: 5px 0;
}
.site-user-trigger::-webkit-details-marker {
  display: none;
}
.site-user-trigger>svg {
  width: 14px;
  height: 14px;
  color: #667085;
}
.site-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #c6dbf5;
}
.site-avatar-fallback {
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--career-blue);
  background: var(--career-blue-soft);
}
.site-username {
  font-size: 13px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.site-user-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 180px;
  padding: 6px;
  background: #fff;
  border: 1px solid var(--career-border);
  border-radius: 8px;
  box-shadow: 0 10px 28px #1d293914;
}
.site-user-panel a,.site-user-panel button {
  display: block;
  width: 100%;
  padding: 10px;
  border-radius: 4px;
  text-align: left;
  font-size: 13px;
  color: #475467;
}
.site-user-panel a:hover,.site-user-panel button:hover {
  background: #f3f6fa;
}
.site-user-panel button {
  margin-top: 4px;
  border-top: 1px solid var(--career-border);
  color: #b42318;
}
@media(max-width:1060px) {
  .site-nav {
    gap: 22px;
  }
  .site-nav-links {
    gap: 15px;
  }
  .site-username {
    display: none;
  }
}
@media(max-width:760px) {
  .site-nav {
    flex-wrap: wrap;
    gap: 0;
    padding-top: 12px;
  }
  .site-account {
    margin-left: auto;
  }
  .site-nav-links {
    order: 3;
    width: 100%;
    overflow-x: auto;
    gap: 22px;
    margin-top: 8px;
    height: 42px;
  }
}
</style>
