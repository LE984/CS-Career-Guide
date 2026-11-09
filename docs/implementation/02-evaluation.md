# 成员2：评估与参数调优

依照 [当前方案](../career_platform_plan.md) 和 [公共约定](00-shared-contracts.md)。已有职业评估页面不能视为本模块完成；目前 EvaluationRun、staff路由和页面可启动，评估执行/查询/导出均501。

## 目标、目录和不做范围

负责 `backend/career_platform/evaluation/`、`views/evaluation.py`、`models/evaluation.py` 和 Evaluation.vue。公共 contracts/serializers/composition、固定测试和迁移由集成人审核。不复制成员1/3/4排序算法，不做预设指标、挑掉失败样本、自动上线参数或“保证提升”。

## Strategy 设计与处理流程

`EvaluationService` 负责载入版本化评估集、校验任务与参数、执行策略、计算指标及保存；`JobEvaluationStrategy`、`ResumeEvaluationStrategy`、`QuestionEvaluationStrategy` 分别调用其他成员公开服务；指标函数只接受排名ID和真实相关ID；repository保存 EvaluationRun。模型输出人工质量检查单独记录，不能混成排名指标。

输入 `{task,dataset_version,strategy,parameters,request_id}`，默认 parameters.k=5。流程：校验staff→读取不可变数据集/拆分清单→解析参数白名单→调用策略→保存逐例预测及判断→聚合指标→原子保存结果。结果携带dataset_version、策略/模型版本、参数、UTC时间、样本数、逐例结果和失败数。GET列表/详情/JSON导出读取同一记录，不能导出时重新跑模型。

未注册数据集/策略或非法K返回400且零成功记录；依赖不可用时明确失败，不能以空预测冒充有效基线。可复现离线策略相同输入必须相同；真实LLM需记录温度/种子支持情况和非确定性限制，不能声称逐字可复现。记录ID属于创建管理员，另一个管理员读取返回404。

## 固定指标与样例

2026-11-09 已提供可独立调用的纯内存 `TextRetrievalStrategy`，输入候选字典、查询条件与 Top-K，输出 `RankedQuestion[]`。默认题干/标签/参考要点/参考答案权重为 `4/3/2/1`，`min_score=0` 且非空查询零匹配必定排除；参数、分词与调用方式见[成员4文本基线说明](04-interview-rag.md#2026-11-09-纯内存文本检索基线)。当前仅完成算法单元测试，虚构测试题不是正式评估集；尚未接入 EvaluationService，也没有正式相关性指标或调优效果结论。

设K=5、相关集合R、去重后的前K预测P；Precision@K=命中数/K（不足K的空位算未命中），Recall@K=命中数/|R|，F1为前两者调和均值，HitRate@K为该query是否命中，MRR为首个相关结果名次倒数（无命中0）。逐query宏平均；R为空的样本作为无关检测组单列，不与正常相关样本分母混算。重复ID不能重复计分。非法未知ID记无关并保留诊断。

```json
{"query_id":"java-test-001","query":"Java集合随机访问","relevant_ids":["q-arraylist"],"predicted_ids":["q-arraylist","q-sql","q-jvm","q-spring","q-lock"],"expected":{"precision_at_k":0.2,"recall_at_k":1.0,"f1_at_k":0.3333333333333333,"hit_rate_at_k":1.0,"mrr":1.0}}
```

只在测试中注入固定排序策略或失败策略；生产从公开服务取真实排序。fixtures/evaluation.json 是契约样例，当前主题相似的dev/test不构成正式独立评估集。成员2须冻结不同query/目标集合的开发集、调参集、最终测试集与哈希清单，人工核对Java基础、集合/JVM、Spring、数据库、并发相关性。最终集不进入提示词示例、特征挑选和调参。

## 开发与验收

| 步骤 | 实施 | 预期/失败条件 |
| --- | --- | --- |
| 1 | 指标纯函数和冻结数据集清单 | 上例精确匹配容差；全错、空预测、重复结果和首名/后位命中正确 |
| 2 | 三类Strategy和可注入依赖 | 调用公开接口；未注册任务失败；禁止复制RAG实现 |
| 3 | 运行/查询/导出及request_id去重 | 同请求复用ID；不同输入同键409；普通账号全组403；跨管理员404 |
| 4 | 基线加一组单变量对照 | Top-K、阈值、特征、提示词每次只改一种；保留全部失败和退化用例 |
| 5 | 页面逐例/参数/版本/对照/导出 | 无结果显示空态、失败明确，不能填固定漂亮图表 |

运行 `python ci/project_acceptance.py --stage complete --module evaluation`，前端测试和构建见00。人工生成质量表逐例检查：事实依据、岗位相关、无关结果、来源、偏差及可理解性，记录审阅人、标准和结论。实验无提升仍可通过诚实可复现验收；测试不以“指标超过某个漂亮阈值”强迫筛数据。

## 验收记录

| 提交号 | 执行命令 | 结果 | 环境 | 模拟/真实范围 | 已知限制 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| d12128b + dirty | 待执行evaluation complete | 未实现 | 本地隔离 | 未运行真实评估 | 501，正式数据集未冻结 | output/ |

## 文档更新与 PR 检查表

| 变更 | 同步内容 |
| --- | --- |
| 数据集/指标/拆分/参数 | 本文、版本清单、逐例结果及对照报告 |
| 调用方字段/策略接口 | 00和对应01/03/04，由集成人审核 |
| 验收完成 | 实际提交、命令、环境、模拟/真实范围、失败及证据 |

- [ ] 指标边界、权限、幂等、复现、无关检测固定验收通过。
- [ ] 最终集与调参材料分离，基线与单变量对照均保留。
- [ ] 没有丢弃失败用例或把确定性替身当真实模型质量。
- [ ] 实现、测试、本文、数据集版本及报告同PR提交。


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

本次调整既有职业评估页面及 career_evaluation 接口，同时涉及公共导航。新的 career-platform 评估数据集、指标计算、策略对照和导出服务没有实现；既有职业评估界面可用不能作为 evaluation complete 成功证据。

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
