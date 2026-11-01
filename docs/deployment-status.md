# 演示部署验收状态与接手记录

## 2026-10-26 最新发布与业务基线：82f1293

这是本次已完成的发布验收快照，不代表后续实时状态。制定需求准备文档时，以最新 `origin/master` 及对应实现为代码基线；下文较早提交仅保留为历史证据。

- [PR #4](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/4) 的文字/音频解耦与控制修复、[PR #5](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/5) 的流式显示、可选时长、整页工作区和简历观览均已合入 master。最终提交 `82f12931de08e2cab71823d9e8c2b9aa6d2a6dec` 的 [Actions 40319566238](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/40319566238) 全部成功，包括双镜像验证、发布、AI 配置同步、容器重建和健康等待。
- 前后端运行 RepoDigests 与[成对发布记录](releases/2026-10-26-82f1293.json)一致；两个容器均 healthy，非 AI 配置摘要与此前基线相同，Watchtower 保持停止。默认演示数据库是 SQLite，保留 MySQL 配置不等于已切换 MySQL；新需求方案中的数据库和 RAG 目标需要另行设计、验收。
- 使用临时账号和虚构简历验证真实注册登录、空简历、简历保存及面板刷新，七类正文分区均显示。默认 45 分钟及对应模型提示词、暂停计时、桌面/手机满视口、回答草稿保留均通过。
- 本次 1 次真实模型请求返回 62 个文字块、0 个音频块，记录到 246 个不同可见文字长度阶段，最终页面文字与完整回复一致。此前 d04157a 上另行验证了真实 TTS 播放、暂停、继续和关闭；本次默认文字验收不等同于重新覆盖完整语音链路。
- 临时账号、虚构简历与测试会话已清理。职业路径、测评题、企业、招聘会及岗位列表再次核对为 HTTP 200、0 条数据；业务数据未导入，不能据此声称这些内容模块完整可用。
- 待完成：域名/HTTPS 和真实浏览器录音；完整职业报告、全部面试风格及多轮质量验收；真实数据导入、MySQL 切换和回滚恢复演练。当前网页面试仍是 legacy 适配器及共享流式接口，不是新方案中的题库 RAG、逐题评价和复练闭环。

## 2026-10-26 实时核验与补通

本节依据当天实际 GitHub 查询、SSH 检查及少量已授权真实模型请求；下文 2026-10-23 内容保留为历史记录。

- [Actions 40279477861](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/40279477861) 已验证、发布并完成真实 AI 环境同步、容器重建和健康等待。部署开关 `DEPLOY_ENV_SYNC_ENABLED=true`，旧 Watchtower 已停止，后续统一由 Actions 更新应用。
- 服务器 Compose 补齐 `CAREER_REPORT_MODEL`、ASR 三项和 TTS 四项映射；部署账号的私有镜像拉取成功。`.env` 的非 AI 行与备份逐字节比较一致，数据库、域名、资源和镜像选择未被同步覆盖。
- 自动同步只读取基础 Compose。首次重建曾丢失旧容器的 80 端口；已将服务器原有 80 和 48080 映射同时写入实际基础文件并重建前端，公网登录页恢复 HTTP 200。不要假设 override 或旧容器参数会自动继承。
- 操作前的配置、SQLite 在线一致性备份及容器身份位于服务器部署目录的 `backups/ai-connect-20261026T062229Z/`，权限限制在服务器内；不上传含密钥或用户数据的备份。
- 真实文本模型 `qwen3.8-flash` 和 `qwen3.7-plus` 均返回短文本；测试显式关闭思考模式并限制输出，初次 16 token 的思考模式测试没有得到正文，失败记录保留。
- 实际 Nginx/Django HTTP 链路的注册、登录、资料、简历保存读取均通过；面试 SSE 返回文本、14 个音频块和会话 ID，复盘保存及详情读取通过。复盘保存使用明确的合成测试记录，不能当作模型生成复盘质量验收；临时账号与测试会话已清理。
- [PR #2](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/2) 已通过完整 PR CI 并合并：补 Fun-ASR `sentence` 协议与失败处理，以及 `career_paths` 初始迁移。本地新增 12 项 ASR 和 1 项隔离真实迁移测试通过；前端 32 项、面试 6 项、配置 16 项、部署 7 项通过，CI 工具 36 项中 Windows 跳过 4 项 POSIX 检查。最终 master [Actions 40280652973](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/40280652973) 的全部验证、镜像发布、配置同步、重建和 release-summary 成功；代码提交为 `4fda51cef670ec33460e9d0db10dbb6e8b918dab`。
- 2026-10-26 14:50（Asia/Shanghai）复测：`career_paths` 路径和题目接口从 500 恢复为 200，目前返回空列表；注册、登录、资料、简历读写及当前页面使用的企业、招聘会、岗位列表接口均成功。`cosyvoice-v3-flash` 合成约 3.1 秒 PCM，再经真实上传接口 `/api/asr/speech-to-text/` 调用 `fun-asr-realtime`，准确返回“你好，这是面试语音测试。”；测试音频和临时账号均已清理。
- 前后端均 healthy，运行镜像的 RepoDigests 与本次成对发布记录一致。永久记录见 [2026-10-26-4fda51c.json](releases/2026-10-26-4fda51c.json)，不把容器 `.Image` 当作 Registry manifest digest。公网登录页 HTTP 200，旧 Watchtower 停止，非 AI 环境行再次核对为原样保留。

### 尚未完成的独立验收

- 职业路径、测评题库、岗位、招聘会、企业评价等当前数据库表为空，接口可用不代表已导入业务数据；不伪造招聘或测评数据。`company_info_backup` 属于未托管的外部数据表，当前缺失。旧 `/company-api` 返回 503，但该旧客户端没有被当前页面使用，不能把它等同于当前企业页面的所有接口都不可用。
- 未配置域名/HTTPS，用户已确认先完成后端服务。公网 HTTP 浏览器麦克风与完整语音页面未验收；后端音频成功不等于浏览器录音权限成功。
- 本地 Embedding 继续关闭并使用关键词降级；完整职业报告工作流、报告质量、全部面试风格和多轮时长未做真实模型全覆盖；没有 MySQL 切换、历史数据导入或回滚演练。

## 2026-10-23 历史快照

核对日期：2026-10-23（Asia/Shanghai）。Git/Actions/配置名称在本次文档维护时重新查询；服务器状态依据本会话前面实际 SSH 检查和账号配置结果，没有为更新文档重启或重新部署服务。区分本地实现、CI、发布、运行状态与业务验收。

## 当前主分支与个人开发分支

本会话先按 main 名称推送了三个提交，用户随后纠正：主分支继续使用 master。本轮将它们整合进 master，并从最终主分支建立长期个人分支 `codex/personal`，以后从该分支提 PR 到本 fork 的 master。`codex/ci-cd-images` 的全部提交已包含在 master，本地 `codex/sync-ai-env` 也没有额外提交，不需要重复 cherry-pick。已有 luochen 分支不改写。

代码提交 `33cbc57` 已通过 [Actions 39979362642](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39979362642)，publisher 和服务器同步按非 master 规则跳过。master 的后续完整验证与发布查看 [当前 Actions](https://github.com/vacontinuejatotired/CS-Career-Guide/actions?query=branch%3Amaster)，不能将 build-only 成功写成 master 镜像已发布。

下文的 `codex/sync-ai-env`、dirty tree、“未提交”以及旧 HEAD 描述保留为提交前的实施快照。当前代码已通过提交保留；未提交的课程资料、`.gitignore` 和 output 仍在工作区，不自动混入主分支。新的 Git/PR/commit 与文档更新规则见 [Git 规范](git-workflow.md)，导航入口见 [agent.md](../agent.md)。

仓库默认关闭 Watchtower、限制容器权限和资源、仅绑定回环地址，详见 [宿主机保护边界](host-protection.md)。服务器已有旧 Watchtower 运行，仓库 profile 不能自动停止它。以下首次发布记录仅作为历史证据。

## 提交前的代码与分支快照

- 仓库：`vacontinuejatotired/CS-Career-Guide`；只在此 fork 开发，不向 `ccccczhang/CS-Career-Guide` 提 PR。
- 本地分支：`codex/sync-ai-env`；HEAD 为 `9837e71ff1d86d7ecfb88f60c49702094a645a84`。工作区包含未提交的 AI 配置同步、Compose 映射、前端 TTS 构建参数、模拟面试重构和文档更新。
- 原有 `.gitignore` 修改、课程需求文档、Typst 文件和 `output/` 已保留，不属于此次部署实现的提交范围。后续应显式分组暂存，不能 `git add .`。
- 最新查询的 master [Actions 39897322500](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39897322500) 对应 `9837e71`，结果成功；该运行没有包含当前未提交改动。
- fork 内的 [PR #1](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/1) 已于 **2026-10-21 15:43:07（北京时间）** 合并到 fork 的 `master`；合并提交为 `c1d7b6ab0ff3c48d732fea55cb88899a33c77e9b`。
- `acad2c8`、`c1d7b6a`、`codex/ci-cd-images` 属于首次发布历史。旧文档的“工作区干净”“从未连接服务器”已不适用于本次快照。

## 2026-10-23 提交前实施状态（历史快照）

| 项目 | 已确认的状态 | 不能据此推断 |
| --- | --- | --- |
| 现有应用容器 | 本会话 SSH 查看时 backend/frontend healthy，旧 Watchtower 运行 | 未核对运行镜像 digest、全部宿主机限制或真实业务效果 |
| 专用部署账号 | `csdeploy` 密钥登录成功；密码锁定，无 sudo，有 Docker 组权限；目录及 `.env` 权限已配置 | Docker 组权限不是受限沙箱；未验证私有 ACR 拉取 |
| Actions 配置 | 三个模型 Secrets、六个 SSH Secrets、十个模型 Variables 已保存并核对名称；Variables 也核对了值 | GitHub 不可回读 Secret 值，不能宣称已验证模型 Key 有效 |
| 服务器 AI 配置 | `.env` 字段元数据检查显示三个 LLM 字段为空；完整 ASR/TTS 字段未配置 | Key 已存 GitHub 不代表运行中的容器已拿到 Key |
| AI 环境同步 | `ci/sync_runtime_env.py`、发布后 Job、白名单合并、健康等待已在本地实现 | 未提交、未推送、未触发新 CI、未同步服务器、未重建 |
| 自动同步开关 | `DEPLOY_ENV_SYNC_ENABLED` 尚不存在，因此关闭 | 不会因为保存 Secret 自动发布 |
| 面试重构 | legacy 适配器、服务契约、后端策略已实现；前端 32 项、面试 6 项、鉴权 16 项测试和前端构建通过 | 无真实模型调用、语音或浏览器全流程验收 |

同步脚本离线 CI 工具测试在 Linux 上 36 项通过，使用模拟 SSH/Compose；后续在 Windows 运行时，4 项 POSIX 测试按平台跳过。上述本地测试不能替代新提交的 Actions 镜像验证。

账号配置仅改变目标目录/`.env` 的所有权和权限，并安装专用公钥；环境文件内容未修改，应用未重启。服务器地址、端口和私钥不写入此文档，实际值由 `DEPLOY_*` Secrets 管理。

## 首次发布的 GitHub Actions 历史证据

| 运行 | 提交 / 事件 | 已确认的结果 |
| --- | --- | --- |
| [39540701547](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39540701547) | `3480b91` / 功能分支 push | 已成功完成；包含 SQLite 首次迁移的镜像冒烟，不再是运行中 |
| [39561641720](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39561641720) | `acad2c8` / 功能分支 push | 前后端测试、双镜像、真实联调、SQLite 持久化、待发布归档身份验证均通过；publisher 跳过 |
| [39562842520](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39562842520) | `acad2c8` / PR | 完整 build-only 验证通过；publisher 跳过 |
| [39563943035](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39563943035) | `acad2c8` / PR | 前后端测试通过；镜像与发布任务跳过，不能将这次绿色状态单独当作镜像验证证据 |
| [39563957000](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39563957000) | `c1d7b6a` / master push | 全部 7 个 Job 成功，包含独立 publisher；2026-10-21 16:01:29（北京时间）完成 |

master 运行的后端日志明确记录：

- 真实 Nginx/Django 注册、登录、鉴权拒绝、资料更新和共享静态文件验证通过。
- 删除并重新创建后端容器后，用户、原密码、原 Token 和资料标记均保留，SQLite 命名卷持久化验证通过。
- 两份待发布归档的提交、镜像 ID 与 `linux/amd64` 平台匹配；publisher 使用相同归档发布，没有重新构建。

## 首次 ACR 发布记录

来源为 master 运行的 `published-images-39563957000` Artifact，其中的 `published-images.json` 已核对：完整源码提交为 `c1d7b6ab0ff3c48d732fea55cb88899a33c77e9b`，`complete` 为 `true`，两个组件均记录了 `sha-c1d7b6a` 和 `latest`。

不含凭据的原始 JSON 已保存至 [2026-10-21-c1d7b6a.json](releases/2026-10-21-c1d7b6a.json)，保留镜像 ID、manifest digest、完整仓库引用和已推送标签，避免只依赖有保留期限的 Artifact。

| 组件 | 发布时的 manifest digest |
| --- | --- |
| backend | `sha256:a88b86560d20e879b3228f1373d0b33ec22a691fd083189d9f9fdb4dc680b8ec` |
| frontend | `sha256:0596c35212f18fd221aff79ad28a9bd998ca4fc2d528e38c36f6e5b3b1150b2f` |

这是该次发布的历史记录。此次没有登录 ACR 或查询当前标签；不能据此断言 `latest` 仍指向这些 digest，也不能证明演示服务器已拉取或启动镜像。

## 当前仍待验证

- `csdeploy` 的 ACR 登录/私有镜像拉取；服务器 Compose 补齐 AI 映射后的候选配置校验；新的自动同步、拉取和重建流程。
- 当前运行镜像与发布 digest 对应关系、运行时宿主机防护参数及浏览器业务交互。观察到 healthy 不等于这些项目均已验收。
- Watchtower 的每 30 秒轮询、带标签容器更新，以及成对 digest 回滚演练。
- 公网 HTTPS、真实 MySQL 运行与数据迁移、已有媒体迁移、付费 AI 功能。

已存在的基础容器运行与新增自动部署链路必须分开验收。不能再写“服务器完全未部署”，也不能据此宣称新配置已经上线或所有 AI 功能可用。

## 后续执行边界

2026-10-22 文档提交 `3289bec` 的 Actions 39706415076 等为历史记录。分支整合后的开发从 `codex/personal` 继续，保留工作区无关草稿，不能切回旧分支重做，也不能用旧镜像证据代替新配置验证。

后续接手仍先查 Git 与最新 Actions，避免依据本页快照重复修复。默认 MySQL settings 保持不变，SQLite 通过独立的 `settings_sqlite` 模块启用；Docker 构建和容器验证只允许在 Actions runner 执行。

本会话已明确授权并完成服务器部署账号创建和相关 Secrets 配置；后来工作范围调整为现有面试实现的结构重构，本次再补运维文档。没有执行应用重建、模型调用或数据迁移。后续提交、推送、发布和服务器操作按当时明确授权执行，不能将历史文档中的临时授权限制当作当前事实，也不能将账号创建授权扩展为任意服务器变更。

上线顺序：先整理并验证改动，再以部署账号验证 ACR，逐项补服务器 Compose 映射，协调停止旧 Watchtower，最后才启用同步并执行已获授权的发布。回滚前关闭同步开关；自动脚本不加载 digest override，见 [AI 环境同步](ai-env-sync.md) 与 [回滚手册](watchtower-rollback.md)。模拟面试实现与验收边界见 [重构说明](interview-refactor.md)。
