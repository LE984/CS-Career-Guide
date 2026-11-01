# 演示项目的宿主机保护边界

> 2026-11-01 交付拆分：以[单仓库独立交付](split-delivery.md)为当前操作入口；实际发布、服务器安装与自动部署开关见[带日期的状态记录](deployment-status.md)。历史证据不能代替当前运行状态。

目标：允许演示应用不可用或丢失演示数据，优先控制它对宿主机权限、CPU、内存、进程数与磁盘的影响。不以生产业务连续性、付费 AI 或正式数据迁移为验收目标。

2026-10-22 至 2026-10-26 的账号与首次防护配置属于历史记录。2026-11-01 已完成独立 gateway 安装并单独重建 frontend，原 backend 容器保持不变；Watchtower 停止。安装核对了项目、卷、环境文件和端口，未重新验收全部宿主机防护参数，runner 防护测试不能代替服务器隔离验收。详细证据见[部署状态](deployment-status.md)。

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

frontend 与 gateway 都以非 root 用户监听容器内 `8080`，PID 放到 `/tmp`；只有 gateway 发布宿主端口。仓库默认 `WEB_PORT=127.0.0.1:48080`，现有服务器经授权保留原 80/48080 映射并转交 gateway，不能将仓库回环默认值写成该服务器的真实绑定。旧内置代理或监听 80 的前端不直接作为新拓扑的回滚版本；先核对镜像/配置兼容。

## Watchtower 默认关闭

Watchtower 移入 `updates` profile，普通 `docker compose up -d` 启动前后端与 gateway。默认不会自动更新或自动清理替换下来的镜像，手动更新流程见 [服务器拉取部署](server-pull.md)。

原因是 Watchtower 需要 Docker socket，其进程一旦被控制，就可能通过 Docker API 管理其他容器和挂载宿主机目录。容器标签、`cap_drop` 或只读挂载 socket 都不能限制这些 API 的权限。显式启用前必须接受这一风险，见 [Watchtower 与回滚](watchtower-rollback.md)。

如仍选择启用，凭据目录限定为只保存本项目 ACR 登录的 `/etc/cs-career-guide/acr`，不复用宿主机通用的 `/root/.docker`。它也有 CPU、内存、进程数和日志上限。2026-11-01 独立审计确认服务器 Watchtower 仍处于停止状态，应用统一由分端 Actions 管理。仓库 profile 不能停止其他环境已有的 Watchtower，安装或恢复更新前仍需协调入口。

## 尚未解决的宿主机边界

- **持久数据卷没有硬容量配额。** 日志和 tmpfs 上限不限制 SQLite、媒体、LanceDB 命名卷的总占盘；应用被控制后仍可能写满这些卷。需要服务器上的独立受限文件系统、用户/项目配额，或专门隔离的演示磁盘。此项未实施、未验证。
- **容器共享宿主机内核。** 非 root、只读目录和资源限制降低影响范围，但不保证应用失陷后绝不影响宿主机；更强的边界需要单独虚拟机或专用演示主机。
- **网络出口与宿主机其他服务尚未隔离验收。** 容器没有使用 host 网络，但未核查服务器的防火墙、Docker 转发规则或其他内网服务。默认回环绑定只减少公网暴露，不等于出站或横向访问已经被阻断。
- **宿主机资源总量尚未核实。** 容器上限不等于能保证系统和其他项目始终有足够资源；可选 MySQL 与 Watchtower 另有上限，启用时需一起计入。

因此只能按证据报告仓库限制、runner 测试与服务器已核验的项目，不能报告“服务器已被隔离保护”或“项目被攻击也绝不影响服务器”。当前不新增强制备份、HTTPS 或生产运维流程。

## CI 验证

1. 本地单元测试验证无权限、资源或日志限制时会被检查器拒绝；全部 Docker 操作均模拟，不启动本机 Docker。
2. Actions runner 解析默认、updates、MySQL 和 digest override 的 Compose 配置。
3. 实际启动前后端与 gateway 后，仅读取容器用户、HostConfig 与挂载元数据，检查权限、资源、日志、回环绑定和挂载边界；不读取 `Config.Env`。
4. 在这些限制下继续验证真实 Nginx/Django 注册登录、静态文件、资料读写，以及后端重建后的 SQLite 持久化。

Actions 结果只证明 runner 上该次容器验证；服务器内核、Docker 配置、防火墙、持久卷配额和运行中容器仍须单独核验。
