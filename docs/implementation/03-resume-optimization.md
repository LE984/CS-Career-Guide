# 成员3：简历 NLP 与有依据的建议

先读 [公共约定](00-shared-contracts.md) 与 [当前方案](../career_platform_plan.md)。已有简历CRUD、只读观览；准备阶段增加 edit_revision、分析/应用回执表、路由及页面。当前分析/确认应用业务501，尚无事实校验或乐观并发应用实现。

## 修改边界与目标

负责 `backend/career_platform/resume/`、`views/resume.py`、`models/resume.py`、`backend/resumes/`、Resume.vue；公共契约/序列化器/组装/迁移集成人审核。不得改自由面试主链路、另建简历表、客户端指定owner、自动将建议覆盖原稿。首版不做文件OCR、自动补经历、自动投递。

## Facade、Strategy 和 Adapter

`ResumeAnalysisService` 是Facade，只提供 analyze/list_runs/get_run/apply。文本匹配Strategy处理JD技能抽取、分段和证据匹配；ModelGateway Adapter隔离供应商与超时；repository读取/保存快照和回执。Vue只处理输入、原文/建议/理由/证据展示和逐条选择，不拼模型请求；Django视图只鉴权和校验。

## 分析与应用流程

| 动作 | 输入、步骤、输出和保存 | 异常与不变量 |
| --- | --- | --- |
| analyze | jd_text、可选job_id、resume_revision、request_id→读取当前用户Resume及子项→检查版本→快照→JD抽取→分段匹配→模型建议→结构/事实校验→保存ResumeAnalysisRun | 无简历404；版本409；超时/无效输出失败且原稿不变，不保存假成功 |
| list/get | 当前用户过滤→分页或UUID详情→返回原快照/匹配/缺项/建议 | 其他账号/不存在404；不得回查新简历替代历史 |
| apply | analysis ID、base_revision、accepted_suggestion_ids、request_id→权限/建议归属→锁Resume→版本检查→仅已接受字段写回→版本递增→回执 | 未接受项不变；旧版本409且零写入；同键复用首次结果 |

建议结构按00，字段位置可用 `skills` 或 `projects.<当前归属子记录ID>.description`，必须使用字段白名单、归属检查和原文比对，禁止任意 setattr 或用户/主键路径。证据必须来自本次resume_snapshot或jd_text，quote须确实存在；JD只能支持“岗位要求/缺项”，不能据此写成用户已有技能。无用户事实依据的技能、职责、成果数字必须拒绝或改为待补充问题，不允许以LLM自检取代规则验证。

示例：原文“使用Java完成课程项目”，JD要求Redis；可以建议清晰说明已有Java项目职责，并将Redis列入 gaps，不能改成“使用Redis将性能提升50%”。分析输出包含该原文片段和字段位置，拒绝建议后数据库完全不变。

用户编辑建议通过 apply.suggestion_edits 提交，格式为建议UUID到编辑文本字典，默认空。只允许编辑本次已接受建议，服务端必须重新校验字段、原文及事实依据，再原子应用。不能只在界面编辑却保存旧建议。

版本方案：模型调用在锁外，对成功分析保留base_revision；应用时事务select_for_update读取当前简历。Resume.save已经维护主表更新版本，成员须覆盖所有子表修改入口及禁止绕过版本的bulk写。并发两次应用只有一个成功；另一个409；相同request_id返回同回执，不重复递增。模型失败与重试保留前端输入，重试必须由用户明确触发。

## 接入与分步验收

构造器注入 matcher/model_gateway/repository；测试模型分别返回有依据建议、虚构数字、非法字段、超时，repository使用隔离ORM或确定性替身。生产不能默认返回固定建议。成员1提供岗位快照，成员2经公开匹配接口评估，不复制分段算法。

| 步骤 | 实施与观察 | 固定验收 |
| --- | --- | --- |
| 1 | JD抽取/简历分段/证据纯函数 | 引文能定位原文；缺项不转成事实 |
| 2 | 完整分析Facade | 成功保存快照、版本和模型/提示词版本；超时/非法输出不改原稿 |
| 3 | 原文、建议、理由、证据与选择/编辑页面 | 拒绝不保存；编辑内容必须实际经过服务端校验和应用 |
| 4 | 应用事务/幂等/版本/所有入口维护 | 旧版409、新版原文保留；并发不覆盖；他人分析404 |
| 5 | 历史分析列表/详情 | 更新简历后旧分析快照仍可还原 |

运行 `python ci/project_acceptance.py --stage complete --module resume`，补跑既有简历/登录回归及前端测试/构建。测试需比较原稿和子项、version、回执数量，不能只检查文本看起来合理。

## 验收记录

| 提交号 | 执行命令 | 结果 | 环境 | 模拟/真实范围 | 已知限制 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| d12128b + dirty | 待执行resume complete | 未实现 | 隔离SQLite | 无真实模型 | 501，编辑字段已预留 | output/ |

## 文档更新与 PR 检查表

| 变更 | 同步文档 |
| --- | --- |
| 字段路径/建议校验/版本更新方式 | 本文及00，列全现有写入口 |
| 匹配策略/模型提示词 | 本文及02，记录版本和证据限制 |
| 验收完成 | 上表实际执行证据，独立写真实模型范围 |

- [ ] 事实不编造、权限、版本、幂等、事务及超时/非法输出用例通过。
- [ ] 编辑确认后写入的是已展示/确认内容；拒绝时原稿不变。
- [ ] 原有简历CRUD/观览不回归，秘密不进入前端。
- [ ] 实现、固定测试、本说明及必要公共约定同PR更新。


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

本次调整既有简历页面及面试简历观览的交互和样式，公共导航变更要求同步本模块记录。新的 JD 对照分析、建议证据、人工确认与幂等应用服务仍未实现，不将原简历 CRUD 的回归通过计为 resume complete。

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
