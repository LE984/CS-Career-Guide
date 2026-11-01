# CI/CD 流水线

## 五人实施门禁（2026-10-28 新增）

主workflow通过可复用 `career-platform.yml` 调用 Platform gates。文档检查按Git基线差异运行 `ci/check_project_changes.py`，使用基线中的模块归属表防止PR自行删除映射逃避验收。成员代码需要对应实施文档，公共契约/固定测试/迁移/CI需要六份；文档须更新包含commit、command、result、environment、scope、limitations、evidence的 `acceptance-record` JSON块，仅改空白不通过。

首次基线没有归属表时识别bootstrap，只要求骨架通过，并实际验证五个complete均因501/FeatureNotImplemented失败；不会标记业务完成。后续由diff选择对应模块complete，公共改动运行全部模块及集成。SQLite/MySQL两个runner都执行真实迁移和读写；本机不跑Docker。测试依赖仅Django/DRF/Pillow/mysqlclient，不读取真实.env或调用模型。

文档检查状态 `Platform documentation`，自定义检查 `Platform acceptance (sqlite)` 和 `Platform acceptance (mysql)`；在UI中嵌套于Platform gates，保护规则设置前须查实际check-run名称，不猜字符串。主发布job依赖Platform gates，门禁失败不能发布新镜像。原登录/API/面试/ASR/配置/双镜像冒烟等回归继续保留，前端运行全部 `tests/*.test.mjs`。

保护规则仅在骨架PR合入且最新检查通过后设置：master必须PR、最新基线、至少1审核、CODEOWNER、必要检查、禁止强推/删除。CODEOWNERS已声明集成人；这份文件本身不代表GitHub保护已启用。管理员不能自审自己的PR，须其他账号参与。当前业务模块未实现，不能把骨架CI绿色写成MVP完成或真实模型验收。

发布后可选的 AI 配置同步与自动重建步骤见 [AI 环境同步](ai-env-sync.md)。该步骤默认关闭，需配置专用 SSH Secrets 并显式启用。

> 2026-10-23：新增同步 Job、面试测试及 TTS 构建参数已随 `33cbc57` 通过 [build-only Actions 39979362642](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39979362642)，并整合进主分支 master。个人开发分支统一为 codex/personal；master 的实际发布结果以对应最新运行记录为准。服务器账号已配置，AI 自动同步仍关闭。完整状态见 [接手记录](deployment-status.md)。

## 触发规则

| 事件 | 目标分支 | 测试 | 构建镜像 | 推送 ACR |
| --- | --- | --- | --- | --- |
| PR 到 `master` | 任意分支 | 是 | 有代码变更时，仅构建不推送 | 否 |
| push 到 `master`，有代码变更 | `master` | 是 | 是 | 是 |
| push 到 `master`，只有 README/docs | `master` | 是 | 否 | 否 |
| push 到其他分支 | 任意 ref | 是 | 有代码变更时，仅构建不推送 | 否 |
| `workflow_dispatch` 手动触发 | 任意选择的分支 | 是 | 是 | 仅 `master` |

纯文档判定只匹配 `README.md` 和 `docs/`。`.github/workflows/**`、`deploy/**`、Dockerfile 和 Nginx 配置都属于代码或部署配置，会触发镜像构建。

## Job 结构

```text
frontend-test --> frontend-image (归档) --|
backend-test ---------------------------+--> backend-image + 真实联调 (归档)
全部测试与镜像验证 ----------------------> publish (仅 fork/master)
publish 成功 + 显式启用 -----------------> sync-runtime-env（SSH / 合并 AI 配置 / 拉取 / 重建 / 等待健康）
验证、发布与同步结果 --------------------> release-summary
```

- **backend-test**：安装完整测试依赖，运行鉴权、配置、部署运行时、面试策略/接口、烟测脚本及发布脚本回归，并执行隔离 Django check。脚本测试使用合成数据和模拟 Docker/模型，不访问 Registry、服务器或真实 AI。
- **frontend-test**：使用 Node 24，执行 `npm ci`、鉴权/配置/API/面试契约测试、Vite 构建，并检查 `dist/index.html`、GLB 和 VAD ONNX。面试基准覆盖四种风格的 12 组旧版请求。
- **backend-image / frontend-image**：所有触发路径均使用 `push: false`、`load: true`，执行单镜像冒烟；master 也执行真实联调、SQLite 持久化和归档身份检查。验证 Job 不读取 Registry Secrets、不登录或推送 ACR。
- **publish**：只在 `vacontinuejatotired/CS-Career-Guide` 的 master 发布事件运行，等待前后端测试及两个镜像 Job 成功。下载本次运行的两份归档，核对完整提交 SHA、镜像 ID 和平台；直接推送已验证的同一份镜像，不重新构建。
- **sync-runtime-env**：仅在本 fork/master、非 PR、publish 成功且 Variable `DEPLOY_ENV_SYNC_ENABLED` 精确为 `true` 时运行。该 Job 才读取模型与 SSH Secrets；传输、合并及失败规则见 [AI 同步](ai-env-sync.md)。跨 ref 使用独立服务器并发组且不取消正在运行的同步，并在服务器加文件锁。
- **release-summary**：分别报告镜像发布与同步；同步启用但未成功时摘要失败，不能把“镜像发布成功、服务器激活失败”当作完整成功。

## 真实联调与持久化校验

所有镜像验证路径均在 Actions runner 执行 `ci/demo_smoke.py`，不在开发机运行 Docker：

1. 通过短期 Artifact 传递已通过前端冒烟的镜像和身份元数据，后端复用当前 Job 已加载的镜像，不重新构建、不拉取 ACR。
2. 使用 `deploy/docker-compose.yml` 加 `ci/docker-compose.smoke.yml`，指定唯一 `ci-demo-<run-id>-<attempt>` 项目，只启动真实 Django 和 Nginx。Watchtower 和 MySQL 均不启动。
3. 使用 `--env-file /dev/null`、虚构密钥和全新命名卷；只监听 runner 的 `127.0.0.1:18080`，关闭嵌入下载和 TTS，不调用 AI 接口。
4. 从 Nginx 入口检查 Vue 路由、后端收集的静态文件、未授权/无效 Token 的 401，以及注册、登录、资料读写。
5. 删除并重新创建后端容器，确认容器 ID 变化；使用原 Token 和原密码重新验证相同用户 ID、资料标记，确认 SQLite 卷持久化。
6. 成功或失败均采集容器日志并清理本次项目的容器、网络和卷；日志不输出测试密码或 Token。通过后导出后端镜像，并真实加载核对两份待发布归档的身份。

当前功能分支还会检查默认 Compose 不包含 Watchtower，`updates` profile 才启用它；真实应用容器须以非 root 用户、只读根目录、无额外 capability 运行，并具有 CPU、内存、进程数和日志上限。Docker inspect 检查明确排除 `Config.Env`；配置与实际容器不一致时 CI 失败。详见 [宿主机保护边界](host-protection.md)。

新增检查是否通过，以对应提交的 Actions 结果为准；本地脚本单元测试不能替代容器验证。

## 变量与 Secrets

以下两项支持 Repository Variables 或同名 Secrets，Variables 优先；已有 Secrets 无需移动或重填：

```text
ACR_REGISTRY=crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com
ACR_NAMESPACE=tencent-ubutun22
```

Actions Secrets：

```text
ALIYUN_ACR_USERNAME
ALIYUN_ACR_PASSWORD
```

仅 publisher 通过 `${{ vars.ACR_REGISTRY || secrets.ACR_REGISTRY }}` 及对应 namespace 表达式读取镜像坐标。配置缺失或格式非法时，在登录前失败。`ACR_REGISTRY` 必须是不带 `https://` 和路径的主机名；`ACR_NAMESPACE` 只能使用小写字母、数字和连字符。

新增的模型 Secrets 为 `LLM_API_KEY`、`ASR_API_KEY`、`TTS_API_KEY`；六个服务器连接 Secrets 为 `DEPLOY_SSH_HOST`、`DEPLOY_SSH_PORT`、`DEPLOY_SSH_USER`、`DEPLOY_ENV_PATH`、`DEPLOY_SSH_KEY`、`DEPLOY_SSH_KNOWN_HOSTS`。它们已保存，但不提供给测试或镜像构建。完整 Variables 表见 [AI 同步配置](ai-env-sync.md#github-配置)。Secret 列表仅证明名称存在，无法读取或验证已保存的值。

`VITE_ENABLE_TTS` 是公开变量：通过前端 Docker build-arg 传入并写入静态资源。更改它必须重新构建前端；不能在该参数或其他 `VITE_*` 中放密钥。仅修改 Secrets/Variables 不会触发 workflow，也不会改变已运行容器。

## 发布顺序与回滚记录

`ci/release_images.py` 先加载归档并核对镜像 ID，然后先推送两个镜像的 `sha-<7位提交>` 和可选版本标签，最后更新两个 `latest`。每次推送都解析并校验 manifest digest；版本标签与 latest 的 digest 必须一致。

发布摘要及 `published-images-<run-id>` Artifact 中的 `published-images.json` 记录完整源码提交、镜像 ID、已推送标签和成对的 `repository@sha256:<digest>` 引用。`complete: true` 才代表全部推送完成；失败时尽可能保留 `complete: false` 的部分发布记录。回滚使用已完成发布的两份 digest 引用，详见 [Watchtower 与回滚](watchtower-rollback.md)。

两个仓库的更新不是原子操作，后半段失败仍可能留下部分标签更新；不会自动回退 Registry 或服务器。演示环境需人工检查部分发布记录，不能据此宣称零中断或原子部署。

## 权限、并发与日志

- 权限限制为 `contents: read`、`packages: write`。
- 同一个 ref 使用同一并发组；PR 可以取消旧运行，push 和手动发布不取消。
- CI 禁止回显 Secrets，禁止上传 `.env` 或 Docker 登录配置。两份镜像归档和身份元数据保留 1 天；测试与容器日志保留 7 天；不含凭据的发布记录保留 30 天。
- 镜像构建使用 `type=gha` 缓存，并关闭 provenance/SBOM，避免个人版 ACR 拒绝不支持的 manifest 附件。
- 手动触发可以附加一个合法 tag；标准标签仍是 `latest` 和 `sha-<7位SHA>`。

## 功能分支验证与边界

日常使用长期个人分支 `codex/personal`，向本 fork 的 master 提 PR。只在 `vacontinuejatotired/CS-Career-Guide` 开发，不创建上游 PR。保留并分离已有 dirty 文件，按职责提交和推送，详见 [Git 规范](git-workflow.md)。

```bash
# 确认分支与工作区，完成适用检查和显式分组提交后执行：
git push -u origin codex/personal
gh run list --repo vacontinuejatotired/CS-Career-Guide --branch codex/personal --workflow ci-cd.yml
```

检查结果时确认：

1. 后端和前端测试 Job 都通过。
2. build-only 镜像可以启动，且没有执行 ACR 登录或推送。
3. 纯文档改动不会触发镜像 Job。
4. 失败时可以下载测试日志，日志中没有凭据。

单镜像冒烟不能替代真实联调与持久化步骤。功能分支的 publisher 必须跳过；即使全部验证通过，也不等于实际 ACR 认证、推送、Watchtower 更新、真实 MySQL、服务器部署或浏览器交互测试通过。

## 常见失败

| 现象 | 检查项 |
| --- | --- |
| `requirements.txt` 编码失败 | 确认原文件仍是 UTF-16 BOM；CI 只转换临时副本为 UTF-8 |
| `mysqlclient` 编译失败 | 检查 `default-libmysqlclient-dev` 和 `pkg-config` |
| ACR 登录失败 | 使用 Registry 访问凭证，不是阿里云账号登录密码 |
| `unknown manifest class` | 确认 `provenance: false` 和 `sbom: false` |
| 镜像坐标配置缺失 | 检查同名 Repository Variables 或 Secrets；仅存在于 Secrets 也可使用 |
| 同步 Job 跳过 | 检查 master、publish 结果及 `DEPLOY_ENV_SYNC_ENABLED` 是否精确为 `true`；默认关闭 |
| 镜像发布成功但同步失败 | 分别检查 SSH 主机密钥、目录/文件权限、AI 映射、部署用户 ACR 权限和容器健康；不要输出 Secret 或原始 config |
| TTS 开关改了页面没变化 | 前端变量在构建时生效，需发布包含新 build-arg 的镜像 |
