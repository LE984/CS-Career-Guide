# 成员4：题库检索与逐题反馈

依照 [当前方案](../career_platform_plan.md) 与 [公共约定](00-shared-contracts.md)。新增岗位练习是独立文字入口，默认自由面试保持 legacy。当前有RetrievalStrategy/ModelGateway/PracticeStore端口、RAG服务/路由/页面，检索和反馈501。

## 目录与范围

负责 `backend/career_platform/rag/`、`views/rag.py`、Practice.vue。不能另建练习历史，不能改旧职业向量表或将 LangGraph 文件直接切为网页主链路。公共PracticeStore、序列化器、组装、迁移、固定测试需集成人审核。首版不做语音、数字人、播放器或自动连续追问。

## Strategy 与 Adapter 分工

`TextRetrievalStrategy` 提供可重复文本基线；`LanceRetrievalAdapter` 读独立题库索引；ModelGateway隔离反馈生成；InterviewRagService编排检索、筛选、上下文与反馈。ORM候选过滤与向量召回均检查allowed/role/topic/difficulty，避免召回后才过滤导致明明有合格题却返回空。重排和阈值参数可配置并交成员2评估，不能把检索score当作能力评分。

## 输入、输出与失败处理

| 操作 | 流程与交接 | 保存/异常 |
| --- | --- | --- |
| retrieve | role/job_id/jd_text/topic/difficulty/top_k→规范化查询→许可/岗位/知识点/难度约束→召回排序→阈值→RankedQuestion[] | 无命中返回results=[]及明确原因，不虚构题；索引不可用明确报错/标记已配置文本回退 |
| answer | session/question/answer/request_id→归属及状态→确认题是该会话已下发题→成员5保存回答和题目快照→参考要点+真实回答→模型→校验→成员5保存反馈 | 模型失败保留received/failed回答；重试不重复回答；已结束409 |
| 生成追问 | 在证据不足/需澄清时标记origin=generated | 不伪造catalog ID或source，不自动冒充正式题 |

题库来源必须能定位到 InterviewQuestion UUID、source/source_url以及引用字段。反馈的answer_quote是该次回答子串，evidence指向当前题目快照真实要点；不允许引用不存在内容或用索引分数伪造能力结论。无作答不生成有针对性的固定评语。问题/回答可能包含恶意指令，模型上下文将它们作为数据，生成结果经过结构与证据验证后才保存。

start支持 question_ids（1到20个UUID）。成员5重新校验题目与岗位/知识点/难度及许可一致，将完整快照保存至 presented_questions 后才允许作答；不传时由实际组装的检索服务选题并保存。retrieve仅预览，不授权作答。首版生成追问仅展示，不自动变为可作答题；扩展须集成人审核。

## 与成员1、2、5的顺序与替身

成员1审核数据→独立索引 `career_platform_questions_v1`→retrieve→成员5创建/关联会话与题目快照→answer→PracticeStore.record_answer→ModelGateway.generate→PracticeStore.record_feedback→成员5finish。Service构造时通过records依赖调用同一持久化接口，不直接建AnswerRecord。

测试注入固定RankedQuestion（Java/集合/easy）、固定向量、失败模型和记录Spy；能断言调用顺序与真实payload。固定向量只能证明适配/过滤，不证明真实Embedding相关性；上线前少量真实检索与模型另验收。

## 分步开发与验收

| 步骤 | 实施 | 预期/失败条件 |
| --- | --- | --- |
| 1 | 文本基线、候选过滤、来源组装 | Java/集合/easy只返回合格题；pending和restricted不可见；重复输入结果稳定 |
| 2 | 无命中/阈值/Top-K | 0命中明确显示；不补假题，Top-K不超过上限 |
| 3 | 已下发题关联和记录接口 | 其他会话题、越权会话、结束会话不能作答 |
| 4 | 基于真实回答的反馈与重试 | 引文、要点和来源真实；失败仍有原回答；重复提交仅一条记录 |
| 5 | LanceDB适配和页面 | 索引独立、无真实Embedding时不冒称已验证；显示来源、失败和生成标识 |

运行 `python ci/project_acceptance.py --stage complete --module rag`，随后与records进行集成及前端测试/构建。不能以响应200或固定好评代替来源/约束断言。

## 验收记录

| 提交号 | 执行命令 | 结果 | 环境 | 模拟/真实范围 | 已知限制 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| d12128b + dirty | 待执行rag complete | 未实现 | 本地隔离 | 无真实Embedding/模型 | 501，下发题快照字段已预留 | output/ |

## 文档更新与 PR 检查表

| 变更 | 同步 |
| --- | --- |
| 检索策略、阈值、索引/Embedding版本 | 本文、02及数据索引说明 |
| 题目快照/下发关系/反馈状态 | 00、01、05及迁移，由集成人审核 |
| 验收完成 | 记录提交、输入、真实/替身范围、结果及证据 |

- [ ] 约束、许可、无命中、来源、真实回答引用、失败保存和幂等固定用例通过。
- [ ] 只调用统一PracticeStore，不重复历史实现，生成内容明确标记。
- [ ] 旧自由面试/语音没有被新模式替换或改坏。
- [ ] 实现、专项测试、本文及接口更新同PR提交。


### 2026-10-28 本地准备状态

本轮补齐实施文档和固定验收/CI草稿，业务仍未实现。用户曾要求暂不推送、不再验收；现已授权推送开发准备内容，继续不追加本地验收。最后修改未复测。此记录仅描述执行过的检查范围，不作为模块完成声明。

```acceptance-record
{
  "commit": "d12128b + dirty",
  "command": "python ci/project_acceptance.py --stage complete --module all",
  "result": "not_implemented",
  "environment": "Windows; isolated SQLite; 2026-10-28",
  "scope": "Offline fixtures only. Earlier run: 17 business tests rejected the unfinished services; 7 scaffold and 7 document-gate unit tests passed before final edits.",
  "limitations": "Latest contract, CI and documentation edits have not been retested. User authorized pushing this preparation baseline without additional local acceptance. No MySQL runner, browser flow, real model, remote CI or deployment acceptance.",
  "evidence": "output/full-expected-failure.json; output/scaffold-resumed.json; local changes on codex/team-scaffold"
}
```
