# 统一登录门槛

2026-10-19。本次修改完成本地代码与隔离验证，并按用户要求准备独立的本地提交；最终提交号以 Git 记录为准，未推送或部署。

## 访问规则

- 前端仅 `/login`、`/register` 公开，其他页面默认要求登录。职业详情和自我介绍的匿名例外已移除。
- 业务路由每次进入前调用 `/api/users/profile/` 校验真实 Token；校验失败不进入业务页。401 清理登录态；网络或服务错误保留 Token，返回登录页以便重试。
- 登录和注册后回到原业务路径，保留查询参数和 hash。回跳只接受站内路径，拒绝外部地址、反斜杠、畸形编码及登录/注册循环；无匹配路由时回首页。
- 后端 `/api` 和 `/api/` 下的全部入口默认要求 DRF Token。公开白名单仅 `/api/users/auth/login/`、`/api/users/auth/register/`，按完整路径匹配。
- 缺失、伪造、撤销、禁用用户的 Token 及畸形认证头返回 401，包含 `WWW-Authenticate: Token`。普通 Django view 与 DRF view 均受保护。
- CORS 预检保留；普通 OPTIONS 返回 204，不执行业务视图。Django `/admin/` 保留原有登录机制。
- 登录和注册请求不发送旧 Token，后端这两个视图也禁用 Token 认证，保证旧凭据不阻止重新登录。
- 登录、注册页不挂载全局 AI 浮窗，导航栏不主动同步旧用户资料。
- 静态资源和现有媒体访问方式保留。第三方定位、地理编码和媒体下载继续使用原生 fetch，不附加用户 Token。

## 本次文件范围

后端：

- `backend/cs_career_guide/middleware.py`：新增统一 API 门禁与普通 Django 视图用户注入。
- `backend/cs_career_guide/settings.py`：注册中间件，DRF 默认权限改为 `IsAuthenticated`。
- `backend/users/views.py`：登录、注册显式不校验旧 Token。
- `backend/company_reviews/views.py`：企业、企业信息、招聘会启用 Token 认证与登录权限。
- `backend/career_evaluation/views.py`：计算机职业接口取消匿名权限。
- `backend/ai_integration/langgraph_views.py`、`optimized_views.py`、`career_report_views.py`：AI 函数视图改为登录权限。

前端：

- `frontend/src/auth/session.js`：统一清理会话、安全回跳、401 跳转及过期请求保护。
- `frontend/src/api/transport.js`、`frontend/src/api/index.js`：主 API、企业 API 共用 Axios 认证策略；新增 apiFetch，保留原始流式 Response。
- `frontend/src/router/guard.js`、`frontend/src/router/index.js`：默认拦截所有业务页，并在进入前校验 Token。
- `frontend/src/App.vue`、`frontend/src/components/Navbar.vue`：公开页隐藏 AI 浮窗并避免旧 Token 资料请求；退出统一清理。
- `frontend/src/views/auth/Login.vue`、`Register.vue`：安全回跳，登录与注册相互切换时保留目标。
- `frontend/src/components/AIFloat.vue`、`frontend/src/views/interview/Index.vue`、`frontend/src/views/company-reviews/Index.vue`：业务 fetch 统一附带 Token 和处理 401。
- `frontend/src/views/career-paths/SelfIntroduction.vue`：提交前必须完成已登录用户资料更新。
- `frontend/src/views/users/Index.vue`：移除重复的局部 401 跳转，交由统一处理保留原目标。

上述文件中的原有配置、AI 和向量相关改动均保留，不能将整个工作区 diff 都归为本次鉴权工作。

## 验证记录

- 后端 `tests/test_auth.py`：14 项通过。包括 16 个路径 × 6 种 HTTP 方法 × 6 种缺失或错误认证头，共 576 个拒绝场景。
- 使用真实用户与 DRF Token 模型验证登录、注册、登出、禁用用户、撤销 Token、Django/DRF 用户身份传递及默认权限。
- 验证未来 API 即使显式允许匿名也会被中间件拦截，认证白名单不能通过附加路径绕过。
- 验证真实聊天函数在模型边界 Mock 后能返回惰性 StreamingHttpResponse；不迭代付费模型生成器。同时通过无付费依赖的流式探针检查中间件不提前消费内容。
- 前端 `tests/auth.test.mjs`：13 项通过，覆盖真实 Vue Router 内存导航、失效凭据、回跳、安全路径、两套 Axios、fetch 与流式 Response。
- 已有后端配置测试 16 项、前端配置测试 6 项通过。
- 前端 Vite 生产模式编译通过，输出到忽略目录 `frontend/.runtime/auth-build`。验证时禁用真实 dotenv 读取，同时保留项目 Tailwind 配置加载；未使用发布配置。
- Playwright 浏览器验证：六个主要业务入口匿名跳转、注册表单提交 201 后回跳、旧 Token 登录 200 且不发送旧认证头、真实 profile 身份确认、伪造 Token 清理、登出 200 后重新拦截、公开页没有 AI 浮窗。浏览器和临时测试服务均已关闭。
- `git diff --check` 和本次后端 Python 编译检查通过。

后端隔离测试从 `backend` 目录运行：

```powershell
..\.venv\Scripts\python.exe -m django test tests.test_auth --settings=tests.auth_settings --verbosity=1
```

前端鉴权测试从 `frontend` 目录运行：

```powershell
node --test tests/auth.test.mjs
```

`tests/auth_settings.py` 禁止加载真实 .env，使用内存 SQLite，不加载 AI 应用，不连接 MySQL 或 LanceDB。新增 `tests/__init__.py`、`auth_urls.py` 支持隔离执行。浏览器验证也使用同一隔离配置与内存数据库。

本地虚拟环境补充了仓库现有锁定版本 `djangorestframework==3.14.0`、`django-cors-headers==4.3.0`，未修改依赖清单或升级 Django。

## 验证边界

- 本次建立统一登录门槛，不代表已完成管理员/普通用户授权、数据归属或所有越权问题审计。企业写入、删除和审核操作登录后的角色规则保持现状。
- 真实 MySQL 业务数据、独立企业服务和付费 AI 未参与本次验证。若另行配置外部企业服务，其服务端仍需自己执行 Token 校验；当前仓库中间件仅保护本 Django 服务。
- 上传媒体仍按已有公开 URL 加载，本次未加入媒体私有访问机制。
- 未进行真实模型文本/语音生成、生产部署验证或真实数据库迁移，旧 LanceDB 保留。
- 构建仍有原有的 Browserslist 数据、Vue 深层选择器和大包体积警告，不影响本次编译通过。
