<template>
  <div class="min-h-screen bg-white relative">
    <!-- Starry Background -->
    <div class="absolute inset-0 z-0">
      <canvas ref="starCanvas" class="w-full h-full"></canvas>
    </div>
    
    <!-- Content -->
    <div class="relative z-10 space-y-8 p-4 lg:p-8">
      <div class="card glass bg-transparent backdrop-blur-lg border border-black/10 text-black">
        <div class="card-body">
          <div class="flex items-center justify-center gap-4 mb-4">
            <span class="text-6xl">{{ pathInfo.icon }}</span>
            <div class="text-center">
              <h1 class="text-4xl font-bold">{{ pathInfo.title }}</h1>
              <p class="text-lg text-black/70">{{ pathInfo.subtitle }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="pathInfo.hasAssessment" class="card glass bg-transparent backdrop-blur-lg border border-black/10 text-black">
        <div class="card-body">
          <h2 class="card-title text-2xl mb-6">{{ pathInfo.assessment.title }}</h2>
          <p class="mb-4">{{ pathInfo.assessment.description }}</p>
          <button class="btn btn-primary" @click="startAssessment">开始测评</button>
          
          <div class="mt-6">
            <h3 class="font-bold mb-2 ">倘若目标清晰，那我们就该考虑入职企业问题了</h3>
            <div class="flex gap-2 flex-wrap">
              <input 
                v-model="targetCareer" 
                type="text" 
                placeholder="直接填写职业" 
                class="input input-bordered max-w-md bg-black/10 border-black/20 text-black placeholder-black/40"
              >
              <button 
                class="btn btn-secondary whitespace-nowrap" 
                @click="goToCompanyReviews"
                :disabled="!targetCareer.trim()"
              >
                查看相关企业
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="card glass bg-transparent backdrop-blur-lg border border-black/10 text-black">
        <div class="card-body">
          <h2 class="card-title text-2xl mb-4">路径说明</h2>
          <p>{{ pathInfo.description }}</p>
        </div>
      </div>

      <div class="card glass bg-transparent backdrop-blur-lg border border-black/10 text-black">
        <div class="card-body">
          <h2 class="card-title text-2xl mb-4">准备建议</h2>
          <ul class="space-y-3">
            <li v-for="(item, index) in pathInfo.suggestions" :key="index" class="flex items-start gap-3">
              <span class="text-primary">✓</span>
              <span>{{ item }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="card glass bg-transparent backdrop-blur-lg border border-black/10 text-black">
        <div class="card-body">
          <h2 class="card-title text-2xl mb-4">相关资源</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a v-for="(resource, index) in pathInfo.resources" :key="index" :href="resource.url" target="_blank" class="card glass bg-transparent hover:bg-black/5 transition-colors border border-black/5">
              <div class="card-body">
                <h3 class="font-bold">{{ resource.name }}</h3>
                <p class="text-sm text-black/70">{{ resource.description }}</p>
              </div>
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const type = route.params.type
const targetCareer = ref('')
const starCanvas = ref(null)
let starCtx = null
let stars = []
let animationId = null

function startAssessment() {
  // 所有职业路径类型都先跳转到自我介绍页面
  router.push(`/career-paths/${type}/self-introduction`)
}

function goToCompanyReviews() {
  if (targetCareer.value.trim()) {
    // 跳转到红黑榜页面，并传递目标职业作为查询参数
    router.push({
      path: '/company-reviews',
      query: { job_title: targetCareer.value.trim() }
    })
  }
}

const pathInfo = computed(() => {
  const paths = {
    employment: {
      icon: '💼',
      title: '就业',
      subtitle: '进入企业工作，积累实战经验',
      hasAssessment: true,
      assessment: {
        title: '职业测评',
        description: '如果仍不知道未来想做什么，来评测一下吧，我们会根据你的自身情况给你推荐',
        buttonText: '开始测评'
      },
      description: '就业是大多数计算机专业学生的首选方向。通过进入企业工作，你可以将所学知识应用到实际项目中，积累实战经验，提升专业技能。就业方向包括互联网公司、金融机构、科技企业等，岗位涵盖软件开发、测试、产品经理等多个领域。',
      suggestions: [
        '打好计算机基础，掌握数据结构、算法等核心课程',
        '寻找实习机会，积累项目经验',
        '积极参加校园招聘，准备面试',
        '学习热门技术栈，如前端框架、后端语言等',
        '构建个人作品集，展示项目成果'
      ],
      resources: [
        { name: 'LeetCode', description: '算法刷题平台', url: 'https://leetcode.cn' },
        { name: '牛客网', description: '求职面试准备', url: 'https://www.nowcoder.com' },
        { name: '拉勾网', description: '互联网招聘平台', url: 'https://www.lagou.com' },
        { name: 'BOSS直聘', description: '直聊招聘平台', url: 'https://www.zhipin.com' }
      ]
    },
    postgraduate: {
      icon: '🎓',
      title: '考研',
      subtitle: '继续深造，提升学术水平',
      description: '考研是提升学历和学术水平的重要途径。通过考研，你可以选择在计算机相关领域进行更深入的学习和研究，为未来的职业发展打下更坚实的基础。考研方向包括计算机科学与技术、软件工程、人工智能等多个专业。',
      suggestions: [
        '提前了解目标院校的招生政策和考试科目',
        '制定合理的复习计划，重点复习专业课',
        '关注考研动态和政策变化',
        '准备英语和政治考试',
        '联系目标院校的导师，了解研究方向'
      ],
      resources: [
        { name: '中国研究生招生信息网', description: '考研官方网站', url: 'https://yz.chsi.com.cn' },
        { name: '考研论坛', description: '考研交流平台', url: 'https://bbs.kaoyan.com' },
        { name: '计算机考研网', description: '计算机专业考研信息', url: 'https://www.cskaoyan.com' },
        { name: '文都教育', description: '考研辅导机构', url: 'https://www.wendu.com' }
      ]
    },
    civil_service: {
      icon: '🏛️',
      title: '考公',
      subtitle: '成为公务员，服务社会',
      description: '考公是进入政府部门工作的重要途径。作为计算机专业的学生，你可以报考与计算机相关的公务员岗位，如网信办、科技部门、公安系统等。公务员工作稳定，福利待遇好，是很多人的理想选择。',
      suggestions: [
        '了解公务员考试的报考条件和考试科目',
        '系统复习行测和申论',
        '关注时事政治和社会热点',
        '参加公务员考试培训',
        '准备面试，提高综合素质'
      ],
      resources: [
        { name: '国家公务员局', description: '公务员考试官方网站', url: 'http://www.scs.gov.cn' },
        { name: '中公教育', description: '公务员考试辅导', url: 'https://www.offcn.com' },
        { name: '华图教育', description: '公务员考试辅导', url: 'https://www.huatu.com' },
        { name: '粉笔公考', description: '公务员考试APP', url: 'https://www.fenbi.com' }
      ]
    },
    military: {
      icon: '🎖️',
      title: '入伍',
      subtitle: '参军入伍，保家卫国',
      description: '入伍是一项光荣的选择。作为计算机专业的学生，你可以通过参军入伍，在部队中发挥专业特长，为国防事业做出贡献。入伍后，你可以从事与计算机相关的工作，如网络安全、信息化建设等。',
      suggestions: [
        '了解参军入伍的条件和流程',
        '保持良好的身体状态',
        '学习军事理论知识',
        '准备入伍体检',
        '了解部队的生活和工作环境'
      ],
      resources: [
        { name: '全国征兵网', description: '征兵官方网站', url: 'https://www.gfbzb.gov.cn' },
        { name: '国防部网站', description: '国防信息发布', url: 'http://www.mod.gov.cn' },
        { name: '中国军网', description: '军队新闻和信息', url: 'http://www.81.cn' },
        { name: '军事科学院', description: '军事科研机构', url: 'http://www.ams.ac.cn' }
      ]
    },
    entrepreneurship: {
      icon: '🚀',
      title: '创业',
      subtitle: '自主创业，实现梦想',
      description: '创业是实现个人价值和梦想的重要途径。作为计算机专业的学生，你可以利用所学知识，开发创新产品或服务，创办自己的企业。创业需要勇气和毅力，但也可能带来巨大的回报。',
      suggestions: [
        '寻找创新的创业方向和项目',
        '学习创业知识和技能',
        '组建优秀的创业团队',
        '了解创业政策和融资渠道',
        '做好市场调研和商业计划'
      ],
      resources: [
        { name: '创业邦', description: '创业资讯和服务', url: 'https://www.cyzone.cn' },
        { name: '36氪', description: '科技创业媒体', url: 'https://www.36kr.com' },
        { name: '创新工场', description: '创业投资机构', url: 'https://www.innovationworks.com' },
        { name: '车库咖啡', description: '创业孵化器', url: 'https://www.chekucafe.com' }
      ]
    }
  }
  
  return paths[type] || paths.employment
})

// Starry background functions
function createStars() {
  stars = []
  for (let i = 0; i < 200; i++) {
    stars.push({
      x: Math.random() * starCanvas.value.width,
      y: Math.random() * starCanvas.value.height,
      size: Math.random() * 2 + 1,
      speed: Math.random() * 0.5 + 0.1,
      opacity: Math.random() * 0.8 + 0.2
    })
  }
}

function animateStars() {
  if (!starCtx || !starCanvas.value) return
  
  starCtx.clearRect(0, 0, starCanvas.value.width, starCanvas.value.height)
  
  stars.forEach(star => {
    starCtx.beginPath()
    starCtx.arc(star.x, star.y, star.size, 0, Math.PI * 2)
    starCtx.fillStyle = `rgba(255, 255, 255, ${star.opacity})`
    starCtx.fill()
    
    star.y -= star.speed
    if (star.y < 0) {
      star.y = starCanvas.value.height
    }
  })
  
  animationId = requestAnimationFrame(animateStars)
}

function resizeCanvas() {
  if (starCanvas.value) {
    starCanvas.value.width = starCanvas.value.offsetWidth
    starCanvas.value.height = starCanvas.value.offsetHeight
    createStars()
  }
}

// Lifecycle hooks
onMounted(() => {
  // Initialize starry background
  if (starCanvas.value) {
    starCtx = starCanvas.value.getContext('2d')
    resizeCanvas()
    animateStars()
  }
  
  // Add event listeners
  window.addEventListener('resize', resizeCanvas)
})

onUnmounted(() => {
  // Clean up
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  
  window.removeEventListener('resize', resizeCanvas)
})
</script>
