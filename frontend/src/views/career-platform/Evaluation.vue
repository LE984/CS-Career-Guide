<template>
  <WorkspaceShell title="评估与调优" description="管理员在冻结的评估集上运行离线文本策略，比较基线与参数结果，并导出可复现的逐例证据。页面不预填指标，也不展示模拟成功。">
    <form class="platform-form" @submit.prevent="runEvaluation">
      <label>
        评估任务
        <select v-model="task" :disabled="busy">
          <option value="question">题库检索</option>
        </select>
      </label>
      <p class="eval-hint">岗位匹配与简历匹配的评估策略分别依赖成员1、成员3的正式服务，当前未注册；请求会被明确拒绝，不会返回空基线。</p>
      <label>
        评估集版本
        <input v-model.trim="datasetVersion" list="eval-datasets" required :disabled="busy" />
        <datalist id="eval-datasets">
          <option value="java-eval-test-v1">最终测试集（只用于报告结论）</option>
          <option value="java-eval-dev-v1">调参集（只用于选参数）</option>
        </datalist>
      </label>
      <label>
        策略
        <select v-model="strategy" :disabled="busy">
          <option value="text-baseline">文本基线（题干4/标签3/要点2/答案1）</option>
          <option value="text-balanced">均衡权重变体（题干3/标签3/要点3/答案1）</option>
        </select>
      </label>
      <label>
        Top-K（1-20）
        <input v-model.number="topK" type="number" min="1" max="20" required :disabled="busy" />
      </label>
      <div class="platform-actions">
        <button class="career-button career-button-primary" :disabled="busy">{{ busy ? '请求中…' : '运行评估' }}</button>
        <button type="button" class="career-button" :disabled="busy" @click="loadRuns">刷新记录</button>
      </div>
    </form>

    <p class="platform-status" role="status">{{ status }}</p>

    <section v-if="selected" class="platform-result">
      <h2>本次结果：{{ selected.strategy }} · {{ selected.dataset_version }}</h2>
      <p class="eval-meta">
        记录 ID {{ selected.id }} · 样本 {{ selected.sample_count }} 条 · 失败 {{ selected.failure_count }} 条 ·
        策略版本 {{ selected.model_version }} · 数据集指纹 {{ shortHash(selected.parameters.dataset_sha256) }}
      </p>
      <ul class="eval-metrics">
        <li v-for="item in metricCards" :key="item.key">
          <span class="eval-metric-label">{{ item.label }}</span>
          <strong>{{ format(item.value) }}</strong>
          <span class="eval-metric-hint">{{ item.hint }}</span>
        </li>
      </ul>
      <p v-if="unrelatedSamples.length" class="eval-hint">
        无关检测组 {{ unrelatedSamples.length }} 条：{{ unrelatedHits }} 条返回了候选，按约定不计入宏平均，仅作诊断。
      </p>
      <table class="eval-table">
        <thead>
          <tr><th>query</th><th>问法</th><th>相关</th><th>返回</th><th>MRR</th><th>组</th></tr>
        </thead>
        <tbody>
          <tr v-for="row in selected.results" :key="row.query_id">
            <td>{{ row.query_id }}</td>
            <td>{{ row.query }}</td>
            <td>{{ row.relevant_ids.length }}</td>
            <td>{{ row.failure ? '失败：' + row.failure : row.predicted_ids.join('、') || '无命中' }}</td>
            <td>{{ row.metrics ? format(row.metrics.mrr) : '—' }}</td>
            <td>{{ row.group === 'unrelated' ? '无关检测' : '相关' }}</td>
          </tr>
        </tbody>
      </table>
      <div class="platform-actions">
        <button type="button" class="career-button" :disabled="busy" @click="exportRun(selected.id)">导出 JSON</button>
      </div>
    </section>

    <section class="platform-result">
      <h2>最近的评估记录</h2>
      <p v-if="!runs.length" class="eval-hint">还没有评估记录。运行一次评估后，这里按创建时间列出结果。</p>
      <table v-else class="eval-table">
        <thead>
          <tr><th>创建时间（UTC）</th><th>任务</th><th>评估集</th><th>策略</th><th>K</th><th>F1@K</th><th>MRR</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.id">
            <td>{{ run.created_at }}</td>
            <td>{{ run.task }}</td>
            <td>{{ run.dataset_version }}</td>
            <td>{{ run.strategy }}</td>
            <td>{{ run.parameters.k }}</td>
            <td>{{ format(run.metrics.f1_at_k) }}</td>
            <td>{{ format(run.metrics.mrr) }}</td>
            <td class="eval-row-actions">
              <button type="button" class="eval-link" :disabled="busy" @click="openRun(run.id)">详情</button>
              <button type="button" class="eval-link" :disabled="busy" @click="exportRun(run.id)">导出</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </WorkspaceShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import { platformAPI as api } from '@/features/career-platform'
import { newRequestId, platformFailure } from '@/features/career-platform/api.js'

const METRIC_CARDS = [
  { key: 'precision_at_k', label: 'Precision@K', hint: '命中数 / K，空位算未命中' },
  { key: 'recall_at_k', label: 'Recall@K', hint: '命中数 / 相关集合大小' },
  { key: 'f1_at_k', label: 'F1@K', hint: 'Precision 与 Recall 的调和均值' },
  { key: 'hit_rate_at_k', label: 'HitRate@K', hint: '至少命中一条的 query 比例' },
  { key: 'mrr', label: 'MRR', hint: '首个相关结果名次的倒数' },
]

const busy = ref(false)
const status = ref('尚未运行评估。选择评估集与策略后提交，返回的指标来自服务端保存的记录。')
const task = ref('question')
const datasetVersion = ref('java-eval-test-v1')
const strategy = ref('text-baseline')
const topK = ref(5)
const runs = ref([])
const selected = ref(null)

const metricCards = computed(() => METRIC_CARDS.map((item) => ({
  ...item, value: selected.value?.metrics?.[item.key],
})))
const unrelatedSamples = computed(() => (selected.value?.results || []).filter((row) => row.group === 'unrelated'))
const unrelatedHits = computed(() => unrelatedSamples.value.filter((row) => (row.predicted_ids || []).length).length)

function format(value) {
  return typeof value === 'number' ? value.toFixed(3) : '—'
}

function shortHash(value) {
  return typeof value === 'string' && value.length > 12 ? value.slice(0, 12) + '…' : '—'
}

function describeError(error) {
  const response = error?.response
  if (!response) return '无法连接后端，请确认服务已启动后重试。'
  const details = response.data?.details
  if (response.status === 400 && details && typeof details === 'object') {
    const parts = Object.entries(details).map(([field, message]) => `${field}: ${Array.isArray(message) ? message.join('；') : message}`)
    if (parts.length) return `输入被拒绝：${parts.join('；')}`
  }
  return platformFailure(error)
}

async function perform(action) {
  if (busy.value) return
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

async function loadRuns() {
  const response = await perform(() => api.evaluations())
  if (!response) return
  runs.value = response.data.results
  status.value = runs.value.length
    ? `已加载 ${response.data.count} 条评估记录，当前页 ${runs.value.length} 条。`
    : '还没有评估记录。'
}

async function runEvaluation() {
  const response = await perform(() => api.evaluate({
    task: task.value,
    strategy: strategy.value,
    dataset_version: datasetVersion.value,
    parameters: { k: topK.value },
    request_id: newRequestId(),
  }))
  if (!response) return
  selected.value = response.data
  await loadRuns()
  status.value = `评估完成：${response.data.sample_count} 条样本，失败 ${response.data.failure_count} 条。`
}

async function openRun(id) {
  const response = await perform(() => api.evaluation(id))
  if (!response) return
  selected.value = response.data
  status.value = `已读取评估记录 ${response.data.id}。`
}

async function exportRun(id) {
  const response = await perform(() => api.exportEvaluation(id))
  if (!response) return
  const payload = response.data
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `evaluation-${payload.run_id || id}.json`
  link.click()
  URL.revokeObjectURL(url)
  status.value = '已导出当前记录的指标与逐例结果（导出内容与详情一致，不会重新运行策略）。'
}

onMounted(loadRuns)
</script>

<style scoped>
.eval-hint { color: var(--career-muted); font-size: 13px; line-height: 1.7; }
.eval-meta { font-size: 13px; color: var(--career-muted); margin-bottom: 16px; }
.eval-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 0 0 20px; }
.eval-metrics li { list-style: none; border: 1px solid var(--career-border); border-radius: 6px; padding: 12px 14px; }
.eval-metric-label { display: block; font-size: 12px; color: var(--career-muted); }
.eval-metrics strong { display: block; font-size: 22px; font-weight: 600; color: var(--career-text); line-height: 1.4; }
.eval-metric-hint { display: block; font-size: 12px; color: var(--career-muted); }
.eval-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 12px; }
.eval-table th, .eval-table td { border-bottom: 1px solid var(--career-border); padding: 8px 10px; text-align: left; vertical-align: top; }
.eval-table th { color: var(--career-muted); font-weight: 500; white-space: nowrap; }
.eval-row-actions { white-space: nowrap; }
.eval-link { border: none; background: none; color: #2b5f9e; cursor: pointer; padding: 0 6px 0 0; font: inherit; }
.eval-link:disabled { color: var(--career-muted); cursor: not-allowed; }
</style>
