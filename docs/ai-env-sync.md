# 单组件激活与后端 AI 配置同步

本分支将原成对容器重建拆成 deploy-backend / deploy-frontend；服务器安装独立网关是前提。2026-10-26 的旧总开关/成对重建属于历史，不代表新分端部署已经启用。完整安装和回滚见[独立交付](split-delivery.md)。

## 门禁与版本

必须同时满足对应 publisher 成功、本 fork/master、非 PR、DEPLOY_ENV_SYNC_ENABLED=true、对应 DEPLOY_BACKEND_ENABLED=true 或 DEPLOY_FRONTEND_ENABLED=true。两个新分端开关缺省关闭，防止旧服务器因原总开关仍开启而切入新拓扑。回滚时关闭目标分端开关，等已运行 Job 退出；旧自动入口仍在时也关闭总开关。

DEPLOY_COMPONENT 指定 backend/frontend；DEPLOY_IMAGE 只能是该组件的完整 repository@sha256 digest，来自本次完成的发布记录。脚本不再按 latest 猜测本次部署版本。主流程仅用基础 Compose 加目标组件 pin override，不会加载另一组件 override，也不会重建另一服务/网关/数据库。

## 凭据与配置归属

SSH Secrets 仍为 DEPLOY_SSH_HOST、DEPLOY_SSH_PORT（空默认22）、DEPLOY_SSH_USER、DEPLOY_ENV_PATH、DEPLOY_SSH_KEY、DEPLOY_SSH_KNOWN_HOSTS。严格主机密钥核验；不使用运行时 ssh-keyscan 建立信任。私钥临时权限600，传送完成后清理。

仅 backend Job 接收 LLM_API_KEY、ASR_API_KEY、TTS_API_KEY Secrets，以及 Variables：LLM_BASE_URL、LLM_MODEL、CAREER_REPORT_MODEL、ASR_WSS_URL、ASR_MODEL、ENABLE_TTS、TTS_WSS_URL、TTS_MODEL、TTS_VOICE。前三个 LLM 配置必填；白名单非空值覆盖、空可选值保留。其余环境行保持，包括 SECRET_KEY、数据库、端口、项目名和自定义配置。

frontend Job 只接收 SSH 字段、组件名与公开 digest，不注入任何模型字段；服务器 .env 不合并、不替换。手工 deploy_component.py 对任一组件都不改 AI/.env。VITE_* 仅在前端镜像构建生效，不由此脚本修改。

## 服务器前提

Linux Python 3、Docker、支持 JSON config / --wait / --pull never 的 Compose v2。部署账号能访问私有 ACR；脚本使用其默认 Docker CLI 凭据，DOCKER_CONFIG_DIR 只负责 Watchtower 挂载，不自动影响 CLI。

现存 .env 须为绝对路径、600、部署账号拥有、普通文件、无软/硬链接；父目录由该账号拥有，不可组/其他人写入。基础 docker-compose.yml 不可为软链接，必须已安装新 gateway、去掉 frontend 的 ports/volumes/depends_on。校验还要求 gateway 发布8080、只读绑定同目录nginx.conf、三端共享网络且backend不发布端口；不满足时在pull前拒绝。脚本不上传、不覆盖服务器 Compose 或 nginx.conf，不迁移卷。

后端合并不接受多行/重复受管键/模糊 dotenv 或含控制字符、单引号、反斜杠的值。SSH stdin 传密钥，绝不进入 argv、Artifact、镜像或日志。Compose/SSH 原始诊断隐藏；请在服务器私下排查。

## 事务与失败边界

在 `.env.ai-sync.lock` 下生成600候选文件；校验 Compose AI映射、拓扑及目标 digest，再只 pull 目标服务。检测环境/pin并发变化，才原子替换 backend 候选 .env（frontend不替换），并保存 docker-compose.<组件>-image.json。随后只对该组件执行 up -d --no-deps --no-build --pull never --force-recreate --wait --wait-timeout 180。

config/pull失败保持原环境与pin，所有候选均清理。激活/健康失败保留新配置与pin并使Actions失败，不自动恢复旧容器/数据库。backend入口仍可能migrate；单端镜像回滚不等于schema恢复。独立重建可能短暂中断，gateway在DNS缓存窗口后恢复，不保证零停机。

pin文件属于运行状态，不入Git。以后直接调用Compose必须显式加载已存在的pin override；旧paired digest override或只改.env中的tag不能覆盖更高优先级pin。回滚推荐使用同一脚本和锁，见[独立交付](split-delivery.md#单服务部署与-digest-回滚)。

## 验证

python -m unittest discover -s ci -p 'test_*.py' -v。全为虚构SSH/Compose、临时文件；Windows跳过POSIX权限测试，WSL/Linux补验。同步健康、实际运行 digest、浏览器和真实模型分别核验；服务器操作的实际结果见[部署状态](deployment-status.md)。
