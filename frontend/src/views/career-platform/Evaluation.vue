<template><WorkspaceShell title="评估与调优" description="管理员比较固定评估集上的基线和参数结果，不预填指标。"><form class="platform-form" @submit.prevent="run(()=>api.evaluate({task:task,dataset_version:dataset,strategy:'tfidf',parameters:{k:5},request_id:newRequestId()}))"><label>评估任务<select v-model="task"><option value="job">岗位匹配</option><option value="resume">简历匹配</option><option value="question">题库检索</option></select></label><label>数据集版本<input v-model="dataset" required /></label><div class="platform-actions"><button class="career-button career-button-primary" :disabled="busy">{{ busy ? '请求中…' : '运行评估' }}</button></div></form><form class="platform-form" @submit.prevent="run(()=>api.evaluation(id))"><label>评估记录 ID<input v-model="id" required /></label><div class="platform-actions"><button class="career-button" :disabled="busy">查看评估详情</button><button type="button" class="career-button" :disabled="busy || !id" @click="run(()=>api.exportEvaluation(id))">导出评估结果</button></div></form><p class="platform-status" role="status">{{ status }}</p><section class="platform-result"><h2>基线、调优结果与误差分析</h2><p>该区域由负责成员接入实际业务结果。骨架不展示模拟成功或虚构内容。</p></section></WorkspaceShell></template>
<script setup>
import {ref,onMounted} from 'vue'
import WorkspaceShell from '@/features/career-platform/WorkspaceShell.vue'
import {platformAPI as api} from '@/features/career-platform'
import {newRequestId} from '@/features/career-platform/api.js'
import {useOperation} from '@/features/career-platform/useOperation.js'
const {busy,status,run}=useOperation()
const id=ref('')
const task=ref('question'),dataset=ref('java-fixture-v1')
onMounted(()=>run(signal=>api.evaluations(signal)))
</script>
