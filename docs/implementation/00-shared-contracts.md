# 五人实施公共约定

需求唯一依据是 [当前需求方案](../career_platform_plan.md)。本文固定开发接口与验收方法；五个业务模块目前仍是返回 501 的骨架，不代表 MVP 完成。日期：2026-10-28。集成人：`@vacontinuejatotired`。

## 团队开工入口

本批准备内容首先交付在本fork的 `codex/team-scaffold` 分支。尚未合入master时，请从该分支拉取统一骨架，再各自新建短期功能分支；不要从旧master重复搭建接口。先读本文，再读本人01至05文档。当前有效请求返回501是预留业务，需成员实现。最终补丁未追加本地验收，CI和保护规则状态以GitHub实际结果为准。

```bash
git fetch origin
git switch -c codex/<自己的模块> origin/codex/team-scaffold
```

上面命令用于干净或已妥善保留修改的工作区，尖括号替换为本人模块名；禁止用reset/clean覆盖已有工作。后续PR目标仍为本fork master；准备PR合入后同步master再提成员PR。

## 现状和范围

已有登录、简历 CRUD、自由模拟面试、只读简历观览、受管理的 Company/Job。默认 `/interview` 仍走 legacy，文字优先、45 分钟可选时长；不要替换为新 RAG。现有职业评估不是本期可复现评估，职业推荐历史向量表也不是面试题库。

本次准备提供模型、迁移、端口、组装入口、接口校验、五个页面与验收门禁。成员分别完成目录数据、评估、简历分析、RAG、练习记录；不做爬虫、数据库切换、语音重做、再答一次或前后对比。SQLite 用于本地隔离测试，MySQL 用于 Actions 迁移和读写；线上迁移须单独审核，不能因骨架合入自动宣称数据已迁移。

## 层次与公共文件所有权

Vue 页面 → `features/career-platform/api.js` → 视图/序列化器 → 应用服务 → 领域 Protocol → ORM/检索/模型 Adapter。页面不直接访问模型厂商；视图不承担检索、生成、状态机或事务业务。

| 目录/公共文件 | 负责人 | 修改时同步文档 | 验收模块 |
| --- | --- | --- | --- |
| `career_platform/catalog/`、`models/catalog.py`、`company_reviews/`、Catalog.vue、`data/career-platform/` | 成员1 | 01 | catalog |
| `career_platform/evaluation/`、`models/evaluation.py`、Evaluation.vue | 成员2 | 02 | evaluation |
| `career_platform/resume/`、`models/resume.py`、`resumes/`、Resume.vue | 成员3 | 03 | resume |
| `career_platform/rag/`、Practice.vue | 成员4 | 04 | rag |
| `career_platform/records/`、`models/practice.py`、Records.vue | 成员5 | 05 | records |
| `views/<模块>.py` | 对应成员 | 对应实施文档 | 对应模块 |
| contracts、composition、api、serializers、urls、permissions、迁移、前端共享客户端/导航/路由、CI/固定测试 | 集成人 | 00及五份受影响文档 | 全部模块及集成 |

上表后端路径均位于 `backend/`，新服务位于 `backend/career_platform/`；页面位于 `frontend/src/views/career-platform/`。以 `ci/project_modules.json` 为机器映射。成员不能自行改公共字段、删除固定用例、加 skip、降低阈值。变更应提交契约调整说明，由集成人先审核并同步调用方。

## 生产组装与替身

`contracts.py` 定义端口，`composition.py:build_services()` 是唯一生产组装点。五个 Service 当前继承 `UnavailableService`，公开操作抛 `FeatureNotImplemented`；有效请求返回 HTTP 501：

```json
{"code":"FEATURE_NOT_IMPLEMENTED","message":"功能待实现","details":{"detail":"功能待实现"}}
```

字段校验或权限失败优先返回 400/401/403/404。未实现操作不得先写业务记录。测试通过构造器注入确定性依赖；生产与开发默认组装均不能导入 `tests/`、测试向量或固定报告。成员完成某操作后改写该方法，不依赖状态旗标跳过验收。

## HTTP 与数据契约 v1

命名空间 `/api/career-platform/`，Token 鉴权。所有列表目标格式为 `{count,page,page_size,results}`，页从1开始，默认20、最大100；稳定按 `created_at,id` 或明确排序。骨架尚无业务成功响应，以下成功结构是实现必须遵循的约定。所有时间为 UTC ISO8601，私有新记录 ID 为 UUID，既有 Company/Job/Resume ID 保留整数；禁止把两种 ID 混用。

| 路径 | 方法、输入和责任 |
| --- | --- |
| `catalog/companies/`、`catalog/jobs/`、`catalog/questions/` | GET：page/page_size/q/city/role/topic/difficulty；成员1，按资源支持的条件筛选，不适用条件返回可理解错误 |
| `catalog/imports/` | POST：kind=companies/jobs/questions、records[1..1000]、dry_run默认true；仅staff，成员1 |
| `resume-analyses/` | GET列表；POST jd_text、可选job_id、resume_revision、request_id；成员3 |
| `resume-analyses/{id}/`、`{id}/apply/` | GET详情；POST base_revision、accepted_suggestion_ids、suggestion_edits（建议UUID到编辑文本字典）、request_id；成员3 |
| `questions/retrieve/` | POST role、可选job_id/jd_text/topic、difficulty默认easy、top_k默认5上限20、request_id；成员4 |
| `practice-sessions/`、`{id}/` | GET列表/详情；POST创建 role、可选job_id/jd_text/topic、difficulty、可选question_ids、request_id；成员5 |
| `practice-sessions/{id}/answers/` | POST question_id、answer、request_id；成员4编排、成员5保存 |
| `practice-sessions/{id}/finish/` | POST request_id、retry_summary默认false；成员5 |
| `evaluation-runs/`、`{id}/`、`{id}/export/` | GET列表/详情/JSON导出；POST task=job/resume/question、dataset_version、strategy、parameters、request_id；仅staff，成员2 |

文本 JD/回答上限20000字符，role/topic上限100。未知字段400，客户端传 user/owner 一律拒绝。记录所有者由登录身份指定，服务端再次按 user 过滤；管理员也不因身份自动读取其他用户私有记录，越权与不存在均404。

错误恒为 `{code,message,details}`。400 VALIDATION_ERROR、401 UNAUTHENTICATED、403 FORBIDDEN、404 NOT_FOUND、409 CONFLICT、501 FEATURE_NOT_IMPLEMENTED；业务增加安全的 MODEL_UNAVAILABLE/INVALID_MODEL_OUTPUT 等错误时先同步本文和客户端，不能泄露原始供应商异常、提示词中的私人数据或凭据。

## 快照和交接结构

```json
{
  "question_id":"10000000-0000-4000-8000-000000000001",
  "question":"解释 equals 与 hashCode 的约束",
  "key_points":["相等对象必须具有相同 hashCode"],
  "evidence":[{"source_id":"10000000-0000-4000-8000-000000000001","field_path":"key_points[0]","quote":"相等对象必须具有相同 hashCode"}],
  "score":0.72,"origin":"catalog"
}
```

`RankedQuestion` 为上述结构的 frozen dataclass，key_points/evidence 在 Python 中使用 tuple，对外 JSON 数组。score 仅表示检索相关度，不能称能力得分。来源说明保存在题库 source/source_url/permission_status/collected_at 中，并进入历史 question_snapshot；生成追问 origin=generated，不得伪造题库 ID 或来源。

简历建议目标结构：`{id,field_path,original,suggested,reason,evidence:[Evidence]}`；分析结果 `{matches,gaps,suggestions}`。field_path 仅允许既有简历字段/当前归属子记录，不能借路径修改 user、ID、版本或其他账号记录。反馈结构 `{answer_quote,key_points_covered,missing_points,evidence,follow_up}`，总结 `{strengths,gaps,next_steps}`；字符串均纯文本，模型内容用文本渲染。

新模型 ResumeAnalysisRun/ResumeApplyReceipt/PracticeSession/AnswerRecord/EvaluationRun 及 InterviewQuestion 均为 Django 托管。Company/Job 兼容补字段，不读取 unmanaged `company_info_backup`。Job 的 `requirements` 兼容旧文本，`description` 保存完整 JD，技能规范化到 `skills`；成员1需明确旧字段回退规则，不能静默丢失旧 JD。

## 状态、并发和失败约定

创建分析/练习/评估由 `(user,request_id)` 去重，回答由 `(session,request_id)` 去重。相同键相同输入返回原记录；相同键不同输入409。应用建议、结束会话也必须保存并复用首次结果，不能仅靠禁用按钮去重。跨动作键冲突按所属操作处理。

简历当前 `edit_revision` 从0开始，旧保存入口每次更新递增；成员3在事务中锁定 Resume、检查 base_revision，再原子更新内容和回执。模型调用在锁外，旧分析不能覆盖新版本。QuerySet.update/bulk_update 或直接修改子记录不得绕过版本维护。

会话目标状态 active → ended；总结状态由 summary 内容携带 pending/succeeded/failed，结束后不可继续回答。回答 received → succeeded/failed；先通过成员5保存用户真实回答，再生成反馈，模型失败保留回答并标注失败，不显示固定报告。分析在生成与校验成功后保存，失败原简历不变；骨架501不产生这些过程记录。结束失败仍保留原回答与结束时间，用户明确重试才再次调用总结。

## 模块集成顺序

成员1先提供可追溯正式数据及查询；成员2并行冻结独立评估集。成员5先提供 PracticeStore 保存接口；成员3使用 ModelGateway/匹配替身开发，成员4使用 RetrievalStrategy/ModelGateway/PracticeStore 替身开发。随后在唯一 composition 注入实际适配器，最后执行“导入→选岗→分析→确认→练习→反馈→复盘”的整体验收。成员4不能直接新建另一套历史表。

Java演示覆盖基础、集合/JVM、Spring、数据库、并发。`tests/fixtures` 仅用于测试，不是正式题库或真实招聘。正式材料至少30道人审题，逐题记录来源或团队创作说明；虚构岗位/企业 is_demo=true。独立索引名 `career_platform_questions_v1`，只包含 allowed 且审核通过的数据。

## 验收命令与门禁

在仓库根，使用当前环境 Python；Windows 工作树可复用 `E:\CS-Career-Guide\.venv\Scripts\python.exe`。下文 `python` 指该解释器：

```powershell
python ci/project_acceptance.py --stage scaffold --output output/scaffold.json
python ci/project_acceptance.py --stage complete --module catalog
python ci/project_acceptance.py --stage complete --module evaluation
python ci/project_acceptance.py --stage complete --module resume
python ci/project_acceptance.py --stage complete --module rag
python ci/project_acceptance.py --stage complete --module records
python ci/project_acceptance.py --stage complete --module all
python -m unittest discover -s ci -p 'test_project*.py'
node --test frontend/tests/*.test.mjs
npm run build --prefix frontend
```

首次骨架 PR 只允许骨架检查通过，完整业务检查应失败并报告未实现。合入后业务目录变更自动选择对应 complete；公共接口变更选择全部模块及集成，不允许修改“阶段”标记跳过。固定测试不能为空、不能 skip；纯文档变更不触发业务 complete。真实模型、真实Embedding和浏览器验收另行记录，离线替身不能替代。

CI 在 PR 使用 base SHA，在 push 使用 before SHA；不能用 HEAD^ 代替 PR 基线。文档门禁按映射要求变更实施文档，并检查验收记录字段。骨架合入后再启用 master 必须PR、最新基线、至少一次审核、公共文件 CODEOWNER、必需检查、禁止强推/删除。仓库管理员用本人账号创建PR时不能给自己审批，须由另一账号审核，不通过降低规则解决。

## 验收记录

每次追加或更新以下记录，替身和真实范围必须明确，不能填未来提交号。当前 HEAD 可表示测试所基于提交，dirty 代表同时包含未提交补丁。

| 提交号 | 执行命令 | 结果 | 环境 | 模拟/真实范围 | 已知限制 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| d12128b + dirty | 待本轮执行 | 未验收 | 本地隔离 | 无真实模型 | 业务仍为501 | output/ |

## PR 检查表

- [ ] 实现、契约、对应成员文档和证据一起提交；新增正式文档已加入 agent.md。
- [ ] 模块固定用例与既有登录/API/简历/面试/ASR/配置/构建回归通过。
- [ ] 权限、幂等、事务、快照和失败路径均有可观察结果；未借修改测试制造通过。
- [ ] 骨架、完整业务、远端CI、真实服务、发布和部署分别报告。
- [ ] 只向本fork提PR，无本机Docker、秘密、真实用户材料或测试产物入库。


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
