# 练习记录、结束总结与历史实施方案

状态：本地实现已按方案落地，待 MySQL、真实模型、远端 CI 与浏览器验收。

日期：2026-11-10。
依据：[公共约定](00-shared-contracts.md)、[成员5需求](05-practice-records.md)、[当前需求方案](../career_platform_plan.md)，以及现有模型、视图、服务骨架和固定验收。

## 1. 方案结论

成员5负责建立唯一的练习记录持久化边界：`PracticeSession` 保存会话和结束总结，`AnswerRecord` 保存真实回答和逐题反馈；成员4只能通过 `PracticeStore` 操作记录，不得直接写 ORM 或创建平行历史表。

实现采用以下原则：

- 先持久化真实输入，再调用模型；模型失败不得丢失回答或结束时间。
- 会话、回答、反馈和总结分别具有明确的状态与幂等尝试键。
- 模型调用不持有数据库长事务；事务只负责锁定、认领尝试和写回结果。
- 历史展示只读取保存时快照，不用当前岗位、简历或题库覆盖旧内容。
- HTTP 响应使用白名单，不返回参考答案、用户归属字段、私人简历字段、提示词或原始供应商异常。
- 现有固定验收只允许补充覆盖，不允许通过改断言、skip 或降低要求制造通过。

首版不做：再答一次、同题前后比较、legacy 历史回填、删除或导出历史、自动清理、跨用户后台查询、替换旧自由模拟面试链路。

## 2. 当前基线

当前仓库已经具备：

- `PracticeSession`、`AnswerRecord` 模型和两次初始迁移。
- `PracticeStore`、`ModelGateway` Protocol。
- `practice-sessions/`、详情、answers、finish 路由及严格输入序列化器。
- `Records.vue` 页面骨架和前端 API 方法。
- records、rag、integration 固定验收。

尚未具备：

- 可用的 Repository、PracticeService 状态机和生产 ModelGateway。
- 快照白名单、幂等冲突比较、并发尝试认领和历史分页查询。
- 逐题反馈失败的独立重试入口。
- Records 真实列表、详情和总结重试页面。

固定验收已经明确以下不可退让行为：

| 行为 | 必须满足 |
| --- | --- |
| 默认依赖 | `PracticeService(model_gateway=spy)` 不传 repository 也能工作 |
| 回答幂等 | 同一 answer 请求只生成一条 AnswerRecord、只调用一次模型 |
| 回答失败 | HTTP 为 502/503/504 之一，但 answer 已保存且记录状态为 failed |
| 未下发题 | answer 请求返回 400，不返回 404 |
| 结束幂等 | 同一或不同 request_id 的普通重复 finish 均返回原结果，不重复调用模型 |
| 总结失败 | 会话已经 ended，所有回答保留，只有显式 retry_summary 才可再尝试 |
| 用户隔离 | 越权和不存在的会话详情均返回 404 |

## 3. 分层与文件职责

调用链保持为：

`Practice.vue / Records.vue → REST View → InterviewRagService / PracticeService → PracticeRepository → ORM`。

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| `PracticeRepository` | ORM、用户过滤、行锁、唯一约束处理、快照构造、分页、尝试日志原子更新 | 模型调用、提示词、HTTP 文案 |
| `PracticeService` | 会话状态机、幂等判断、结束总结编排、公共输出白名单 | 直接拼散落 QuerySet、在事务中等待网络 |
| `InterviewRagService` | 反馈提示词、模型调用、反馈证据校验、调用 PracticeStore | 直接新建或更新 AnswerRecord |
| View/Serializer | 鉴权、严格字段校验、HTTP 状态映射 | owner、业务状态机、提示词 |
| Records 页面 | 历史列表、详情、总结状态和总结重试 | 提交新回答、推断 owner、伪造成功总结 |
| Practice 页面 | 正式检索、创建会话、提交回答、反馈失败重试 | 直接访问记录 ORM |

建议目录：

- `records/repository.py`：`DjangoPracticeRepository`、锁定写入、分页和快照。
- `records/service.py`：`PracticeService` 和结束总结编排。
- `records/sanitize.py`：快照、反馈和总结白名单；内容较少时可并入 service。
- `records/prompts.py`：总结输入和提示词版本，View 中不得拼提示词。

依赖装配：

- `PracticeService(repository=None, model_gateway=None)` 在 repository 为空时构造 `DjangoPracticeRepository()`，满足固定验收和独立使用。
- `composition.build_services()` 生产环境仍显式注入同一 Repository 和共享 ModelGateway，作为唯一生产组装点。
- 生产和开发组装不得导入 tests、测试向量或固定报告。

## 4. 正式业务链路

### 4.1 检索与会话创建

正式 UI 链路为：

1. 成员4调用 `questions/retrieve/`，获得有序题目、证据、相关度和一个用户绑定的 `retrieval_id`。
2. 前端选择题目后调用 `POST practice-sessions/`，提交 `retrieval_id`、有序 `question_ids` 及岗位条件。
3. records 在服务端解析 retrieval receipt，验证用户、过期时间、题目顺序和所选题目，然后把当时的 RankedQuestion 快照写入 `presented_questions`。
4. 会话创建后 `presented_questions` 只读；答题只能引用其中的 question_id。

`retrieval_id` 的推荐实现是 Django cache 中的短期回执，内容包括 user_id、检索 request_id、role/topic/difficulty/query/top_k、生成时间和有序 RankedQuestion；默认有效期建议 15 分钟。回执只用于在 retrieve 与 start 之间可信传递检索现场，不保存回答或长期历史。

为兼容固定验收和内部调用，start 可以只带 `question_ids`：此时 records 从正式题库构造快照，保存 `selection_mode=explicit_ids`，相关度 `score=null`，并保存 role/topic/difficulty 等选择参数。正式页面应优先使用 retrieval_id，不能把客户端提交的题目 JSON 当作可信快照。

首版要求至少一个 question_id。该要求需要在编码前同步 00/04/05 和 StartPractice 契约；未同步前不能把它当作既有事实。

### 4.2 回答与反馈

正式回答链路：

1. `InterviewRagService.answer` 调用 `record_answer`。
2. `record_answer` 在事务内保存真实回答，并原子认领首次反馈尝试。
3. 只有收到 `should_generate_feedback=true` 的调用方可以调用模型。
4. 模型成功或失败后，成员4调用 `record_feedback`，使用同一反馈尝试键写回 succeeded/failed。
5. HTTP 同一请求重放只返回当前记录，不再次调用模型。

反馈失败重试不能伪装成“再次回答”。推荐新增独立接口：

`POST practice-sessions/{session_id}/answers/{answer_id}/retry-feedback/`

输入仅包含新的 request_id。成员4通过 PracticeStore 原子认领新反馈尝试，继续使用原 question_snapshot 和原 answer；不创建新的 AnswerRecord。该 URL、Serializer 和 Protocol 属共享契约，必须由成员4、成员5和集成人共同确认后实施。

### 4.3 会话结束与总结

首次 finish 在事务内立即把会话改为 ended 并写 ended_at，然后认领总结尝试；事务提交后同步调用模型并写回结果。正常情况下 HTTP 返回最终 succeeded 或 failed，而不是把 pending 当作最终结果。

并发重放可能在首个模型调用尚未完成时读到 pending，此时只返回当前状态，不发起第二次模型调用。普通重复 finish 无论使用原 request_id 还是新 request_id，均返回当前已保存结果。

只有 `retry_summary=true` 才能认领新的总结尝试。允许的前置状态：

- summary failed；或
- summary pending 已超过“ModelGateway 硬超时 + 安全余量”。认领前先把旧 pending 尝试原子标记为 `SUMMARY_ATTEMPT_EXPIRED`，再创建新尝试，避免两个尝试同时被视为有效。

超时阈值必须来自共享模型配置，不在业务代码中硬编码 300 秒。迟到结果只有在 request_id 仍是当前尝试时才能写回。

空会话允许结束，但不调用模型、不生成模板总结；保存为 ended，summary 为 failed、failure_code=`NO_ANSWERS`、三个结果列表为空。对该状态重复 retry_summary 仍返回原结果，避免无意义模型调用。

## 5. 数据模型与迁移

继续使用唯一的 `PracticeSession` 和 `AnswerRecord`，不新增平行历史表。

### 5.1 PracticeSession

新增用于可移植查询和总结尝试的字段：

| 字段 | 用途 |
| --- | --- |
| `role` | 列表展示和 role 筛选 |
| `topic` | 列表展示和 topic 筛选 |
| `difficulty` | 列表展示和 difficulty 筛选 |
| `job_title` | 列表展示和 q 搜索，避免查询 JSON |
| `summary_started_at` | 当前总结尝试开始时间 |
| `summary_attempt_log` | 有界 JSON 列表，记录已使用 request_id、状态、时间和安全 failure_code |

保留 `finish_request_id` 作为首次结束键，`summary_request_id` 作为当前总结尝试键。`summary` 只保存当前结果：status、strengths、gaps、next_steps、failure_code、prompt_version；尝试次数由 attempt log 推导，不在 summary 中重复保存。

`status` 仅允许 active、ended。新会话直接为 active；ended_at 只写一次。

### 5.2 AnswerRecord

新增：

| 字段 | 用途 |
| --- | --- |
| `question_key` | 非空字符串，保存快照 question_id；题目外键删除后仍可唯一识别 |
| `feedback_request_id` | 当前反馈尝试键 |
| `feedback_started_at` | 当前反馈尝试开始时间 |
| `feedback_attempt_log` | 有界 JSON 列表，保存已使用尝试键和最终状态 |

状态仅允许 received、succeeded、failed。received 表示真实回答已保存且反馈尝试进行中；失败写安全 failure_code，不清空 answer 或已有合法反馈。

约束与索引：

- 保留 `(session, request_id)` 唯一约束。
- 新增 `(session, question_key)` 唯一约束，落实首版每题仅一条真实回答。
- 新增 AnswerRecord `(session, created_at)` 索引。
- 新增 PracticeSession `(user, created_at)` 及 `(user, role, topic, difficulty)` 索引；查询继续显式使用倒序，不依赖索引声明中的数据库特定语法。

### 5.3 正确迁移顺序

迁移不得先查询尚不存在的 question_key。顺序固定为：

1. 新增可空的 question_key、查询字段、attempt log 和时间字段。
2. 数据迁移回填 role/topic/difficulty/job_title 和 question_key。
3. question_key 优先取 question_snapshot.question_id，其次取 question 外键 ID；仍缺失时使用 `legacy:<answer_id>`，并记录审计数量。
4. 回填完成后只读检查 `(session, question_key)` 重复、空值和快照/外键不一致。
5. 无冲突后把 question_key 改为非空并添加唯一约束和索引。
6. 有存量冲突时停止约束步骤并输出审计结果，由集成人决定处理；成员5不得自行删除或合并用户数据。

本地 SQLite 与 Actions MySQL 都必须执行完整迁移和约束测试。

## 6. 快照与隐私

### 6.1 岗位快照

保存：id、title、company、description、requirements、skills、city、source、source_url、permission_status、collected_at、is_demo，以及 jd_source。

JD 规则：

- 仅 job_id：优先 description，空时回退 requirements。
- 仅 jd_text：使用用户输入并标记 jd_source=input。
- job_id 与 jd_text 同时提供：返回 400，避免不明确的覆盖关系。
- 两者均无：允许按 role 练习，jd_source=none。

不存在的 job 或 question 返回 404；存在但 permission_status 不是 allowed 返回 400。question_ids 重复或不属于 retrieval receipt 返回 400。

### 6.2 简历快照

保存练习需要的当时版本与内容：id、edit_revision、target_position、skills、self_evaluation，以及教育、经历、项目、证书和奖项的展示字段。

不保存：姓名、电话、邮箱、地址、头像文件、Token、凭据和与练习无关的账户字段。

### 6.3 题目快照

保存：question_id、question、key_points、evidence、source、source_url、permission_status、collected_at、role、topic、difficulty、origin、score 和 retrieval_context。

不把 reference_answer 写入 PracticeSession。逐题反馈以 key_points 和 evidence 为依据，减少参考答案泄露面。所有 HTTP 输出继续使用白名单，绝不直接返回原始 JSONField。

## 7. 幂等、并发和尝试日志

### 7.1 start 与 record_answer

start 使用 `(user, request_id)`，record_answer 使用 `(session, request_id)`。

命中同键后从已持久化输入字段重建规范化 payload：UUID 转字符串、字典键排序、列表保持业务顺序、排除服务器时间和状态。相同输入返回原记录，不同输入返回 409。

不单独保存 fingerprint 列，避免摘要与真实字段双源。数据库唯一约束仍是并发下的最终保护；捕获唯一冲突后重新读取并执行相同输入比较。

### 7.2 尝试日志

summary_attempt_log 和 feedback_attempt_log 保存每个已使用 request_id 的最小状态，不保存提示词或模型文本。每项只包含：request_id、status、started_at、completed_at、failure_code。

作用：

- 任意旧 request_id 在后续重放时仍能识别，不能因“当前 request_id 已改变”而再次调用模型。
- pending 尝试可在达到共享超时后明确转为 expired。
- 便于测试模型 Spy 次数和排查失败。

尝试日志上限由 `PRACTICE_MAX_MODEL_ATTEMPTS` 配置，默认 5；超过上限返回 409 并记录安全日志。pending 失效余量由 `PRACTICE_ATTEMPT_GRACE_SECONDS` 配置。

### 7.3 反馈认领

新 AnswerRecord 创建时：

- feedback_request_id 使用原 answer request_id。
- attempt log 追加 pending。
- 只有成功创建记录的事务返回 `should_generate_feedback=true`。

相同 answer 请求重放返回 `should_generate_feedback=false`，无论当前状态是 received、succeeded 还是 failed，都不能自动重复调用模型。显式重试只能走 retry-feedback 接口的新 request_id。

`record_feedback` 只允许写回当前 feedback_request_id；旧模型结果或迟到结果不覆盖新尝试。

### 7.4 总结认领

首次 finish：

- 锁会话并写 ended、ended_at、finish_request_id。
- summary_request_id 使用 finish request_id。
- attempt log 追加 pending。
- 事务外调用模型，完成后按当前 request_id 写回。

普通重复 finish 不新增 attempt。显式 retry_summary 使用新 request_id；若该键已在日志中，直接返回当前会话，不重复调用。

## 8. 操作行为

### 8.1 start

1. 校验 user、role、岗位/JD、topic、difficulty、question_ids、retrieval_id、request_id。
2. 读取当前用户简历并构造最小快照。
3. 解析 retrieval receipt；无 receipt 时从正式题库按 question_ids 构造显式选择快照。
4. 深拷贝岗位、简历、题目和检索上下文。
5. 事务内创建 active 会话；并发唯一冲突后读取并判断同键同输入。
6. 返回会话详情白名单。

### 8.2 record_answer / record_feedback

1. 按 user + session id 锁会话。
2. session 非 active 返回 409；question_id 未下发、answer 空或超长返回 400。
3. 从 presented_questions 取得规范快照；内部调用附带的 question_snapshot 只核对 question_id 与 question。
4. 原子创建 AnswerRecord 并认领首次反馈尝试。
5. 成员4仅在 should_generate_feedback=true 时调用模型。
6. feedback 成功前验证结构、answer_quote 是真实 answer 子串、evidence 来自 question_snapshot；失败则写 failed 和安全 failure_code。

### 8.3 list_sessions / get_session

列表：

- 只查询当前用户，默认 20、最大 100。
- 稳定按 created_at DESC、id DESC。
- 后端支持既有 Query 的 q、role、topic、difficulty；q 匹配 job_title 或 role。
- answer_count 使用 annotate 聚合，禁止逐行查询。
- 首版不提供 status 筛选，前端也不显示“仅过滤当前页”的伪筛选。

详情：

- 返回岗位、简历、题目快照，summary 和按 created_at ASC、id ASC 排列的 answers。
- 不存在与越权均 404。
- 所有时间为 UTC ISO8601；具体 `Z` 或 `+00:00` 表示由公共序列化约定统一，前端不得依赖某一种字面形式。

分页越界行为在阶段A与公共列表约定统一；未确认前不新增固定断言。

### 8.4 finish

1. 锁会话并执行首次结束、普通重放或显式重试认领。
2. 首次结束立即关闭答题入口。
3. 空会话直接写 NO_ANSWERS，不调用模型。
4. 非空会话在事务外调用 ModelGateway，只传该用户该会话的真实记录。
5. 成功结果必须是纯文本 strengths/gaps/next_steps；不能用固定评分或模板报告代替模型成功。
6. 失败保留 ended_at 和全部回答，summary.status=failed，并返回 HTTP 200 的会话结果；只有逐题反馈生成失败使用 502/503/504。

## 9. 最小响应与错误契约

以下是最小必需字段，允许后续以向后兼容方式增加字段，但删除或改名必须同步 00/04/05 和前端。

### 9.1 会话详情

- id、status、created_at、ended_at。
- role、topic、difficulty、filters。
- job_snapshot、resume_snapshot、presented_questions。
- summary：status、strengths、gaps、next_steps、failure_code、prompt_version。
- answers；start 成功时为空数组，detail 返回实际内容。

### 9.2 列表项

- id、status、created_at、ended_at。
- role、topic、difficulty、job_title。
- answer_count、summary_status。

### 9.3 回答项

- id、question_id、question_snapshot、answer。
- status、failure_code、feedback。
- created_at、updated_at。

公共响应不得出现 user、owner、request_id、attempt log、reference_answer、私人简历字段、提示词或原始异常。Service 内部返回的 `should_generate_feedback` 必须由 InterviewRagService 消费并从 HTTP 响应移除。

### 9.4 错误映射

| 场景 | HTTP | code |
| --- | --- | --- |
| 字段错误、未下发题、重复 question_ids、不允许的数据来源 | 400 | VALIDATION_ERROR |
| 未登录 | 401 | UNAUTHENTICATED |
| 资源不存在或不属于当前用户 | 404 | NOT_FOUND |
| 同键不同输入、结束后作答、同题二次回答、尝试次数超限 | 409 | CONFLICT |
| 逐题反馈模型输出非法 | 502 | INVALID_MODEL_OUTPUT |
| 逐题反馈模型不可用 | 503 | MODEL_UNAVAILABLE |
| 逐题反馈模型超时 | 504 | MODEL_TIMEOUT |
| 未实现 | 501 | FEATURE_NOT_IMPLEMENTED |

502/503/504 仅用于 answers/retry-feedback 的反馈生成失败，需要在共享 errors.py 和 api.py 中增加安全异常映射；响应不得包含供应商异常文本。finish 内部捕获同类异常并持久化 `summary.status=failed`，仍返回 HTTP 200 的会话结果。

## 10. 前端方案

### 10.1 Records 页面

Records 页面负责：

- 历史分页列表及 q/role/topic/difficulty 筛选。
- 通过 `?id=` 恢复选中的详情；Vue Router 原生保留 query，不为此单独修改路由表。
- 岗位、题目、真实回答、反馈证据和总结展示。
- summary pending/failed/succeeded 状态。
- summary failed 时显式生成新 request_id 并调用 retry_summary。
- feedback failed 时展示状态；若 retry-feedback 契约已通过，可提供重试按钮，否则只引导回 Practice 页面。

Records 页面不提交新回答，也不处理回答接口的 502/503/504 文案。

### 10.2 Practice 页面交接

成员4负责：

- retrieve 后保存 retrieval_id，并在 start 时一并提交。
- 回答接口 502/503/504 时提示“回答已保存，反馈生成失败”，刷新会话详情。
- retry-feedback 入口和反馈模型调用。

### 10.3 前端客户端

共享 `api.js` 需要：

- sessions 支持查询参数和 signal；修改签名时同步全部调用方和前端契约测试，不宣称旧调用方式自动兼容。
- session、answer、finish 支持独立 signal。
- 若契约通过，增加 retryFeedback 方法。

Records 模块使用独立 AbortController 和递增序号，切换筛选或详情时丢弃迟到响应。操作相关的 502/503/504 文案由页面按接口上下文处理，不放进无法区分回答与总结的全局 `platformFailure`。

所有模型文本以普通文本渲染，不使用 `v-html`。

## 11. 测试与验收

### 11.1 既有固定验收

保持 `accept_records.py`、`accept_rag.py`、`accept_integration.py` 已有断言不变。若需要覆盖新契约，由集成人新增测试，不修改既有行为预期。

### 11.2 后端新增覆盖

- start 同键同输入、同键不同输入、并发唯一冲突。
- retrieval receipt 的用户绑定、过期、题目子集和顺序校验。
- job/question 不存在 404，未 allowed、重复或未下发题 400。
- job、resume、question 修改或删除后历史快照不变。
- 同题新 request_id 返回 409。
- 回答创建者独占 should_generate_feedback；并发重放只调用一次模型。
- retry-feedback 复用原 AnswerRecord；旧 request_id 和迟到模型结果不能再次写入。
- finish 同键和不同键普通重放；失败显式重试；旧尝试重放不再次调用。
- pending 超时后先 expired 再认领，迟到结果不覆盖当前尝试。
- 空会话 NO_ANSWERS 且无模型调用。
- 不同用户 list/get/answer/finish/retry 均隔离；未登录 401。
- 列表稳定分页、查询数固定、无 N+1。
- 所有 HTTP 输出不含 reference_answer、attempt log、owner、私人简历字段或原始异常。
- SQLite 与 MySQL 的迁移、唯一约束和事务行为均通过。

### 11.3 前端新增覆盖

- 列表分页、筛选、空态、404 和网络失败。
- 切换详情后迟到响应不覆盖当前选择。
- summary pending/failed/succeeded 与 retry_summary request_id 行为。
- feedback failed 展示和已批准后的 retry-feedback 行为。
- 参考答案和私人字段不出现在 DOM。
- 320/390/820/1280px 无横向溢出，键盘焦点和状态提示可用。

### 11.4 执行顺序

1. `python ci/project_acceptance.py --stage complete --module records`
2. `python ci/project_acceptance.py --stage complete --module rag`
3. `python ci/project_acceptance.py --stage complete --module all`
4. `python -m unittest discover -s ci -p 'test_project*.py'`
5. `node --test frontend/tests/*.test.mjs`
6. `npm run build --prefix frontend`

离线替身、SQLite、MySQL、真实模型、浏览器和部署结果分别记录，不能互相替代。

## 12. 实施阶段

### 阶段A：契约确认

- 集成人确认生产 ModelGateway 的实现位置、超时和安全异常。
- 成员4/5确认 retrieval_id、question_ids 必填规则和 retry-feedback 路径。
- 同步 00/04/05、contracts、serializers、urls 和新增测试范围。

完成标志：本方案第13节的集成决策已落实到公共契约与配置。

### 阶段B：Repository、迁移与基础记录

- 按正确顺序完成字段、回填、审计、约束和索引迁移。
- 实现快照白名单、start、record_answer、list/get。
- 完成用户隔离、幂等、快照和查询数测试。

完成标志：刷新可恢复，原数据修改/删除不影响历史，无 N+1。

### 阶段C：总结状态机

- 实现首次结束、普通重放、显式重试、attempt log、超时失效和迟到结果保护。
- 完成空会话、模型失败和并发总结测试。

完成标志：ended_at 只写一次，重复结束不重复调用模型。

### 阶段D：成员4集成

- 接通 retrieve receipt、answer 的反馈认领、record_feedback 和 retry-feedback。
- 生产 composition 注入共享 ModelGateway 和同一 PracticeService。

完成标志：检索、创建会话、回答、反馈、结束和历史全部使用同一记录链路。

### 阶段E：Records 页面与完整验收

- 完成历史列表、详情、summary 重试和移动端状态。
- 运行 records、rag、all、前端测试和构建。
- 在 05 文档记录真实提交、环境、命令、替身/真实范围和证据。

## 13. 已采用的集成决策

| 项目 | 已采用结论 | 当前验证范围 |
| --- | --- | --- |
| 生产 ModelGateway | 新增共享 `JsonModelGateway`，records 与 rag 共用；读取既有 LLM 配置 | 仅完成配置接线和离线 Spy 验收，未调用真实模型 |
| retrieval receipt | retrieve 返回用户绑定的短期 retrieval_id，TTL 由 `PRACTICE_RETRIEVAL_TTL` 配置 | SQLite 离线回执、顺序和快照测试通过 |
| question_ids 必填 | 正式 start 至少一个 ID；可附 retrieval_id | 固定 integration 输入兼容，空列表由 Service 拒绝 |
| retry-feedback | 使用独立嵌套 URL 和原 AnswerRecord 尝试认领 | HTTP 失败后原记录重试测试通过 |
| 模型错误码 | 反馈使用 502/503/504；finish 持久化失败状态并返回 200 | 固定 records/rag 验收通过 |
| 尝试日志上限 | `PRACTICE_MAX_MODEL_ATTEMPTS` 默认 5，超限 409 | 配置与状态机已实现，真实并发仍待 MySQL 验收 |

## 14. 完成定义

只有同时满足以下条件才能将 records 标记为完成：

- Repository、PracticeService、InterviewRagService 和 ModelGateway 边界清晰，生产组装不引用测试实现。
- start、record_answer、record_feedback、retry-feedback、list/get、finish 均有成功、失败、幂等、并发和越权覆盖。
- 任意相同尝试键在后续重放时都不会再次调用模型。
- 历史在岗位、简历或题目修改/删除后仍完整；参考答案和私人字段不经 HTTP 泄露。
- 反馈失败保留原 AnswerRecord；总结失败保留 ended_at 和全部回答；迟到结果不能覆盖新尝试。
- Records 页面只展示真实数据和真实状态，不展示虚构成功内容。
- records、rag、all 固定验收、前端测试和构建通过；MySQL 迁移与约束通过。
- `05-practice-records.md` 更新实际验收证据，且实现、测试、迁移、契约与文档在同一 PR 中提交。
