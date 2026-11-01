<template>
  <div class="bg-gradient-to-r from-white to-purple-100 text-gray-900 min-h-screen selection:bg-secondary selection:text-white">
    <main class="pt-24 pb-16 px-4 md:px-8 max-w-7xl mx-auto">
      <!-- 顶部操作栏 -->
      <div class="flex flex-col gap-4 mb-8">
        <div class="flex justify-between items-center">
          <h1 class="text-2xl font-bold text-gray-900">实习简历</h1>
          <div class="flex gap-4">
            
            <button @click="saveResume" class="px-6 py-2 bg-gray-200 text-gray-800 rounded-md font-medium hover:bg-gray-300 transition-colors">
              保存草稿
            </button>
            <button @click="exportPDF" class="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition-colors">
              导出简历
            </button>
            <button @click="goToInterview" class="px-6 py-2 bg-purple-600 text-white rounded-md font-medium hover:bg-purple-700 transition-colors">
              模拟面试
            </button>
          </div>
        </div>
        
        <!-- 语音输入状态 -->
        <div v-if="voiceInputStatus" class="p-4 rounded-md bg-gray-100 border border-gray-200">
          <div class="flex items-center gap-2">
            <span v-if="isListening" class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
            <span v-else-if="isProcessing" class="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
            <span v-else class="w-2 h-2 bg-green-500 rounded-full"></span>
            <span class="text-gray-700">{{ voiceInputStatus }}</span>
          </div>
          <div v-if="voiceInputText" class="mt-2 text-sm text-gray-600">
            <span class="font-medium">识别结果:</span> {{ voiceInputText }}
          </div>
        </div>
      </div>
      
      <!-- 左右分栏布局 -->
      <div class="flex flex-col lg:flex-row gap-8">
        <!-- 左侧编辑区域 -->
        <div class="lg:w-1/2 bg-white rounded-lg shadow-md p-6">
          <!-- 基本信息 -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-bold text-gray-800 flex items-center">
                <span class="w-2 h-6 bg-blue-500 mr-2"></span>
                基本信息
              </h2>
              <button @click="toggleBasicInfo" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                {{ showBasicInfo ? '隐藏' : '显示' }}
              </button>
            </div>
            <div v-if="showBasicInfo" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">头像</label>
                <div class="flex flex-col items-center">
                  <div class="w-24 h-24 border border-gray-300 flex items-center justify-center mb-2 overflow-hidden">
                    <img v-if="avatarPreview || resume.avatar_url" :src="avatarPreview || resume.avatar_url" class="w-full h-full object-cover" alt="头像"/>
                  </div>
                  <button @click="triggerAvatarUpload" class="text-sm text-blue-600 hover:text-blue-800 font-medium">
                    {{ uploadingAvatar ? '上传中...' : '上传头像' }}
                  </button>
                  <button v-if="resume.avatar_url" @click="removeAvatar" class="text-sm text-red-600 hover:text-red-800 font-medium mt-1">
                    删除头像
                  </button>
                  <input ref="avatarInput" type="file" accept="image/*" @change="handleAvatarChange" class="hidden"/>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                <input v-model="resume.name" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">意向岗位</label>
                <input v-model="resume.target_position" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">电话</label>
                <input v-model="resume.phone" type="tel" class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <input v-model="resume.email" type="email" class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              </div>
              <div class="md:col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">地址</label>
                <input v-model="resume.address" type="text" class="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              </div>
            </div>
          </div>
          
          <!-- 个人自评 -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-bold text-gray-800 flex items-center">
                <span class="w-2 h-6 bg-blue-500 mr-2"></span>
                个人自评
              </h2>
              <button @click="toggleSelfEvaluation" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                {{ showSelfEvaluation ? '隐藏' : '显示' }}
              </button>
            </div>
            <div v-if="showSelfEvaluation" class="space-y-4">
              <div class="border border-gray-200 rounded-md p-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">编辑内容（支持 Markdown 语法）</label>
                <textarea 
                  v-model="resume.self_evaluation" 
                  rows="6" 
                  placeholder="例如：&#10;- 熟练掌握 Java/Python&#10;- 具备良好的团队协作能力&#10;- 热爱技术，持续学习"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                ></textarea>
                <p class="text-xs text-gray-500 mt-1">支持 **加粗**、*斜体*、`代码`、- 列表 等 Markdown 语法</p>
              </div>
            </div>
          </div>
          
          <!-- 教育背景 -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-bold text-gray-800 flex items-center">
                <span class="w-2 h-6 bg-blue-500 mr-2"></span>
                教育背景
              </h2>
              <div class="flex gap-2">
                <button @click="addEducation" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  + 添加
                </button>
                <button @click="toggleEducation" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  {{ showEducation ? '隐藏' : '显示' }}
                </button>
              </div>
            </div>
            <div v-if="showEducation" class="space-y-4">
              <div v-for="(edu, index) in resume.education" :key="index" class="border border-gray-200 rounded-md p-4">
                <div class="flex justify-between items-start">
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">学校</label>
                      <input v-model="edu.school" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">专业</label>
                      <input v-model="edu.major" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">学历</label>
                      <input v-model="edu.degree" type="text" placeholder="例如：本科、硕士、博士" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">时间</label>
                      <input v-model="edu.period" type="text" placeholder="2020.09-2024.06" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                  </div>
                  <button @click="removeEducation(index)" class="text-red-500 hover:text-red-700 ml-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="resume.education.length === 0" class="border border-dashed border-gray-300 rounded-md p-4 text-center">
                <p class="text-gray-500 mb-2">暂无教育背景，点击"添加"按钮添加</p>
              </div>
            </div>
          </div>
          
          <!-- 实习经历 -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-bold text-gray-800 flex items-center">
                <span class="w-2 h-6 bg-blue-500 mr-2"></span>
                实习经历
              </h2>
              <div class="flex gap-2">
                <button @click="addExperience" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  + 添加
                </button>
                <button @click="toggleExperience" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  {{ showExperience ? '隐藏' : '显示' }}
                </button>
              </div>
            </div>
            <div v-if="showExperience" class="space-y-4">
              <div v-for="(exp, index) in resume.experience" :key="index" class="border border-gray-200 rounded-md p-4">
                <div class="flex justify-between items-start">
                  <div class="w-full">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-2">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">公司</label>
                        <input v-model="exp.company" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">职位</label>
                        <input v-model="exp.position" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">时间</label>
                        <input v-model="exp.period" type="text" placeholder="2023.06-至今" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">工作描述</label>
                      <textarea v-model="exp.description" rows="3" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
                    </div>
                  </div>
                  <button @click="removeExperience(index)" class="text-red-500 hover:text-red-700 ml-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="resume.experience.length === 0" class="border border-dashed border-gray-300 rounded-md p-4 text-center">
                <p class="text-gray-500 mb-2">暂无实习经历，点击"添加"按钮添加</p>
              </div>
            </div>
          </div>
          
          <!-- 项目经验 -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-bold text-gray-800 flex items-center">
                <span class="w-2 h-6 bg-blue-500 mr-2"></span>
                项目经验
              </h2>
              <div class="flex gap-2">
                <button @click="addProject" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  + 添加
                </button>
                <button @click="toggleProjects" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  {{ showProjects ? '隐藏' : '显示' }}
                </button>
              </div>
            </div>
            <div v-if="showProjects" class="space-y-4">
              <div v-for="(project, index) in resume.projects" :key="index" class="border border-gray-200 rounded-md p-4">
                <div class="flex justify-between items-start">
                  <div class="w-full">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-2">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">项目名称</label>
                        <input v-model="project.name" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">担任角色</label>
                        <input v-model="project.role" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">时间</label>
                        <input v-model="project.period" type="text" placeholder="2023.06-2023.09" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">项目链接</label>
                        <input v-model="project.url" type="url" placeholder="https://github.com/xxx/xxx" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">项目描述（支持 Markdown 语法）</label>
                      <textarea v-model="project.description" rows="4"  class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"></textarea>
                      <p class="text-xs text-gray-500 mt-1">支持 **加粗**、*斜体*、`代码`、- 列表 等 Markdown 语法</p>
                    </div>
                  </div>
                  <button @click="removeProject(index)" class="text-red-500 hover:text-red-700 ml-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="resume.projects.length === 0" class="border border-dashed border-gray-300 rounded-md p-4 text-center">
                <p class="text-gray-500 mb-2">添加项目经验，展示你的技术能力</p>
                <button @click="addProject" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  + 添加项目经验
                </button>
              </div>
            </div>
          </div>
          
          <!-- 专业技能 -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-bold text-gray-800 flex items-center">
                <span class="w-2 h-6 bg-blue-500 mr-2"></span>
                专业技能
              </h2>
              <button @click="toggleSkills" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                {{ showSkills ? '隐藏' : '显示' }}
              </button>
            </div>
            <div v-if="showSkills" class="space-y-4">
              <div class="border border-gray-200 rounded-md p-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">技能描述（支持 Markdown 语法）</label>
                <textarea 
                  v-model="resume.skills" 
                  rows="4" 
                  placeholder="- 编程语言: Java, Python, Go&#10;- 框架: Spring Boot, Vue3, React&#10;- 工具: Git, Docker, Kubernetes&#10;- 数据库: MySQL, Redis, MongoDB"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                ></textarea>
                <p class="text-xs text-gray-500 mt-1">支持 **加粗**、*斜体*、`代码`、- 列表 等 Markdown 语法</p>
              </div>
            </div>
          </div>
          
          <!-- 证书认证 -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-lg font-bold text-gray-800 flex items-center">
                <span class="w-2 h-6 bg-blue-500 mr-2"></span>
                证书认证
              </h2>
              <div class="flex gap-2">
                <button @click="addCertificate" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  + 添加
                </button>
                <button @click="toggleCertificates" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  {{ showCertificates ? '隐藏' : '显示' }}
                </button>
              </div>
            </div>
            <div v-if="showCertificates" class="space-y-4">
              <div v-for="(cert, index) in resume.certificates" :key="index" class="border border-gray-200 rounded-md p-4">
                <div class="flex justify-between items-start">
                  <div class="w-full">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-2">
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">证书名称</label>
                        <input v-model="cert.name" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">颁发机构</label>
                        <input v-model="cert.issuer" type="text" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">获得日期</label>
                        <input v-model="cert.period" type="text" placeholder="2024.06" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                      </div>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">描述（支持 Markdown 语法）</label>
                      <textarea v-model="cert.description" rows="3" class="w-full px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"></textarea>
                      <p class="text-xs text-gray-500 mt-1">支持 **加粗**、*斜体*、`代码`、- 列表 等 Markdown 语法</p>
                    </div>
                  </div>
                  <button @click="removeCertificate(index)" class="text-red-500 hover:text-red-700 ml-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="resume.certificates.length === 0" class="border border-dashed border-gray-300 rounded-md p-4 text-center">
                <p class="text-gray-500 mb-2">添加获得的证书和认证</p>
                <button @click="addCertificate" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  + 添加证书
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧预览区域 -->
        <div class="lg:w-1/2">
          <div class="bg-white rounded-lg shadow-md p-8 border border-gray-200">
            <!-- 预览头部 -->
            <div class="border-b border-gray-200 pb-4 mb-6 flex items-start">
              <div class="w-20 h-20 border border-gray-300 flex-shrink-0 overflow-hidden mr-4">
                <img v-if="avatarPreview || resume.avatar_url" :src="avatarPreview || resume.avatar_url" class="w-full h-full object-cover" alt="头像"/>
              </div>
              <div class="flex-grow">
                <h2 class="text-xl font-bold text-gray-900">{{ resume.name || '姓名' }}</h2>
                <div class="text-sm">求职意向：{{ resume.target_position || '意向岗位' }}</div>
                <div class="flex flex-wrap gap-4 mt-2 text-gray-600 text-sm">
                  <span>{{ resume.phone || '电话' }}</span>
                  <span>{{ resume.email || '邮箱' }}</span>
                  <span>{{ resume.address || '地址' }}</span>
                </div>
              </div>
            </div>
            
            <!-- 个人自评预览 -->
            <div v-if="resume.self_evaluation" class="mb-6">
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1 h-4 bg-blue-500 mr-2"></span>
                个人自评
              </h3>
              <div class="prose prose-sm max-w-none text-gray-700" v-html="renderedSelfEvaluation"></div>
            </div>
            
            <!-- 教育背景预览 -->
            <div v-if="resume.education.length > 0" class="mb-6">
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1 h-4 bg-blue-500 mr-2"></span>
                教育背景
              </h3>
              <div v-for="(edu, index) in resume.education" :key="index" class="mb-3">
                <div class="flex justify-between font-medium">
                  <span>{{ edu.school || '学校名称' }}</span>
                  <span>{{ edu.period || '时间' }}</span>
                </div>
                <p class="text-gray-600 text-sm">{{ edu.major || '专业' }}{{ edu.degree ? ' | ' + edu.degree : '' }}</p>
              </div>
            </div>
            
            <!-- 实习经历预览 -->
            <div v-if="resume.experience.length > 0" class="mb-6">
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1 h-4 bg-blue-500 mr-2"></span>
                实习经历
              </h3>
              <div v-for="(exp, index) in resume.experience" :key="index" class="mb-4">
                <div class="flex justify-between font-medium">
                  <span>{{ exp.company || '公司名称' }}</span>
                  <span>{{ exp.period || '时间' }}</span>
                </div>
                <p class="text-gray-600 text-sm mb-2">{{ exp.position || '职位' }}</p>
                <div v-if="exp.description" class="prose prose-sm max-w-none text-gray-700" v-html="renderMarkdown(exp.description)"></div>
                <div v-else class="text-gray-400 text-sm italic">工作描述</div>
              </div>
            </div>
            
            <!-- 项目经验预览 -->
            <div v-if="resume.projects.length > 0" class="mb-6">
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1 h-4 bg-blue-500 mr-2"></span>
                项目经验
              </h3>
              <div v-for="(project, index) in resume.projects" :key="index" class="mb-3">
                <div class="flex justify-between font-medium">
                  <span>{{ project.name || '项目名称' }}</span>
                  <span>{{ project.period || '时间' }}</span>
                </div>
                <p class="text-gray-600 text-sm">{{ project.role || '担任角色' }}</p>
                <p v-if="project.url" class="text-gray-600 text-sm mt-1">
                  <a :href="project.url" target="_blank" class="text-blue-600 hover:text-blue-800">
                    {{ project.url }}
                  </a>
                </p>
                <div v-if="project.description" class="mt-2 prose prose-sm max-w-none text-gray-700" v-html="renderMarkdown(project.description)"></div>
              </div>
            </div>
            
            <!-- 专业技能预览 -->
            <div v-if="resume.skills" class="mb-6">
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1 h-4 bg-blue-500 mr-2"></span>
                专业技能
              </h3>
              <div class="prose prose-sm max-w-none text-gray-700" v-html="renderMarkdown(resume.skills)"></div>
            </div>
            
            <!-- 证书认证预览 -->
            <div v-if="resume.certificates && resume.certificates.length > 0" class="mb-6">
              <h3 class="text-lg font-bold text-gray-800 mb-3 flex items-center">
                <span class="w-1 h-4 bg-blue-500 mr-2"></span>
                证书认证
              </h3>
              <div v-for="(cert, index) in resume.certificates" :key="index" class="mb-3">
                <div class="flex justify-between font-medium">
                  <span>{{ cert.name || '证书名称' }}</span>
                  <span>{{ cert.period || '时间' }}</span>
                </div>
                <p class="text-gray-600 text-sm">{{ cert.issuer || '颁发机构' }}</p>
                <div v-if="cert.description" class="mt-2 prose prose-sm max-w-none text-gray-700" v-html="renderMarkdown(cert.description)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'

// 设置为同步解析
marked.setOptions({ async: false })

import api from '@/api'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

const router = useRouter()

const showPreview = ref(false)
const avatarInput = ref(null)
const avatarPreview = ref(null)
const uploadingAvatar = ref(false)
const showBasicInfo = ref(true)
const showSelfEvaluation = ref(true)
const showEducation = ref(true)
const showExperience = ref(true)
const showProjects = ref(true)
const showSkills = ref(true)
const showCertificates = ref(true)

// 语音输入相关
const isListening = ref(false)
const voiceInputText = ref('')
const voiceInputStatus = ref('')
const recognition = ref(null)
const isProcessing = ref(false)

const resume = ref({
  avatar_url: null,
  name: '',
  target_position: '',
  phone: '',
  email: '',
  address: '',
  self_evaluation: '',
  skills: '',
  education: [],
  experience: [],
  projects: [],
  certificates: [],
  awards: []
})

// 初始化数据
const initializeResume = () => {
  if (!resume.value.education) resume.value.education = []
  if (!resume.value.experience) resume.value.experience = []
  if (!resume.value.projects) resume.value.projects = []
  if (!resume.value.certificates) resume.value.certificates = []
  if (!resume.value.awards) resume.value.awards = []
}

// 切换基本信息显示/隐藏
const toggleBasicInfo = () => {
  showBasicInfo.value = !showBasicInfo.value
}

// 切换个人自评显示/隐藏
const toggleSelfEvaluation = () => {
  showSelfEvaluation.value = !showSelfEvaluation.value
}

// 切换教育背景显示/隐藏
const toggleEducation = () => {
  showEducation.value = !showEducation.value
}

// 切换实习经历显示/隐藏
const toggleExperience = () => {
  showExperience.value = !showExperience.value
}

// 切换项目经验显示/隐藏
const toggleProjects = () => {
  showProjects.value = !showProjects.value
}

// 切换专业技能显示/隐藏
const toggleSkills = () => {
  showSkills.value = !showSkills.value
}

// 切换证书认证显示/隐藏
const toggleCertificates = () => {
  showCertificates.value = !showCertificates.value
}

// 渲染 Markdown 格式的个人自评
const renderedSelfEvaluation = computed(() => {
  if (!resume.value.self_evaluation) return '<p class="text-gray-400 italic">暂无内容，请在上方编辑</p>'
  return marked.parse(resume.value.self_evaluation, { breaks: true })
})

// 渲染 Markdown 文本
const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text, { breaks: true })
}

const loadResume = async () => {
  try {
    // 先尝试从本地存储加载数据
    const localResume = localStorage.getItem('resume')
    if (localResume) {
      try {
        const parsedData = JSON.parse(localResume)
        Object.assign(resume.value, {
          avatar_url: parsedData.avatar_url || null,
          name: parsedData.name || '',
          target_position: parsedData.target_position || '',
          phone: parsedData.phone || '',
          email: parsedData.email || '',
          address: parsedData.address || '',
          self_evaluation: parsedData.self_evaluation || '',
          skills: parsedData.skills || '',
          education: parsedData.education || [],
          experience: parsedData.experience || [],
          projects: parsedData.projects || [],
          certificates: parsedData.certificates || [],
          awards: parsedData.awards || []
        })
      } catch (parseError) {
        console.error('解析本地存储数据失败:', parseError)
      }
    }
    
    // 然后尝试从API加载数据
    try {
      const data = await api.get('/resumes/my/')
      console.log('API返回的数据:', data)
      if (data) {
        Object.assign(resume.value, {
          avatar_url: data.avatar_url || resume.value.avatar_url,
          name: data.name || resume.value.name,
          target_position: data.target_position || resume.value.target_position,
          phone: data.phone || resume.value.phone,
          email: data.email || resume.value.email,
          address: data.address || resume.value.address,
          self_evaluation: data.self_evaluation || resume.value.self_evaluation,
          skills: data.skills || resume.value.skills,
          education: data.education && data.education.length > 0 ? data.education : resume.value.education,
          experience: data.experience && data.experience.length > 0 ? data.experience : resume.value.experience,
          projects: data.projects || resume.value.projects,
          certificates: data.certificates || resume.value.certificates,
          awards: data.awards || resume.value.awards
        })
        // 将API数据保存到本地存储
        localStorage.setItem('resume', JSON.stringify(resume.value))
      }
    } catch (apiError) {
      console.log('API加载失败，使用本地存储数据:', apiError)
    }
  } catch (error) {
    console.error('加载简历数据失败:', error)
    // API失败时，再次尝试从本地存储加载
    const localResume = localStorage.getItem('resume')
    if (localResume) {
      try {
        const parsedData = JSON.parse(localResume)
        Object.assign(resume.value, parsedData)
      } catch (parseError) {
        console.error('解析本地存储数据失败:', parseError)
      }
    }
  }
  
  // 初始化所有数组字段
  initializeResume()
}

const triggerAvatarUpload = () => {
  avatarInput.value?.click()
}

const handleAvatarChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    alert('只支持 JPEG, PNG, GIF, WEBP 格式的图片')
    return
  }
  
  // 验证文件大小 (最大 5MB)
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过 5MB')
    return
  }
  
  // 预览图片
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarPreview.value = e.target.result
  }
  reader.readAsDataURL(file)
  
  // 上传图片
  uploadingAvatar.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', file)
    
    const response = await api.post('/resumes/upload_avatar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    console.log('上传响应:', response)
    if (response && response.avatar_url) {
      resume.value.avatar_url = response.avatar_url
      avatarPreview.value = null
      alert('头像上传成功！')
    } else {
      throw new Error('响应中没有 avatar_url')
    }
  } catch (error) {
    console.error('上传头像失败:', error)
    alert('上传头像失败，请重试')
    avatarPreview.value = null
  } finally {
    uploadingAvatar.value = false
  }
  
  // 清空 input
  event.target.value = ''
}

const removeAvatar = async () => {
  if (!confirm('确定要删除头像吗？')) return
  
  try {
    await api.delete('/resumes/delete_avatar/')
    resume.value.avatar_url = null
    avatarPreview.value = null
    alert('头像删除成功！')
  } catch (error) {
    console.error('删除头像失败:', error)
    alert('删除头像失败，请重试')
  }
}

const addEducation = () => {
  resume.value.education.push({
    school: '',
    major: '',
    degree: '',
    period: '',
    description: ''
  })
}

const removeEducation = (index) => {
  resume.value.education.splice(index, 1)
}

const addExperience = () => {
  resume.value.experience.push({
    company: '',
    position: '',
    period: '',
    description: ''
  })
}

const removeExperience = (index) => {
  resume.value.experience.splice(index, 1)
}

const addProject = () => {
  resume.value.projects.push({
    name: '',
    role: '',
    period: '',
    url: '',
    description: ''
  })
}

const removeProject = (index) => {
  resume.value.projects.splice(index, 1)
}

const addCertificate = () => {
  if (!resume.value.certificates) {
    resume.value.certificates = []
  }
  resume.value.certificates.push({
    name: '',
    issuer: '',
    period: '',
    description: ''
  })
}

const removeCertificate = (index) => {
  if (!resume.value.certificates) {
    resume.value.certificates = []
    return
  }
  resume.value.certificates.splice(index, 1)
}

const saveResume = async () => {
  try {
    // 字段归一化处理
    const normalizeData = () => {
      const education = (resume.value.education || []).filter(edu => edu.school && edu.period).map((edu, index) => ({
        ...edu,
        school: edu.school || '',
        major: edu.major || '',
        degree: edu.degree || '',
        period: edu.period || '',
        description: edu.description || '',
        sort: index
      }))
      
      const experience = (resume.value.experience || []).filter(exp => exp.company && exp.position && exp.period).map((exp, index) => ({
        ...exp,
        company: exp.company || '',
        position: exp.position || '',
        period: exp.period || '',
        description: exp.description || '',
        sort: index
      }))
      
      const projects = (resume.value.projects || []).filter(project => project.name && project.role && project.period).map((project, index) => ({
        ...project,
        name: project.name || '',
        role: project.role || '',
        period: project.period || '',
        url: project.url || '',
        description: project.description || '',
        sort: index
      }))
      
      const certificates = (resume.value.certificates || []).filter(cert => cert.name && cert.issuer && cert.period).map((cert, index) => ({
        ...cert,
        name: cert.name || '',
        issuer: cert.issuer || '',
        period: cert.period || '',
        description: cert.description || '',
        sort: index
      }))
      
      const awards = (resume.value.awards || []).filter(award => award.name && award.issuer && award.period).map((award, index) => ({
        ...award,
        name: award.name || '',
        issuer: award.issuer || '',
        period: award.period || '',
        description: award.description || '',
        sort: index
      }))
      
      return {
        avatar_url: resume.value.avatar_url || null,
        name: resume.value.name || '',
        target_position: resume.value.target_position || '',
        phone: resume.value.phone || '',
        email: resume.value.email || '',
        address: resume.value.address || '',
        self_evaluation: resume.value.self_evaluation || '',
        skills: resume.value.skills || '',
        education,
        experience,
        projects,
        certificates,
        awards
      }
    }
    
    const data = normalizeData()
    console.log('保存的数据:', data)
    
    const response = await api.post('/resumes/my/', data)
    console.log('保存响应:', response)
    
    // 保存成功后，重新加载数据验证
    await loadResume()
    alert('简历保存成功！')
  } catch (error) {
    console.error('保存简历失败:', error)
    // 如果API失败，保存到本地存储
    localStorage.setItem('resume', JSON.stringify(resume.value))
    alert('简历已保存到本地！')
  }
}

// 将图片URL转换为base64
const imageToBase64 = async (url) => {
  if (!url) return null
  // 已经是 base64 则直接返回
  if (url.startsWith('data:')) return url

  // 将相对路径转为绝对路径
  let absoluteUrl = url
  if (!url.startsWith('http://') && !url.startsWith('https://') && !url.startsWith('//')) {
    absoluteUrl = new URL(url, window.location.origin).href
  }

  try {
    const response = await fetch(absoluteUrl)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const blob = await response.blob()
    
    // 如果是 WebP 格式，转换为 PNG 以确保兼容性
    if (url.endsWith('.webp') || blob.type === 'image/webp') {
      return new Promise((resolve, reject) => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        const img = new Image()
        
        img.onload = () => {
          canvas.width = img.width
          canvas.height = img.height
          ctx.drawImage(img, 0, 0)
          
          try {
            const pngDataUrl = canvas.toDataURL('image/png')
            resolve(pngDataUrl)
          } catch (error) {
            reject(error)
          }
        }
        
        img.onerror = reject
        img.src = URL.createObjectURL(blob)
      })
    }
    
    // 其他格式直接转换为 base64
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        let result = reader.result
        // 确保返回正确的 MIME 类型
        if (result.startsWith('data:application/octet-stream')) {
          // 尝试根据文件扩展名猜测 MIME 类型
          if (url.endsWith('.png')) {
            result = result.replace('data:application/octet-stream', 'data:image/png')
          } else if (url.endsWith('.jpg') || url.endsWith('.jpeg')) {
            result = result.replace('data:application/octet-stream', 'data:image/jpeg')
          } else if (url.endsWith('.gif')) {
            result = result.replace('data:application/octet-stream', 'data:image/gif')
          }
        }
        resolve(result)
      }
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  } catch (error) {
    console.error('头像转 base64 失败:', error, 'URL:', absoluteUrl)
    return null
  }
}

const exportPDF = async () => {
  // 显示加载提示
  const loading = document.createElement('div')
  loading.id = 'pdf-loading'
  loading.innerHTML = '正在生成PDF...'
  loading.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,0.8);color:white;padding:20px 40px;border-radius:8px;z-index:9999;'
  document.body.appendChild(loading)

  try {
    // 优先使用 avatarPreview（上传后的临时预览），它一定是 base64
    let avatarBase64 = avatarPreview.value || null
    if (!avatarBase64 && resume.value.avatar_url) {
      // 没有预览但存在服务器 URL，再尝试转换
      avatarBase64 = await imageToBase64(resume.value.avatar_url)
      console.log('头像 base64 转换结果:', avatarBase64 ? '成功' : '失败')
    }

    // 创建 iframe 来隔离样式
    const iframe = document.createElement('iframe')
    iframe.style.cssText = 'position:fixed;top:0;left:0;width:210mm;height:100vh;z-index:9998;border:none;'
    document.body.appendChild(iframe)

    // 构建简历 HTML 内容
    const resumeHTML = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { 
            font-family: Arial, sans-serif; 
            background-color: #ffffff; 
            padding: 32px;
            width: 210mm;
          }
        </style>
      </head>
      <body>
        <div style="display: flex; align-items: flex-start; gap: 24px; margin-bottom: 24px;">
          ${avatarBase64 ? `
          <div style="flex-shrink: 0;">
            <img src="${avatarBase64}" style="width: 96px; height: 96px; object-fit: cover; border: 2px solid #e5e7eb;" alt="头像">
          </div>
          ` : ''}
          <div style="flex: 1; text-align: center;">
            <h1 style="font-size: 24px; font-weight: bold; margin: 0;">${resume.value.name || ''}</h1>
            <div style="margin-top: 8px; font-size: 14px;">
              <p style="margin: 0;">手机号:${resume.value.phone || ''} | 邮箱:${resume.value.email || ''}</p>
            </div>
          </div>
        </div>

        ${resume.value.self_evaluation ? `
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 18px; font-weight: 600; border-bottom: 1px solid #000000; padding-bottom: 8px; margin-bottom: 12px;">个人自评</h2>
          <div style="font-size: 14px; color: #4b5563;">${renderedSelfEvaluation.value}</div>
        </div>
        ` : ''}

        ${resume.value.education.length > 0 ? `
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 18px; font-weight: 600; border-bottom: 1px solid #000000; padding-bottom: 8px; margin-bottom: 12px;">教育背景</h2>
          ${resume.value.education.map(edu => `
          <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-weight: 500;">
              <span>${edu.school || ''}</span>
              <span>${edu.period || ''}</span>
            </div>
            <div style="font-size: 14px; color: #4b5563;">
              <p style="margin: 0;">${edu.major || ''}${edu.degree ? ' | ' + edu.degree : ''}${edu.description ? ' | ' + edu.description : ''}</p>
            </div>
          </div>
          `).join('')}
        </div>
        ` : ''}

        ${resume.value.experience.length > 0 ? `
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 18px; font-weight: 600; border-bottom: 1px solid #000000; padding-bottom: 8px; margin-bottom: 12px;">实习经历</h2>
          ${resume.value.experience.map(exp => `
          <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-weight: 500;">
              <span>${exp.company || ''}</span>
              <span>${exp.period || ''}</span>
            </div>
            <div style="font-size: 14px; color: #4b5563;">
              <p style="margin: 0;">${exp.position || ''}</p>
              ${exp.description ? `<p style="margin: 4px 0 0 0;">${exp.description}</p>` : ''}
            </div>
          </div>
          `).join('')}
        </div>
        ` : ''}

        ${resume.value.projects.length > 0 ? `
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 18px; font-weight: 600; border-bottom: 1px solid #000000; padding-bottom: 8px; margin-bottom: 12px;">项目经历</h2>
          ${resume.value.projects.map(project => `
          <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-weight: 500;">
              <span>${project.name || ''}</span>
              <span>${project.period || ''}</span>
            </div>
            <div style="font-size: 14px; color: #4b5563;">
              <p style="margin: 0;">${project.role || ''}</p>
              ${project.url ? `<p style="margin: 4px 0 0 0;"><a href="${project.url}" target="_blank" style="color: #2563eb; text-decoration: none;">项目链接: ${project.url}</a></p>` : ''}
              ${project.description ? `<div style="margin: 4px 0 0 0;">${renderMarkdown(project.description)}</div>` : ''}
            </div>
          </div>
          `).join('')}
        </div>
        ` : ''}

        ${resume.value.skills ? `
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 18px; font-weight: 600; border-bottom: 1px solid #000000; padding-bottom: 8px; margin-bottom: 12px;">专业技能</h2>
          <div style="font-size: 14px; color: #4b5563;">${renderMarkdown(resume.value.skills)}</div>
        </div>
        ` : ''}

        ${resume.value.certificates && resume.value.certificates.length > 0 ? `
        <div style="margin-bottom: 24px;">
          <h2 style="font-size: 18px; font-weight: 600; border-bottom: 1px solid #000000; padding-bottom: 8px; margin-bottom: 12px;">证书认证</h2>
          ${resume.value.certificates.map(cert => `
          <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-weight: 500;">
              <span>${cert.name || ''}</span>
              <span>${cert.period || ''}</span>
            </div>
            <div style="font-size: 14px; color: #4b5563;">
              <p style="margin: 0;">${cert.issuer || ''}</p>
              ${cert.description ? `<div style="margin: 4px 0 0 0;">${renderMarkdown(cert.description)}</div>` : ''}
            </div>
          </div>
          `).join('')}
        </div>
        ` : ''}
      </body>
      </html>
    `

    // 写入 iframe
    iframe.contentDocument.open()
    iframe.contentDocument.write(resumeHTML)
    iframe.contentDocument.close()

    // 等待 iframe 加载完成
    await new Promise(resolve => {
      iframe.onload = resolve
      // 为了安全起见，设置一个最大等待时间
      setTimeout(resolve, 2000)
    })

    // 额外等待 1 秒，确保图片完全加载
    await new Promise(resolve => setTimeout(resolve, 1000))

    // 调试：检查 iframe 中的头像元素
    const avatarElement = iframe.contentDocument.querySelector('img[src^="data:"]')
    console.log('iframe 中的头像元素:', avatarElement)
    console.log('头像元素是否存在:', !!avatarElement)
    if (avatarElement) {
      console.log('头像元素 src:', avatarElement.src.substring(0, 100) + '...')
      console.log('头像元素样式:', avatarElement.style.cssText)
      console.log('头像元素父容器:', avatarElement.parentElement)
    }

    // 使用 html2canvas 渲染 iframe 内容
    const canvas = await html2canvas(iframe.contentDocument.body, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      logging: true,
      backgroundColor: '#ffffff',
      width: 794,
      height: iframe.contentDocument.body.scrollHeight,
      imageTimeout: 5000
    })
    
    // 调试：保存 canvas 为图片，查看是否包含头像
    const canvasUrl = canvas.toDataURL('image/png')
    console.log('Canvas 生成成功，包含头像:', canvasUrl.substring(0, 100) + '...')

    // 移除 iframe
    document.body.removeChild(iframe)

    // 获取 canvas 尺寸
    const imgWidth = 210
    const pageHeight = 297
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    // 创建 PDF
    const pdf = new jsPDF('p', 'mm', 'a4')

    let heightLeft = imgHeight
    let position = 0

    const imgData = canvas.toDataURL('image/png')
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight

    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }

    // 下载 PDF
    const pdfBlob = pdf.output('blob')
    const pdfUrl = URL.createObjectURL(pdfBlob)
    const fileName = `${resume.value.name || '简历'}_${new Date().toISOString().split('T')[0]}.pdf`

    const downloadLink = document.createElement('a')
    downloadLink.href = pdfUrl
    downloadLink.download = fileName
    document.body.appendChild(downloadLink)
    downloadLink.click()
    document.body.removeChild(downloadLink)

    setTimeout(() => URL.revokeObjectURL(pdfUrl), 1000)

    // 移除加载提示
    const loadingEl = document.getElementById('pdf-loading')
    if (loadingEl) {
      document.body.removeChild(loadingEl)
    }

    alert('PDF导出成功！')
  } catch (error) {
    console.error('导出PDF失败:', error)
    const loadingEl = document.getElementById('pdf-loading')
    if (loadingEl) {
      document.body.removeChild(loadingEl)
    }
    alert('导出PDF失败: ' + (error.message || '请重试'))
  }
}

// 模拟面试
const goToInterview = () => {
  router.push('/interview')
}

// 语音输入相关函数
const initializeRecognition = () => {
  if ('webkitSpeechRecognition' in window) {
    recognition.value = new webkitSpeechRecognition()
    recognition.value.continuous = false
    recognition.value.interimResults = true
    recognition.value.lang = 'zh-CN'
    
    recognition.value.onstart = () => {
      isListening.value = true
      voiceInputStatus.value = '正在聆听...'
    }
    
    recognition.value.onresult = (event) => {
      let transcript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript
      }
      voiceInputText.value = transcript
    }
    
    recognition.value.onend = () => {
      isListening.value = false
      voiceInputStatus.value = '语音输入已结束'
      processVoiceInput()
    }
    
    recognition.value.onerror = (event) => {
      isListening.value = false
      voiceInputStatus.value = `错误: ${event.error}`
      console.error('语音识别错误:', event.error)
    }
  } else {
    voiceInputStatus.value = '您的浏览器不支持语音识别'
    console.error('浏览器不支持语音识别')
  }
}

const startVoiceInput = () => {
  if (!recognition.value) {
    initializeRecognition()
  }
  
  if (recognition.value) {
    voiceInputText.value = ''
    voiceInputStatus.value = '准备开始聆听...'
    recognition.value.start()
  }
}

const stopVoiceInput = () => {
  if (recognition.value && isListening.value) {
    recognition.value.stop()
  }
}

const processVoiceInput = async () => {
  if (!voiceInputText.value) {
    voiceInputStatus.value = '没有检测到语音输入'
    return
  }
  
  isProcessing.value = true
  voiceInputStatus.value = '正在分析语音内容...'
  
  try {
    // 调用后端API处理语音输入
    const response = await api.post('/ai/voice-to-resume/', {
      voice_text: voiceInputText.value
    })
    
    if (response.success) {
      // 更新简历数据
      const generatedResume = response.data
      if (generatedResume) {
        // 合并生成的简历数据到当前简历
        Object.assign(resume.value, generatedResume)
        voiceInputStatus.value = '简历生成成功！'
        
        // 显示成功提示
        setTimeout(() => {
          voiceInputStatus.value = ''
        }, 3000)
      }
    } else {
      voiceInputStatus.value = `生成失败: ${response.message || '请重试'}`
    }
  } catch (error) {
    console.error('处理语音输入失败:', error)
    voiceInputStatus.value = '处理失败，请重试'
  } finally {
    isProcessing.value = false
  }
}

// 监听resume对象的变化，实时保存到本地存储
watch(
  resume,
  (newValue) => {
    try {
      localStorage.setItem('resume', JSON.stringify(newValue))
    } catch (error) {
      console.error('保存到本地存储失败:', error)
    }
  },
  { deep: true, immediate: true }
)

onMounted(async () => {
  await loadResume()
})
</script>

<style scoped>
/* 可添加自定义样式 */
</style>