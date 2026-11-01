# 部署与运维总览

> 2026-10-26：已启用 Actions AI 配置同步，并通过一次真实发布、服务器配置同步、容器重建和健康等待；旧 Watchtower 已停止。文本模型及面试 SSE/TTS 已用少量真实请求验证；Fun-ASR 和职业路径数据库补丁已合并，最终版本与业务验收见 [当前状态](deployment-status.md)。日常开发仍使用 codex/personal。

2026-10-26 最新已验证发布为 `82f1293`，包含面试交互和真实简历观览；成对镜像、服务器及线上验收记录见[最新部署快照](deployment-status.md)。本页后续“当前功能分支”等表述来自最初实施阶段，不能代替该快照。需求与五人分工以[当前方案](career_platform_plan.md)为准，方案中的 MySQL/RAG 等目标不表示当前演示环境已经具备。

当前功能分支按“保护宿主机优先”收紧了容器权限、资源和日志上限，并将 Watchtower 改为显式启用。此改动不等于已更新服务器或已发布新镜像，见 [宿主机保护边界](host-protection.md)。

仓库默认行为与服务器既有状态需要分开看：profile 不会停止已运行的旧容器。2026-10-23 的账号配置没有重新部署应用，也没有停止旧 Watchtower。

## 发布链路

```text
功能分支 / PR
  -> 后端测试 + 前端测试 + 双镜像构建、联调、持久化验证
  -> 合入 master
  -> master 再次完整验证，独立 publisher 推送同一份已验收镜像
  -> 记录前后端 digest，再更新 ACR latest
  -> 服务器手动拉取并重建 backend / frontend 容器
     或：启用 AI 同步后，经 SSH 合并白名单配置、拉取并重建、等待健康检查
  -> 若选择 Watchtower 更新，应与 Actions 自动重建协调，不同时管理
```

默认演示环境使用 SQLite 持久卷，前后端各自一个镜像。正式数据阶段仍保留原 MySQL settings 和可选 Compose profile。

## 镜像坐标

```text
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-backend
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-frontend
```

两个镜像的 `latest` 是可变的演示版本入口，`sha-<7位提交>` 用于追踪源码但可以被覆盖。默认不启动 Watchtower。精确回滚使用一次完整发布记录中的前后端 `repository@sha256:<digest>` 引用，不能把 SHA tag 当作不可变保证。ACR 密码、Django `SECRET_KEY`、LLM key、数据库密码都不得写入仓库。

## 前置条件

1. 在 ACR `tencent-ubutun22` 命名空间下创建 `cs-career-guide-backend` 与 `cs-career-guide-frontend` 两个私有仓库。
2. 在 GitHub Actions Variables 或同名 Secrets 配置以下坐标；Variables 优先，现有 Secrets 可直接使用：
   - `ACR_REGISTRY=crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com`
   - `ACR_NAMESPACE=tencent-ubutun22`
3. 确认 Action Secrets 已有 `ALIYUN_ACR_USERNAME`、`ALIYUN_ACR_PASSWORD`。
4. 手动拉取前先登录 ACR；若单独启用 Watchtower，使用只包含本项目 ACR 登录的独立配置目录，不挂载宿主机通用 Docker 凭据目录。
5. 服务器独有配置保留在 `.env`；模型密钥保存在 Actions Secrets，并仅在启用同步后传入服务器。不得将真实环境文件提交或上传 Artifact。
6. 自动同步需要专用 `csdeploy` SSH Secrets、部署账号的 ACR 登录、服务器 AI 配置映射及显式启用开关，见 [AI 环境同步](ai-env-sync.md)。

## 文档索引

| 主题 | 文档 |
| --- | --- |
| 权限、资源、端口与剩余宿主机风险 | [宿主机保护边界](host-protection.md) |
| 已验证结果、发布记录与接手边界 | [验收状态与接手记录](deployment-status.md) |
| CI 触发、Job、变量与排障 | [CI/CD 流水线](ci-cd.md) |
| AI 配置白名单、专用账号、自动重建与失败处理 | [AI 环境同步](ai-env-sync.md) |
| 前后端镜像、依赖和构建上下文 | [Docker 镜像](docker-images.md) |
| 服务器登录 ACR、Compose、SQLite 与持久卷 | [服务器拉取部署](server-pull.md) |
| Watchtower 更新、SHA 回滚和故障排查 | [Watchtower 与回滚](watchtower-rollback.md) |
| 模拟面试 legacy 重构、接口兼容与发布验收 | [模拟面试重构](interview-refactor.md) |

环境变量基础规则仍见 [环境变量配置](environment.md)；统一登录行为和验证边界见 [统一登录门槛](authentication-gate.md)。

## 首次发布的历史证据与当前边界

- workflow、Dockerfile、Nginx、Compose 和 SQLite settings 已随 fork 的 PR #1 合入 `master`，合并提交为 `c1d7b6ab0ff3c48d732fea55cb88899a33c77e9b`。
- 功能分支 `acad2c8` 的 Actions 39561641720 已通过 build-only；master 的 Actions 39563957000 再次通过完整测试、双镜像冒烟、真实联调、SQLite 卷重建持久化和归档身份验证，并成功推送 ACR。
- 首次发布记录 `complete: true`，镜像标签为 `sha-c1d7b6a` 和 `latest`；成对 digest 记录已归档到 [发布记录 JSON](releases/2026-10-21-c1d7b6a.json)。这只能证明该次发布成功，不能证明标签此后未改变或服务器已拉取。
- 2026-10-22 在功能分支同步验收文档并补充宿主机保护配置；不再次合并、不发布镜像、不连接服务器或执行部署。新配置以对应提交的 Actions 为准，不复用历史发布的验收结论。
- 所有镜像构建路径均执行真实 Django/Nginx 注册登录、资料读写、SQLite 卷重建和待发布归档身份校验，使用 runner 临时数据；结果以对应提交的 Actions 为准。
- CI 不覆盖浏览器交互、私有 ACR 拉取、Watchtower 自动更新或真实服务器部署。
- 不包含生产数据库迁移、已有媒体迁移、真实 AI 付费调用或公网 HTTPS。

以上 `c1d7b6a` 等记录为首次发布历史。2026-10-23 的当前分支、账号、配置和未完成事项以 [当前验收状态](deployment-status.md) 为准；镜像发布、容器健康、真实模型成功和浏览器验收是不同状态。
