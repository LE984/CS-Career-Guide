# 成员1：岗位、企业和题库数据

先读 [公共约定](00-shared-contracts.md)。需求依据为 [当前方案](../career_platform_plan.md)，本文是实施任务，不是完成声明。当前数据业务均为501；已有 Company/Job 和兼容来源字段、InterviewQuestion 迁移、查询/导入路由及 Catalog 页面骨架。

## 目标、目录和边界

负责 `backend/career_platform/catalog/`、`views/catalog.py`、`models/catalog.py`、`backend/company_reviews/`、`frontend/src/views/career-platform/Catalog.vue`、`data/career-platform/`。公共序列化器、端口、组装、迁移须由集成人审核。不能新建平行岗位表、接 unmanaged company_info_backup、改成员4检索协议或绕过管理员权限。首版支持 JSON/人工整理，不做爬虫、外部实时招聘同步。

## 设计与逐项实现

采用 Adapter 隔离来源：`JsonSourceAdapter` 只将输入映射为规范记录；验证器负责字段/许可/可定位错误；CatalogService 编排固定流程；ORM repository 负责持久化；index_notifier 在事务提交后触发，不把索引调用放在行级循环中。无需为每种字段创建继承类。

| 功能 | 输入→处理→输出/保存 | 异常行为 |
| --- | --- | --- |
| 企业/岗位查询 | Query→过滤许可/有效期→关键词、城市、岗位条件→分页；读取 Company/Job | 非法分页400，无命中 results=[]；不依赖外部服务 |
| 题库查询 | role/topic/difficulty/q→AND约束→稳定排序→分页含source | pending/restricted不进入正式结果；不把空结果替换为假题 |
| JSON导入 | kind/records/dry_run→全量校验→清洗→dedupe_key→事务保存→提交后索引通知 | 返回行号、字段路径；任一非法记录整批400、零写入；索引失败记录可重试状态，不谎报检索已更新 |
| 来源展示 | 原始source/source_url/permission_status/collected_at/valid_until/is_demo→纯文本展示 | 缺审核信息保持pending；不能自动提升为allowed |

去重按“来源标识+来源内稳定ID”优先，人工材料按规范化题干/岗位和企业标识生成稳定摘要；不要用Python随机hash。重复导入返回原ID和 created/updated/unchanged 计数，不产生新行。dry_run 只报告预期影响，数据库和索引均不变。source_url 不是许可证明；团队创作写明作者/审阅者和创作说明。日期统一UTC。保留原始JD到description，旧requirements回退必须明确；skills 使用规范化字符串数组。

共享数据写权限要同时覆盖新导入、旧 CompanyViewSet 及任何直接写入口。不得只在前端隐藏按钮。目录结果中显示 is_demo，虚构岗位不冒充真实招聘。

## 交接样例与依赖

### 2026-11-10 records/rag 对目录数据的实际依赖

`b127df1` 未实现 CatalogService 的导入、查询或审核流程，catalog 固定验收仍失败；下列是共享组装/迁移变化对成员1的影响，不是目录模块完成声明：

- `DjangoQuestionRetriever` 直接读取托管 `InterviewQuestion` 的 allowed 数据，再复用 `TextRetrievalStrategy` 按 role/topic/difficulty 和 Top-K 排序；当前不调用 CatalogService，不读取 unmanaged `company_info_backup`，也未接 LanceDB 索引。
- start 可按 question_ids 读取正式题库并校验许可和筛选条件；有 retrieval_id 时固化缓存回执的有序题目、score、evidence 与检索条件。当前回执路径不会重新读取许可变化，成员1调整审核或撤销许可后的即时生效语义仍需集成补齐。
- Job 的 description 为空时回退 requirements；不存在岗位404，未 allowed 岗位400。检索/创建练习均不接受 job_id 与非空 jd_text 同传。
- `0003_practice_records_runtime` 只增加练习记录查询字段、题目唯一键、尝试日志和索引，不导入正式题库、不改变 Job/InterviewQuestion schema，不回填 legacy 面试历史。
- 历史详情读取练习快照；原题/岗位外键 SET_NULL 后仍保留当时内容。正式材料数量、来源审核和向量索引仍由成员1验收，测试 fixture 不算正式数据。

```json
{"kind":"questions","dry_run":true,"records":[{"role":"Java后端","category":"Java","topic":"集合","difficulty":"easy","question":"ArrayList适用什么场景","key_points":["随机访问"],"reference_answer":"基于数组，适合随机访问","source":"团队创作：成员1；审核记录见数据说明","permission_status":"pending","is_demo":true,"dedupe_key":"team-java-001"}]}
```

测试注入 source_adapter/index_notifier，通知替身记录调用次数，失败替身抛异常；生产默认不得指向它们。成员4只读取 allowed 题库并使用 `career_platform_questions_v1`；成员2消费同一目录接口，不复制清洗逻辑。正式演示至少30道人审题，Java基础、集合/JVM、Spring、数据库、并发均覆盖。当前空的 java-backend.json 及6道测试fixture不能算交付。

## 开发步骤与固定验收

| 顺序 | 实施与可观察结果 | 测试/失败条件 |
| --- | --- | --- |
| 1 | 规范化、来源校验、去重键纯函数；错误含records[行].字段 | 相同输入输出稳定；非法难度/空题干被拒 |
| 2 | 事务导入和dry_run，返回真实计数 | 同批/跨批重复不增行；第2行失败第1行不落库 |
| 3 | 查询、过滤、分页、旧写权限 | 仅allowed可查询；过期岗位不进入正式推荐；普通账号导入/旧PATCH均403 |
| 4 | 页面真实列表、筛选、来源/演示标记与管理员导入 | 空、加载、400、403、501、重试可区分；不使用硬编码成功 |
| 5 | 30题审阅材料与索引通知 | 提交失败不通知；成功提交才通知；来源缺审核无法正式索引 |

运行 `python ci/project_acceptance.py --stage complete --module catalog`；另跑完整前端测试及构建，命令见公共约定。验收必须断言实际ID、行数、字段与筛选集合，不能只断言HTTP 200。离线成功不等于真实招聘来源或真实Embedding已验收。

## 验收记录

| 提交号 | 执行命令 | 结果 | 环境 | 模拟/真实范围 | 已知限制 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| d12128b + dirty | 待执行模块complete | 未实现 | 隔离SQLite | fixture非正式题库 | 501，正式30题未交付 | output/ |

## 文档更新与 PR 检查表

| 变更 | 必须更新 |
| --- | --- |
| 来源/清洗/去重/数据版本 | 本文、data/career-platform数据说明和审阅记录 |
| 输出字段、权限或索引通知 | 本文、00、02及04，集成人审核 |
| 验收完成 | 上表填写实际提交、命令、范围、证据，列出未通过项 |

- [ ] 固定catalog用例、旧企业读写回归、页面及构建通过。
- [ ] 无秘密/真实私人材料；数据许可与30道人审题证据完整。
- [ ] 未修改固定期望/skip掩盖失败，公共变更有CODEOWNER审核。
- [ ] 提交实现、专项测试、本文和验收证据索引后提PR。


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

本次修改 backend/company_reviews/views.py 的既有企业/学长建议查询，并调整相关页面的分页、检索、排序与错误状态；该路径属于 catalog，需同步本记录。新 career-platform 目录导入、来源校验和题库查询服务仍未实现，既有页面回归不能替代 catalog complete。

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


### 2026-11-10 records/rag 对目录交接的同步验收

同步新增正式题库读取方、岗位JD回退、许可处理、练习快照与迁移边界；未实现或调整CatalogService导入/查询，不增加演示材料或自动提升许可。当前回执许可重验证和完整来源元数据仍有差距，不能以records专项通过代替目录交付。

```acceptance-record
{
  "commit": "b127df1 + dirty",
  "command": "python -m unittest discover -s ci -p 'test_project*.py' -v; python -m django test career_platform.tests.test_scaffold career_platform.tests.accept_records career_platform.tests.accept_rag career_platform.tests.test_records_runtime --settings=career_platform.test_settings --testrunner=career_platform.tests.runner.FixedAcceptanceRunner --verbosity=1; python ci/project_acceptance.py --stage complete --module all --output .runtime/docs-sync-20261110/all.json; python -m unittest discover -s backend/tests -p 'test_retrieval_demo.py' -v",
  "result": "failed",
  "environment": "2026-11-10；Windows；Python 3.12 / Django 4.2.7；隔离内存SQLite、Gateway Spy；文档门禁PyYAML位于忽略目录，不调用真实模型",
  "scope": "本轮完整all固定17项复核中，catalog4项均因501失败；evaluation/rag/records共9项通过，resume3项与integration1项失败。已更新成员1交接说明和结构化记录。",
  "limitations": "目录功能、30道人审材料和索引通知未完成；正式检索读取托管ORM不代表catalog API已完成。未改数据、导入器、schema或旧企业写权限；无MySQL、真实Embedding或生产验收。",
  "evidence": "ci/check_project_changes.py; ci/test_project_changes.py; backend/career_platform/tests/test_records_runtime.py; backend/tests/test_retrieval_demo.py; .runtime/docs-sync-20261110/all.json（本机忽略产物，可按命令复现）; GitHub Actions 42771897363 job状态查询"
}
```
