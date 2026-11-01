# 模拟面试：保留现有实现，建立替换边界

本次将现有提示词驱动的模拟面试提取为 `legacy` 实现，保留现有页面、接口、数据表和模型连接配置。范围是结构重构；没有接入新模型、适配 Fun-ASR、调整并发/缓存/检索、部署服务器或消耗试用额度。

## 已有实现的真实路径

网页面试通过 `/api/ai/llm/chat/` 流式接口发起请求。页面从 `localStorage.resume` 拼接简历，构造开始、回答与复盘提示词。后端拼接历史、选择风格系统提示词，直接调用 `ChatOpenAI.stream`，并通过 SSE 返回文本、音频和 session ID。复盘通过 `/api/ai/interview/save_review/` 保存到 `InterviewReviewRecord`。

仓库另有 `create_interview_agent()` 和 LangGraph 面试节点，但它们不是这条网页主路径。本次没有把它们改成主实现，也没有将现有实现描述为完整的面试状态机。

## 边界与设计模式

```mermaid
flowchart TD
    Page[Vue 面试页面：状态、计时、录音和播放] --> Facade[InterviewService：统一操作入口]
    Facade --> Adapter[LegacyInterviewImplementation：现有请求与提示词]
    Adapter --> Decoder[SSE 协议适配]
    Adapter --> API[已有 HTTP API]
    API --> Shared[共享聊天视图：会话、模型流、TTS、存储]
    Shared --> Port[后端 InterviewService]
    Port --> Strategy[LegacyPromptInterview：现有提示词与复盘解析]
```

- **Facade（外观）**：前端页面只调用 `start`、`answer`、`generateReview`、`saveReview`、`transcribe`，不再拼提示词、解析网络流或决定后端请求参数。页面继续拥有 Vue 状态、倒计时和浏览器媒体资源。
- **Adapter（适配器）**：前端 legacy 实现将统一操作转换为旧接口和 SSE 协议。HTTP 方法以依赖注入方式传入，适配器不导入 Vue、DOM、具体 Axios 客户端或播放器。读取简历也以回调注入，测试可使用虚构数据。
- **Strategy（策略）**：后端以 `InterviewImplementation` Protocol 描述提示词准备和复盘解析，由 `LegacyPromptInterview` 实现。HTTP 层依赖服务入口，不再内联面试风格和复盘文本解析规则。
- **单一组装点**：前端 `frontend/src/features/interview/index.js`、后端 `backend/ai_integration/interview/__init__.py` 选择现有实现。没有新增空的实现类、全局注册中心、运行时切换开关或未使用的 Repository 层。

## 前端操作契约

2026-10-26 交互修复：面试默认文字模式，模型流式回复期间可编辑草稿；Enter 发送、Shift+Enter 换行，中文输入法选词不触发发送。麦克风与播报独立控制；请求必须显式带 JSON 布尔值 `enable_tts: true` 且服务器允许 TTS 才调用语音合成，缺省或字符串值均按关闭处理。暂停面试会同时暂停播报、释放麦克风，继续时按此前状态恢复；单独暂停播报不会被后续音频块自动解除。关闭/暂停麦克风后丢弃未完成识别请求的迟到结果。结束/离开页面取消当前请求并清理媒体资源，音频能力不可用时仍可文字回答。

对话区提供放大/还原，放大后占用视口，Escape 还原并恢复焦点；面试及复盘要求模型输出纯文本，显示层去除旧内容的常见 Markdown 标记，复盘保存纯文本。全局浮动 AI 助手入口暂时从 App 移除，独立面试功能继续保留。上述变更不新增表或迁移，旧客户端未显式选择播报时也不会自动合成语音。

### 2026-10-26 面试工作区交互更新

- 面试默认 45 分钟，开始前可选 15、30、45、60 分钟；所选时长同时进入开场提示词、倒计时与复盘耗时计算。`start` 上下文增加 `durationMinutes`，`saveReview` 增加 `totalDurationSeconds`；旧保存调用省略总时长时继续按原 900 秒计算，页面始终显式传入。后端字段及数据库结构不变。
- 倒计时根据实际时间差计算，后台标签页被限速后仍能追上，暂停时间不计入面试耗时。普通视图与展开视图共用固定在对话顶部的控制栏，剩余时间、暂停和结束操作始终在该栏显示。
- 放大对话填满整个网页视口，移除原先的四周留白；保留 Escape 还原、焦点循环及恢复。桌面简历观览在对话右侧并排，手机在对话区域内切换；Escape 优先关闭简历，再还原对话。手机简历打开时，遮住的对话区域不可获取焦点。
- 简历观览打开时通过已有鉴权客户端调用 `GET /api/resumes/my/`，只读展示已保存的姓名、意向岗位、联系方式、自评、技能及教育/工作/项目/证书/获奖经历。面板内可刷新，关闭后再次打开重新读取；加载中、404/空简历、请求失败与重试分别显示。关闭或离开页面取消读取，不把本地缓存冒充服务器已保存内容，也不覆盖本地简历草稿。编辑链接在新页面打开，保存后返回面板刷新；接口失败不影响面试和回答草稿。内容以普通文本插值展示，不执行简历内 HTML 或链接。
- 面试与复盘文字使用独立的逐帧显示缓冲，按 Unicode 字素逐步呈现并加速消化大块回复；网络读取不等待动画，保存和上下文始终使用完整文本。减少动态效果、标签页隐藏或长时间丢帧时直接显示完整文字。该效果平滑已收到的文字，不缩短模型首字等待或填补尚未收到的内容。
- 自动跟随滚动按帧合并；用户向上翻阅后暂停跟随，发送下一条回答时回到底部。

本轮本地验证使用离线模拟响应，不调用真实模型。44 项前端测试与生产构建通过；本地浏览器验证了分帧吐字、45 分钟提示词、暂停计时、普通视图计时器可见、桌面/手机满视口、简历占位及草稿/焦点保留。CI、发布、部署与线上验收独立核对。

同日简历接口接入补充：45 项前端测试及生产构建通过；使用现有后端序列化字段的模拟响应，浏览器验证全部七类正文分区、带鉴权 GET、404/空简历、500 后重试、关闭重开后的旧响应丢弃，以及桌面/手机布局。HTML 与项目 URL 均作为普通文字显示；读取不覆盖本地缓存，编辑链接在新页面打开。本轮没有调用真实模型，也没有把模拟响应验证当作线上 API 验收。

上述为本地开发阶段证据。随后 PR #4/#5 已合并并随 `82f1293` 发布，真实线上简历保存/观览、45 分钟提示词、连续吐字、暂停计时和桌面/手机满视口验收通过，见[最新部署快照](deployment-status.md)。规划新需求时仍需区分：观览面板从服务器读取，面试首轮上下文仍沿用 `localStorage.resume`；JD 快照、题库检索、逐题证据反馈和训练历史关联尚不是当前 legacy 主链路的能力。

| 操作 | 输入 | 输出／副作用 |
| --- | --- | --- |
| `start(context, onEvent)` | `style`、`sessionId` | 流式面试事件 |
| `answer(context, onEvent)` | `answer`、`style`、`sessionId` | 流式面试事件 |
| `generateReview(context, onEvent)` | `messages`、`style`、`sessionId` | `{content, skipped}`，并发送流式事件 |
| `saveReview(context)` | 对话、报告、风格、会话、剩余时间 | 旧版保存结果 |
| `transcribe(formData)` | 音频表单 | 旧版识别结果 |

事件保留 `type` 以及相应的 `content`、`session_id`、`audio`、`message`。文本生成失败时继续交给页面显示错误，不以模拟内容冒充真实生成。复盘内容不足时返回 `skipped=true`，不调用模型。

SSE 读取集中到一个模块：支持 UTF-8 跨字节分块、CRLF、结束时剩余帧；`[DONE]` 后仍读取 session 事件，避免旧接口先发 DONE、再发 session 时丢失会话。去除了旧复盘循环重复解析未完成帧的路径，这是提取协议边界时的正确性修正。

## 后端契约与兼容范围

`prepare_turn(message, history, style, review=False)` 返回不可变的 `InterviewPrompt(system, user)`；`parse_review(content)` 返回原有的 strengths、weaknesses、suggestions、overall_score 字段。

保留四种风格、历史顺序、3000 字符截断、复盘标记提取及评分规则。旧实现的复盘仍使用 chat 系统提示词、在用户提示词前拼 review 提示词；本次不顺手改变这项行为。普通聊天与职业咨询不走面试策略。

共享聊天视图仍拥有 HTTP/SSE、ORM、模型流和 TTS 生命周期。本次抽出的后端策略只负责面试提示词与复盘解析，不能据此声称后端整条链路已经独立为完整面试引擎。后续重写会话编排或模型执行时，可以在保留前端操作契约的前提下增加专用接口和对应适配器。

最初的结构重构保留了 localStorage 简历、15 分钟计时、旧 session 回退规则及页面样式；2026-10-26 后续交互更新已将时长与工作区调整为上文行为。仍未新增数据库字段或迁移。

## 后续如何替换

1. 实现前端相同的五个操作与事件契约，可选择调用未来的专用面试接口。
2. 在前端组装点替换 `LegacyInterviewImplementation`，页面继续使用 `interviewService`。
3. 如果只调整后端提示词或复盘解析，实现后端 Protocol 并替换后端组装点即可；若重写会话编排，应另建应用服务，不把流程规则塞入旧共享聊天视图。
4. 将新实现套入相同的接口契约测试，再新增其业务行为测试。legacy 基准用来证明旧实现没有被无意改变，不要求新业务行为永远与旧提示词相同。

## 2026-10-26 ASR 协议补通

`/api/asr/speech-to-text/` 保留上传 `audio` 和成功返回 `result/text` 的契约，音频仍为 16 kHz PCM。
根据阿里云 [Fun-ASR 客户端事件](https://help.aliyun.com/en/model-studio/fun-asr-client-events)及[服务端事件](https://help.aliyun.com/en/model-studio/fun-asr-server-events)，识别结果从 `payload.output.sentence` 读取，只拼接最终句并忽略心跳；同时保留原 Gummy `transcription` 字段兼容。
Fun-ASR 请求不再发送旧协议的 `transcription_enabled`。启动失败、识别失败或连接提前结束均不能伪装为空文本成功；请求设 120 秒上限，失败时取消仍在发送的音频任务。

缺少音频返回 HTTP 400，服务失败返回 502，超时返回 504；响应不包含服务商原始错误或凭据。`backend/tests/test_asr.py` 使用假 WebSocket 离线验证上述协议、失败取消和响应脱敏，并纳入 CI。12 项本地测试通过；真实服务与浏览器麦克风验收分别记录，不能由离线测试推断。

2026-10-26 线上少量真实调用结果：面试 SSE 返回文字、14 个音频块和 session ID，复盘测试记录保存读取成功；CosyVoice 合成的短句通过实际 ASR 上传接口准确识别。对应发布、运行镜像及证据见 [部署状态](deployment-status.md)。公网浏览器录音仍待域名/HTTPS 与用户媒体权限验收，不据此宣称完整浏览器语音面试通过。

## 验证

2026-10-23 本地结果：前端 32 项、后端面试 6 项、原有鉴权 16 项测试通过，生产模式前端构建通过，模板/CSS 与重构前一致。代码已随 `33cbc57` 通过 build-only CI 的镜像和联调验证，并整合进 master；master 发布与真实模型/浏览器验收仍需分别核对，见 [运维接手记录](deployment-status.md)。

- `frontend/tests/fixtures/interview-legacy.json` 从重构前提交 `9837e71` 的实际页面函数捕获，使用虚构简历与对话。覆盖四种风格的开始、回答和复盘请求，共 12 组请求。
- 前端测试检查请求与旧基准一致、SSE 分块、音频事件、错误事件、session ID、复盘保存字段以及替换实现可通过同一服务运行。
- 后端测试以虚构提示词和模型响应执行实际聊天视图函数，检查惰性流式调用、SSE、历史记录保存及普通聊天/职业咨询不经过面试策略；不连接真实数据库或模型。
- 原有登录、路由、API 合同与配置测试仍应通过；构建只能验证工程可编译，不代表浏览器或真实模型验收。

```bash
node --test frontend/tests/auth.test.mjs frontend/tests/config.test.mjs frontend/tests/api-contract.test.mjs frontend/tests/interview.test.mjs
python -m unittest discover -s backend/tests -p 'test_interview.py' -v
cd backend
../.venv/Scripts/python.exe -m django test tests.test_auth --settings=tests.auth_settings
```

## 发布与业务验收

本次重构不增加服务、依赖或数据库字段，不需要专项数据迁移；镜像入口原有的 `manage.py migrate` 仍会执行，发布其他改动时应一并核对。无需为切换 legacy 新增环境变量，现有模型配置继续生效。前端和后端需构建发布包含对应代码的镜像，不能只改服务器 `.env`。

配置同步和容器健康通过后，再独立验收：登录进入面试、四种风格开始提问、文字回答与继续提问、session 连续、结束复盘、复盘保存及历史详情。真实模型验收会消耗账户额度，应在明确授权后执行并记录模型、时间和结果；离线基准不能代替回答质量验证。

ASR/TTS 和浏览器麦克风/播放权限另行验收。2026-10-26 已补 Fun-ASR 协议适配，真实调用结果见 [部署状态](deployment-status.md)；不能将最初的结构拆分或 TTS 开关传递写成浏览器语音面试已跑通。当前独立企业服务和本地向量模型的缺口也没有由最初的重构补齐。
