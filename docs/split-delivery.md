# 单仓库、前后端独立交付

本仓库继续保留 `frontend/` 和 `backend/`。拆分的是构建、镜像、发布与激活边界，不调整页面、API、Token 鉴权或 legacy 面试实现。本文描述本分支的实现；截至 2026-11-01，服务器尚未安装该拓扑，本轮没有生产部署或数据库迁移。

## 构建与交付选择

| 变更 | 自动选择 | 发布与部署 |
| --- | --- | --- |
| 仅 `frontend/`（包括 revert、删除文件） | 前端测试、前端镜像及无后端冒烟 | 只发布前端；满足分端开关时只激活前端 |
| 仅 `backend/` | 后端测试、后端镜像及启动冒烟 | 只发布后端；满足分端开关时只激活后端 |
| 两端、`deploy/`、`ci/`、共享/未知路径 | 两端测试、两镜像、完整候选网关联调 | 两个独立 publisher，完整联调失败时两者均不得发布 |
| 仅 `README.md`、`docs/` | 文档门禁 | 不构建、不发布、不部署镜像 |
| 手动 workflow | `component=frontend/backend/all`，默认 all | 只有本 fork/master 才发布；其他分支 build-only |

`ci/component_changes.py` 是组件选择入口，分类不依赖提交标题或所谓 revert 类型；Git diff 使用 `--no-renames`，跨目录移动会选择两端。首次主题分支 push 与 master 的共同祖先比较，避免仅检查最后一个提交。未知路径保守选择两端。backend-image 不再等待 frontend-image，各 publisher 只下载自身已验证的归档；不重新构建，也不修改另一镜像仓库的标签。

构建上下文严格为 `frontend/` 和 `backend/`，Dockerfile、`.dockerignore` 与各自依赖位于对应目录。backend 的 UTF-16 `requirements.txt` 和运行依赖只搬迁、不升级；根目录两个 requirements 文件是 pip 转发入口。前端公开 build args 为 `VITE_API_BASE_URL`、`VITE_COMPANY_API_BASE_URL`、`VITE_ENABLE_TTS`，不允许传密钥。

Actions 在正式镜像构建前，使用 scratch COPY 导出实际上下文，放入虚构环境/私钥/运行数据探针并核对它们被 Dockerignore 排除。仅 runner 执行；不读取真实环境文件。

## 单端兼容策略与门禁

单端变更运行自身完整离线回归与镜像冒烟。前端沿用 API/Token/401、legacy 面试请求与 SSE 解码合同测试；后端沿用鉴权、配置、面试/ASR 和迁移隔离回归。前端镜像冒烟不创建 backend，也不提供 backend DNS。

单端发布**不执行完整候选前后端容器联调**，不能将其写成已通过。`release-summary` 明确标注 SKIPPED；这也不证明任意旧版本组合兼容。破坏 API、鉴权、事件或资源路径的变更应保持兼容窗口，必要时两端一起修改并运行 `component=all`；跨版本兼容发布须另行指定并验证目标 digest 组合。

共享交付变更必须运行两个候选镜像的 `integration`：真实 Django/Nginx 的登录、鉴权拒绝、资料读写、后端静态文件、SQLite 重建持久化；分别重建单端并确认另一端与 gateway 容器 ID 不变。`gateway_smoke.py` 再以合成上游验证 Authorization/Cookie/query、static/media、首个 SSE 事件及时到达，以及两端强制换 IP 后 gateway 无需重启即可恢复。合成 SSE 不调用真实模型。

业务门禁独立于交付门禁：`ci/check_project_changes.py` 仅在基线与当前前后端测试 Job 保持一致时，将 `.github/workflows/ci-cd.yml` 视作交付编排例外；测试命令、跳过条件、continue-on-error、删除测试等变化仍触发原完整业务门禁。业务路径/公共契约/未知业务文件仍按基线归属表要求实施文档和原 complete 用例。`career-platform.yml`、`ci/project_*`、检查器、固定测试等验收规则改动仍要求全部业务验收；交付文件与业务文件混改不能逃逸。普通前端静态变更不启动数据库 runner，前端业务模块变更仍执行其原业务验收。

**本轮限制：本分支修改了门禁检查器与 career-platform.yml，因此自身仍选择原完整业务验收。五个模块当前是 501 骨架，2026-11-01 的本地 17 项 complete 用例为 14 failures、3 errors，均为 501/FeatureNotImplemented；没有降低该门禁或实现这五项业务来制造绿色。交付构建/网关联调与此业务阻塞分别记录。**

## 稳定网关

```text
浏览器/宿主反代 -> WEB_PORT -> gateway:8080
                              |-- /api/ -> backend:8000
                              |-- /static/、/media/ -> 后端命名卷（只读）
                              `-- / -> frontend:8080（纯静态资源和 history fallback）
```

网关是受审阅的部署配置，不随前端镜像发布。保留现有 `/api/ai/llm/chat/` 的 HTTP/1.1、关闭 buffering/cache、300s 超时与请求路径；其他 API 维持原代理行为，`/company-api` 未接入服务时仍返回 503。前端不挂载后端卷、不依赖后端、不占宿主机端口。网关通过 Docker DNS `127.0.0.11` 与变量 upstream 每 5s 重新解析，避免单服务重建后的旧 IP 长期缓存。短暂重建/解析失败可能出现 502，不承诺零停机。

同源部署继续使用 `/api`。若前端部署到独立域名/CDN，构建时可提供完整 API URL（含 `/api`），并在 backend 的服务器配置显式设置 `CORS_ALLOWED_ORIGINS`、`CSRF_TRUSTED_ORIGINS`、`ALLOWED_HOSTS`。默认 `CORS_ALLOW_ALL_ORIGINS=False`；跨域与 Cookie/HTTPS 需单独验收，不能只因环境变量已接线就宣称可用。

## 首次安装新拓扑（仅操作说明）

此步骤会改变流量入口，只能在后续获得服务器授权后执行。本轮未执行。

1. 首次合并时保持 `SPLIT_DELIVERY_RELEASE_ENABLED` 缺省关闭，确保 master 也只 build-only。暂停现有 Actions 自动激活并确认无运行中任务；协调/停止旧 Watchtower。通过手动 `Split delivery maintenance` 的只读 audit 核对容器、镜像、端口和卷，保留现有 Compose、环境、容器身份及数据备份。
2. 核对已通过 runner 验证的前后端 digest。新纯静态前端必须与独立网关同时启用；旧内置代理前端的直接端口部署不能只替换为新静态镜像。
3. 逐项合并新的 `deploy/docker-compose.yml` 和 `deploy/nginx.conf`，保持原 Compose 项目名、卷名、服务器端口、自定义配置和已有卷属主；绝不直接覆盖真实 `.env` 或执行 `down -v`。宿主原有 80/48080 映射应移到 gateway，而不是发布 backend。
4. 首次启动应显式拉取 backend、frontend、gateway，并启动这三项。gateway 配置必须可由 UID 10001 读取；backend 写入的 static/media 卷继续只读挂到 gateway。核验新入口的登录、SSE、资源及已有数据。
5. 首次安装可在服务器 `.env` 中设置两端 digest；自动激活后生成的单端 pin 文件优先级更高。今后手工 Compose 应显式加载已存在的 `docker-compose.backend-image.json` 与 `docker-compose.frontend-image.json`，避免基础文件回到旧 tag。
6. 安装脚本 `ci/sync_runtime_env.py` 和 `ci/deploy_component.py` 到可信的同一工具目录；自动 SSH 会传送当前同步脚本，不上传 Compose。部署目录归部署账号、不可组/其他用户写入，`.env`、生成的 pin 文件均为 600 且无软/硬链接。
7. 已协调旧更新入口、准备好切换与回退后，才显式开启 `SPLIT_DELIVERY_RELEASE_ENABLED=true`，发布首个拆分版本。完成网关安装与业务检查后，才按需启用 `DEPLOY_ENV_SYNC_ENABLED=true` 和 `DEPLOY_FRONTEND_ENABLED=true` / `DEPLOY_BACKEND_ENABLED=true`。新增开关默认关闭，不能因旧总开关已开启就自动切换服务器。

网关只由明确的拓扑维护操作更新；普通前端/后端发布与回滚不重建网关。现有 `docker-compose.digest.yml` 仍保留为显式同时指定两端的维护入口，但日常单端回滚使用下面的脚本。

## 单服务部署与 digest 回滚

各组件 publisher 的 `published-<组件>-<run-id>` Artifact 内含 `published-images.json`：检查 `complete=true`、`components`、`compatibility` 证据范围、完整源码 commit 和 `images.<组件>.reference`。不同组件可来自不同已完成发布，不要求同一个源码提交；仍须核对目标 API/schema 兼容。

自动激活从对应 publisher output 读取完整 digest，`DEPLOY_IMAGE` 不追踪 latest。脚本在锁内校验候选 Compose，pull 单服务，再持久化 `docker-compose.<组件>-image.json`，最后执行：

```bash
docker compose ... up -d --no-deps --no-build --pull never --force-recreate --wait --wait-timeout 180 <组件>
```

frontend 不接收 AI Secrets，不合并/替换 `.env`（inode 也不变）；backend 才沿用原 AI 白名单合并。两端均不改另一组件 pin，不拉取另一镜像，不重建另一服务/网关/数据库，也不删除用户卷。

手工回滚前先关闭目标分端 Actions 开关、等待进行中任务退出，协调 Watchtower；如仍有旧式自动同步，则同时关闭总开关。脚本与自动激活共用 `.env.ai-sync.lock`。下面在服务器执行，digest 为经核对的完整引用；工具文件须已安装到实际路径。

```bash
python3 /srv/career-tools/ci/deploy_component.py \
  --env-path /srv/cs-career-guide/.env --component frontend \
  --image 'registry.example/demo/cs-career-guide-frontend@sha256:<64位digest>'

# 只有后端需要回滚时才执行这一条；不会同步 AI 配置或修改 .env。
python3 /srv/career-tools/ci/deploy_component.py \
  --env-path /srv/cs-career-guide/.env --component backend \
  --image 'registry.example/demo/cs-career-guide-backend@sha256:<64位digest>'
```

脚本使用部署账号默认 Docker 凭据；若使用独立配置目录，私下设置 `DOCKER_CONFIG`，不要打印登录文件。新拓扑不满足、digest 组件不符、权限不安全或并发修改时拒绝激活。旧 `--remote <env-path>` 与草稿 `--remote <env-path> <component>` 参数仍接受，保留既有 pin；新 Actions 路径强制传当前发布 digest。

config/pull 失败保留原 `.env` 和 pin，删除候选文件；激活/健康失败保留已写入的新配置与 pin并报错，不自动恢复旧容器、数据库或环境。后端入口沿用 collectstatic/migrate：后端发布或回滚前必须检查 schema 兼容与备份，前端操作不会运行后端入口。应用镜像回滚不等于数据/schema 回滚。

## 验证证据分层

- 本地：Windows/WSL 离线单元测试、虚构 SSH/Compose、原鉴权/API/面试回归、离线缓存 npm 安装和前端构建；没有本机 Docker。
- Actions：只有对应 commit 的真实镜像与 runner 联调成功，才可报告构建/容器结果。
- Registry：只有 publisher 成功且记录 complete，才可报告该组件镜像已发布。
- 服务器：分端激活健康与业务检查单独记录；发布本身不证明服务器运行该 digest。
- 浏览器、真实模型、语音和生产数据库迁移：均需单独授权与验收，本轮没有执行。

### 2026-11-01 Actions 阶段证据

修复网关临时目录后的 `a1ea092` 已在 push 运行 41301386969 与 PR 运行 41301390611 通过两端代码测试、各自实际构建/无发布归档验证、实际 Dockerignore scratch 导出探针，以及完整 gateway/Django/SQLite 联调。合成上游的 headers/query、static/media、无缓冲 SSE、两端强制 IP 变更也通过。

上述运行的总结果仍为 failure：SQLite/MySQL 的原完整业务验收因现有 501 骨架失败，release-summary 正确报告业务门禁失败，两个 publisher/deploy 均 skipped。不能将交付检查通过写成整个 CI 通过或已发布/已部署。其后的公司查询默认构建参数保持 /company-api 与服务器拓扑校验补丁，需以最终 head 的 Actions 再确认，不能沿用此处提交证据。
