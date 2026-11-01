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
