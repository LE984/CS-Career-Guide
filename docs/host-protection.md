# 演示项目的宿主机保护边界

> 2026-11-01 交付拆分：以[单仓库独立交付](split-delivery.md)为当前操作入口；实际发布、服务器安装与自动部署开关见[带日期的状态记录](deployment-status.md)。历史证据不能代替当前运行状态。

目标：允许演示应用不可用或丢失演示数据，优先控制它对宿主机权限、CPU、内存、进程数与磁盘的影响。不以生产业务连续性、付费 AI 或正式数据迁移为验收目标。

2026-10-22 的修改与首次发布属于历史记录。2026-10-23 本会话已连接服务器、创建并验证专用部署账号，观察到前后端健康及旧 Watchtower 运行；没有重新验收全部运行时防护参数。新增同步/重构已经过 build-only CI 并整合进 master，但不能用旧镜像或 runner 证据代替服务器验收。详细状态见 [接手记录](deployment-status.md)。

新增 `csdeploy` 密码锁定、无 sudo、使用独立且带 `restrict` 的 SSH 公钥，目录权限 750、`.env` 权限 600。它拥有 Docker 组权限，因此具有很高的宿主机控制能力；无 sudo 和 SSH 转发限制不构成 Docker 沙箱。Actions workflow 可修改者进入部署信任边界；同步仅在 master 发布成功并显式启用时运行，凭据与失败边界见 [AI 配置同步](ai-env-sync.md)。

## 默认应用容器

| 项目 | backend | frontend |
| --- | --- | --- |
| 用户 | `10001:10001` | `10001:10001` |
| 根文件系统 | 只读 | 只读 |
| Linux capability | 全部移除 | 全部移除 |
| 提升权限 | `no-new-privileges` | `no-new-privileges` |
| CPU 上限 | 0.50 核 | 0.25 核 |
| 内存上限 | 512 MiB | 96 MiB |
| 额外 swap | 禁止 | 禁止 |
| 进程数上限 | 128 | 64 |
| 临时目录 | `/tmp`：64 MiB tmpfs | `/tmp`：16 MiB、Nginx 缓存：32 MiB tmpfs |
| 容器日志 | `local` 驱动，5 MiB/文件，最多 3 个 | 同左 |
| 宿主机端口 | 不发布 | 不发布；由 gateway 映射 `WEB_PORT` 到 `8080` |

应用只挂载本项目命名数据卷和有大小限制的临时目录，不挂载宿主机根目录、Docker socket、SSH 密钥或 Docker 登录目录；前端不挂后端卷；gateway 才只读挂载 static/media 与唯一的 `deploy/nginx.conf`。gateway 同样以 UID 10001、只读根目录、drop ALL、CPU 0.25 核/内存 64 MiB/PID 64 和受限日志运行，临时目录为 32 MiB tmpfs。Gunicorn 在演示 Compose 中默认只启动 1 个 worker。可编辑的资源参数集中在 `deploy/.env.example`；上限不是预留给系统的剩余资源，服务器容量仍需单独核实。

Nginx 改用非 root 用户和容器内 `8080` 端口，PID 放到 `/tmp`。旧发布 `c1d7b6a` 的前端监听 `80`，不能与本分支的新 Compose 混用；只有在后续获授权发布同版本镜像后，才可配套更新服务器。此次不会自动影响正在运行的服务。

## Watchtower 默认关闭

Watchtower 移入 `updates` profile，普通 `docker compose up -d` 启动前后端与 gateway。默认不会自动更新或自动清理替换下来的镜像，手动更新流程见 [服务器拉取部署](server-pull.md)。

原因是 Watchtower 需要 Docker socket，其进程一旦被控制，就可能通过 Docker API 管理其他容器和挂载宿主机目录。容器标签、`cap_drop` 或只读挂载 socket 都不能限制这些 API 的权限。显式启用前必须接受这一风险，见 [Watchtower 与回滚](watchtower-rollback.md)。

如仍选择启用，凭据目录限定为只保存本项目 ACR 登录的 `/etc/cs-career-guide/acr`，不复用宿主机通用的 `/root/.docker`。它也有 CPU、内存、进程数和日志上限。本会话确已观察到服务器旧 Watchtower 运行，仅修改仓库 profile 不会把它停止；此次没有停止它，启用 Actions 自动重建前需协调更新入口。

## 尚未解决的宿主机边界

- **持久数据卷没有硬容量配额。** 日志和 tmpfs 上限不限制 SQLite、媒体、LanceDB 命名卷的总占盘；应用被控制后仍可能写满这些卷。需要服务器上的独立受限文件系统、用户/项目配额，或专门隔离的演示磁盘。此项未实施、未验证。
- **容器共享宿主机内核。** 非 root、只读目录和资源限制降低影响范围，但不保证应用失陷后绝不影响宿主机；更强的边界需要单独虚拟机或专用演示主机。
- **网络出口与宿主机其他服务尚未隔离验收。** 容器没有使用 host 网络，但未核查服务器的防火墙、Docker 转发规则或其他内网服务。默认回环绑定只减少公网暴露，不等于出站或横向访问已经被阻断。
- **宿主机资源总量尚未核实。** 容器上限不等于能保证系统和其他项目始终有足够资源；可选 MySQL 与 Watchtower 另有上限，启用时需一起计入。

因此只能报告“分支中已加入限制，并通过对应级别的测试”，不能报告“服务器已被隔离保护”或“项目被攻击也绝不影响服务器”。当前不新增强制备份、HTTPS 或生产运维流程。

## CI 验证

1. 本地单元测试验证无权限、资源或日志限制时会被检查器拒绝；全部 Docker 操作均模拟，不启动本机 Docker。
2. Actions runner 解析默认、updates、MySQL 和 digest override 的 Compose 配置。
3. 实际启动前后端与 gateway 后，仅读取容器用户、HostConfig 与挂载元数据，检查权限、资源、日志、回环绑定和挂载边界；不读取 `Config.Env`。
4. 在这些限制下继续验证真实 Nginx/Django 注册登录、静态文件、资料读写，以及后端重建后的 SQLite 持久化。

Actions 结果只证明 runner 上该次容器验证；服务器内核、Docker 配置、防火墙、持久卷配额和运行中容器仍须单独核验。
