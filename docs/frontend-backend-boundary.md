# 前后端边界与 API 模块

## 当前边界

前端是独立的 Vue/Vite 单页应用，后端提供 Django HTTP API。前端构建时通过 `VITE_API_BASE_URL`、`VITE_COMPANY_API_BASE_URL` 注入公开 API 地址；本地开发使用 `DEV_*_PROXY_TARGET` 配置 Vite 代理。`VITE_*` 会进入浏览器，不能放置密钥。

前端不直接依赖 Django 模型、序列化器或数据库。页面通过 `frontend/src/api/` 调用后端，Token 注入、401 处理和流式请求分别集中在 `api/transport.js` 与 `auth/session.js`。

## API 模块

| 模块 | 前端入口 | 后端范围 |
| --- | --- | --- |
| 认证 | `api/auth.js` | `/api/users/auth/` |
| 用户 | `api/users.js` | `/api/users/` |
| 简历 | `api/resumes.js` | `/api/resumes/` |
| 面试与 AI | `api/interview.js` | `/api/ai/`、`/api/asr/`、`/api/career-report/` |
| 企业与职业数据 | `api/companies.js` | `/api/company-reviews/`、`/api/career-evaluation/` 及独立企业服务 |

`api/index.js` 仅作为兼容性聚合入口，新页面应直接依赖对应业务模块。拆分 API 模块不改变现有路径、请求字段、响应格式或认证方式。

## 独立部署约束

- 前端只配置公开 API 地址；密钥、模型配置和数据库凭据只在后端部署环境维护。
- 生产环境需分别验证前端静态资源、Django API、独立企业服务和 SSE/文件上传路径。
- 更换前端时优先复用本目录中的模块和合同测试，不从页面代码复制请求细节。
- 新增或修改接口时，先更新对应 API 模块和合同测试，再修改页面。
