<template>
  <WorkspaceShell
    title="练习记录"
    description="查看自己的题目、真实回答、逐题反馈与结束总结。"
    stage-label="练习历史 · 真实记录"
  >
    <form class="record-filters" @submit.prevent="loadSessions(1)">
      <label>关键词<input v-model.trim="filters.q" maxlength="500" placeholder="岗位标题或方向" /></label>
      <label>岗位方向<input v-model.trim="filters.role" maxlength="100" placeholder="如 Java后端" /></label>
      <label>知识点<input v-model.trim="filters.topic" maxlength="100" placeholder="如 集合" /></label>
      <label>难度
        <select v-model="filters.difficulty">
          <option value="">全部</option><option value="easy">基础</option>
          <option value="medium">进阶</option><option value="hard">深入</option>
        </select>
      </label>
      <button class="career-button career-button-primary" :disabled="listBusy">{{ listBusy ? '加载中…' : '查询记录' }}</button>
    </form>

    <p class="platform-status" :class="{'record-error': error}" role="status">{{ status }}</p>

    <div class="records-layout">
      <section class="records-list" aria-labelledby="records-list-title">
        <div class="records-heading"><h2 id="records-list-title">历史列表</h2><span>{{ total }} 条</span></div>
        <p v-if="!listBusy && !sessions.length" class="record-empty">还没有符合条件的练习记录。</p>
        <button
          v-for="item in sessions" :key="item.id" type="button"
          class="record-card" :class="{active:selectedId===item.id}"
          @click="selectSession(item.id)"
        >
          <span class="record-card-top"><strong>{{ item.job_title || item.role || '未命名练习' }}</strong><em>{{ sessionState(item) }}</em></span>
          <span>{{ item.topic || '不限知识点' }} · {{ difficultyLabel(item.difficulty) }} · {{ item.answer_count }} 道回答</span>
          <small>{{ formatDate(item.created_at) }}</small>
        </button>
        <div v-if="total > pageSize" class="record-pages">
          <button type="button" class="career-button" :disabled="page<=1 || listBusy" @click="loadSessions(page-1)">上一页</button>
          <span>第 {{ page }} 页</span>
          <button type="button" class="career-button" :disabled="page*pageSize>=total || listBusy" @click="loadSessions(page+1)">下一页</button>
        </div>
      </section>

      <section class="record-detail" aria-labelledby="record-detail-title" :aria-busy="detailBusy">
        <div class="records-heading"><h2 id="record-detail-title">练习详情</h2><span v-if="detail">{{ formatDate(detail.created_at) }}</span></div>
        <p v-if="detailBusy">正在读取练习详情…</p>
        <p v-else-if="!detail" class="record-empty">从左侧选择一条记录查看详情。</p>
        <template v-else>
          <div class="record-overview">
            <div><span>岗位</span><strong>{{ detail.job_snapshot?.title || detail.role || '未指定' }}</strong></div>
            <div><span>知识点</span><strong>{{ detail.topic || '不限' }}</strong></div>
            <div><span>难度</span><strong>{{ difficultyLabel(detail.difficulty) }}</strong></div>
            <div><span>状态</span><strong>{{ detail.status === 'ended' ? '已结束' : '进行中' }}</strong></div>
          </div>

          <section class="summary-panel">
            <div class="summary-title"><h3>结束总结</h3><span :class="`summary-${detail.summary?.status || 'pending'}`">{{ summaryLabel(detail.summary) }}</span></div>
            <p v-if="detail.summary?.status==='pending'">总结正在生成或等待完成，请稍后刷新。</p>
            <p v-else-if="detail.summary?.failure_code==='NO_ANSWERS'">本次没有提交回答，因此没有生成总结。</p>
            <template v-else-if="detail.summary?.status==='succeeded'">
              <SummaryList title="做得较好" :items="detail.summary.strengths" />
              <SummaryList title="需要补强" :items="detail.summary.gaps" />
              <SummaryList title="下一步" :items="detail.summary.next_steps" />
            </template>
            <div v-else-if="detail.summary?.status==='failed'" class="summary-failed">
              <p>总结生成失败，已有题目和回答均已保留。</p>
              <button type="button" class="career-button" :disabled="actionBusy" @click="retrySummary">{{ actionBusy ? '重试中…' : '重试总结' }}</button>
            </div>
          </section>

          <div class="answer-list">
            <article v-for="(answer,index) in detail.answers || []" :key="answer.id" class="answer-card">
              <div class="answer-index">题目 {{ index + 1 }}</div>
              <h3>{{ answer.question_snapshot?.question }}</h3>
              <div class="answer-block"><h4>我的回答</h4><p>{{ answer.answer }}</p></div>
              <div class="answer-block"><h4>逐题反馈</h4>
                <template v-if="answer.status==='succeeded'">
                  <p v-if="answer.feedback?.answer_quote">引用：{{ answer.feedback.answer_quote }}</p>
                  <SummaryList title="已覆盖" :items="answer.feedback?.key_points_covered" />
                  <SummaryList title="遗漏要点" :items="answer.feedback?.missing_points" />
                  <p v-if="answer.feedback?.follow_up">追问：{{ answer.feedback.follow_up }}</p>
                </template>
                <div v-else-if="answer.status==='failed'" class="feedback-failed">
                  <p>回答已保存，但反馈生成失败。</p>
                  <button type="button" class="career-button" :disabled="actionBusy" @click="retryFeedback(answer.id)">重试反馈</button>
                </div>
                <p v-else>反馈生成中…</p>
              </div>
              <details v-if="answer.question_snapshot?.evidence?.length"><summary>查看题目来源证据</summary>
                <dl v-for="(evidence,i) in answer.question_snapshot.evidence" :key="i"><dt>{{ evidence.field_path }}</dt><dd>{{ evidence.quote }}</dd></dl>
              </details>
            </article>
            <p v-if="!detail.answers?.length" class="record-empty">本次会话还没有回答记录。</p>
          </div>
        </template>
      </section>
    </div>
  </WorkspaceShell>
</template>

<script setup>
import { defineComponent, h, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import { platformAPI as api } from '@/features/career-platform'
import { newRequestId, platformFailure } from '@/features/career-platform/api.js'

const SummaryList = defineComponent({
  props:{title:String,items:{type:Array,default:()=>[]}},
  setup(props){return()=>props.items?.length?h('div',{class:'summary-list'},[h('h4',props.title),h('ul',props.items.map(item=>h('li',item))) ]):null},
})

const route=useRoute(),router=useRouter()
const filters=reactive({q:'',role:'',topic:'',difficulty:''})
const sessions=ref([]),detail=ref(null),selectedId=ref('')
const total=ref(0),page=ref(1),pageSize=20
const listBusy=ref(false),detailBusy=ref(false),actionBusy=ref(false),error=ref(false)
const status=ref('正在读取练习记录…')
let listController=null,detailController=null,listSequence=0,detailSequence=0

function payload(response){return response?.data ?? response}
function difficultyLabel(value){return ({easy:'基础',medium:'进阶',hard:'深入'})[value] || '未指定'}
function formatDate(value){return value?new Intl.DateTimeFormat('zh-CN',{dateStyle:'medium',timeStyle:'short'}).format(new Date(value)):'—'}
function summaryLabel(summary){return summary?.status==='succeeded'?'已完成':summary?.status==='failed'?'生成失败':'生成中'}
function sessionState(item){return item.status==='active'?'进行中':item.summary_status==='failed'?'总结失败':'已结束'}
function messageFor(errorValue){
  const response=errorValue?.response
  if(response?.status===400)return '筛选条件无效，请检查后重试。'
  if(response?.status===502||response?.status===503||response?.status===504)return '模型服务暂时不可用，记录已保留。'
  return platformFailure(errorValue)
}

async function loadSessions(targetPage=1){
  listController?.abort();listController=new AbortController();const sequence=++listSequence
  listBusy.value=true;error.value=false;status.value='正在读取练习记录…'
  try{
    const params={page:targetPage,page_size:pageSize}
    for(const [key,value] of Object.entries(filters))if(value)params[key]=value
    const result=payload(await api.sessions(params,listController.signal))
    if(sequence!==listSequence)return
    sessions.value=Array.isArray(result?.results)?result.results:[]
    total.value=Number(result?.count||0);page.value=Number(result?.page||targetPage)
    status.value=sessions.value.length?`已加载 ${total.value} 条记录。`:'还没有符合条件的练习记录。'
    const requested=typeof route.query.id==='string'?route.query.id:''
    const next=requested||selectedId.value||sessions.value[0]?.id||''
    if(next)await selectSession(next,false);else{selectedId.value='';detail.value=null}
  }catch(failure){if(sequence!==listSequence||failure?.name==='CanceledError')return;error.value=true;status.value=messageFor(failure)}
  finally{if(sequence===listSequence)listBusy.value=false}
}

async function selectSession(id,updateRoute=true){
  if(!id)return
  selectedId.value=id
  if(updateRoute&&route.query.id!==id)router.replace({query:{...route.query,id}})
  detailController?.abort();detailController=new AbortController();const sequence=++detailSequence
  detailBusy.value=true;error.value=false
  try{
    const result=payload(await api.session(id,detailController.signal))
    if(sequence!==detailSequence)return
    detail.value=result;status.value='练习详情已更新。'
  }catch(failure){if(sequence!==detailSequence||failure?.name==='CanceledError')return;detail.value=null;error.value=true;status.value=messageFor(failure)}
  finally{if(sequence===detailSequence)detailBusy.value=false}
}

async function retrySummary(){
  if(!detail.value||actionBusy.value)return
  actionBusy.value=true;error.value=false
  try{detail.value=payload(await api.finish(detail.value.id,{request_id:newRequestId(),retry_summary:true}));status.value=detail.value.summary?.status==='succeeded'?'总结已重新生成。':'总结重试已记录。'}
  catch(failure){error.value=true;status.value=messageFor(failure)}finally{actionBusy.value=false}
}

async function retryFeedback(answerId){
  if(!detail.value||actionBusy.value)return
  actionBusy.value=true;error.value=false
  try{await api.retryFeedback(detail.value.id,answerId,{request_id:newRequestId()});await selectSession(detail.value.id,false);status.value='逐题反馈已重新生成。'}
  catch(failure){const message=messageFor(failure);await selectSession(detail.value.id,false);error.value=true;status.value=message}finally{actionBusy.value=false}
}

watch(()=>route.query.id,id=>{if(typeof id==='string'&&id!==selectedId.value)selectSession(id,false)})
onMounted(()=>loadSessions(1))
onBeforeUnmount(()=>{listController?.abort();detailController?.abort()})
</script>

<style scoped>
.record-filters{display:grid;grid-template-columns:repeat(4,minmax(0,1fr)) auto;gap:14px;align-items:end}.record-filters label{display:grid;gap:7px;color:var(--career-muted);font-size:12px}.record-filters input,.record-filters select{padding:10px 12px;border:1px solid var(--career-border);border-radius:6px;background:#fff;font:inherit}.record-error{color:#9b2c2c;background:#fff3f1}.records-layout{display:grid;grid-template-columns:minmax(250px,330px) minmax(0,1fr);gap:28px}.records-heading,.record-card-top,.summary-title{display:flex;justify-content:space-between;gap:16px;align-items:center}.records-heading h2{font-size:18px;color:var(--career-text);margin:0}.records-heading span{font-size:12px;color:var(--career-muted)}.records-list{display:grid;align-content:start;gap:12px}.record-card{text-align:left;border:1px solid var(--career-border);border-radius:8px;background:#fff;padding:16px;display:grid;gap:7px;color:var(--career-muted);font:inherit}.record-card:hover,.record-card.active{border-color:#527c60;background:#f4f8f3}.record-card strong{color:var(--career-text)}.record-card em{font-size:11px;font-style:normal;color:#3f7351}.record-card small{font-size:11px}.record-pages{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:8px}.record-detail{min-width:0;border-left:1px solid var(--career-border);padding-left:28px}.record-empty{padding:24px;background:#f6f8f5;border-radius:8px;color:var(--career-muted)}.record-overview{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:20px 0}.record-overview div{padding:13px;background:#f5f8f4;border-radius:7px;display:grid;gap:4px}.record-overview span{font-size:11px;color:var(--career-muted)}.record-overview strong{font-size:13px;color:var(--career-text)}.summary-panel,.answer-card{border:1px solid var(--career-border);border-radius:9px;padding:20px;margin-top:18px}.summary-title h3,.answer-card h3{font-size:18px;color:var(--career-text);margin:0}.summary-title span{font-size:12px;padding:3px 8px;border-radius:12px;background:#f1f4ef}.summary-succeeded{color:#2f6b45}.summary-failed{color:#9b2c2c}.summary-list h4,.answer-block h4{font-size:13px;margin:14px 0 6px;color:var(--career-text)}.summary-list ul{padding-left:20px;margin:0}.answer-list{display:grid;gap:18px}.answer-index{font-size:11px;color:#527c60;margin-bottom:8px}.answer-block{margin-top:16px;padding:14px;background:#f7f8f6;border-radius:7px}.answer-block p{white-space:pre-wrap;overflow-wrap:anywhere}.feedback-failed,.summary-failed{color:#8f3c32}.answer-card details{margin-top:14px}.answer-card dl{display:grid;grid-template-columns:150px minmax(0,1fr);gap:8px;font-size:12px}.answer-card dt{color:var(--career-muted)}.answer-card dd{margin:0;overflow-wrap:anywhere}
@media(max-width:980px){.record-filters{grid-template-columns:repeat(2,1fr)}.records-layout{grid-template-columns:1fr}.record-detail{border-left:0;border-top:1px solid var(--career-border);padding:24px 0 0}.record-overview{grid-template-columns:repeat(2,1fr)}}
@media(max-width:520px){.record-filters{grid-template-columns:1fr}.record-overview{grid-template-columns:1fr}.record-card-top,.summary-title{align-items:flex-start}.answer-card{padding:16px}.answer-card dl{grid-template-columns:1fr}}
</style>
