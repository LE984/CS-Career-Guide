# 环境变量配置

> 2026-11-01 交付拆分：以[单仓库独立交付](split-delivery.md)为当前操作入口；实际发布、服务器安装与自动部署开关见[带日期的状态记录](deployment-status.md)。历史证据不能代替当前运行状态。

## 配置文件与优先级

后端复制 `backend/.env.example` 为 `backend/.env`，前端复制 `frontend/.env.example` 为 `frontend/.env`。也可以在服务器或容器中直接注入环境变量。后端的系统环境变量优先于 `.env`；前端沿用 Vite 的环境变量规则。

2026-10-23 新增可选的 [Actions AI 配置同步](ai-env-sync.md)，已经过 build-only CI 并整合进 master，启用开关未设置。模型 Key 和模型配置已保存在 Actions；保存并不会自动传给服务器或改变运行中容器。镜像发布以对应 master Actions 为准。

配置归属按以下规则管理：

| 来源 | 配置 | 更新方式 |
| --- | --- | --- |
| Actions Secrets | 三个模型 API Key、六个 SSH 连接字段 | 只在启用后的同步 Job 使用；SSH 字段不写应用 `.env` |
| Actions Variables | 模型名、LLM/ASR/TTS URL、音色、`ENABLE_TTS` | AI 白名单合并到服务器 `.env`；非空值更新，空可选值保留旧值 |
| 前端构建 Variable | `VITE_API_BASE_URL`、`VITE_COMPANY_API_BASE_URL`、`VITE_ENABLE_TTS` | Docker build-arg 写入静态资源，需重建前端；不能存密钥 |
| 服务器 `.env` | `SECRET_KEY`、数据库、`COMPOSE_PROJECT_NAME`、域名、端口、路径、资源、镜像选择等 | 本地维护，自动同步不得覆盖 |

白名单内的 AI 字段由 Actions 负责，不能同时期待保留服务器同名覆盖值。`ASR_API_KEY`/`TTS_API_KEY` 的留空复用规则属于 Django 设置；同步空值跳过时可能保留服务器旧 Key，如需清除必须另行处理。Compose 环境映射补齐后，候选配置校验才会通过；具体名单与启用顺序见同步文档。

示例不包含真实密码或 API key。生产环境必须生成独立 `SECRET_KEY`，填写数据库账号、密码和服务凭据。后端关键配置缺失时会报错，而不是使用源码中的密码。

生成密钥（只在自己本地执行，把结果填入后端配置）：

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 后端变量

| 变量 | 说明 |
| --- | --- |
| `SECRET_KEY` | 必填；Django 签名密钥，无源码默认值 |
| `DEBUG` | 默认关闭，支持 true/false、1/0、yes/no、on/off，大小写不限 |
| `ALLOWED_HOSTS` | 逗号分隔的域名或 IP，不带协议；默认只允许 localhost 和 127.0.0.1 |
| `DATABASE_NAME` / `DATABASE_USER` / `DATABASE_PASSWORD` | 必填的 MySQL 数据库名、用户和密码；数据库需预先创建 |
| `DATABASE_HOST` / `DATABASE_PORT` | MySQL 地址和端口，支持云数据库；默认 localhost:3306 |
| `DATABASE_CONN_MAX_AGE` | 数据库连接复用时间，单位秒，默认 0 |
| `DATABASE_POOL_SIZE` / `DATABASE_MAX_OVERFLOW` / `DATABASE_POOL_TIMEOUT` / `DATABASE_POOL_RECYCLE` | 关键词检索的 SQLAlchemy 连接池参数；数据库密码中的 @、/、# 等字符按原值处理 |
| `CORS_ALLOW_ALL_ORIGINS` / `CORS_ALLOWED_ORIGINS` | 默认不开放跨域；允许来源使用完整 origin，以逗号分隔 |
| `CSRF_TRUSTED_ORIGINS` | 逗号分隔，带 http/https 协议 |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | HTTPS 部署时设为 True |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | 所有 ChatOpenAI 调用统一读取；调用 AI 时必填；模型需由你的服务支持 |
| `CAREER_REPORT_MODEL` | 可选，为职业报告单独选模型；留空时使用 LLM_MODEL |
| `LLM_TIMEOUT` | 模型请求超时，单位秒，默认 120 |
| `ASR_API_KEY` / `ASR_WSS_URL` / `ASR_MODEL` | 语音识别的凭据、WebSocket 地址和模型；使用该功能时必填，空 key 复用 LLM_API_KEY |
| `ENABLE_TTS` | 默认 False；启用后会调用语音合成服务 |
| `TTS_API_KEY` / `TTS_WSS_URL` / `TTS_MODEL` / `TTS_VOICE` | 语音合成配置；空 key 复用 LLM_API_KEY；前端也需要 VITE_ENABLE_TTS=True |
| `LANCEDB_PATH` | 向量数据库目录，默认项目根目录 .runtime/lancedb；同步脚本与查询使用同一配置 |
| `EMBEDDING_ENABLED` | False 时跳过本地模型导入和加载，检索降级为关键词检索；本机示例默认 False |
| `EMBEDDING_DIMENSION` | 默认 512，与中文 BGE-small-zh-v1.5 一致；所有建表、写入及模型输出校验共用此值 |
| `EMBEDDING_MODEL` | 默认 BAAI/bge-small-zh-v1.5；替换时必须与配置的维度一致，旧向量应重新计算 |
| `EMBEDDING_MODEL_PATH` | 可选，优先使用指定的本地模型目录；相对路径基于 backend/ |
| `EMBEDDING_DEVICE` | 默认 cpu，可由实际运行环境选择其他设备 |
| `EMBEDDING_ALLOW_DOWNLOAD` | 是否允许联网补下载权重；示例设为 False；离线时也会尝试已有 Hub 缓存 |
| `SEARCH_MAX_WORKERS` | 各检索线程池的并发上限，默认 3；小内存服务器可设为 1 |
| `CAREER_REPORT_MAX_WORKERS` | 职业报告并行分析数量，默认 4；小内存服务器可设为 1 |
| `STATIC_URL` / `STATIC_ROOT` | Django 静态文件 URL 与 collectstatic 输出目录 |
| `MEDIA_URL` / `MEDIA_ROOT` | 用户上传文件 URL 与保存目录 |
| `CACHE_BACKEND` / `CACHE_LOCATION` / `CACHE_TIMEOUT` | 默认进程内缓存；切换 Redis 时需自行准备 Redis 服务及对应 location |
| `SESSION_ENGINE` / `TIME_ZONE` / `LANGUAGE_CODE` | 会话后端、时区、语言 |
| `RESET_PASSWORD_USERNAME` / `RESET_PASSWORD_PASSWORD` | 仅密码重置工具需要；不再内置管理员账号或密码，也不会输出密码 |

数据目录支持绝对路径；相对路径基于 `backend/`，不依赖启动命令的当前目录。模型目录支持 `~` 和操作系统环境变量展开。

兼容旧变量 `api_key`、`base_url`、`career_report_model`、`WSS_URL`。优先使用新的规范变量名；`WSS_URL` 可兼容旧的共享语音地址，新的 ASR_WSS_URL/TTS_WSS_URL 支持分开设置。

模型权重仍需另行准备。历史提交把 `~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5` 作为仓库内的字面路径纳入 Git；其中两个 133 字节的 LFS 指针不能作为完整权重使用。现已取消该缓存目录的版本跟踪，并从 Docker 构建上下文排除，本地已有文件保留。旧 Git 历史未改写，新克隆不再从当前源码树获得这些缓存文件。

`BAAI/bge-small-zh-v1.5` 用于把文本转换成 512 维向量供语义检索使用，不是聊天/模拟面试的远程 LLM，也不需要模型 API Key。需要启用时，把完整权重放到仓库外的本地目录并配置 `EMBEDDING_MODEL_PATH`，或使用实际用户目录中的 Hugging Face Hub 缓存；正常的 `~` 表示用户目录，与仓库内名为 `~` 的遗留文件夹不同。代码仍兼容查找本地遗留目录，此次没有更改模型选择、开关或检索逻辑。

开发示例默认 `EMBEDDING_ENABLED=False`、`EMBEDDING_ALLOW_DOWNLOAD=False`，不会因这次清理自动下载模型。配置路径不会修复缺失的权重；关闭自动下载且无可用模型时，原有关键词检索降级行为仍会生效。注意 settings.py 在未显式设置开关时的默认值与开发样例不同，实际运行应使用明确配置。

## 旧向量库的显式迁移

原仓库的向量表是 384 维，并且存在多个不一致的建表入口。现在所有入口共用 512 维 schema，并检查真实模型输出维度。缺少模型时向量为空，不再补零或截断向量伪造结果。

旧库仍保留在 `backend/ai_integration/lancedb`，代码不会自动修改它。需要使用旧记录时，手动复制迁移到一个新的目录：

```bash
python backend/migrate_vector_store.py --source backend/ai_integration/lancedb --destination .runtime/lancedb --dimension 512
```

该工具无需连接 MySQL，也不加载模型；保留原库，检查业务字段和行数，拒绝覆盖已有目标表。旧的 384 维或全零向量会置为空，等待真实模型重新生成；不会把旧向量补零当作有效的 512 维向量。运行时若指向旧 schema，会提示先迁移。

以后在模型权重、数据库和环境变量配置完成后，可手动运行 `python backend/sync_recommendations.py`，按 ID 同步数据库记录并重算向量。同步脚本不再删除现有 LanceDB 表；关闭模型时仅同步文本和业务字段。

提示词初始化已移到迁移完成后的 post_migrate 阶段，启动钩子不再提前查询尚未创建的表。企业外部表和业务数据仍需另行准备；这些不是硬件配置问题。

## 前端与开发代理

| 变量 | 说明 |
| --- | --- |
| `VITE_API_BASE_URL` | Django API 前缀，默认 /api；支持反向代理路径或完整服务 URL |
| `VITE_COMPANY_API_BASE_URL` | 原项目独立企业查询服务的 API 前缀；未设置时使用主 API 前缀 |
| `VITE_API_TIMEOUT_MS` / `VITE_COMPANY_API_TIMEOUT_MS` | Axios 请求超时，单位毫秒，默认 120000 / 30000 |
| `VITE_VAD_ASSET_BASE_URL` | VAD ONNX、worklet、WASM 的资源目录；默认应用 public/models/vad/ |
| `VITE_AVATAR_MODEL_URL` | 3D 数字人 GLB 文件地址 |
| `VITE_ENABLE_TTS` | 浏览器侧语音合成开关；默认 False |
| `VITE_GEOCODING_URL` | 可选的兼容 OpenCage 响应结构的逆地理编码接口，自动附加 q 和 language 参数 |
| `VITE_IP_GEOLOCATION_URL` | 可选的 IP 定位接口，响应需有 status=success 及 city/regionName；可在 URL 中配置查询参数 |
| `DEV_HOST` / `DEV_PORT` | 本地 Vite 监听地址与端口，默认 127.0.0.1:3002 |
| `DEV_API_PROXY_TARGET` | 本地 Vite 对主 API 的代理目标，示例指向 Django 开发服务器 |
| `DEV_COMPANY_API_PROXY_TARGET` | 独立企业服务的开发代理，示例指向旧端口 3000，并将 /company-api 前缀替换为 /api |

所有直接 fetch 请求（流式聊天、浮动助手、面试复盘、职位查询）和 Axios 请求使用相同 API 前缀。默认的同源路径不再指向访问者机器上的 localhost。

定位接口留空时跳过远程定位，保留手动选城市。需要 provider key 的服务应通过你自己的后端代理处理；不要把秘密 key 放入 VITE_* 或客户端 URL。

独立企业查询接口是原项目已有的服务调用，本仓库的 Django 没有提供 /api/search、/api/city 等对应接口。示例中的 3000 端口不会启动该服务，需要自行接入，或者后续改造为 Django 接口。

VITE_* 在 `npm run build` 时写入静态文件，修改后必须重新构建。DEV_* 不会进入客户端代码，只用于 `npm run dev` 的代理；生产环境需配置 Nginx 对主 API、可选企业 API、media/static 路径的代理或文件服务。流式 API 还需关闭代理缓冲并设置合适的超时。

## 生产配置示例

以下片段用于说明，须替换为真实域名并通过服务器环境补充密钥与数据库密码：

```env
# backend/.env
DEBUG=False
ALLOWED_HOSTS=career.example.com
CSRF_TRUSTED_ORIGINS=https://career.example.com
CORS_ALLOW_ALL_ORIGINS=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SEARCH_MAX_WORKERS=1
EMBEDDING_DEVICE=cpu
EMBEDDING_ALLOW_DOWNLOAD=False
```

同源部署的前端主 API 可以保留 `/api`；只需在 Nginx 中反向代理该路径，无需把公网 IP 写入源码。

## 配置回归检查

```bash
python -m unittest discover -s backend/tests -p 'test_*.py'
cd frontend
node --test tests/config.test.mjs
npm run build
```

配置测试无需真实数据库或 AI key；完整启动、迁移和业务验证还需要实际数据库、业务数据、模型和对应 API 凭据。

## 独立交付配置

- Actions `workflow_dispatch.component` 为 frontend/backend/all，默认 all；手动指定只影响当前构建/发布选择，不改变服务器开关。
- `DEPLOY_ENV_SYNC_ENABLED` 是自动激活总开关；新 `DEPLOY_FRONTEND_ENABLED` / `DEPLOY_BACKEND_ENABLED` 默认关闭，必须精确为 `true` 才激活相应组件。回滚期间可独立关闭目标组件。
- `DEPLOY_COMPONENT` 与 `DEPLOY_IMAGE` 由 workflow 写入同步进程环境；后者来自该组件完成发布的完整 digest，不是用户密钥，也不进入应用容器。
- `BACKEND_IMAGE` / `FRONTEND_IMAGE` 是基础 Compose 的可选完整引用；空值回退到各自 `*_TAG`。自动激活生成的 `docker-compose.<组件>-image.json` 优先于基础配置；手工维护需明确加载 pin 文件。
- Compose 已接入 `CORS_ALLOW_ALL_ORIGINS`、`CORS_ALLOWED_ORIGINS`、`CSRF_TRUSTED_ORIGINS`；跨域时仅允许所需的完整 origin，同源默认不变。前端构建 URL 必须包含 API 前缀；构建参数不能传密钥。

操作、文件权限和失败保留见[独立交付](split-delivery.md)。
