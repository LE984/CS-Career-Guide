# 服务器拉取部署

> 2026-11-01 本分支交付拆分：以[单仓库独立交付](split-delivery.md)为当前操作入口；本轮未修改服务器。历史发布/部署证据不代表新拓扑已安装。

> 2026-10-26：已验证 `csdeploy` 的私有 ACR 拉取，补齐服务器 AI 映射并通过 Actions 同步与重建应用；旧 Watchtower 已停止。服务器定制的 80 和 48080 端口已写入实际基础 Compose，避免同步只加载基础文件时丢失 80 端口。操作前已备份 SQLite、环境文件、Compose 和容器身份；实时业务验收见 [当前状态](deployment-status.md)。下文 2026-10-23 的账号创建记录是历史背景。

当前仓库以保护宿主机优先：默认仅绑定回环地址、限制资源与日志、启动前后端与独立 gateway，Watchtower 需要单独启用。新前端监听 `8080`，不能把新 Compose 与旧 `c1d7b6a` 前端镜像混用；执行部署前确认镜像与配置兼容，见 [宿主机保护边界](host-protection.md)。本次仅更新操作手册。

## 专用部署账号与配置归属

本会话已创建 `csdeploy`：独立 Ed25519 密钥登录、密码锁定、没有 sudo、加入 Docker 组。部署目录由 `csdeploy:ubuntu` 拥有且权限为 750，`.env` 为 `csdeploy:csdeploy`、600；只更改了所有权和权限，没有改环境文件内容。账号的 `authorized_keys` 使用 `restrict`，不提供 PTY、端口/agent/X11 转发；管理隧道继续使用管理员自己的连接。

实际服务器主机、端口、账号、环境文件路径和专用凭据保存在六个 `DEPLOY_*` Secrets 中，见 [配置表](ai-env-sync.md#github-配置)。不要将私钥、服务器真实 `.env` 或未经脱敏的 `docker inspect`/`docker compose config` 输出放进文档。

部署账号已验证目录读写、Docker 调用和 Python 3，2026-10-26 已以该账号成功拉取前后端私有镜像。现有管理员或 Watchtower 的登录不能替代部署账号登录。自动同步脚本使用部署账号默认 Docker CLI 凭据，须以该账号配置本项目 ACR 登录；`DOCKER_CONFIG_DIR` 只决定 Watchtower 挂载目录，不会自动影响 CLI。

启用前逐项合并服务器 Compose 中的 AI environment 映射，保留服务器定制配置；不要用仓库样例覆盖现有 `.env`。`SECRET_KEY`、数据库、`COMPOSE_PROJECT_NAME`、域名、端口、路径、资源限制和镜像选择留在服务器。AI 白名单由 Actions 管理，空的可选值不会删除已有值。

## 部署拓扑

```text
反向代理 / SSH 隧道 -> 宿主机 127.0.0.1:48080 -> gateway（Nginx :8080）
                              |-- /api/ -> backend :8000
                              |-- /static、/media -> 共享卷
                              `-- / -> frontend :8080

backend -> sqlite-data:/data
backend -> backend-static:/data/staticfiles
backend -> media:/data/media
watchtower（仅显式启用 updates profile） -> Docker socket + 独立 ACR 凭据目录
```

默认端口不对公网绑定；后端、SQLite 和 Watchtower 不发布业务端口。如确需直接公网演示，需显式修改 `WEB_PORT` 的绑定地址，并单独评估宿主机网络规则，不能把 Docker 端口发布当作已经受 UFW 完整限制。

## 低资源演示默认值

- 数据库：SQLite，保存到 `sqlite-data` 持久卷。
- Django 配置：`cs_career_guide.settings_sqlite`。
- 向量模式：LanceDB 目录存在，但默认关闭嵌入模型；语义检索可能返回空结果。
- 媒体：空持久卷，现有上传文件不会自动复制。
- 静态文件：后端 `collectstatic` 写入共享卷，Nginx 只读提供。
- MySQL：只通过可选 `mysql` Compose profile 和显式 settings 切换启用。

SQLite 只适合低并发演示，不是正式生产数据库方案。

## ACR 登录

GitHub Actions 使用公网 Registry：

```text
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com
```

服务器如果位于同一 VPC，可以使用 VPC 地址：

```text
crpi-gbihc3e57h3o3f2l-vpc.cn-hangzhou.personal.cr.aliyuncs.com
```

公网和 VPC 地址指向同一组仓库，按服务器实际网络选择；不要假设 GitHub Actions 能访问 VPC 地址。

默认手动拉取前先登录：

```bash
docker --config /etc/cs-career-guide/acr login --username=<ACR_USERNAME> crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com
```

不要把 Registry 密码写入 Compose 或 `.env`。

后续手动拉取使用同一 `docker --config /etc/cs-career-guide/acr compose ...` 配置。目录只保存本项目 ACR 登录；只有选择启用 Watchtower 时，才通过 `DOCKER_CONFIG_DIR` 把这个目录只读挂载给它。

## 准备服务器

要求：

- Docker Engine 与 Compose v2。
- 能访问 ACR。
- 可写的部署目录。
- 生成的 Django `SECRET_KEY`。

把部署文件放到服务器后，从样例创建环境文件：

```bash
cd deploy
cp .env.example .env
# 在服务器本地编辑 .env，不能提交。
docker compose config --quiet
```

如果服务器使用 VPC 地址，请只修改 `.env` 中的 Registry 主机名。设置 `SECRET_KEY`，并让 `ALLOWED_HOSTS` 与演示地址一致；IP 访问只适合临时演示，不能宣称已具备公网生产条件。

## 启动与验证

```bash
cd deploy
docker --config /etc/cs-career-guide/acr compose pull backend frontend gateway
docker compose up -d --no-build backend frontend gateway
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

检查项：

1. 通过 SSH 隧道或已有反向代理访问默认绑定的 `127.0.0.1:48080`，确认 Vue 页面可显示。
2. `/login` 和 `/register` 可以打开。
3. 没有 Token 访问业务页面会跳转登录。
4. 注册、登录后能拿到 Token 并返回原业务路径。
5. `/api/` 由 Nginx 代理，后端端口不对宿主机公开。
6. `/static/` 和 `/media/` 能通过 Nginx 访问。
7. 容器日志中不出现密钥。

应用使用进程级检查，不是业务健康接口；端口可连不等于数据库、AI 或外部企业服务都健康。

## 数据持久化与备份

默认卷：

```text
sqlite-data
backend-static
media
mysql-data   # 只有启用 MySQL profile 时使用
```

SQLite 建议在应用停止时冷备份：

```bash
docker compose stop watchtower
docker compose stop backend
docker run --rm -v <PROJECT>_sqlite-data:/data -v "$PWD/backups:/backup" alpine \
  sh -c 'cp /data/cs-career-guide.sqlite3 /backup/cs-career-guide.sqlite3'
docker compose start backend
```

先用 `docker volume ls` 确认真实卷名，不要直接使用占位符。媒体卷和静态卷有用户内容时也要分别备份；后端恢复并检查通过后，才恢复 Watchtower。

## 以后切换 MySQL

先启动可选服务：

```bash
docker compose --profile mysql up -d mysql
```

然后在 `.env` 中显式切换到原有 MySQL settings，并提供完整数据库变量：

```text
DJANGO_SETTINGS_MODULE=cs_career_guide.settings
DATABASE_NAME=cs_career_guide
DATABASE_USER=cs_career_guide
DATABASE_PASSWORD=<服务器密钥>
DATABASE_HOST=mysql
DATABASE_PORT=3306
MYSQL_ROOT_PASSWORD=<服务器密钥>
```

只加 `--profile mysql` 不会让 Django 自动改用 MySQL。不要自动迁移现有 SQLite 数据；迁移必须单独设计、备份和验证。

Compose 会把 `DATABASE_NAME`、`DATABASE_USER`、`DATABASE_PASSWORD`、`DATABASE_HOST`、`DATABASE_PORT` 传入 backend；空密码不会破坏默认 SQLite profile，但 MySQL profile 必须提供独立密码。CI 只验证配置接线，不代表已有 MySQL 数据或真实迁移已经验收。

## 更新与回滚

日常只更新或回滚目标组件，使用[独立交付](split-delivery.md#单服务部署与-digest-回滚)中的 `deploy_component.py`，固定完整 digest，pull 单服务并以 `--no-deps --pull never` 重建。脚本生成单端 pin 文件；今后手工 Compose 必须加载已存在的对应 pin override，不能用不带 override 的基础命令覆盖版本。

首次安装新网关属于拓扑维护，不能与日常单端更新混为一谈。现有端口、项目名、命名卷和数据必须保留；仅有旧总同步开关不会启用新分端自动部署。Watchtower 与 Actions 不应并行管理同一组件。

## 当前限制

- 没有 HTTPS 和域名证书。
- 没有自动迁移已有媒体或 SQLite 数据。
- 没有真实 MySQL 迁移验证。
- 少量真实文本和面试音频调用已授权并验证，不代表完整费用、配额或负载验收。
- 不能宣称已完成公网上线。
