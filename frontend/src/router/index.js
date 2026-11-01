import { createRouter, createWebHistory } from 'vue-router'
import { userAPI } from '../api'
import { createAuthGuard } from './guard.js'

const routes = [
  {path:'/career-platform/catalog',name:'PlatformCatalog',component:()=>import('../views/career-platform/Catalog.vue')},
  {path:'/career-platform/resume',name:'PlatformResume',component:()=>import('../views/career-platform/Resume.vue')},
  {path:'/career-platform/practice',name:'PlatformPractice',component:()=>import('../views/career-platform/Practice.vue')},
  {path:'/career-platform/records',name:'PlatformRecords',component:()=>import('../views/career-platform/Records.vue')},
  {path:'/career-platform/evaluation',name:'PlatformEvaluation',component:()=>import('../views/career-platform/Evaluation.vue')},

  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/auth/Register.vue')
  },
  {
    path: '/career-paths',
    name: 'CareerPaths',
    component: () => import('../views/career-paths/Index.vue')
  },
  {
    path: '/career-paths/:type',
    name: 'CareerPathDetail',
    component: () => import('../views/career-paths/Detail.vue')
  },
  {
    path: '/career-paths/:type/self-introduction',
    name: 'SelfIntroduction',
    component: () => import('../views/career-paths/SelfIntroduction.vue')
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/users/Index.vue')
  },
  {
    path: '/career-evaluation',
    name: 'CareerEvaluation',
    component: () => import('../views/career-evaluation/Index.vue')
  },
  {
    path: '/career-plan',
    name: 'CareerPlan',
    component: () => import('../views/career-evaluation/CareerPlan.vue')
  },
  {
    path: '/company-reviews',
    name: 'CompanyReviews',
    component: () => import('../views/company-reviews/Index.vue')
  },
  {
    path: '/company-reviews/senior-advice/form',
    name: 'SeniorAdviceForm',
    component: () => import('../views/company-reviews/SeniorAdviceForm.vue')
  },
  {
    path: '/interview',
    name: 'Interview',
    component: () => import('../views/interview/Index.vue')
  },
  {
    path: '/resume',
    name: 'Resume',
    component: () => import('../views/resume/Index.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 始终滚动到顶部
    return { top: 0 }
  }
})

// 路由守卫
router.beforeEach(createAuthGuard(() => userAPI.getProfile({ redirectOnUnauthorized: false })))

export default router
