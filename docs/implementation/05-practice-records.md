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
