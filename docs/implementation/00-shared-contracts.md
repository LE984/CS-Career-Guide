# 五人实施公共约定

需求唯一依据是 [当前需求方案](../career_platform_plan.md)。本文固定开发接口与验收方法。catalog 的企业/岗位/题库查询与 JSON 导入已实现并通过本地固定验收；evaluation、records、rag 已有本地实现；resume 仍未完成并继续返回 501。完整 MVP、真实模型、MySQL、远端 CI 与部署仍需独立确认。日期：2026-11-10。集成人：`@vacontinuejatotired`。

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

`contracts.py` 定义端口，`composition.py:build_services()` 是唯一生产组装点。未实现操作继续继承 `UnavailableService` 并抛 `FeatureNotImplemented`，有效请求返回 HTTP 501；catalog 已实现四个公开操作，resume 仍整体不可用：

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
| `questions/retrieve/` | POST role、可选job_id/jd_text/topic、difficulty默认easy、top_k默认5上限20、request_id；返回有序结果及短期、用户绑定的 retrieval_id；成员4 |
| `practice-sessions/`、`{id}/` | GET列表/详情；POST创建 role、可选job_id/jd_text/topic、difficulty、question_ids、可选retrieval_id、request_id；成员5 |
| `practice-sessions/{id}/answers/` | POST question_id、answer、request_id；成员4编排、成员5保存 |
| `practice-sessions/{id}/answers/{answer_id}/retry-feedback/` | POST request_id；复用原回答并显式重试反馈，不新增 AnswerRecord；成员4编排、成员5认领尝试 |
| `practice-sessions/{id}/finish/` | POST request_id、retry_summary默认false；成员5 |
| `evaluation-runs/`、`{id}/`、`{id}/export/` | GET列表/详情/JSON导出；POST task=job/resume/question、dataset_version、strategy、parameters、request_id；仅staff，成员2 |

文本 JD/回答上限20000字符，role/topic上限100。未知字段400，客户端传 user/owner 一律拒绝。记录所有者由登录身份指定，服务端再次按 user 过滤；管理员也不因身份自动读取其他用户私有记录，越权与不存在均404。

错误恒为 `{code,message,details}`。400 VALIDATION_ERROR、401 UNAUTHENTICATED、403 FORBIDDEN、404 NOT_FOUND、409 CONFLICT、502 INVALID_MODEL_OUTPUT、503 MODEL_UNAVAILABLE、504 MODEL_TIMEOUT、501 FEATURE_NOT_IMPLEMENTED。502/503/504 用于逐题反馈接口；finish 将同类失败保存到 summary 并返回 HTTP 200 的会话结果。任何错误均不得泄露原始供应商异常、提示词中的私人数据或凭据。

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

会话目标状态 active → ended；总结状态由 summary 内容携带 pending/succeeded/failed，结束后不可继续回答。回答 received → succeeded/failed；创建回答的事务同时认领首次反馈尝试，只有认领者调用模型。相同 answer request_id 的重放不重复模型；失败后使用独立 retry-feedback request_id 原地更新同一 AnswerRecord。结束失败仍保留原回答与结束时间，用户明确 retry_summary 才再次调用总结；旧尝试键和迟到结果不得覆盖当前尝试。

## 模块集成顺序

成员1先提供可追溯正式数据及查询；成员2并行冻结独立评估集。成员5先提供 PracticeStore 保存接口；成员3使用 ModelGateway/匹配替身开发，成员4使用 RetrievalStrategy/ModelGateway/PracticeStore 替身开发。随后在唯一 composition 注入实际适配器，最后执行“导入→选岗→分析→确认→练习→反馈→复盘”的整体验收。成员4不能直接新建另一套历史表。

Java演示覆盖基础、集合/JVM、Spring、数据库、并发。`tests/fixtures` 仅用于测试，不是正式题库或真实招聘。`data/career-platform/java-backend.json` 已提供2家虚构企业、3个虚构岗位和30道团队自编题，题目保持 `pending`，须集成人逐题复核并记录来源或团队创作说明后改为 `allowed`；虚构岗位/企业 is_demo=true。独立索引名 `career_platform_questions_v1`，只包含 allowed 且审核通过的数据。

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

本次既有页面、导航与接口调整包含 frontend/src/components/Navbar.vue，按既有 shared_paths 映射要求公共文档、五份模块记录和全模块 complete 验收。继续保留原映射、固定测试与发布依赖；不会把手动触发时的空差异当成本次业务验收通过。

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


### 2026-11-09 文本检索演示发布候选

本次新增经过 Token 鉴权的 `POST /api/career-platform/questions/demo-retrieve/`，与正式 `questions/retrieve/` 隔离。页面 `/career-platform/practice` 改为明确标注的文本检索演示，提供条件筛选、排名与来源证据。候选为 `rag/demo.py` 专门编写的9条虚构演示材料，不导入测试 fixture、不写数据库、不创建会话或反馈；pending/restricted 不返回。正式五模块服务和旧自由面试边界保留。共享 URL 新增使本次按原规则核对六份文档与全部固定验收，不降低既有用例。详细输入、输出和范围见成员4说明。

```acceptance-record
{
  "commit": "93640dd + dirty",
  "command": "python -m unittest discover -s backend/tests -p test_text_retrieval.py -v; python -m unittest discover -s backend/tests -p test_retrieval_demo.py -v; node --test frontend/tests/*.test.mjs; node frontend/node_modules/vite/bin/vite.js build (cwd=frontend); python ci/project_acceptance.py --stage scaffold; python ci/project_acceptance.py --stage complete --module all",
  "result": "failed",
  "environment": "2026-11-09；Windows；隔离内存 SQLite；本地浏览器通过隔离预览 API 调用真实文本策略，无生产数据",
  "scope": "文本策略17项、演示接口6项、前端78项和生产构建通过；骨架7项通过。固定完整业务17项仍为14 failures、3 errors，原因是五模块正式服务501。独立演示不冒充正式业务完成。",
  "limitations": "仅发布候选准备。用户明确授权将标注演示的半成品部署到现有网站；允许使用既有手动发布流程，固定测试和门禁规则不改。未接数据库题库、真实模型、练习记录；远端CI、发布和线上浏览器结果另记。",
  "evidence": "backend/tests/test_text_retrieval.py; backend/tests/test_retrieval_demo.py; output/retrieval-demo-20261109/scaffold.json; output/retrieval-demo-20261109/complete.json; pre-deploy audit Actions 42551685730"
}
```


### 2026-11-09 课程页面字体统一

共享页面样式调整：沿用全站无衬线字体，课程标题桌面32px/手机28px，内容标题18px、正文与表单14px、辅助文字12px。仅视觉调整，不改变本模块接口、状态或数据流，不代表业务实现完成。

```acceptance-record
{
  "commit": "8607c29",
  "command": "gh run view 42578102031 --repo vacontinuejatotired/CS-Career-Guide; node --test frontend/tests/*.test.mjs; node frontend/node_modules/vite/bin/vite.js build (cwd=frontend)",
  "result": "failed",
  "environment": "2026-11-09；Windows 本地隔离浏览器及 GitHub Actions",
  "scope": "仅课程页面字体样式。前端78项与生产构建通过；浏览器1440/390px检查五个课程入口和个人中心、简历页，共14视图无横向溢出或JS运行异常。Actions前端检查及镜像构建成功，但共享组件变更缺实施文档导致总门禁失败。",
  "limitations": "五模块正式业务未完成，未宣称complete通过；本轮完整业务重跑因WSL互操作失败未启动。浏览器使用隔离模拟API，仅初始页面，不覆盖检索结果和全部失败状态。用户已授权半成品演示上线；仅按既有手动流程发布前端，不修改门禁、不部署后端。线上结果另记。",
  "evidence": "Actions 42578102031；output/playwright/typography-result.txt；frontend/src/features/career-platform/WorkspaceShell.vue；frontend/src/views/career-platform/Practice.vue"
}
```


### 2026-11-09 课程导航统一

五个课程入口共用CourseNav，保持名称、顺序、选中样式与顶部位置一致；自由模拟面试作为练习页辅助入口。内容轻量淡入，尊重减少动态效果设置；不改变本模块业务实现状态。

```acceptance-record
{
  "commit": "66a5159 + dirty",
  "command": "node --test frontend/tests/*.test.mjs; vite build; playwright-cli run-code --filename output/playwright/course-nav-check.js",
  "result": "passed",
  "environment": "2026-11-09；Windows；本地隔离模拟API与Chromium",
  "scope": "仅统一课程导航和切换样式。78项前端测试、生产构建通过；1440/390px各点击五个入口，共10次切换均为同名同序五项导航、一个当前项、无横向溢出，导航纵向位置同尺寸一致；减少动态效果时动画为none。",
  "limitations": "不改变五模块正式业务、API、鉴权或数据；passed仅指此次前端专项，不代表五模块complete成功。未调用真实模型；线上发布及服务器运行版本另验收。用户要求验证后直接上线，仅发布前端，沿用既有半成品演示发布流程，不修改门禁。",
  "evidence": "output/playwright/course-nav-tests.log；output/playwright/course-nav-build.log；output/playwright/course-nav-check.js；output/playwright/course-nav-1440.png；output/playwright/course-nav-390.png"
}
```
