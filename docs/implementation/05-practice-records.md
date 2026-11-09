# 成员5：练习记录、结束总结与历史

先读 [公共约定](00-shared-contracts.md) 与 [当前方案](../career_platform_plan.md)。已有legacy复盘表不包含本期逐题契约。当前新PracticeSession/AnswerRecord受管理模型、唯一约束、路由及历史页面骨架已建，所有业务仍501。

## 目标、目录与不做范围

负责 `backend/career_platform/records/`、`views/records.py`、`models/practice.py`、Records.vue。向成员4提供唯一PracticeStore持久化接口，不能各自保存一套。公共端口/迁移/前端共享文件和固定测试集成人审核。首版不做再答一次、同题比较、历史回填或替换legacy表。

## Repository/Adapter 与应用服务

`PracticeRepository` Adapter封装ORM、用户过滤、快照、唯一键和事务；`PracticeService`负责会话状态与结束总结；ModelGateway负责模型。成员4调用record_answer/record_feedback，不直接操作ORM。视图不拼总结提示词，页面不决定用户归属和状态合法性。

## 按操作实现

| 操作 | 输入→步骤→输出/保存 | 失败行为 |
| --- | --- | --- |
| start | role/job_id/jd_text/topic/difficulty/request_id→当前用户→读取岗位/简历→深拷贝快照→创建active会话 | 来源不存在404；同键同输入同ID；不同输入409 |
| record_answer | 会话、题目快照、真实回答、request_id→锁会话→检查active/题归属→AnswerRecord | 先保存后生成，模型失败不丢输入；已结束409 |
| record_feedback | 原AnswerRecord、已校验feedback/status→检查归属与允许状态→原记录更新 | 重试不新增回答；未经成员4证据校验不得成功保存 |
| list/get | user+分页/UUID→查询会话、回答及快照→时间/岗位列表和详情 | 越权404；读取历史不依赖原题、原岗位现值 |
| finish | request_id→锁会话→关闭作答入口、记ended_at→锁外总结→保存summary状态与内容 | 重复结束不再调用模型；失败原记录仍在，summary失败明确，允许明确重试 |

会话active→ended与summary pending/succeeded/failed独立；结束时先封闭回答，再调用模型，禁止网络请求持有长事务。finish_request_id保存首次结束键，summary_request_id保存当前总结尝试键。重复结束复用原结果；只有summary失败且retry_summary=true的新request_id才允许重试。相同尝试键不重复调用模型，并发尝试须用事务和原子状态保护。

快照至少保存岗位ID/标题/JD/来源、简历版本与当时内容、题干/参考要点/source/source_url/证据及检索参数；按实际需要最少化私人数据，不写凭据。来源后改/删除后历史仍完整，question/job外键SET_NULL后不影响快照。只读快照，不能从JSON字段反向修改当前题库或简历。

总结输入仅包含该用户该会话真实记录；输出strengths/gaps/next_steps纯文本，不能用固定评分或模板报告假装生成成功。回答或总结模型失败要可见状态和重试入口，不清空草稿或已有反馈。

## 成员4交接与替身

成员4调用 `record_answer(user=user,data={id:session_id,question_id,question_snapshot,answer,request_id})` 获得record ID；调用 `record_feedback(user=user,data={id:record_id,feedback,status,failure_code})`。这些是服务内契约，不是允许HTTP用户直接指定status/owner。具体返回字段和下发题快照关联由04/05一起审核固定后同步00，不能各选字段名。

测试repository可注入隔离ORM，模型替身记录调用及抛超时；生产默认不能固定返回总结。成员2经公开服务读取脱敏评估材料，不直接读取其他用户历史。

## 分步实施与验收

| 步骤 | 实施与可观察结果 | 固定验收 |
| --- | --- | --- |
| 1 | repository、岗位/简历/题目快照、答案保存 | 刷新可恢复；原题改动/删除不影响旧内容 |
| 2 | request_id/并发/状态事务 | 同键仅1条；不同payload409；结束后作答409 |
| 3 | 当前用户列表/详情和页面 | 不同账号404；稳定分页，真实空态/失败状态 |
| 4 | finish和总结失败/明确重试 | ended_at只设一次；重复结束不重复模型；失败仍有所有回答 |
| 5 | 成员4集成及端到端 | 检索、作答、反馈、结束、刷新历史一致，无平行历史表 |

运行 `python ci/project_acceptance.py --stage complete --module records`，最后 `--stage complete --module all`；前端测试/构建见00。用数据库数量、快照内容、时间、状态和模型Spy次数断言，不能只检查列表能打开。

## 验收记录

| 提交号 | 执行命令 | 结果 | 环境 | 模拟/真实范围 | 已知限制 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| d12128b + dirty | 待执行records complete | 未实现 | 隔离SQLite | 无真实总结 | 501，finish回执/重试字段已预留 | output/ |

## 文档更新与 PR 检查表

| 变更 | 同步 |
| --- | --- |
| 状态、幂等、快照、总结和重试行为 | 本文及00/04 |
| 字段/索引/迁移和记录接口 | 00及受影响成员，由集成人审核 |
| 验收完成 | 实际提交、命令、结果、环境、替身范围及证据 |

- [ ] 刷新、快照、用户隔离、并发幂等、结束拒答、失败保存固定用例通过。
- [ ] 总结失败没有固定报告，明确重试不会产生重复记录。
- [ ] 与成员4使用相同接口，端到端通过后再标记模块完成。
- [ ] 实现、测试、本文及验收证据同PR提交。


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

本次没有实现 career-platform 的练习记录业务，因公共导航变更仍需同步本模块记录。会话创建、逐题快照、幂等回答、结束总结和显式重试等固定用例仍失败，既有面试页面展示不能代表 records complete。

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
