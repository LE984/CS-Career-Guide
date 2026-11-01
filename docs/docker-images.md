# Docker 镜像

当前分支的构建入口为 frontend/Dockerfile 与 backend/Dockerfile，构建上下文分别是 frontend/、backend/。仓库仍是一个 Git 仓库，ACR 仍为 cs-career-guide-frontend、cs-career-guide-backend 两个独立镜像仓库；不再成对构建或成对发布。历史发布证据见 deployment-status.md，新拓扑与操作见[独立交付](split-delivery.md)。

## 独立构建

以下命令只供 Actions runner 或以后明确授权的构建环境使用，本机本轮不执行 Docker：

```bash
docker build -f frontend/Dockerfile -t cs-career-guide-frontend:local frontend
docker build -f backend/Dockerfile -t cs-career-guide-backend:local backend
```

后端 Python 3.11 多阶段 wheel 构建，运行用户 UID/GID 10001；编译依赖与 MariaDB 客户端运行库维持原配置。backend/requirements-runtime.txt 未升级依赖，仍排除 torch/transformers/sentence-transformers 等重依赖；backend/requirements.txt 保持 UTF-16。根目录 requirements 只是 pip 转发入口，前端不会进入后端上下文。

入口仍执行 collectstatic、migrate、Gunicorn；本轮不改变模型调用、数据库或 legacy 面试主链路。后端回滚仍需核对 schema；镜像端口/TCP 健康不能证明业务或模型成功。

前端 Node 24 编译、nginx:1.27-alpine 静态运行，UID/GID 10001、端口 8080、PID 位于 /tmp。只提供 dist、history fallback 和资源缓存；无 backend upstream、无共享后端卷。standalone Nginx 不依赖 backend DNS，单镜像冒烟不创建后端。

## 公开构建参数

VITE_API_BASE_URL 默认 /api；VITE_COMPANY_API_BASE_URL 默认 /company-api，保持原 Docker 构建路径；VITE_ENABLE_TTS 默认 False。工作流从同名 Variables 显式传入，完整 API URL 需含 /api。VITE_* 会写入浏览器，不得传 Key/Token/密码；运行时改服务器 .env 不能改变已编译静态包。

GLB 与 VAD ONNX/WASM/worklet 为公开运行资源，必须保留。根 `.dockerignore` 不再控制这两个上下文；各组件的 `.dockerignore` 排除 .env 及嵌套环境文件、私钥、依赖缓存、产物和本地运行数据。仅 .env.example 可保留；backend 的 SQLite、LanceDB、media/staticfiles 等不进入镜像。源码静态目录与迁移仍保留。

## 网关与发布

独立 gateway 使用受审阅的 deploy/nginx.conf，继续承接同源 API、SSE、static/media；它属于部署配置，不嵌在前端镜像中、不由单端 publisher 推送。网关配置更新需明确拓扑维护，普通单端发布不重建它。

两端 cache scope 不变，使用 type=gha，provenance/sbom=false。各自测试后导出归档，publisher 验证完整 commit、image ID、linux/amd64 后发布同一镜像；不重新构建、不要求另一端归档。单端/共享验证策略、发布记录和 digest 回滚见[独立交付](split-delivery.md)。

截至 2026-11-01，本地只验证离线测试与生产前端编译；Docker、网关联调结果必须来自当前提交 Actions，未部署服务器。
