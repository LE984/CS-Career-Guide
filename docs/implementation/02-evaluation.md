# 成员2：评估与参数调优

依照 [当前方案](../career_platform_plan.md) 和 [公共约定](00-shared-contracts.md)。已有职业评估页面不能视为本模块完成；目前 EvaluationRun、staff路由和页面可启动，评估执行/查询/导出均501。

## 目标、目录和不做范围

负责 `backend/career_platform/evaluation/`、`views/evaluation.py`、`models/evaluation.py` 和 Evaluation.vue。公共 contracts/serializers/composition、固定测试和迁移由集成人审核。不复制成员1/3/4排序算法，不做预设指标、挑掉失败样本、自动上线参数或“保证提升”。

## Strategy 设计与处理流程

`EvaluationService` 负责载入版本化评估集、校验任务与参数、执行策略、计算指标及保存；`JobEvaluationStrategy`、`ResumeEvaluationStrategy`、`QuestionEvaluationStrategy` 分别调用其他成员公开服务；指标函数只接受排名ID和真实相关ID；repository保存 EvaluationRun。模型输出人工质量检查单独记录，不能混成排名指标。

输入 `{task,dataset_version,strategy,parameters,request_id}`，默认 parameters.k=5。流程：校验staff→读取不可变数据集/拆分清单→解析参数白名单→调用策略→保存逐例预测及判断→聚合指标→原子保存结果。结果携带dataset_version、策略/模型版本、参数、UTC时间、样本数、逐例结果和失败数。GET列表/详情/JSON导出读取同一记录，不能导出时重新跑模型。

未注册数据集/策略或非法K返回400且零成功记录；依赖不可用时明确失败，不能以空预测冒充有效基线。可复现离线策略相同输入必须相同；真实LLM需记录温度/种子支持情况和非确定性限制，不能声称逐字可复现。记录ID属于创建管理员，另一个管理员读取返回404。

## 固定指标与样例

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
