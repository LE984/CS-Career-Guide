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

### 2026-11-09 纯内存文本检索基线

`backend/career_platform/rag/retrieval.py` 已实现独立的 `TextRetrievalStrategy`，调用签名沿用 `RetrievalStrategy`，输出沿用 `RankedQuestion`，未修改题库模型或公共契约。`InterviewRagService` 和生产组装仍未接入该策略，HTTP 检索与反馈继续返回 501；本节仅交付离线算法，不代表 RAG 完整业务完成。

调用方将一组已物化的题目字典传入构造器，键名沿用 `InterviewQuestion`，不传 ORM QuerySet。候选至少应有 `id`、`permission_status`、`role`、`topic`、`difficulty`、`question`、`source`；`tags`、`key_points` 为字符串列表，`reference_answer`、`source_url` 为字符串。候选由可信数据适配层保证类型，本策略不承担导入校验。构造时深拷贝为快照，来源或许可变更后必须重新构造；未来接入正式题库时，数据层与会话下发环节仍需重新核验最新许可。

```python
from career_platform.rag.retrieval import TextRetrievalStrategy

# candidate_questions 是调用方提供的题目字典序列；这里不加载任何测试题。
retriever = TextRetrievalStrategy(candidate_questions)
results = retriever.retrieve(
    query="集合", role="Java 后端", topic="集合", difficulty="easy", top_k=5,
)
# results: list[RankedQuestion]；实际无命中时为 []。
```

- 筛选：只接受 `permission_status == "allowed"`；缺少稳定 ID、非空题干或来源的题目不返回。岗位、知识点和难度去除首尾空白、统一全半角和大小写后精确匹配，空条件表示不限；不做岗位别名或同义词推断。
- 排序：英文/数字按词匹配，连续中文使用相邻二字片段。每个字段得分为“命中的查询词数量 / 查询词总数”，题干、标签、参考要点、参考答案默认权重分别为 `4/3/2/1`，加权后除以总权重，分数范围为 `[0, 1]`。重复词不累计加分，标签和要点分别作为独立文本分词，不拼接出跨字段词组。同分按题目 ID 字符串升序，输入候选顺序变化不影响同分结果。
- 阈值与数量：构造器可传 `min_score`（默认 `0`）及 `field_weights`（上述四字段的非负权重，至少一个为正）。非空文本查询零匹配必定排除，`score >= min_score` 才返回；空白查询只筛选，分数为 `0`，正阈值会排除它；仅有标点的查询无结果。`top_k` 沿用公共上限，须为 `1..20` 整数，非法参数抛 `ValueError`，不冒充无命中。
- 来源：每条 evidence 的 `source_id` 为题目 ID，`field_path` 指向原始 `source`、可选 `source_url`、题干、参考答案、`tags[i]` 或 `key_points[i]`，`quote` 保留原文；没有来源 URL 时不编造。`origin="catalog"` 仅沿用题库候选契约，不代表这些离线测试题是正式人审题。

离线验证（仓库根目录，无需 Django 配置、数据库、Embedding 或模型 Key）：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_text_retrieval.py -v
```

虚构题目仅位于 `backend/tests/test_text_retrieval.py`，生产代码不导入。用例覆盖 Java 后端/集合/easy、未知知识点、pending/restricted/未知许可、四字段权重与查询覆盖率、中文匹配、全半角和大小写、空查询、Top-K、阈值、稳定排序、原文证据、缺少来源、快照隔离和契约签名。2026-11-09 本地 `codex/personal + dirty` 实际运行：上述 17 项全部通过；既有离线回归 `python -m unittest discover -s backend/tests -p test_interview.py` 的 6 项全部通过。未执行数据库、真实模型、练习记录、远端 CI 或部署。本基线参数尚未经过成员2正式评估，score 不能解释为语义置信度或能力评分；后续 LanceDB 和逐题反馈接入另行实现与验收。

### 2026-11-03 本地空实现预留

本次仅增加成员四的显式方法与中文 `TODO(成员4)` 注释，不代表检索或反馈已经实现：

- `backend/career_platform/rag/retrieval.py`：`TextRetrievalStrategy.retrieve()` 预留文本检索基线，签名沿用 `RetrievalStrategy`；下次优先实现候选许可/条件过滤、文本匹配、稳定排序、Top-K 和真实来源证据。
- `backend/career_platform/rag/service.py`：显式预留 `InterviewRagService.retrieve()`、`answer()`，注明检索预览、会话校验、先存回答再生成反馈、证据校验与幂等的后续步骤。
- 三个方法均继续抛 `FeatureNotImplemented`；生产组装保持原样，不返回假题、固定反馈或默认空结果，不访问数据库、索引或真实模型。尚未新增 LanceDB 适配器或调整旧自由面试。
- 其他成员未开工时，可先用仅供测试的虚构题目完成文本策略；正式数据与持久化依赖分别待成员一、成员五接口就绪后接入。专项完整业务验收在真实逻辑补齐前仍应失败。

本地验证基于 `93640dd + dirty`：运行 `python ci/project_acceptance.py --stage scaffold --output output/rag-placeholders-20261103/scaffold.json`，隔离 SQLite 骨架 7 项通过；另行直接调用三个空方法，确认均抛 501、不会调用注入依赖，文本策略签名与现有 Protocol 一致，Python 语法检查通过。报告 `business_complete=false`。未执行完整 RAG 业务验收、真实模型/Embedding、浏览器、远端 CI、发布或部署；本次结果仅证明预留未冒充实现。

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

演示请求字段：`role` 必填，`query` 默认空文本（最大500字符），`topic` 默认空（不限），`difficulty` 默认easy，`top_k` 默认5、范围1到20；不接受岗位ID、题目ID、用户ID或练习会话。响应包含 `is_demo=true`、`dataset=text-retrieval-demo-v1`、`count`、`results`，每个结果也标记 `is_demo=true`，其余字段沿用 RankedQuestion。题目ID只能在本演示材料中追溯，不能用于正式会话下发。页面不再显示未实现的手工会话ID和作答按钮，原正式API仍保留501。生产组装保持五个服务，演示由现有 InterviewRagService 的独立 demo_retrieve 操作调用。


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
