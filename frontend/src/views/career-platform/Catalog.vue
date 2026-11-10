<template>
  <WorkspaceShell
    title="岗位、企业与面试题库"
    description="查询可追溯来源的岗位、企业和面试题；公开结果只包含已审核通过的记录。"
    stage-label="成员1 · 目录数据"
  >
    <form class="platform-form catalog-filters" @submit.prevent="load(1)">
      <div class="catalog-filter-grid">
        <label>资料类型
          <select v-model="kind" @change="changeKind">
            <option value="jobs">岗位</option>
            <option value="companies">企业</option>
            <option value="questions">题库</option>
          </select>
        </label>
        <label>关键词
          <input v-model="query" maxlength="500" placeholder="岗位、企业、题干或来源" />
        </label>
        <label v-if="kind !== 'questions'">城市
          <input v-model="city" maxlength="100" placeholder="例如：杭州" />
        </label>
        <label v-if="kind === 'jobs'">岗位方向
          <input v-model="role" maxlength="100" placeholder="例如：Java后端" />
        </label>
        <template v-else-if="kind === 'questions'">
          <label>岗位方向
            <input v-model="role" maxlength="100" placeholder="例如：Java后端" />
          </label>
          <label>知识点
            <input v-model="topic" maxlength="100" placeholder="例如：集合" />
          </label>
          <label>难度
            <select v-model="difficulty">
              <option value="">全部</option>
              <option value="easy">基础 easy</option>
              <option value="medium">进阶 medium</option>
              <option value="hard">深入 hard</option>
            </select>
          </label>
        </template>
        <label>每页
          <select v-model.number="pageSize" @change="load(1)">
            <option :value="10">10 条</option>
            <option :value="20">20 条</option>
            <option :value="50">50 条</option>
          </select>
        </label>
      </div>
      <div class="platform-actions">
        <button class="career-button career-button-primary" :disabled="busy">{{ busy ? '查询中…' : '查询资料' }}</button>
        <button type="button" class="career-button" :disabled="busy" @click="resetFilters">重置条件</button>
      </div>
    </form>

    <p class="platform-status" role="status">{{ status }}</p>
    <p class="catalog-policy">公开查询只返回 <code>permission_status=allowed</code> 的记录；pending 和 restricted 不会出现在结果中。</p>

    <section class="platform-result" aria-live="polite">
      <div class="catalog-result-heading">
        <h2>{{ kindLabel }}列表</h2>
        <span v-if="loaded">{{ count }} 条记录 · 第 {{ page }} 页</span>
      </div>

      <p v-if="!loaded" class="catalog-empty">选择条件后查询，结果按来源和时间展示。</p>
      <p v-else-if="!items.length" class="catalog-empty">没有符合条件的记录。未审核或受限的数据不会补入结果。</p>

      <template v-else>
        <div v-if="kind === 'questions'" class="catalog-cards">
          <article v-for="item in items" :key="item.id" class="catalog-card">
            <header class="catalog-card-top">
              <span class="catalog-tag">{{ item.category }} · {{ item.topic }}</span>
              <span class="catalog-tag">{{ item.role }} · {{ difficultyLabel(item.difficulty) }}</span>
            </header>
            <h3>{{ item.question }}</h3>
            <div class="catalog-points">
              <h4>参考要点</h4>
              <ul><li v-for="point in item.key_points" :key="point">{{ point }}</li></ul>
            </div>
            <details>
              <summary>参考回答与来源</summary>
              <p>{{ item.reference_answer }}</p>
              <dl class="catalog-meta">
                <dt>来源</dt><dd>{{ item.source }}</dd>
                <dt>来源链接</dt><dd>{{ item.source_url || '未提供' }}</dd>
                <dt>采集时间</dt><dd>{{ item.collected_at || '未记录' }}</dd>
                <dt>记录 ID</dt><dd>{{ item.id }}</dd>
              </dl>
            </details>
            <footer class="catalog-card-foot">
              <span>{{ item.is_demo ? '演示数据' : '正式数据' }}</span>
              <span>{{ item.permission_status }}</span>
              <span v-if="item.tags?.length">{{ item.tags.join(' / ') }}</span>
            </footer>
          </article>
        </div>

        <div v-else class="catalog-table-wrap">
          <table class="catalog-table">
            <thead>
              <tr v-if="kind === 'jobs'">
                <th scope="col">岗位</th><th scope="col">企业</th><th scope="col">城市</th>
                <th scope="col">薪资</th><th scope="col">来源</th><th scope="col">采集时间</th>
              </tr>
              <tr v-else>
                <th scope="col">企业</th><th scope="col">城市</th><th scope="col">行业</th>
                <th scope="col">来源</th><th scope="col">采集时间</th><th scope="col">许可</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.id">
                <template v-if="kind === 'jobs'">
                  <td>
                    <strong>{{ item.title }}</strong>
                    <p class="catalog-muted">{{ item.experience || '经验不限' }} · {{ item.education || '学历不限' }}</p>
                    <p v-if="item.skills?.length" class="catalog-muted">技能：{{ item.skills.join('、') }}</p>
                    <p v-if="item.is_demo" class="catalog-demo">演示岗位</p>
                  </td>
                  <td>{{ item.company?.name || '未关联' }}</td>
                  <td>{{ item.city || item.company?.city || '未提供' }}</td>
                  <td>{{ salaryText(item) }}</td>
                  <td>{{ item.source }}</td>
                  <td>{{ item.collected_at || '未记录' }}</td>
                </template>
                <template v-else>
                  <td>
                    <strong>{{ item.name }}</strong>
                    <p v-if="item.description" class="catalog-muted">{{ item.description }}</p>
                    <p v-if="item.is_demo" class="catalog-demo">演示企业</p>
                  </td>
                  <td>{{ item.city }}</td>
                  <td>{{ item.industry || '未提供' }}</td>
                  <td>{{ item.source }}</td>
                  <td>{{ item.collected_at || '未记录' }}</td>
                  <td>{{ item.permission_status }}</td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="catalog-pagination">
          <button type="button" class="career-button" :disabled="busy || page <= 1" @click="load(page - 1)">上一页</button>
          <span>第 {{ page }} / {{ totalPages }} 页</span>
          <button type="button" class="career-button" :disabled="busy || page >= totalPages" @click="load(page + 1)">下一页</button>
        </div>
      </template>
    </section>

    <details class="catalog-import">
      <summary>管理员导入 JSON</summary>
      <form class="platform-form" @submit.prevent="importBatch">
        <label>导入类型
          <select v-model="importKind">
            <option value="companies">企业</option>
            <option value="jobs">岗位</option>
            <option value="questions">题库</option>
          </select>
        </label>
        <label>记录数组（最多 1000 条）
          <textarea v-model="batch" required spellcheck="false" placeholder='[{"name":"演示企业","city":"杭州","source":"团队创作：成员1","permission_status":"pending","is_demo":true}]' />
        </label>
        <label class="catalog-check"><span><input v-model="dryRun" type="checkbox" /> 仅校验，不写入数据库</span></label>
        <p class="catalog-hint">每条记录必须提供 source；可提供 collected_at、permission_status、dedupe_key。省略 dedupe_key 时服务端按来源和稳定标识生成，重复导入不会新增记录。</p>
        <div class="platform-actions">
          <button class="career-button career-button-primary" :disabled="busy">{{ busy ? '处理中…' : dryRun ? '校验记录' : '导入记录' }}</button>
          <button type="button" class="career-button" :disabled="busy" @click="batch = exampleBatch">填入示例</button>
        </div>
      </form>
      <section v-if="importResult" class="catalog-import-result" aria-live="polite">
        <h3>导入结果</h3>
        <p>{{ importResult.dry_run ? '仅校验，未写入。' : '已提交数据库。' }} 新增 {{ importResult.created }} 条，更新 {{ importResult.updated }} 条，未变化 {{ importResult.unchanged }} 条。</p>
        <p v-if="importResult.index_notification === 'not_configured'" class="catalog-hint">数据库已提交；当前未配置题库索引通知，检索仍以数据库为准。</p>
        <p v-if="importResult.index_notification === 'scheduled'" class="catalog-hint">数据库已提交，题库索引通知已安排在事务提交后执行。</p>
        <details v-if="importResult.records?.length">
          <summary>逐条结果</summary>
          <ul>
            <li v-for="row in importResult.records" :key="row.index">
              第 {{ row.index + 1 }} 条：{{ row.action }}{{ row.id ? ` · ID ${row.id}` : '' }}
            </li>
          </ul>
        </details>
      </section>
    </details>
  </WorkspaceShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import { platformAPI as api } from '@/features/career-platform'
import { platformFailure } from '@/features/career-platform/api.js'

const kind = ref('jobs')
const query = ref('')
const city = ref('')
const role = ref('')
const topic = ref('')
const difficulty = ref('')
const page = ref(1)
const pageSize = ref(20)
const busy = ref(false)
const loaded = ref(false)
const status = ref('选择条件后查询岗位、企业或题库。')
const items = ref([])
const count = ref(0)

const importKind = ref('questions')
const batch = ref('[]')
const dryRun = ref(true)
const importResult = ref(null)

const kindLabel = computed(() => ({ jobs: '岗位', companies: '企业', questions: '题库' })[kind.value])
const totalPages = computed(() => Math.max(1, Math.ceil(count.value / pageSize.value)))
const exampleBatch = computed(() => {
  const common = {
    source: '团队创作：成员1',
    source_url: '',
    permission_status: 'pending',
    collected_at: '2026-11-10T00:00:00Z',
    is_demo: true,
  }
  const examples = {
    companies: [{
      ...common, name: '演示企业（虚构）', city: '杭州', industry: '互联网',
      description: '仅用于演示导入流程，不代表真实招聘。',
    }],
    jobs: [{
      ...common, company: '演示企业（虚构）', title: '演示岗位',
      city: '杭州', description: '仅用于演示导入流程。', requirements: '熟悉 Java 基础。',
      skills: ['Java'],
    }],
    questions: [{
      ...common, category: 'Java', role: 'Java后端', topic: 'Java基础',
      difficulty: 'easy', question: '示例题：equals 与 hashCode 的约定是什么？',
      key_points: ['相等对象必须有相同 hashCode'], reference_answer: '相等对象必须具有相同的 hashCode。',
    }],
  }
  return JSON.stringify(examples[importKind.value], null, 2)
})

function difficultyLabel(value) {
  return ({ easy: '基础', medium: '进阶', hard: '深入' })[value] || value
}

function salaryText(item) {
  if (!item.salary_min && !item.salary_max) return '未提供'
  return `${item.salary_min || '—'} - ${item.salary_max || '—'}`
}

function describeError(error) {
  const response = error?.response
  if (!response) return '无法连接后端，请确认服务已启动后重试。'
  const details = response.data?.details
  if (response.status === 400 && details && typeof details === 'object') {
    const parts = Object.entries(details).map(([field, message]) => {
      const text = Array.isArray(message) ? message.join('；') : String(message)
      return `${field}: ${text}`
    })
    if (parts.length) return `输入被拒绝：${parts.join('；')}`
  }
  return platformFailure(error)
}

async function perform(action) {
  if (busy.value) return null
  busy.value = true
  try {
    return await action()
  } catch (error) {
    status.value = describeError(error)
    return null
  } finally {
    busy.value = false
  }
}

function changeKind() {
  items.value = []
  loaded.value = false
  page.value = 1
  status.value = `已切换到${kindLabel.value}查询。`
}

function resetFilters() {
  query.value = ''
  city.value = ''
  role.value = ''
  topic.value = ''
  difficulty.value = ''
  load(1)
}

async function load(targetPage = 1) {
  const params = { q: query.value.trim(), page: targetPage, page_size: pageSize.value }
  if (kind.value === 'questions') {
    if (role.value.trim()) params.role = role.value.trim()
    if (topic.value.trim()) params.topic = topic.value.trim()
    if (difficulty.value) params.difficulty = difficulty.value
  } else {
    if (city.value.trim()) params.city = city.value.trim()
    if (kind.value === 'jobs' && role.value.trim()) params.role = role.value.trim()
  }
  const response = await perform(() => api.catalog(kind.value, params))
  if (!response) return
  items.value = response.data.results || []
  count.value = response.data.count || 0
  page.value = response.data.page || targetPage
  loaded.value = true
  status.value = items.value.length
    ? `已加载 ${count.value} 条${kindLabel.value}记录，当前页 ${items.value.length} 条。`
    : `没有符合条件的${kindLabel.value}记录。`
}

async function importBatch() {
  let records
  try {
    records = JSON.parse(batch.value)
    if (records && !Array.isArray(records) && Array.isArray(records.records)) records = records.records
    if (!Array.isArray(records)) throw new Error('必须是数组')
  } catch {
    status.value = '导入 JSON 必须是记录数组，或包含 records 数组的对象。'
    return
  }
  importResult.value = null
  const response = await perform(() => api.importBatch({
    kind: importKind.value,
    records,
    dry_run: dryRun.value,
  }))
  if (!response) return
  importResult.value = response.data
  status.value = response.data.dry_run
    ? `校验通过：将新增 ${response.data.created} 条、更新 ${response.data.updated} 条、未变化 ${response.data.unchanged} 条。`
    : `导入完成：新增 ${response.data.created} 条、更新 ${response.data.updated} 条、未变化 ${response.data.unchanged} 条。`
  if (!response.data.dry_run) {
    kind.value = importKind.value
    await load(1)
  }
}

onMounted(() => load(1))
</script>

<style scoped>
.catalog-filter-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }
.catalog-policy, .catalog-hint { color: var(--career-muted); font-size: 12px; line-height: 1.8; margin: -8px 0 16px; }
.catalog-policy code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
.catalog-result-heading { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.catalog-result-heading span { color: var(--career-muted); font-size: 12px; }
.catalog-empty { color: var(--career-muted); padding: 18px 0; }
.catalog-cards { display: grid; gap: 14px; }
.catalog-card { border: 1px solid var(--career-border); border-radius: 8px; padding: 16px; background: #fbfcf8; }
.catalog-card-top { display: flex; flex-wrap: wrap; gap: 8px; }
.catalog-tag { padding: 2px 8px; background: #eef1e8; border-radius: 999px; font-size: 11px; color: #5d6b52; }
.catalog-card h3 { color: var(--career-text); font-size: 16px; line-height: 1.6; margin: 10px 0; }
.catalog-points h4 { font-size: 12px; color: var(--career-muted); margin-bottom: 4px; }
.catalog-points ul { padding-left: 18px; list-style: disc; color: var(--career-text); }
.catalog-card details { margin-top: 8px; }
.catalog-card summary { cursor: pointer; color: var(--career-blue); font-size: 13px; }
.catalog-card details p { margin: 8px 0; color: var(--career-text); }
.catalog-meta { display: grid; grid-template-columns: 88px minmax(0, 1fr); gap: 4px 10px; font-size: 12px; }
.catalog-meta dt { color: var(--career-muted); }
.catalog-meta dd { color: var(--career-text); word-break: break-all; }
.catalog-card-foot { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px; font-size: 11px; color: var(--career-muted); }
.catalog-table-wrap { overflow-x: auto; }
.catalog-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.catalog-table th, .catalog-table td { border-bottom: 1px solid var(--career-border); padding: 10px 8px; text-align: left; vertical-align: top; }
.catalog-table th { color: var(--career-muted); font-weight: 500; white-space: nowrap; }
.catalog-table strong { color: var(--career-text); }
.catalog-muted { color: var(--career-muted); font-size: 12px; margin-top: 2px; }
.catalog-demo { color: #8a5a16; font-size: 11px; margin-top: 2px; }
.catalog-pagination { display: flex; align-items: center; gap: 14px; margin-top: 18px; flex-wrap: wrap; }
.catalog-pagination span { color: var(--career-muted); font-size: 12px; }
.catalog-import { margin-top: 24px; border-top: 1px solid var(--career-border); padding-top: 20px; }
.catalog-import > summary { cursor: pointer; color: var(--career-blue); min-height: 44px; display: flex; align-items: center; }
.catalog-check span { display: flex; align-items: center; gap: 8px; }
.catalog-check input { width: auto; }
.catalog-import-result { margin-top: 16px; padding: 14px; background: #f6f8fb; border-radius: 6px; color: var(--career-text); font-size: 13px; }
.catalog-import-result h3 { font-size: 14px; margin-bottom: 6px; }
.catalog-import-result ul { padding-left: 18px; list-style: disc; }
@media (max-width: 640px) { .catalog-table { min-width: 640px; } }
</style>
