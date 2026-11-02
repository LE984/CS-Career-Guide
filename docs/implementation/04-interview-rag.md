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


### 2026-11-01 交付拆分与原业务门禁

仅细化交付配置选择，不修改本模块业务或固定验收用例。交付编排和真实网关联调独立验证；验收规则变更仍触发原完整业务门禁。本模块仍是未完成骨架，不将交付验证作为业务完成证据。

```acceptance-record
{
  "commit": "15828fa + dirty",
  "command": "python ci/project_acceptance.py --stage complete --module all --output output/split-delivery/business-complete.json",
  "result": "failed",
  "environment": "Windows；隔离 SQLite；2026-11-01",
  "scope": "交付拆分仅调整选择范围，原固定 complete 用例保留。17 项业务测试因 501/FeatureNotImplemented 出现 14 failures、3 errors；骨架 7 项通过。",
  "limitations": "五个业务模块仍未实现；此本地记录不覆盖 MySQL runner、镜像发布、服务器部署、真实模型或浏览器验收。",
  "evidence": "output/split-delivery/business-complete.json; output/split-delivery/scaffold.json; ci/test_project_changes.py; docs/split-delivery.md"
}
```


### 2026-11-01 首次网关切换工具

本模块业务与固定验收不变；交付工具测试不代表业务完成。

```acceptance-record
{
  "commit": "7909ecf + dirty",
  "command": "python -m unittest discover -s ci -p test_*.py -q; preserved complete acceptance in Actions 41304123356",
  "result": "failed",
  "environment": "Windows/WSL isolated offline fixtures; 2026-11-01",
  "scope": "85 delivery tests passed on WSL; 71 passed and 14 POSIX skipped on Windows. Cutover success, pull failure, environment mismatch and frontend rollback tested. Original business complete suite remains failed (501 skeletons), not modified.",
  "limitations": "No business implementation; no model calls or database migrations. Server install not yet performed in this record. Existing business failure accepted for delivery-only merge.",
  "evidence": "ci/test_server_cutover.py; ci/test_split_topology.py; Actions 41304123356; docs/split-delivery.md"
}
```


### 2026-11-01 首次维护传输与超时修复

交付工具变更保留本模块现有业务状态；不将构建或服务器审计作为业务完成证据。

```acceptance-record
{
  "commit": "e301070 + dirty",
  "command": "wsl -d Ubuntu-22.04 --cd /mnt/e/CS-Career-Guide-split-delivery -- python3 -m unittest discover -s ci -p 'test_*.py' -q; original complete suite: Actions 41305627720",
  "result": "failed",
  "environment": "2026-11-01；WSL 离线隔离测试；既有完整业务验收为 Actions SQLite/MySQL",
  "scope": "压缩网关归档、限量解压及旧归档兼容；87 项交付测试通过。维护 workflow 超时变更仍触发原完整业务门禁，五模块 501 骨架失败保留，不修改业务代码或固定验收。",
  "limitations": "本记录的交付单元测试不代表业务完成。线上首次切换尚未成功；独立审计确认旧容器健康且未变。无真实模型、数据库迁移或浏览器验收。",
  "evidence": "ci/test_server_maintenance.py; ci/test_server_cutover.py; Actions 41308721534; docs/deployment-status.md"
}
```


### 2026-11-01 首次网关 ACR 传输

不修改本模块业务及验收规则；交付测试和业务完成分别记录。

```acceptance-record
{
  "commit": "7ab4193 + dirty",
  "command": "wsl -d Ubuntu-22.04 --cd /mnt/e/CS-Career-Guide-split-delivery -- python3 -m unittest discover -s ci -p 'test_*.py' -q; original complete suite: Actions 41309171882",
  "result": "failed",
  "environment": "2026-11-01；WSL 离线隔离测试；Actions SQLite/MySQL 原业务验收",
  "scope": "88 项交付单元测试通过。首次网关镜像改走已授权 ACR 专用基础设施标签，按 digest/image ID 验证；业务接口和固定验收保持原样，现有完整业务 14 failures/3 errors 为 501 骨架。",
  "limitations": "此交付验证不代表五模块实现；没有重启线上后端、迁移数据或真实模型调用。此前 SSH 传输超时，审计确认旧容器未变。",
  "evidence": "ci/test_server_maintenance.py; ci/cutover_smoke.py; Actions 41311002510; docs/deployment-status.md"
}
```

### 2026-11-02 发布门禁复核

本次涉及既有面试工作区与简历观览，默认自由面试继续使用 legacy 适配器；没有切换至新 RAG 主链路。新的题库检索、来源约束、基于真实回答的反馈与记录交接服务仍未实现，全模块验收中的 rag complete 保持失败。

```acceptance-record
{
  "commit": "c34a98a6a2d0538e3b9c47d53f2e0c066e326202",
  "command": "python ci/project_acceptance.py --stage scaffold --output .runtime/gate-repair/scaffold.json; python ci/project_acceptance.py --stage complete --module all --output .runtime/gate-repair/complete.json",
  "result": "failed",
  "environment": "2026-11-02；Windows；现有 D:/python/python.exe；隔离内存 SQLite；PLATFORM_TEST_MYSQL=0",
  "scope": "骨架 7 项通过；固定完整业务验收 17 项为 14 failures、3 errors，五模块 501 / FeatureNotImplemented。测试提交 c34a98a 与部署目标 master 0f64e4e 的 tree 均为 cb53fd5f04e5e5197b289dadef18a8aea55c48b3。",
  "limitations": "五个业务模块尚未实现，本次未修改业务代码、固定测试或门禁。未重新验证 MySQL、真实模型或浏览器，未执行镜像发布、服务器重建或线上迁移。用户选择保留门禁，完整验收通过前不部署。",
  "evidence": ".runtime/gate-repair/scaffold.json; .runtime/gate-repair/scaffold.log; .runtime/gate-repair/complete.json; .runtime/gate-repair/complete.log; GitHub Actions 41456388774（文档门禁失败、应用测试/双镜像/联调成功）；41467510972（只读 SSH 审计成功）"
}
```
