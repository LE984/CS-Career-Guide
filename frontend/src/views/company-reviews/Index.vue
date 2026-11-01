<template>
  <div class="min-h-screen bg-gradient-to-r from-white to-purple-100 text-on-surface antialiased">
    <main class="pt-24 pb-24 max-w-7xl mx-auto px-2">
      <!-- Page Header -->
      <header class="mb-16">
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 class="text-5xl font-extrabold tracking-tight text-primary-container mb-4">企业招聘</h1>
            <p class="text-xl text-on-primary-container max-w-3xl">精选计算机行业优质职位，结合学长学姐真实评价，助你精准对接理想 Offer</p>
          </div>
          <div class="flex gap-3">
            <router-link to="/resume" class="px-10 py-4 bg-secondary-container text-black rounded-2xl font-bold hover:shadow-xl hover:shadow-secondary/60 transition-all active:scale-95 border-2 border-black">
              简历优化
            </router-link>
          </div>
        </div>
      </header>
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <!-- Main Content Area -->
        <div class="lg:col-span-8 space-y-12">
          <!-- Filter & Tabs -->
          <section class="space-y-8">
            <div class="flex flex-wrap items-center gap-2 p-1 bg-surface-container-low rounded-2xl w-fit">
              <button 
                @click="switchTab('recommended')"
                :class="activeTab === 'recommended' ? 'px-8 py-2.5 bg-surface-container-lowest text-secondary font-bold rounded-xl shadow-sm rounded-2xl border-2 border-black' : 'px-8 py-2.5 text-on-surface-variant hover:text-secondary transition-all font-medium rounded-2xl border-2 border-black'"
              >推荐职位</button>
              <button 
                @click="switchTab('red')"
                :class="activeTab === 'red' ? 'px-8 py-2.5 bg-surface-container-lowest text-secondary font-bold rounded-2xl shadow-sm border-2 border-black' : 'px-8 py-2.5 text-on-surface-variant hover:text-secondary transition-all font-medium rounded-2xl border-2 border-black'"
              >红榜 (推荐)</button>
              <button 
                @click="switchTab('black')"
                :class="activeTab === 'black' ? 'px-8 py-2.5 bg-surface-container-lowest text-secondary font-bold rounded-2xl shadow-sm border-2 border-black' : 'px-8 py-2.5 text-on-surface-variant hover:text-secondary transition-all font-medium rounded-2xl border-2 border-black'"
              >黑榜 (避坑)</button>
              <button 
                @click="switchTab('safety')"
                :class="activeTab === 'safety' ? 'px-8 py-2.5 bg-surface-container-lowest text-secondary font-bold rounded-2xl shadow-sm border-2 border-black' : 'px-8 py-2.5 text-on-surface-variant hover:text-secondary transition-all font-medium rounded-2xl border-2 border-black'"
              >求职安全</button>
              <button 
                @click="switchTab('advice')"
                :class="activeTab === 'advice' ? 'px-8 py-2.5 bg-surface-container-lowest text-secondary font-bold rounded-2xl shadow-sm border-2 border-black' : 'px-8 py-2.5 text-on-surface-variant hover:text-secondary transition-all font-medium rounded-2xl border-2 border-black'"
              >学长学姐建议</button>
            </div>
           
          </section>

          
          <!-- Job List Content -->
          <section class="space-y-6">
            <!-- 推荐职位 -->
            <div v-if="activeTab === 'recommended'">
              <!-- 搜索框 -->
              <div class="mb-6">
                <div class="relative">
                  <input 
                    v-model="searchKeyword" 
                    @input="handleSearch"
                    type="text" 
                    placeholder="搜索职位、公司、地址或行业..."
                    class="w-full px-4 py-3 pl-14 pr-12 bg-surface-container-lowest border border-outline/5 rounded-xl focus:outline-none focus:ring-2 focus:ring-secondary/20"
                  >
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-outline">
                    <span class="material-symbols-outlined">搜索：</span>
                  </span>
                  <button 
                    v-if="searchKeyword"
                    @click="clearSearch"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-outline hover:text-secondary transition-colors"
                  >
                    <span class="material-symbols-outlined">清空</span>
                  </button>
                </div>
              </div>
              <div v-if="jobsLoading" class="flex items-center justify-center py-16">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary"></div>
              </div>
              <div v-else-if="filteredJobs.length === 0" class="text-center py-16">
                <p class="text-on-surface-variant">{{ searchKeyword ? '没有找到匹配的职位' : '暂无职位数据' }}</p>
              </div>
              <div v-else class="space-y-6">
                <div 
                  v-for="job in currentFilteredJobs" 
                  :key="job.id"
                  class="bg-surface-container-lowest rounded-[1.5rem] p-6 border border-outline/5 hover:border-secondary/20 hover:shadow-xl hover:shadow-secondary/5 transition-all group"
                >
                  <div class="flex flex-col md:flex-row gap-6">
                    <div class="flex-1">
                      <div class="flex flex-wrap justify-between items-start mb-3 gap-4">
                        <div>
                          <h3 class="text-xl font-bold mb-1 group-hover:text-secondary transition-colors">{{ job.title }}</h3>
                          <p class="text-on-primary-container font-medium">{{ job.company }}</p>
                        </div>
                        <div class="text-right">
                          <span class="text-2xl font-black text-secondary">{{ job.salary }}</span>
                        </div>
                      </div>
                      <div class="flex flex-wrap gap-2 mb-4">
                        <span 
                          v-for="(tag, index) in job.tags" 
                          :key="index"
                          class="px-3 py-1 bg-surface-container-low text-on-surface-variant text-xs rounded-lg font-medium truncate max-w-[480px]"
                        >
                          {{ tag }}
                        </span>
                      </div>
                      <div class="mb-6">
                        <p class="text-sm text-on-primary-container line-clamp-2">{{ filterBrTags(job.jobDetails) }}</p>
                      </div>
                      
                      <div class="flex items-center justify-between pt-4 border-t border-outline/5">
                        <div class="flex-1 min-w-0">
                          <p v-if="isCompanyDetailsValid(job.companyDetails)" class="text-xs text-on-primary-container line-clamp-1">公司详细：{{ filterBrTags(job.companyDetails) }}</p>
                        </div>
                        <a 
                          :href="job.jobSourceUrl" 
                          target="_blank"
                          class="ml-4 px-6 py-2 bg-primary-container text-black rounded-xl text-sm font-bold hover:bg-secondary transition-colors whitespace-nowrap"
                        >
                          立即申请
                        </a>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- 职位分页 -->
                <div v-if="filteredJobsTotalPages > 1" class="flex items-center justify-center gap-2 mt-8">
                  <button 
                    @click="handleJobsPageChange(jobsPage - 1)" 
                    :disabled="jobsPage === 1"
                    class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span class="material-symbols-outlined">上一页</span>
                  </button>
                  <span class="text-sm text-on-surface-variant mx-4">
                    {{ jobsPage }} / {{ filteredJobsTotalPages }}
                  </span>
                  <button 
                    @click="handleJobsPageChange(jobsPage + 1)" 
                    :disabled="jobsPage >= filteredJobsTotalPages"
                    class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span class="material-symbols-outlined">下一页</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- 红榜内容 -->
            <div v-else-if="activeTab === 'red'" class="bg-surface-container-lowest rounded-[2rem] p-8 border border-outline/5">
              <h3 class="text-xl font-bold mb-6 flex items-center gap-2">
                红榜职位推荐
                <span class="material-symbols-outlined text-red-500" style="font-variation-settings: 'FILL' 1;">Trending_up</span>
              </h3>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[1000px]">
                  <thead>
                    <tr class="border-b border-outline/10">
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 60px;">排名</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 120px;">岗位名称</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 220px;">公司名称</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 120px;">工作地点</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 120px;">薪资范围</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant">红榜理由</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in currentRedListData" :key="item.rank" class="border-b border-outline/5 hover:bg-surface-container-low transition-colors">
                      <td class="py-3 px-3 font-bold text-secondary">{{ item.rank }}</td>
                      <td class="py-3 px-3 font-medium">{{ item.position }}</td>
                      <td class="py-3 px-3">{{ item.company }}</td>
                      <td class="py-3 px-3 text-on-primary-container">{{ item.location }}</td>
                      <td class="py-3 px-3 font-medium text-green-500">{{ item.salary || '-' }}</td>
                      <td class="py-3 px-3 text-on-primary-container">{{ item.reason }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <!-- 红榜分页 -->
              <div class="flex items-center justify-center gap-2 mt-8">
                <button 
                  @click="handleRedListPageChange(redListPage - 1)" 
                  :disabled="redListPage === 1"
                  class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span class="material-symbols-outlined">上一页</span>
                </button>
                <span class="text-sm text-on-surface-variant mx-4">
                  {{ redListPage }} / {{ redListTotalPages }}
                </span>
                <button 
                  @click="handleRedListPageChange(redListPage + 1)" 
                  :disabled="redListPage >= redListTotalPages"
                  class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span class="material-symbols-outlined">下一页</span>
                </button>
              </div>
            </div>

            <!-- 黑榜内容 -->
            <div v-else-if="activeTab === 'black'" class="bg-surface-container-lowest rounded-[2rem] p-8 border border-outline/5">
              <h3 class="text-xl font-bold mb-6 flex items-center gap-2">
                黑榜职位避坑
                <span class="material-symbols-outlined text-red-500" style="font-variation-settings: 'FILL' 1;">Trending_down</span>
              </h3>
              <div class="overflow-x-auto">
                <table class="w-full min-w-[1000px]">
                  <thead>
                    <tr class="border-b border-outline/10">
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 60px;">排名</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 120px;">岗位名称</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 220px;">公司名称</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 120px;">工作地点</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant" style="width: 120px;">薪资范围</th>
                      <th class="text-left py-3 px-3 font-semibold text-on-surface-variant">黑榜理由</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in currentBlackListData" :key="item.rank" class="border-b border-outline/5 hover:bg-surface-container-low transition-colors">
                      <td class="py-3 px-3 font-bold text-red-500">{{ item.rank }}</td>
                      <td class="py-3 px-3 font-medium">{{ item.position }}</td>
                      <td class="py-3 px-3">{{ item.company }}</td>
                      <td class="py-3 px-3 text-on-primary-container">{{ item.location }}</td>
                      <td class="py-3 px-3 font-medium text-red-500">{{ item.salary || '-' }}</td>
                      <td class="py-3 px-3 text-on-primary-container">{{ item.reason }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <!-- 黑榜分页 -->
              <div class="flex items-center justify-center gap-2 mt-8">
                <button 
                  @click="blackListPage--" 
                  :disabled="blackListPage === 1"
                  class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span class="material-symbols-outlined">上一页</span>
                </button>
                <span class="text-sm text-on-surface-variant mx-4">
                  {{ blackListPage }} / {{ blackListTotalPages }}
                </span>
                <button 
                  @click="blackListPage++" 
                  :disabled="blackListPage >= blackListTotalPages"
                  class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span class="material-symbols-outlined">下一页</span>
                </button>
              </div>
            </div>

            <!-- 求职安全 -->
            <div v-else-if="activeTab === 'safety'" class="bg-surface-container-lowest rounded-[2rem] p-8 border border-outline/5">
              <h3 class="text-xl font-bold mb-6 flex justify-center items-center gap-2">
                求职安全指南
                <span class="material-symbols-outlined text-blue-500" style="font-variation-settings: 'FILL' 1;">security</span>
              </h3>
              
              <!-- 核心内容 -->
              <div class="mb-8">
                <h4 class="text-lg font-bold mb-4 text-blue-600 flex justify-center items-center gap-2">求职诈骗的四大类型与识别方法</h4>
                <p class="text-on-primary-container mb-6">根据法治网、各地人社局及公安部门的通报，目前的求职诈骗呈现"技术化"和"集团化"特征。</p>
                <p class="text-on-primary-container mb-6">以下是四类常见陷阱：</p>
              </div>
              
              <!-- 诈骗类型卡片 -->
              <div class="space-y-6 mb-8">
                <!-- 招转培与培训贷 -->
                <div class="bg-surface-container-low p-6 rounded-xl border-l-4 border-red-500">
                  <div class="flex items-start gap-4">
                    <span class="material-symbols-outlined text-red-500 text-2xl mt-1">警惕培训贷骗局：</span>
                    <div class="flex-1">
                      <h5 class="font-bold text-lg mb-2">1. "招转培"与"培训贷"</h5>
                      <p class="text-on-primary-container mb-3">这是目前高发的诈骗类型，通常以"高薪"、"零基础"、"内推"为诱饵。</p>
                      <div class="space-y-2 mb-3">
                        <div>
                          <span class="font-semibold text-on-surface">诈骗手法：</span>
                          <p class="text-on-primary-container">冒充猎头或大厂HR，声称提供免费的岗前实训，承诺"包就业、月薪过万"。实训结束后，以"就业服务费"名义诱导求职者签署合同，办理分期贷款（培训贷），费用高达2-3万元。一旦签约，即便未就业也难以退款。</p>
                        </div>
                        <div>
                          <span class="font-semibold text-on-surface">识别要点：</span>
                          <p class="text-on-primary-container">正规企业不会在入职前收取高额培训费；警惕"先学后付"的贷款诱导。</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 虚假招聘与违规收费 -->
                <div class="bg-surface-container-low p-6 rounded-xl border-l-4 border-orange-500">
                  <div class="flex items-start gap-4">
                    <span class="material-symbols-outlined text-orange-500 text-2xl mt-1">入职前不缴费：</span>
                    <div class="flex-1">
                      <h5 class="font-bold text-lg mb-2">2. 虚假招聘与违规收费</h5>
                      <div class="space-y-2 mb-3">
                        <div>
                          <span class="font-semibold text-on-surface">诈骗手法：</span>
                          <p class="text-on-primary-container">利用"高薪"、"轻松"、"急聘"等字眼吸引眼球，随后以押金、报名费、体检费、服装费、资料审核费等名义多次收费。还有的黑中介虚假宣传"保过拿证"、"内推落户"，利用求职者迫切心理收取巨额中介费后跑路。</p>
                        </div>
                        <div>
                          <span class="font-semibold text-on-surface">识别要点：</span>
                          <p class="text-on-primary-container">任何入职前要求转账到私人账户的行为，都是诈骗。</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 刷单返利与轻松兼职 -->
                <div class="bg-surface-container-low p-6 rounded-xl border-l-4 border-yellow-500">
                  <div class="flex items-start gap-4">
                    <span class="material-symbols-outlined text-yellow-500 text-2xl mt-1">刷单垫资是诈骗：</span>
                    <div class="flex-1">
                      <h5 class="font-bold text-lg mb-2">3. 刷单返利与"轻松兼职"</h5>
                      <div class="space-y-2 mb-3">
                        <div>
                          <span class="font-semibold text-on-surface">诈骗手法：</span>
                          <p class="text-on-primary-container">以"零门槛、高佣金、日结"为诱饵，诱导下载非官方App进行刷单。前期小额返利获取信任，后期以"连单任务"、"账户冻结"为由拒绝返款。</p>
                        </div>
                        <div>
                          <span class="font-semibold text-on-surface">识别要点：</span>
                          <p class="text-on-primary-container">凡是要求垫资的兼职都是诈骗；不要下载不明来源的App。</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 境外高薪与非法拘禁 -->
                <div class="bg-surface-container-low p-6 rounded-xl border-l-4 border-red-600">
                  <div class="flex items-start gap-4">
                    <span class="material-symbols-outlined text-red-600 text-2xl mt-1">境外高薪需警惕：</span>
                    <div class="flex-1">
                      <h5 class="font-bold text-lg mb-2">4. "境外高薪"与非法拘禁</h5>
                      <div class="space-y-2 mb-3">
                        <div>
                          <span class="font-semibold text-on-surface">诈骗手法：</span>
                          <p class="text-on-primary-container">打着"境外高薪招聘"、"月入数万"的旗号，甚至谎称是剧组招人、海外陪游，实则诱骗求职者偷渡出境，从事电信诈骗或面临非法拘禁。</p>
                        </div>
                        <div>
                          <span class="font-semibold text-on-surface">识别要点：</span>
                          <p class="text-on-primary-container">对于门槛极低、薪资极高且工作地点在境外的岗位，保持高度警惕。</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 防骗指南 -->
              <div class="bg-primary-container rounded-xl p-6 text-black">
                <h4 class="text-lg font-bold mb-4">二、 防骗"五防三要"指南</h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <!-- 五防 -->
                  <div>
                    <h5 class="font-bold text-blue-700 mb-3 flex items-center gap-2">
                      <span class="material-symbols-outlined">屏障</span>
                      "五防"
                    </h5>
                    <ul class="space-y-2">
                      <li class="flex items-start gap-2">
                        <span><strong>防黑中介：</strong>核实资质，拒绝无证机构。</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span><strong>防乱收费：</strong>拒绝一切入职前的收费要求。</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span><strong>防培训贷：</strong>谨慎对待"包就业"培训，绝不轻易贷款。</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span><strong>防付费实习：</strong>正规实习不应收费。</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span><strong>防非法传销：</strong>警惕"拉人头"、"轻松赚大钱"的话术。</span>
                      </li>
                    </ul>
                  </div>
                  
                  <!-- 三要 -->
                  <div>
                    <h5 class="font-bold text-orange-700 mb-3 flex items-center gap-2">
                      <span class="material-symbols-outlined">信息</span>
                      "三要"
                    </h5>
                    <ul class="space-y-2">
                      <li class="flex items-start gap-2">
                        <span><strong>要核实：</strong>利用国家企业信用信息公示系统，核查企业资质。</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span><strong>要留证：</strong>保存聊天记录、转账凭证、合同协议。</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span><strong>要报警：</strong>遭遇诈骗第一时间拨打110或向人社部门投诉。</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 学长学姐建议 -->
            <div v-else-if="activeTab === 'advice'" class="bg-surface-container-lowest rounded-[2rem] p-8 border border-outline/5">
              <div class="flex justify-between items-center mb-6">
                <h3 class="text-xl font-bold flex items-center gap-2">
                  学长学姐建议
                  <span class="material-symbols-outlined text-secondary" style="font-variation-settings: 'FILL' 1;">advice</span>
                </h3>
                <router-link to="/company-reviews/senior-advice/form" class="px-6 py-2 bg-secondary text-white rounded-xl text-sm font-bold hover:bg-secondary/90 transition-colors">
                  提交建议
                </router-link>
              </div>
              
              <!-- 搜索和筛选 -->
              <div class="flex flex-wrap gap-4 mb-6">
                <div class="flex-1 min-w-[200px]">
                  <input 
                    v-model="adviceSearchKeyword" 
                    type="text" 
                    placeholder="搜索公司或职位..."
                    class="w-full px-4 py-2 bg-surface-container-low border border-outline/5 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary/20"
                  >
                </div>
                <div>
                  <select v-model="adviceFilter" class="px-4 py-2 bg-surface-container-low border border-outline/5 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary/20">
                    <option value="">全部</option>
                    <option value="high-rating">评分最高</option>
                    <option value="recent">最新提交</option>
                  </select>
                </div>
              </div>
              
              <!-- 建议列表 -->
              <div v-if="adviceLoading" class="flex items-center justify-center py-16">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary"></div>
              </div>
              <div v-else-if="adviceList.length === 0" class="text-center py-16">
                <p class="text-on-surface-variant">暂无学长学姐建议</p>
                <router-link to="/company-reviews/senior-advice/form" class="inline-block mt-4 px-6 py-2 bg-secondary text-white rounded-xl text-sm font-bold hover:bg-secondary/90 transition-colors">
                  成为第一个提交建议的人
                </router-link>
              </div>
              <div v-else class="space-y-6">
                <div 
                  v-for="advice in filteredAdviceList" 
                  :key="advice.id"
                  class="bg-surface-container-low p-6 rounded-xl border border-outline/5 hover:border-secondary/20 hover:shadow-lg transition-all"
                >
                  <div class="flex flex-col md:flex-row md:items-start gap-6">
                    <div class="flex-1">
                      <div class="flex flex-wrap justify-between items-start mb-3 gap-4">
                        <div>
                          <h4 class="text-lg font-bold mb-1 text-secondary">{{ advice.company }}</h4>
                          <p class="text-on-primary-container font-medium">{{ advice.position }}</p>
                        </div>
                        <div class="flex items-center gap-2">
                          <span class="text-sm text-on-surface-variant">评分:</span>
                          <span class="text-lg font-bold text-secondary">{{ advice.rating }}/5</span>
                        </div>
                      </div>
                      
                      <div class="flex flex-wrap gap-2 mb-4">
                        <span class="px-3 py-1 bg-surface-container-lowest text-on-surface-variant text-xs rounded-lg font-medium">
                          {{ advice.senior_name }} ({{ advice.graduation_year }}届)
                        </span>
                        <span v-if="advice.current_company" class="px-3 py-1 bg-surface-container-lowest text-on-surface-variant text-xs rounded-lg font-medium">
                          现就职: {{ advice.current_company }}
                        </span>
                        <span v-if="advice.salary_info" class="px-3 py-1 bg-surface-container-lowest text-on-surface-variant text-xs rounded-lg font-medium">
                          薪资: {{ advice.salary_info }}
                        </span>
                      </div>
                      
                      <div class="mb-4">
                        <p class="text-sm text-on-primary-container">{{ advice.advice }}</p>
                      </div>
                      
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div v-if="advice.pros && advice.pros.length > 0">
                          <h5 class="text-sm font-semibold text-green-600 mb-2">优点:</h5>
                          <ul class="text-sm text-on-primary-container space-y-1">
                            <li v-for="(pro, index) in advice.pros" :key="index" class="text-sm text-on-primary-container">
                              {{ pro }}
                            </li>
                          </ul>
                        </div>
                        <div v-if="advice.cons && advice.cons.length > 0">
                          <h5 class="text-sm font-semibold text-red-600 mb-2">缺点:</h5>
                          <ul class="text-sm text-on-primary-container space-y-1">
                            <li v-for="(con, index) in advice.cons" :key="index" class="text-sm text-on-primary-container">
                              {{ con }}
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 分页 -->
                <div v-if="adviceTotalPages > 1" class="flex items-center justify-center gap-2 mt-8">
                  <button 
                    @click="handleAdvicePageChange(advicePage - 1)" 
                    :disabled="advicePage === 1"
                    class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span class="material-symbols-outlined">上一页</span>
                  </button>
                  <span class="text-sm text-on-surface-variant mx-4">
                    {{ advicePage }} / {{ adviceTotalPages }}
                  </span>
                  <button 
                    @click="handleAdvicePageChange(advicePage + 1)" 
                    :disabled="advicePage >= adviceTotalPages"
                    class="px-4 py-2 bg-surface-container-lowest rounded-lg border border-outline/20 hover:bg-surface-container-low transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span class="material-symbols-outlined">下一页</span>
                  </button>
                </div>
              </div>
            </div>
          </section>

        </div>
        <!-- Sidebar Section -->
        <aside class="lg:col-span-4 space-y-8 mr-1">
          <!-- 湖南高校双选会 -->
          <div class="bg-surface-container-low rounded-[2rem] p-8">
            <h3 class="text-lg font-bold mb-6 flex items-center gap-1">
              湖南高校双选会
              <span class="material-symbols-outlined text-secondary" style="font-variation-settings: 'FILL' 1;">school</span>
            </h3>
            <div v-if="loading" class="flex items-center justify-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
            </div>
            <div v-else-if="jobFairs.length === 0" class="text-center py-8">
              <p class="text-on-surface-variant">暂无双选会数据</p>
            </div>
            <div v-else class="space-y-4">
              <div 
                v-for="(fair, index) in jobFairs" 
                :key="fair.id"
                class="flex items-center gap-4 group cursor-pointer"
              >
                <span class="text-2xl font-extrabold text-outline/30 group-hover:text-secondary transition-colors italic">{{ (currentPage - 1) * pageSize + index + 1 }}</span>
                <div class="flex-1">
                  <h4 class="font-bold text-on-surface group-hover:text-secondary transition-colors">{{ getUniversityName(fair.university) }}</h4>
                  <a 
                    :href="fair.university_url" 
                    target="_blank" 
                    class="text-xs text-secondary hover:underline flex items-center gap-1"
                  >
                    {{ fair.name }}
                  </a>
                </div>
              </div>
              
              <!-- 分页 -->
              <div v-if="totalCount > pageSize" class="flex items-center justify-center gap-2 mt-8">
                <button 
                  @click="handlePageChange(currentPage - 1)" 
                  :disabled="currentPage === 1"
                  class="px-3 py-1 rounded-lg border border-outline/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  上一页
                </button>
                <span class="text-sm text-on-surface-variant">
                  {{ currentPage }} / {{ Math.ceil(totalCount / pageSize) }}
                </span>
                <button 
                  @click="handlePageChange(currentPage + 1)" 
                  :disabled="currentPage >= Math.ceil(totalCount / pageSize)"
                  class="px-3 py-1 rounded-lg border border-outline/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
          <!-- Local Recruitment News -->
          <div class="bg-surface-container-low rounded-[2rem] p-8 border border-outline/5">
            <h3 class="text-lg font-bold mb-6 flex items-center gap-1">
              地区招聘资讯
              <span class="material-symbols-outlined text-secondary" style="font-variation-settings: 'FILL' 1;">location</span>
            </h3>
            
            <div v-if="locationStatus === 'loading'" class="flex items-center justify-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
            </div>
            
            <div v-else-if="locationStatus === 'denied'" class="text-center py-8">
              <div class="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <span class="material-symbols-outlined text-3xl text-red-400">location_disabled</span>
              </div>
              <p class="text-on-surface-variant text-sm">用户未授权位置权限</p>
            </div>
            
            <div v-else-if="locationStatus === 'success' && locationJobs.length === 0" class="text-center py-8">
              <p class="text-on-surface-variant text-sm">{{ currentCity }}暂无相关职位</p>
            </div>
            
            <div v-else-if="locationStatus === 'success'" class="space-y-4">
              <div 
                v-for="job in locationJobs.slice(0, 3)" 
                :key="job.id"
                class="p-4 bg-surface-container-lowest rounded-2xl border border-outline/10 hover:border-secondary transition-all cursor-pointer group"
              >
                <div class="flex justify-between items-start mb-2">
                  <span class="px-2 py-0.5 bg-secondary/10 text-secondary text-[10px] font-bold rounded">职位</span>
                  <span v-if="job.salary_range" class="text-[10px] text-secondary font-medium">{{ job.salary_range }}</span>
                </div>
                <h4 class="font-bold text-on-surface mb-2 group-hover:text-secondary transition-colors">{{ job.position_name }}</h4>
                <div class="flex items-center gap-2 text-xs text-on-primary-container">
                  <span class="material-symbols-outlined text-sm">business</span>
                  <span>{{ job.company_name }}</span>
                </div>
                <div class="flex items-center gap-2 text-xs text-on-primary-container mt-1">
                  <span class="material-symbols-outlined text-sm">location_on</span>
                  <span>{{ job.address }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Career Tip Card -->
          <div class="bg-base-container rounded-[2rem] p-8 text-white relative group overflow-hidden">
            <div class="relative z-10">
              <p class="font-headline text-lg font-bold mb-4 text-blue-400">“选择第一份实习工作时，实习经历远比多出 2k 的薪资更重要”</p>
            </div>
            <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <span class="material-symbols-outlined text-6xl">terminal</span>
            </div>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { jobFairAPI, computerCareerAPI, apiFetch } from '@/api'
import { IP_GEOLOCATION_URL } from '@/config'
import api from '@/api'

const router = useRouter()

// 搜索查询
const searchQuery = ref('')

// 双选会数据
const jobFairs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(8)
const totalCount = ref(0)

// 高校名称映射
const universityNameMap = {
  'csu': '中南大学',
  'hnu': '湖南大学',
  'hunnu_science': '湖南师范大学',
  'csust': '长沙理工大学',
  'hunnu': '湖南农业大学',
  'csuft': '中南林业科技大学',
  'hnu_medicine': '湖南医药学院',
  'xtu': '湘潭大学',
  'hnust': '湖南科技大学',
  'usc': '南华大学',
  'hutb': '湖南工商大学',
  'hnctu': '湖南工业大学',
  'jsu': '吉首大学',
  'hhtc': '怀化学院',
  'hnfnu': '湖南第一师范学院',
  'hufe': '湖南财政经济学院',
  'hnxxy': '湖南信息学院',
  'hnyxy': '湖南应用技术学院',
  'hnist': '湖南理工学院',
  'hynu': '衡阳师范学院',
  'huas': '湖南文理学院',
  'hnjcxy': '湖南警察学院',
  'hngxy': '湖南工学院',
  'syxy': '邵阳学院',
  'xnu': '湘南学院',
  'hnrwkjxy': '湖南人文科技学院',
  'hnjtgcxy': '湖南交通工程学院',
  'hnrjzy': '湖南软件职业技术大学',
  'other': '其他高校'
}

// 获取高校名称
const getUniversityName = (universityCode) => {
  return universityNameMap[universityCode] || universityCode
}

// 地区招聘资讯
const locationStatus = ref('loading')
const currentCity = ref('')
const locationJobs = ref([])

const getCityFromIP = async () => {
  if (!IP_GEOLOCATION_URL) return null
  try {
    console.log('[Geolocation Debug] 使用 IP 地址获取城市（仅精确到市）')
    const response = await fetch(IP_GEOLOCATION_URL)
    const data = await response.json()
    console.log('[Geolocation Debug] IP 地理定位响应:', data)
    
    if (data.status === 'success') {
      // 只使用 city 字段，确保只精确到市级别
      if (data.city && data.city.trim()) {
        console.log(`[Geolocation Debug] IP定位城市: ${data.city}`)
        return data.city
      }
      // 如果没有 city，使用 regionName（省级）作为备选
      if (data.regionName && data.regionName.trim()) {
        console.log(`[Geolocation Debug] IP定位地区: ${data.regionName}`)
        return data.regionName
      }
    }
    console.log('[Geolocation Debug] IP定位失败，使用默认城市: 北京')
    return '北京'
  } catch (error) {
    console.error('[Geolocation Debug] IP 地理定位失败:', error)
    return '北京'
  }
}

const getLocationAndLoadJobs = async () => {
  console.log('[Geolocation Debug] 开始获取位置信息（使用免费 IP 定位）')
  
  try {
    // 直接使用 IP 定位（免费服务）
    const city = await getCityFromIP()
    currentCity.value = city
    console.log(`[Geolocation Debug] IP定位获取城市: ${city}`)
    await loadJobsByCity(city)
    
  } catch (error) {
    console.error('[Geolocation Debug] IP定位失败:', error)
    // 使用默认城市
    currentCity.value = '长沙'
    await loadJobsByCity('长沙')
  }
}

// 地区层级映射表（区 -> 市 -> 省）
const regionHierarchy = {
  // 长沙地区
  '天心区': { city: '长沙市', province: '湖南省' },
  '岳麓区': { city: '长沙市', province: '湖南省' },
  '芙蓉区': { city: '长沙市', province: '湖南省' },
  '开福区': { city: '长沙市', province: '湖南省' },
  '雨花区': { city: '长沙市', province: '湖南省' },
  '望城区': { city: '长沙市', province: '湖南省' },
  '长沙县': { city: '长沙市', province: '湖南省' },
  '宁乡市': { city: '长沙市', province: '湖南省' },
  '浏阳市': { city: '长沙市', province: '湖南省' },
  
  // 益阳地区
  '赫山区': { city: '益阳市', province: '湖南省' },
  '赫山': { city: '益阳市', province: '湖南省' },
  '资阳区': { city: '益阳市', province: '湖南省' },
  '沅江市': { city: '益阳市', province: '湖南省' },
  
  // 北京
  '北京': { city: '北京市', province: '北京市' },
  '东城区': { city: '北京市', province: '北京市' },
  '西城区': { city: '北京市', province: '北京市' },
  '朝阳区': { city: '北京市', province: '北京市' },
  '海淀区': { city: '北京市', province: '北京市' },
  
  // 上海
  '上海': { city: '上海市', province: '上海市' },
  '黄浦区': { city: '上海市', province: '上海市' },
  '徐汇区': { city: '上海市', province: '上海市' },
  '浦东新区': { city: '上海市', province: '上海市' },
  
  // 广州
  '广州': { city: '广州市', province: '广东省' },
  '天河区': { city: '广州市', province: '广东省' },
  '越秀区': { city: '广州市', province: '广东省' },
  '海珠区': { city: '广州市', province: '广东省' },
  
  // 深圳
  '深圳': { city: '深圳市', province: '广东省' },
  '南山区': { city: '深圳市', province: '广东省' },
  '福田区': { city: '深圳市', province: '广东省' },
  '宝安区': { city: '深圳市', province: '广东省' },
  
  // 杭州
  '杭州': { city: '杭州市', province: '浙江省' },
  '西湖区': { city: '杭州市', province: '浙江省' },
  '滨江区': { city: '杭州市', province: '浙江省' },
  
  // 成都
  '成都': { city: '成都市', province: '四川省' },
  '锦江区': { city: '成都市', province: '四川省' },
  '高新区': { city: '成都市', province: '四川省' },
  
  // 武汉
  '武汉': { city: '武汉市', province: '湖北省' },
  '武昌区': { city: '武汉市', province: '湖北省' },
  '洪山区': { city: '武汉市', province: '湖北省' },
  
  // 湖南省其他城市
  '益阳市': { city: '益阳市', province: '湖南省' },
  '岳阳市': { city: '岳阳市', province: '湖南省' },
  '株洲市': { city: '株洲市', province: '湖南省' },
  '湘潭市': { city: '湘潭市', province: '湖南省' },
  '衡阳市': { city: '衡阳市', province: '湖南省' },
  '常德市': { city: '常德市', province: '湖南省' },
  '郴州市': { city: '郴州市', province: '湖南省' },
  '永州市': { city: '永州市', province: '湖南省' },
  '邵阳市': { city: '邵阳市', province: '湖南省' },
  '娄底市': { city: '娄底市', province: '湖南省' },
  '怀化市': { city: '怀化市', province: '湖南省' },
  '张家界市': { city: '张家界市', province: '湖南省' },
  
  // 城市直接映射
  '长沙市': { city: '长沙市', province: '湖南省' },
  '北京市': { city: '北京市', province: '北京市' },
  '上海市': { city: '上海市', province: '上海市' },
  '广州市': { city: '广州市', province: '广东省' },
  '深圳市': { city: '深圳市', province: '广东省' },
  '杭州市': { city: '杭州市', province: '浙江省' },
  '成都市': { city: '成都市', province: '四川省' },
  '武汉市': { city: '武汉市', province: '湖北省' },
  
  // 省级直接映射
  '湖南省': { city: '湖南省', province: '湖南省' },
  '广东省': { city: '广东省', province: '广东省' },
  '浙江省': { city: '浙江省', province: '浙江省' },
  '四川省': { city: '四川省', province: '四川省' },
  '湖北省': { city: '湖北省', province: '湖北省' },
  '北京市': { city: '北京市', province: '北京市' },
  '上海市': { city: '上海市', province: '上海市' },
  '湖南': { city: '湖南省', province: '湖南省' },
  '广东': { city: '广东省', province: '广东省' },
  '浙江': { city: '浙江省', province: '浙江省' },
  '四川': { city: '四川省', province: '四川省' },
  '湖北': { city: '湖北省', province: '湖北省' }
}

// 获取地区层级信息
const getRegionHierarchy = (location) => {
  if (!location) return { district: null, city: null, province: null }
  
  // 如果在映射表中找到
  if (regionHierarchy[location]) {
    return {
      district: location,
      ...regionHierarchy[location]
    }
  }
  
  // 尝试去除后缀后查找
  const suffixes = ['区', '县', '市', '市辖区', '自治县', '旗']
  for (const suffix of suffixes) {
    if (location.endsWith(suffix)) {
      const baseName = location.slice(0, -suffix.length)
      if (regionHierarchy[baseName]) {
        return {
          district: location,
          ...regionHierarchy[baseName]
        }
      }
    }
  }
  
  // 默认返回
  return {
    district: location,
    city: location,
    province: location
  }
}

// 逐级查询职位：区 -> 市 -> 省
const loadJobsByCity = async (location) => {
  try {
    console.log(`[Geolocation Debug] 开始逐级查询职位，起点: ${location}`)
    
    // 获取地区层级
    const hierarchy = getRegionHierarchy(location)
    console.log(`[Geolocation Debug] 地区层级:`, hierarchy)
    
    // 查询顺序：区 → 市 → 省
    const searchLevels = []
    
    if (hierarchy.district && hierarchy.district !== hierarchy.city) {
      searchLevels.push({ level: 'district', value: hierarchy.district, label: `${hierarchy.district}(区/县)` })
    }
    if (hierarchy.city) {
      searchLevels.push({ level: 'city', value: hierarchy.city, label: `${hierarchy.city}(市)` })
    }
    if (hierarchy.province && hierarchy.province !== hierarchy.city) {
      searchLevels.push({ level: 'province', value: hierarchy.province, label: `${hierarchy.province}(省)` })
    }
    
    console.log(`[Geolocation Debug] 查询层级顺序:`, searchLevels.map(s => s.label))
    
    // 逐级查询
    for (const level of searchLevels) {
      console.log(`[Geolocation Debug] 正在查询 ${level.label}: ${level.value}`)
      
      // 使用后端API的address参数进行查询
      const searchUrl = `/career-evaluation/computer-careers/?address=${encodeURIComponent(level.value)}`
      console.log(`[Geolocation Debug] API地址: ${searchUrl}`)
      
      try {
        const searchResponse = await apiFetch(searchUrl, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        console.log(`[Geolocation Debug] HTTP状态码: ${searchResponse.status}`)
        
        if (!searchResponse.ok) {
          console.error(`[Geolocation Debug] HTTP错误: ${searchResponse.status} - ${searchResponse.statusText}`)
          continue
        }
        
        const searchData = await searchResponse.json()
        console.log(`[Geolocation Debug] ${level.label}查询结果:`, searchData)
        
        if (searchData.results && searchData.results.length > 0) {
          locationJobs.value = searchData.results
          currentCity.value = level.value
          console.log(`[Geolocation Debug] ✅ 在 ${level.label} 级别找到 ${locationJobs.value.length} 个职位`)
          locationStatus.value = 'success'
          return
        }
        
      } catch (fetchError) {
        console.error(`[Geolocation Debug] ${level.label}查询失败:`, fetchError)
      }
      
      console.log(`[Geolocation Debug] ❌ ${level.label} 级别没有找到职位，继续上一级`)
    }
    
    // 如果所有级别都没有结果，尝试直接查询所有数据并在前端筛选
    console.log('[Geolocation Debug] 尝试获取所有职位数据进行前端筛选')
    try {
      const allJobsResponse = await computerCareerAPI.getComputerCareers(1, 100)
      console.log('[Geolocation Debug] 获取所有职位总数:', allJobsResponse.results?.length || 0)
      
      if (allJobsResponse.results && allJobsResponse.results.length > 0) {
        // 在前端进行模糊匹配
        for (const level of searchLevels) {
          const matched = allJobsResponse.results.filter(job => 
            job.address && (job.address.includes(level.value) || level.value.includes(job.address))
          )
          console.log(`[Geolocation Debug] 前端筛选 ${level.label} (${level.value}): ${matched.length} 条`)
          
          if (matched.length > 0) {
            locationJobs.value = matched
            currentCity.value = level.value
            console.log(`[Geolocation Debug] ✅ 前端筛选在 ${level.label} 级别找到 ${matched.length} 个职位`)
            locationStatus.value = 'success'
            return
          }
        }
      }
    } catch (error) {
      console.error('[Geolocation Debug] 获取所有职位失败:', error)
    }
    
    // 如果所有级别都没有结果
    console.log('[Geolocation Debug] ❌ 所有级别都没有找到职位')
    locationJobs.value = []
    currentCity.value = location
    locationStatus.value = 'success'
    
  } catch (error) {
    console.error('[Geolocation Debug] 职位查询失败:', error)
    locationJobs.value = []
    locationStatus.value = 'success'
  }
}

// 职位数据
const jobs = ref([])
const jobsLoading = ref(false)
const jobsPage = ref(1)
const jobsPageSize = ref(10)
const jobsTotalCount = ref(0)

// 搜索相关
const searchKeyword = ref('')

// 过滤后的职位数据
const filteredJobs = computed(() => {
  if (!searchKeyword.value.trim()) {
    return jobs.value
  }
  const keyword = searchKeyword.value.toLowerCase().trim()
  return jobs.value.filter(job => {
    return (
      job.title.toLowerCase().includes(keyword) ||
      job.company.toLowerCase().includes(keyword) ||
      job.tags.some(tag => tag.toLowerCase().includes(keyword)) ||
      (job.jobDetails && job.jobDetails.toLowerCase().includes(keyword)) ||
      (job.companyDetails && job.companyDetails.toLowerCase().includes(keyword))
    )
  })
})

// 搜索处理
const handleSearch = async () => {
  console.log('搜索关键词:', searchKeyword.value)
  // 搜索时重置到第一页
  jobsPage.value = 1
}

// 清空搜索
const clearSearch = async () => {
  searchKeyword.value = ''
  console.log('搜索已清空')
  // 清空搜索后重置到第一页
  jobsPage.value = 1
}

// 标签页状态
const activeTab = ref('recommended')

// 红榜数据
const redListData = ref([
  { rank: 1, position: 'C/C++', company: '外企德科数字技术有限公司', location: '上海-青浦区', salary: '1.7-3万·16薪', reason: '高薪、知名大厂（华为系）、技术核心' },
  { rank: 2, position: 'Java', company: '外企德科数字技术有限公司', location: '深圳-龙岗区', salary: '1.5-3万·14薪', reason: '高薪、知名大厂、16薪、技术核心' },
  { rank: 3, position: '科研人员', company: '中国信息通信研究院', location: '北京-海淀区', salary: '1.9-2.1万', reason: '国家级科研机构、薪资高、稳定' },
  { rank: 4, position: '科研人员', company: '中国科学院微电子研究所', location: '北京-朝阳区', salary: '2-3万', reason: '中科院平台、薪资高、学术背景强' },
  { rank: 5, position: '科研人员', company: '浙江大学绍兴研究院', location: '绍兴-越城区', salary: '1.6-3万·15薪', reason: '高校平台、薪资优厚、福利好（15薪）' },
  { rank: 6, position: 'Java', company: '外企德科数字技术有限公司', location: '西安-雁塔区', salary: '1.6-3万·14薪', reason: '高薪、知名大厂、14薪' },
  { rank: 7, position: '测试工程师', company: '深圳市新凯来技术有限公司', location: '深圳-龙岗区', salary: '2-4万·15薪', reason: '高薪（2-4万）、行业领先、福利优厚' },
  { rank: 8, position: '科研人员', company: '中国科学院上海应用物理研究所', location: '上海-嘉定区', salary: '1.2-2万', reason: '中科院平台、科研导向、稳定' },
  { rank: 9, position: '技术支持工程师', company: '北京飞斯科科技有限公司', location: '北京-海淀区', salary: '1-1.5万', reason: '硕士起、专业对口、技术性强' },
  { rank: 10, position: 'C/C++', company: '联合汽车电子有限公司（UAES）', location: '重庆-渝北区', salary: '1.2-1.5万·17薪', reason: '知名合资企业、17薪、技术核心' },
  { rank: 11, position: '测试工程师', company: '中电科思仪科技股份有限公司', location: '青岛-None', salary: '6000-8000元', reason: '央企背景、稳定、福利好' },
  { rank: 12, position: '科研人员', company: '龙子湖新能源实验室', location: '郑州-金水区', salary: '1.4-2万', reason: '省实验室平台、薪资高、博士优先' },
  { rank: 13, position: 'Java', company: '外企德科数字技术有限公司', location: '南京-雨花台区', salary: '1.8-3.5万·16薪', reason: '高薪、大厂背景、16薪' },
  { rank: 14, position: '技术支持工程师', company: '上海柏楚电子科技股份有限公司', location: '上海-闵行区', salary: '8000-12000元·15薪', reason: '科创板上市企业、15薪、福利好' },
  { rank: 15, position: '科研人员', company: '中国信息通信研究院', location: '北京-海淀区', salary: '1.9-2.1万', reason: '国家级科研机构、薪资高、稳定' },
  { rank: 16, position: 'C/C++', company: '北京瑞鑫天算资产管理有限公司', location: '北京-海淀区', salary: '1.5-3万', reason: '量化私募、薪资高、对技术有热情' },
  { rank: 17, position: '科研人员', company: '河南省科学院高能物理研究中心', location: '郑州-金水区', salary: '1.5-3万', reason: '省级科研平台、薪资高、博士进编' },
  { rank: 18, position: '科研人员', company: '清华大学合肥公共安全研究院', location: '合肥-蜀山区', salary: '1.2-2.4万·15薪', reason: '顶尖高校研究院、15薪、科研导向' },
  { rank: 19, position: '实施工程师', company: '南京高速齿轮制造有限公司', location: '南京-江宁区', salary: '1-1.2万·15薪', reason: '上市公司、15薪、发展前景好' },
  { rank: 20, position: 'C/C++', company: '外企德科数字技术有限公司', location: '苏州-工业园区', salary: '1.5-3万·15薪', reason: '高薪、大厂背景、15薪' },
  { rank: 21, position: '科研人员', company: '北京大学深圳研究院', location: '深圳-南山区', salary: '8000-10000元', reason: '顶尖高校平台、学术环境好' },
  { rank: 22, position: '技术支持工程师', company: '江苏富科思科技有限公司', location: '南京-鼓楼区', salary: '7000-10000元', reason: '中科院院士团队、技术前沿' },
  { rank: 23, position: 'Java', company: '外企德科数字技术有限公司', location: '杭州-滨江区', salary: '1.5-3万·14薪', reason: '高薪、大厂背景、14薪' },
  { rank: 24, position: '实施工程师', company: '浪潮集团', location: '杭州-西湖区', salary: '1.2-2.2万', reason: '知名IT企业、薪资高、发展稳定' },
  { rank: 25, position: '科研人员', company: '浙江清华长三角研究院', location: '嘉兴-南湖区', salary: '1.5-2万', reason: '清华研究院平台、薪资高' },
  { rank: 26, position: 'C/C++', company: '外企德科数字技术有限公司', location: '成都-郫都区', salary: '1.5-3万', reason: '高薪、大厂背景' },
  { rank: 27, position: '科研人员', company: '中国科学院长春应用化学研究所', location: '长春-朝阳区', salary: '1-2万', reason: '中科院平台、稳定、博士优先' },
  { rank: 28, position: '软件测试', company: '博彦科技承德有限公司', location: '西安-雁塔区', salary: '120-130元/天', reason: '知名IT公司、实习机会、26届可投' },
  { rank: 29, position: '技术支持工程师', company: '深圳市北电仪表有限公司', location: '深圳-南山区', salary: '5000-10000元', reason: '双休、有住宿、发展空间大' },
  { rank: 30, position: '前端开发', company: '四川锐狐网络科技有限公司', location: '成都-锦江区', salary: '3000-5000元', reason: '双休、明确培养26/27届、有转正机会' },
  { rank: 31, position: '科研人员', company: '中国船舶集团有限公司第七六〇研究所', location: '大连-中山区', salary: '8000-12000元', reason: '船舶军工研究所、稳定、技术强' },
  { rank: 32, position: 'C/C++', company: '外企德科数字技术有限公司', location: '武汉-江夏区', salary: '1.1-2.2万', reason: '高薪、大厂背景' },
  { rank: 33, position: '测试工程师', company: '中国汽车技术研究中心有限公司', location: '广州-增城区', salary: '面议', reason: '央企、行业龙头、发展前景好' },
  { rank: 34, position: '实施工程师', company: '北京冠群信息技术股份有限公司', location: '南京-浦口区', salary: '1.1-1.6万', reason: '知名企业、海外机会、双休' },
  { rank: 35, position: '技术支持工程师', company: '超年实业(上海)有限公司', location: '上海-松江区', salary: '6000-8000元', reason: '五险一金、双休、技术培训' },
  { rank: 36, position: '科研人员', company: '国防科技大学电子科学学院', location: '长沙-开福区', salary: '1-2万', reason: '军校平台、稳定、薪资待遇好' },
  { rank: 37, position: '测试工程师', company: '中船海丰航空科技有限公司', location: '北京-丰台区', salary: '1-1.6万·13薪', reason: '中船集团背景、13薪、福利好' },
  { rank: 38, position: '科研人员', company: '上海建科咨询集团股份有限公司', location: '上海-闵行区', salary: '2-3万', reason: '国企背景、薪资高、科研平台' },
  { rank: 39, position: '实施工程师', company: '上海柏楚电子科技股份有限公司', location: '济南-历下区', salary: '8000-12000元·15薪', reason: '科创板上市公司、15薪' },
  { rank: 40, position: 'Java', company: '外企德科数字技术有限公司', location: '杭州-滨江区', salary: '1.5-3万·15薪', reason: '高薪、15薪、核心业务' },
  { rank: 41, position: '科研人员', company: '国汽轻量化(江苏)汽车技术有限公司', location: '扬州-邗江区', salary: '6000-12000元', reason: '新型研发机构、硕士起、技术前沿' },
  { rank: 42, position: '技术支持工程师', company: '深圳市合杰电子有限公司', location: '苏州-吴中区', salary: '6000-7000元', reason: '大小周但提供专业培训、发展空间大' },
  { rank: 43, position: '测试工程师', company: '上海微创软件股份有限公司', location: '深圳-南山区', salary: '8000-13000元', reason: '知名外企、五险一金、双休' },
  { rank: 44, position: '实施工程师', company: '浪潮集团', location: '西安-未央区', salary: '1-1.5万·13薪', reason: '浪潮集团、13薪、智慧矿山方向' },
  { rank: 45, position: '技术支持工程师', company: '北京飞斯科科技有限公司', location: '北京-海淀区', salary: '1-1.5万', reason: '硕士起、专业对口、技术性强' },
  { rank: 46, position: '科研人员', company: '浙江大学绍兴研究院', location: '绍兴-越城区', salary: '1.6-3万·15薪', reason: '高校平台、薪资优厚、福利好' },
  { rank: 47, position: '前端开发', company: '湖南恒昌医药集团股份有限公司', location: '长沙-开福区', salary: '1.5-2.3万·13薪', reason: '医药集团、薪资高、13薪' },
  { rank: 48, position: '测试工程师', company: '广州赛西标准检测研究院有限公司', location: '广州-黄埔区', salary: '1-2万', reason: '五险一金、双休、技术驱动' },
  { rank: 49, position: '技术支持工程师', company: '浙江浙仪控股集团有限公司', location: '杭州-钱塘区', salary: '2.5-3万', reason: '博士后岗位、薪资极高、科研前沿' },
  { rank: 50, position: 'Java', company: '外企德科数字技术有限公司', location: '广州-白云区', salary: '1.4-2.8万·14薪', reason: '高薪、大厂背景、14薪' }
])

// 红榜分页
const redListPage = ref(1)
const redListPageSize = ref(10)

// 黑榜数据
const blackListData = ref([
  { rank: 1, position: '软件测试', company: '麦田房产', location: '北京-海淀区', salary: '1.5-1.7万', reason: 'JD与岗位不符：实为房产销售，职位描述与“软件测试”完全无关，误导求职者。' },
  { rank: 2, position: '测试工程师', company: '河南歌络影视传媒有限公司', location: '开封-龙亭区', salary: '9000-15000元', reason: '公司背景不符：影视传媒公司招聘测试工程师，岗位描述模糊，无具体技术栈。' },
  { rank: 3, position: '测试工程师', company: '河南歌络影视传媒有限公司', location: '开封-龙亭区', salary: '8000-9000元·13薪', reason: '公司背景不符：同上，一家影视传媒公司发布大量测试、车载测试岗，存在较大风险。' },
  { rank: 4, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '成都-成华区', salary: '6000-10000元', reason: '外包性质：人力资源公司发布，岗位JD模板化，薪资虚高，实际可能是外派岗位。' },
  { rank: 5, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '成都-武侯区', salary: '8000-11000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化，薪资吸引力高但需警惕。' },
  { rank: 6, position: '测试工程师', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 7, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '南昌-新建区', salary: '6000-9000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 8, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 9, position: '测试工程师', company: '青岛瑞晟元人力资源有限公司', location: '长春-朝阳区', salary: '1-1.2万·13薪', reason: '外包性质：人力资源公司发布，JD模板化，无具体业务描述。' },
  { rank: 10, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '焦作-山阳区', salary: '6000-9000元', reason: '外包性质：人力资源公司发布，岗位描述与“硬件测试”无关，内容混乱。' },
  { rank: 11, position: '软件测试', company: '青岛瑞晟元人力资源有限公司', location: '北京-海淀区', salary: '1.5-2万·13薪', reason: '外包性质：人力资源公司发布，JD模板化，内容为空。' },
  { rank: 12, position: '软件测试', company: '青岛瑞晟元人力资源有限公司', location: '镇江-润州区', salary: '1.5-2万·13薪', reason: '外包性质：同上，人力资源公司发布，JD模板化，内容为空。' },
  { rank: 13, position: '测试工程师', company: '青岛瑞晟元人力资源有限公司', location: '郑州-金水区', salary: '1-1.2万·13薪', reason: '外包性质：同上，人力资源公司发布，JD模板化。' },
  { rank: 14, position: '软件测试', company: '青岛瑞晟元人力资源有限公司', location: '长沙-岳麓区', salary: '8000-10000元', reason: '外包性质：同上，人力资源公司发布，JD模板化。' },
  { rank: 15, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '7000-12000元', reason: '外包性质：人力资源公司发布，薪资虚高，岗位描述混乱。' },
  { rank: 16, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 17, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-二七区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 18, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '焦作-修武县', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 19, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '焦作-解放区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 20, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '重庆-丰都县', salary: '8000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 21, position: '硬件测试', company: '重庆科满福人力资源服务有限公司', location: '东莞-None', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 22, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '南昌-新建区', salary: '6000-9000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 23, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '郑州-管城回族区', salary: '6000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 24, position: '软件测试', company: '重庆科满福人力资源服务有限公司', location: '成都-锦江区', salary: '7000-10000元', reason: '外包性质：同上，人力资源公司发布，岗位内容模板化。' },
  { rank: 25, position: '测试工程师', company: '重庆科满福人力资源服务有限公司', location: '抚州-南城县', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
  { rank: 26, position: '测试工程师', company: '重庆科满福人力资源服务有限公司', location: '抚州-南丰县', salary: '7000-12000元', reason: '外包性质：同上，人力资源公司发布，岗位描述混乱。' },
])

// 学长学姐建议数据
const adviceList = ref([])
const adviceLoading = ref(false)
const advicePage = ref(1)
const advicePageSize = ref(10)
const adviceTotalPages = ref(1)
const adviceSearchKeyword = ref('')
const adviceFilter = ref('')

// 过滤后的建议
const filteredAdviceList = computed(() => {
  let filtered = adviceList.value
  if (adviceSearchKeyword.value) {
    const keyword = adviceSearchKeyword.value.toLowerCase()
    filtered = filtered.filter(advice => 
      advice.company.toLowerCase().includes(keyword) ||
      advice.position.toLowerCase().includes(keyword)
    )
  }
  
  if (adviceFilter.value === 'high-rating') {
    filtered.sort((a, b) => b.rating - a.rating)
  } else if (adviceFilter.value === 'recent') {
    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }
  
  return filtered
})

// 加载建议数据
const loadAdviceData = async () => {
  adviceLoading.value = true
  try {
    const response = await api.get('/ai/senior-advice/')
    adviceList.value = response.results || []
    adviceTotalPages.value = Math.ceil((response.count || 0) / advicePageSize.value)
  } catch (error) {
    console.error('加载建议数据失败:', error)
  } finally {
    adviceLoading.value = false
  }
}

// 建议分页
const handleAdvicePageChange = (page) => {
  if (page >= 1 && page <= adviceTotalPages.value) {
    advicePage.value = page
    loadAdviceData()
  }
}

// 黑榜分页
const blackListPage = ref(1)
const blackListPageSize = ref(10)

// 获取双选会数据
const fetchJobFairs = async () => {
  try {
    loading.value = true
    const response = await jobFairAPI.getJobFairs(currentPage.value, pageSize.value)
    jobFairs.value = response.results
    totalCount.value = response.count
  } catch (error) {
    console.error('获取双选会数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取职位数据
const fetchJobs = async () => {
  try {
    jobsLoading.value = true
    // 尝试调用计算机职业API
    try {
      // 先获取第一页数据，了解总数量
      const firstPageResponse = await computerCareerAPI.getComputerCareers(1, 100)
      let allJobs = firstPageResponse.results
      const totalCount = firstPageResponse.count
      
      // 计算需要获取的页数
      const totalPages = Math.ceil(totalCount / 100)
      
      // 如果有更多页，继续获取
      if (totalPages > 1) {
        const fetchPromises = []
        for (let page = 2; page <= totalPages; page++) {
          fetchPromises.push(computerCareerAPI.getComputerCareers(page, 100))
        }
        
        // 并行获取所有页数据
        const responses = await Promise.all(fetchPromises)
        responses.forEach(response => {
          allJobs = [...allJobs, ...response.results]
        })
      }
      
      // 转换数据结构
      jobs.value = allJobs.map(item => ({
        id: item.id,
        title: item.position_name,
        company: item.company_name,
        salary: item.salary_range,
        tags: [item.address, item.industry].filter(Boolean),
        jobDetails: item.position_details,
        companyDetails: item.company_details,
        jobSourceUrl: item.position_source_url
      }))
      jobsTotalCount.value = totalCount
      console.log('成功获取所有计算机职业数据，共', jobs.value.length, '条')
    } catch (apiError) {
      console.error('调用API失败')
    }
  } catch (error) {
    console.error('获取职位数据失败:', error)
  } finally {
    jobsLoading.value = false
  }
}

// 分页处理
const handlePageChange = (page) => {
  currentPage.value = page
  fetchJobFairs()
}

// 职位分页处理
const handleJobsPageChange = (page) => {
  jobsPage.value = page
  fetchJobs()
}

// 计算职位总页数
const jobsTotalPages = computed(() => {
  return Math.ceil(jobsTotalCount.value / jobsPageSize.value)
})

// 计算过滤后职位总页数
const filteredJobsTotalPages = computed(() => {
  return Math.ceil(filteredJobs.value.length / jobsPageSize.value)
})

// 计算当前页显示的过滤后职位
const currentFilteredJobs = computed(() => {
  const start = (jobsPage.value - 1) * jobsPageSize.value
  const end = start + jobsPageSize.value
  return filteredJobs.value.slice(start, end)
})

// 生命周期
onMounted(async () => {
  try {
    // 并行加载数据，避免阻塞
    await Promise.all([
      fetchJobFairs(),
      fetchJobs(),
      loadAdviceData(),
      getLocationAndLoadJobs()
    ])
    
    console.log('所有数据加载完成')
  } catch (error) {
    console.error('数据加载失败:', error)
  }
})

// 标签页切换
const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'red') {
    redListPage.value = 1
  }
}

// 红榜分页处理
const handleRedListPageChange = (page) => {
  redListPage.value = page
}

// 计算当前红榜页数据
const currentRedListData = computed(() => {
  const start = (redListPage.value - 1) * redListPageSize.value
  const end = start + redListPageSize.value
  return redListData.value.slice(start, end)
})

// 计算红榜总页数
const redListTotalPages = computed(() => {
  return Math.ceil(redListData.value.length / redListPageSize.value)
})

// 计算当前黑榜页数据
const currentBlackListData = computed(() => {
  const start = (blackListPage.value - 1) * blackListPageSize.value
  const end = start + blackListPageSize.value
  return blackListData.value.slice(start, end)
})

// 计算黑榜总页数
const blackListTotalPages = computed(() => {
  return Math.ceil(blackListData.value.length / blackListPageSize.value)
})



// 模拟地区招聘资讯
const regionNews = ref([
  {
    id: 1,
    type: '双选会',
    date: '3月25日',
    title: '2024春季计算机专场双选会',
    location: '清华大学 - 综合体育馆',
    locationIcon: 'apartment'
  },
  {
    id: 2,
    type: '宣讲会',
    date: '3月22日 19:00',
    title: '米哈游 2024 春招宣讲会',
    location: '上海交通大学 - 闵行校区',
    locationIcon: 'school'
  },
  {
    id: 3,
    type: '职场沙龙',
    date: '3月28日',
    title: '大厂面试官一对一辅导',
    location: '线上直播间 / 腾讯会议',
    locationIcon: 'video_chat'
  }
])

// 模拟热度飙升企业
const trendingCompanies = ref([
  {
    id: 1,
    rank: '01',
    name: '字节跳动 (ByteDance)',
    description: '今日搜索量 +240%'
  },
  {
    id: 2,
    rank: '02',
    name: '米哈游 (miHoYo)',
    description: '福利评价热度极高'
  }
])

// 导航到简历管理页面
const navigateToResume = () => {
  router.push('/resume')
}

// 导航到面试页面
const navigateToInterview = () => {
  router.push('/interview')
}

// 过滤 br 标签的函数
const filterBrTags = (text) => {
  if (!text) return ''
  return text.replace(/<br\s*\/?>/g, ' ')
}

// 过滤 nan 数据的函数
const isCompanyDetailsValid = (companyDetails) => {
  if (!companyDetails) return false
  const cleaned = companyDetails.trim().toLowerCase()
  return cleaned !== 'nan' && cleaned !== 'null' && cleaned !== 'undefined'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .grid-cols-12 {
    grid-template-columns: 1fr;
  }
  
  .lg\:col-span-8,
  .lg\:col-span-4 {
    grid-column: span 1;
  }
  
  .text-5xl {
    font-size: 2.5rem;
  }
  
  .rounded-\[2rem\] {
    border-radius: 1rem;
  }
  
  .rounded-\[2\.5rem\] {
    border-radius: 1.5rem;
  }
}
</style>
