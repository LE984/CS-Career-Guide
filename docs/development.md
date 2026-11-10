# 开发指南

> 2026-11-01 交付拆分：以[单仓库独立交付](split-delivery.md)为当前操作入口；实际发布、服务器安装与自动部署开关见[带日期的状态记录](deployment-status.md)。历史证据不能代替当前运行状态。

先读根目录 [agent.md](../agent.md) 选择任务文档。主分支为 master，日常使用 codex/personal；分支和 PR 规则见 [Git 规范](git-workflow.md)。

## 代码定位

| 位置 | 当前职责 |
| --- | --- |
| `frontend/src/views/` | Vue 页面；模拟面试在 interview/Index.vue |
| `frontend/src/api/` | Axios/fetch、登录凭据与共享 API 入口 |
| `frontend/src/features/interview/` | 面试服务契约、legacy 适配器、SSE 解码及实现组装 |
| `frontend/src/config.js` | 公开前端配置与 URL/超时设置 |
| `backend/cs_career_guide/` | Django 配置、总路由、鉴权中间件及向量存储契约 |
| `backend/users/`、`resumes/` | 用户、资料和简历接口 |
| `backend/career_paths/`、`career_evaluation/`、`company_reviews/` | 职业路径、评估、企业相关业务 |
| `backend/ai_integration/` | 共享模型接口、会话/复盘记录、职业报告、检索和 LangGraph 实现 |
| `backend/ai_integration/interview/` | 网页面试当前使用的提示词策略与复盘解析 |
| `backend/asr/` | Fun-ASR 协议和真实短音频上传已验证；浏览器录音权限与完整语音流程另行验收 |
| `ci/`、`.github/workflows/` | 离线脚本测试、runner 联调、镜像发布及可选 AI 配置同步 |
| `deploy/` | Compose、部署配置样例与 digest override |

总路由在 backend/cs_career_guide/urls.py，前端路由在 frontend/src/router/index.js。新增接口前先核对两端实际路径与鉴权，不只按文件名判断实现是否被页面调用。

## 本地环境

后端使用 Python 3.11，前端/CI 使用 Node 24。遵循 [README 环境步骤](../README.md) 与 [配置说明](environment.md)，只复制 `.env.example` 创建自己的配置，不覆盖已有环境文件。真实秘密不入库。

低资源开发可使用 SQLite 演示配置 `cs_career_guide.settings_sqlite`，MySQL 是另一种显式选择。SQLite 不要求 MySQL 凭据；应用仍需有效 SECRET_KEY。嵌入模型关闭时走关键词检索，不下载或伪造向量。

前端开发代理目标由 DEV_* 配置；VITE_* 会进入浏览器。独立企业查询服务不由 Django 自动提供，默认生产 Nginx 对 company-api 返回 503；不要把前后端启动等同于全部功能可用。

backend/requirements.txt 保留现有 UTF-16 编码，CI 会转换临时副本；根 requirements.txt 为 pip 转发入口，不要顺手转码或升级依赖。镜像使用 backend/requirements-runtime.txt，缺少本地 Embedding 的可选重依赖是当前演示方案的一部分。

## 选择与改动相关的验证

纯文档检查链接和命令即可；业务/协议重构跑对应测试，公共鉴权、配置或 API 变化补相关回归。下面是可在仓库根目录运行的 Windows 命令，使用已有 `.venv`；测试均为隔离数据或虚构模型，不需要真实 Key。

```powershell
node --test frontend/tests/auth.test.mjs frontend/tests/config.test.mjs frontend/tests/api-contract.test.mjs frontend/tests/interview.test.mjs
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_interview.py
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_env_config.py
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_deploy_runtime.py
.\.venv\Scripts\python.exe -m unittest discover -s ci -p test_*.py
```

鉴权测试使用 Django runner，不要直接用普通 unittest discover 导入它：

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m django test tests.test_auth --settings=tests.auth_settings
Pop-Location
```

Linux/macOS 对应 Python 路径通常为 `.venv/bin/python`。ci/sync_runtime_env 的 POSIX 权限测试在 Windows 跳过、Linux 执行；跳过不能写成已验证 Linux 文件行为。

前端生产编译在 frontend 目录运行 `npm run build`；确认已有环境配置符合本次验证目的，输出写忽略目录。构建通过不能替代浏览器和模型验收。Docker 构建、真实容器冒烟、Nginx/Django 联调、SQLite 持久化在 Actions runner 验证，不为完成本地测试启动 Docker。

2026-10-26 补齐 `career_paths` 初始迁移，修复新部署只运行 `migrate` 时职业路径、题目和结果表没有创建的问题。新库按原流程执行 `migrate`；历史数据库若已手动建齐这三张表，先备份并核对模型与表结构，再使用 `migrate career_paths --fake-initial` 登记初始迁移，不能直接对部分存在或结构不一致的表使用 fake。本次迁移只建表，不导入题库、职业或招聘数据。`test_career_path_migrations.py` 在内存 SQLite 中执行真实迁移并验证三类记录读写与模型无漂移。

真实模型/语音、浏览器账号和服务器检查按实际授权执行，记录时间、环境、输入范围及结果；保留失败证据，不把模拟通过写成真实服务成功。相关接口与验收见 [面试重构](interview-refactor.md)。

## 五人课程模块开发准备（2026-10-28）

以下为初始骨架阶段说明。当前b127df1已有evaluation的question任务、records和正式RAG文本检索/反馈；catalog/resume仍是501。Records页面已接真实历史，Practice页面仍为独立只读演示，不能把旧段落“所有接口501”或“页面都有骨架标签”当作当前事实。最新操作行为见00/04/05实施文档。

2026-11-10在b127df1上的历史文档复核：隔离SQLite组合专项18项通过；完整all固定17项有8项失败，旧检索演示测试1项仍断言正式接口501。后续c117908已将该演示测试迁移为正式检索隔离断言；合入a4dc576后，应分别查阅04实施文档中的后续回归记录，不能把早期结果视为当前结果。修改后的文档门禁记录只使用passed/failed，并说明实际范围；共享contracts/composition/api/迁移等改动必须同步00至05全部六份文档。仅修改文档不代表业务或部署通过。

先读 [公共约定](implementation/00-shared-contracts.md) 和本人实施文档。新入口位于 `/career-platform/catalog`、`resume`、`practice`、`records`、`evaluation`；这些页面明确显示开发骨架，新业务有效请求返回501，不能据此演示业务已完成。默认自由面试保持原入口。

隔离命令 `python ci/project_acceptance.py --stage scaffold` 验证路由/鉴权/真实迁移和空实现；`--stage complete --module <catalog|evaluation|resume|rag|records|all>` 运行固定业务验收，当前空实现应失败。报告区分business_complete、commit、dirty、环境和real_model。工作树可复用原目录Python，不能误在个人目录执行开发。

服务端从应用服务实现，依赖通过 contracts.py 端口注入，唯一生产组装点 composition.py。测试替身仅在tests内。Company/Job来源字段默认pending，既有数据不会自动视为已审核；新增托管题库/分析/练习/评估表，简历增加edit_revision。迁移本地仅隔离SQLite，MySQL迁移/读写由Actions验证；本阶段不切线上数据库或导入服务器数据。

正式题库材料说明见 `data/career-platform/README.md`，fixture不是30道正式人审演示题。CI和审阅见 [CI/CD](ci-cd.md) 及公共约定，不能用修改状态标记跳过complete。

## 独立交付与客户端边界

前端/后端的构建入口分别为 `frontend/Dockerfile`、`backend/Dockerfile`，上下文各自限定在本目录；应用间通过现有 API/Token 协议通信。日常单端改动独立测试、发布和激活，公共契约或共享交付配置按[CI/CD](ci-cd.md)选择必要联调。App 客户端由其他成员负责，本轮不新增 App 页面、接口或鉴权协议；浏览器跨域的公开 API URL 与 CORS/CSRF 配置见[环境变量](environment.md)。

`Platform acceptance (sqlite/mysql)` 同时检验数据库迁移、契约与按变更范围选择的业务，并非只测数据库连接。2026-11-01 的五模块完整验收因 `501 / FEATURE_NOT_IMPLEMENTED` 失败，已发布服务与这一未完成业务分别记录。排查依据和哪些改动会阻止发布见[业务门禁](ci-cd.md#业务门禁)；不得删除固定测试或把完整联调的 skipped 写成通过。

## 前端极简视觉（2026-11-01）

- 全站使用暖白背景、深灰正文、低饱和绿色强调色和细边框；首页重排为首屏、核心模块、面试入口、平台优势与技术栈，原有素材文件保留，页面内容按已确认的局部调整更新。
- 公共视觉覆盖层位于 `frontend/src/assets/css/minimal-theme.css`，在 `career-theme.css` 后导入；Tailwind / DaisyUI 主色同步维护于 `frontend/tailwind.config.js`。新增页面优先复用 `career-container`、`career-button` 和已有工作台结构；传统页面通过 `minimal-page` 限定覆盖范围。
- 登录/注册表单补充显式标签关联与自动填充语义；导航、页面跳转、鉴权、简历保存/导出、legacy 面试接口及课程模块开发状态保持原约定。手机导航横向滚动，职业图谱底部操作栏可换行，减少动态效果设置继续生效。
- 本地验收使用隔离浏览器和模拟 API，检查桌面/手机布局、素材加载、页面入口、表单标签、岗位选择和面试工作区。执行现有前端测试与生产构建；浏览器模拟验证不代表真实模型、CI、发布或部署验收。
- 2026-11-01 初版本地结果：48 项既有前端测试通过；`node node_modules/vite/bin/vite.js build`（在 frontend 目录）通过。14 个页面在 1440px / 390px 下共 28 个视图无横向溢出、图片加载失败或运行时异常，另验证 820px 导航与 7 项交互。当时模板比对确认原文字、图片引用和 SVG 保留，图片及 public 资产文件没有改动。
- 2026-11-02 后续调整：首页主视觉改用新增的 `career-journey.svg`，旧图片文件保留；两段模块说明在桌面单行、手机换行，移除首页红黑榜的推荐/预警标签。职业路径卡片采用 16px 圆角，标题靠右并与图标中心对齐，说明标签使用默认光标，入口改为带无障碍名称的 SVG 箭头；恢复卡片上浮、图片缩放和灰度转彩色效果，并限制在支持悬停的设备、尊重减少动态效果设置。职业路径独立页脚删除，版权标语统一由公共 Footer 显示，年份随渲染时的设备日期更新。
- 2026-11-02 本地复核：48 项前端测试通过；首页、职业路径和公共页脚已检查桌面、平板及手机尺寸，另检查鼠标悬停、键盘跳转和减少动态效果。手机检查为浏览器模拟视口，不代表真机验收。
- 2026-11-02 个人自述页后续改版：`/career-paths/employment/self-introduction` 按基本信息与职业目标、技能评估、经历与偏好分区；桌面提示栏置于布局内部，手机技能分组默认折叠并提供底部操作栏。原 PNG、24 个技能值及提交字段保留，进度仅作提示，不新增必填约束。
- 主导航将“自我介绍”（`/career-paths/employment/self-introduction`）与“规划报告”（`/career-evaluation`）分为独立入口，分别高亮；`/career-plan` 仍归属规划报告。两个页面保持独立路由和组件，自我介绍提交成功后继续进入原测评流程。
- 个人自述草稿沿用浏览器 `selfIntroduction` 键，输入停顿 600ms 自动保存，也可手动保存；离开页面时刷新待保存内容。保存前核对当前登录凭据，退出或换账号后的延迟保存、返回结果不能重新写入个人资料。草稿保存失败显示提示，草稿不跨设备同步。
- 提交仍先更新 `/api/users/profile/`，再调用原职业推荐接口或复用 24 小时缓存。资料保存、推荐或结果存储失败时留在表单并显示错误；防止重复提交，兼容新旧推荐响应，缓存同时保留详细分析，避免带入上一次的分析与会话标识。
- 2026-11-02 性别选项调整：页面仅显示男、女，仍为选填；未选择时提交 `gender: null`，旧草稿中的“暂不填写”恢复为未选择。后端只接受男、女或 null，兼容旧客户端空字符串并存成 NULL，拒绝“暂不填写”等字符串。
- `users.0013_normalize_gender_choices` 将历史空字符串及“暂不填写”转换为 NULL，并增加数据库 CHECK 约束。已有男、女资料及其他个人字段不变；遇到其他历史值会停止迁移，需核对后处理。回滚约束不会重新制造被清理的占位值。本地 MySQL 已应用该迁移并确认占位记录为 0；服务器尚未应用，后续部署需按正常流程执行迁移。
- 性别调整验证：57 项前端测试、22 项用户字段与鉴权测试、1 项历史数据迁移测试通过，生产构建通过；浏览器模拟确认仅两个选项、旧草稿恢复、null/女提交与桌面/手机布局。后端测试使用内存 SQLite，实际本地 MySQL 仅应用授权迁移并只读核对约束，未以真实用户执行接口写入；MySQL 流程测试仍由 Actions 承担。
- 本次本地验证：56 项前端测试（含 8 项自述数据与草稿测试）通过，生产构建通过。隔离浏览器执行 33 项检查，覆盖 1440/1280/1024/820/390/320px 布局、章节定位、键盘操作、草稿恢复与退出清理、提交失败重试、缓存、新旧响应和结果存储失败。模拟 API 未调用真实模型，手机尺寸不代表真机验收；未提交、发布或部署本次改动。新增测试可运行 `node --test frontend/tests/self-introduction.test.mjs`。

### 职业方向选择页（2026-11-02）

- `/career-evaluation` 使用暖白与灰绿卡片布局，保留原图片素材和全部 62 个不同岗位名称；9 个领域支持搜索、筛选和折叠，手机推荐卡片可横向滑动，底部单选操作栏限制在页面内容内，不遮挡公共页脚。自我介绍页和规划报告入口仍是独立路由。
- 推荐及分析只展示浏览器中已有的测评结果，无结果时提示填写自我介绍，不再填充固定推荐、匹配分数或虚构背景。推荐卡片和岗位目录共用一个明确选择，沿用 `selectedCareers` 数组格式即时保存并在刷新后恢复；存储失败及退出/换账号会提示并阻止继续。生成报告须有自述资料和显式岗位选择，`/career-plan` 不再默认取第一项推荐。
- 数据适配位于 `frontend/src/features/career-paths/evaluation.js`，兼容新旧推荐字段、百分比字符串和缺失的分析字段；分析以转义文本和结构化列表呈现。现有接口、报告请求结构与缓存约定不变。
- 本地验证：68 项前端测试（含 11 项方向选择数据测试）、生产构建和 40 项隔离浏览器检查通过。覆盖 1440/1280/1024/820/390/320px，无横向溢出、图片加载失败或运行时异常；另验证选择恢复、搜索筛选、键盘焦点、页脚、异常存储、换账号保护及明确岗位的报告请求。浏览器使用模拟 API，未调用真实模型，手机视口不代表真机验收；本轮未提交、发布或部署。可运行 `node --test frontend/tests/evaluation.test.mjs`。

### 企业与职位页面（2026-11-02）

- `/company-reviews` 采用暖白、灰绿和细边框布局，职位、红榜、黑榜、安全指南与建议共用明确的栏目导航。榜单桌面用表格、手机用卡片；保留原有 50 条红榜、26 条黑榜的内容和顺序。岗位说明继续限制为两行，申请按钮链接到原招聘页面，不引入个性化推荐或按更新时间排序。
- 职位和建议仅请求当前页，支持每页 10/20/50 条；搜索停顿 350ms 后请求服务端，切换搜索、页码或栏目时取消旧请求并忽略过期响应。URL 的 `tab/q/page/size/sort` 保存栏目、搜索、分页与建议排序，刷新及后退可恢复；兼容职业路径入口的 `job_title` 搜索参数。页码按钮数量有上限，避免大量数据时渲染所有页码。
- `GET /api/career-evaluation/computer-careers/` 保留 `page/page_size` 及既有单字段筛选，新增 `search` 跨岗位、公司、地址、行业及说明搜索；按主键稳定排列，默认 10 条、接口上限 100 条。前端不再遍历所有分页后自行截取。数据库搜索目前沿用 `icontains` 和页码分页；超大规模全表模糊搜索及深页偏移的性能仍需在导入后的真实数据上评估，本次没有新增索引、全文检索或迁移。
- `GET /api/ai/senior-advice/` 按已审核记录分页，参数为 `page/page_size/search/ordering`，默认 10 条、上限 50 条；`search` 匹配公司或职位，`ordering=recent` 按提交时间倒序，`rating` 按评分倒序，均用时间/主键处理并列。响应保留 `success/count/results`，增加 `next/previous`；调用方需遵循分页，不能将 `results` 当作全部记录。接口实现移至 `ai_integration/senior_advice_views.py`，原 URL 与鉴权要求不变。
- 投稿的 `current_company`、`salary_info` 在前后端均为选填，省略或空字符串均可；公司、岗位、姓名、四位毕业年份、建议和 1–5 分评分必填。优缺点支持中文/英文逗号分隔，后端校验字符串列表。成功为 HTTP 201、顶层 `message`；校验失败为 HTTP 400、`errors` 字段错误；前端显示错误摘要与字段定位，并阻止重复点击，成功后隐藏表单。提交仍需审核，未更改数据库模型或审核流程。
- 职位、双选会、建议的数据库读取失败分别返回 HTTP 503 和 `JOBS_UNAVAILABLE/JOB_FAIRS_UNAVAILABLE/ADVICE_UNAVAILABLE`，投稿保存失败也返回对应 503；前端区分网络异常、超时、权限、无效页码、服务失败与真正的空结果，提供重试。响应不暴露数据库连接细节或堆栈，内部诊断留在服务端日志。
- 双选会仅调整展示和分页 UI，每页 6 条，未更改现有记录。地区资讯暂显示按城市搜索入口，未启用定位或高德服务。求职安全改为折叠主题、核实/留存/求助清单和官方来源链接；公共 Footer 未改动。SVG 图标、关联表单标签、栏目方向键/Home/End 导航、焦点与加载状态提供基础无障碍支持。
- 本地验证：78 项前端测试、32 项后端相关测试及生产构建通过。使用隔离内存 SQLite 和模拟浏览器 API：后端 1,205 条职位及 61 条已审核建议验证分页、全库搜索、查询条数、校验和错误响应；浏览器以 100,000 条职位、123 条建议验证按页请求、搜索、排序、刷新恢复、错误重试及模拟投稿。五个栏目在 320/390/820/1280px 下均无页面横向溢出，另检查 1440px 桌面、手机表单及键盘导航。浏览器模拟规模不等同于真实数据库压力测试，手机视口不代表真机验收；未写入模拟业务数据到本地 MySQL，未执行数据重抓、迁移、CI、发布或部署。

```powershell
node --test frontend/tests/company-browse.test.mjs frontend/tests/api-contract.test.mjs
Push-Location backend
python -m django test tests.test_company_browse tests.test_auth tests.test_user_gender --settings=tests.browse_settings
Pop-Location
```

### 简历、模拟面试与个人中心 UI（2026-11-02）

- `/resume` 延续暖白与灰绿风格，统一工具栏、卡片、表单和图标；增加七个章节导航，手机端可在编辑和实时预览之间切换，切换不丢失输入。表单标签、折叠状态及删除条目的无障碍名称补齐；姓名、经历、图片和现有 Markdown 内容继续进入原预览。简历保存字段、缓存、语音输入和 PDF 导出实现保持原逻辑。
- `/interview` 调整风格选择卡片、时长选择、对话工具栏、回答区与辅助提示；手机操作按钮分为两列。继续使用既有四种风格、时长、文字默认模式和 legacy 流式适配器，暂停/继续、全屏、简历观览、语音开关及复盘服务不变；未接入新面试引擎或真实模型测试。
- `/users` 分为账号资料、个人信息、复盘记录、简历摘要和下一步入口。复盘列表沿用原接口与顺序，在客户端每页展示 6 条；此次未新增后端分页参数。简历/复盘读取失败与空记录分开显示，详情支持加载和失败重试。资料编辑修正 `profile` 简介回填，保存时防止重复点击；推荐和旧自述缓存复用已有标准化函数。
- 三页共用线性 SVG；个人中心头像缺失或加载失败时显示 SVG 占位。资料与复盘弹窗使用 `WorkspaceDialog.vue` 的原生 `dialog`，支持滚动内容、键盘焦点循环、Escape 关闭与焦点恢复。公共导航与 Footer、数据库结构、后端接口及资产文件未在此轮改动。
- 本地验证：78 项前端测试及生产构建通过。三个页面在 320/390/820/1280px 下共 12 个视图无横向溢出或可见图片加载失败，另检查 1440px 桌面、手机预览、320px 弹窗、资料/简历模拟保存、记录分页与详情、错误/空状态，以及模拟面试开始、回答、暂停、全屏、手机简历观览与复盘。浏览器接口与账户资料均使用隔离模拟数据，未执行真实资料写入、真实模型、麦克风或新 PDF 文件导出；保存与导出原实现另经源码比对确认。手机视口不代表真机验收，此轮未运行 CI、推送或部署。

## 文档维护

修改功能时优先补对应文档中的行为、使用方法和验证，不扩写无关内容；新主题文档加入 agent.md 索引。配置、接口、迁移和部署变化的具体要求见 [文档更新表](git-workflow.md#开发时补多少文档)。历史接手记录提供线索，实际开发仍以当前代码和查询结果为准。
