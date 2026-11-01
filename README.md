# 计算机学院本科生就业指南

计算机学院本科生就业指南是一个专为计算机专业学生打造的**全栈职业指导平台**，通过数据驱动和AI技术，为学生提供从职业规划到求职面试的全方位支持。

## 开发与文档入口

先读 [agent.md 文档索引](agent.md)，日常开发参考 [开发指南](docs/development.md) 和 [Git/PR/commit 规范](docs/git-workflow.md)。自动化协作入口为 [AGENTS.md](AGENTS.md)。主分支统一使用 `master`，个人长期开发使用 `codex/personal`，通过 PR 合入本 fork 的 master；误建的 main 不再用于日常开发。功能、接口、配置或部署行为改变时，在同一 PR 补最少必要文档。

当前需求与五人分工统一以 [career_platform_plan.md](docs/career_platform_plan.md) 为准。该文件是待开发目标；当前代码与线上能力、SQLite 演示环境、数据缺口和验收边界见 [部署状态](docs/deployment-status.md)，不要仅凭下方技术栈或功能介绍判断已实现范围。

## 🎯 项目目标

- 为计算机学院本科生提供全方位的职业指导
- 利用数据与AI填补信息差
- 打造沉浸式求职体验
- 帮助学生锁定顶级Offer

## 🏗️ 技术架构

### 前端技术栈

- **框架**: Vue 3 + Vue Router + Pinia
- **UI组件**: DaisyUI
- **构建工具**: Vite
- **样式**: Tailwind CSS

### 后端技术栈

- **框架**: Django + Django REST Framework
- **数据库**: MySQL + LanceDB
- **AI集成**: LangGraph 多智能体工作流
- **语义搜索**: Sentence-BERT (bge-small-zh-v1.5)

### 预留功能接口

- 国内大模型API接口
- 3D数字人接口

## ✨ 核心功能模块

### 1. 职业发展路径选择

- 就业、考研、考公、入伍、创业五大方向
- 20+ 细分技术方向的技能树
- 根据技术趋势动态更新的学习路径

### 2. 职业测评系统

- 多维人格评估
- 技术栈匹配度分析
- 个性化职业建议

### 3. 企业评价系统

- 真实职场评价（脱敏处理）
- 企业推荐与预警
- 严格的人工审核与身份核验

### 4. AI 面试模拟仓

- 深度集成 LangGraph 多智能体
- 模拟真实技术面试官
- 实时反馈与专业改进建议
- 支持语音交互（ASR/TTS）

### 5. 简历管理

- 简历创建与优化
- 模板选择
- 简历投递跟踪

### 6. 语义搜索

- 基于向量数据库的智能搜索
- 支持关键词搜索、语义搜索、混合搜索

## 🚀 快速开始

### 环境要求

- Python 3.11（当前 requirements.txt 中 NumPy / Pandas 要求至少 3.11）
- Node.js >= 22.12（当前 Vite 版本的要求）
- MySQL >= 8.0

### 后端启动

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 SECRET_KEY、数据库密码和所需 AI 服务配置。
cd backend
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 前端启动

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

### 配置说明

复制 `backend/.env.example` 和 `frontend/.env.example` 为各自目录下的 `.env`，然后填写真实配置；真实 `.env` 文件已被 Git 忽略，示例文件可以提交。

- 后端读取 `backend/.env`，系统环境变量优先。`SECRET_KEY`、`DATABASE_NAME`、`DATABASE_USER` 和 `DATABASE_PASSWORD` 缺失时会明确报错。
- 所有聊天代理统一读取 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。语音接口和模型、本地向量模型、数据目录、并发数均可单独配置。
- 前端读取 `VITE_API_BASE_URL`、`VITE_COMPANY_API_BASE_URL` 和模型资源地址；流式聊天同样使用配置后的 API 地址。
- **`VITE_*` 会进入浏览器代码，不得放密钥。修改前端配置后需重新构建；修改后端配置后需重启服务。**
- 云服务器上使用 `DEBUG=False`、明确的 `ALLOWED_HOSTS`，通过 Nginx 提供前端构建产物并反向代理 API；开发用的 Vite 代理不会随构建产物部署。

完整变量说明、兼容规则和部署示例见 [环境变量配置](docs/environment.md)。

## 🚀 部署与运维

2026-10-23，AI 环境同步、自动重建和面试 legacy 重构的提交 `33cbc57` 已通过 [build-only Actions 39979362642](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39979362642)，随后按主分支约定整合进 master。本会话已观察到服务器前后端健康、旧 Watchtower 运行，并完成专用部署账号及 Actions 配置。当前 master 的验证与发布以 [Actions](https://github.com/vacontinuejatotired/CS-Career-Guide/actions?query=branch%3Amaster) 为准；服务器 AI 同步仍关闭，真实模型、语音及浏览器全流程待验收。请先阅读：

- [部署与运维总览](docs/deployment.md)
- [宿主机保护边界](docs/host-protection.md)
- [验收状态与接手记录](docs/deployment-status.md)
- [CI/CD 流水线](docs/ci-cd.md)
- [AI 配置同步与自动重建](docs/ai-env-sync.md)
- [Docker 镜像](docs/docker-images.md)
- [服务器拉取部署](docs/server-pull.md)
- [Watchtower 与回滚](docs/watchtower-rollback.md)
- [模拟面试重构与替换边界](docs/interview-refactor.md)

真实密钥、ACR 密码、数据库密码和服务器 `.env` 不得提交到仓库。

## 🌟 技术亮点

- **多智能体协作**: 基于LangGraph构建的面试代理、职业代理、推荐代理等专业智能体
- **实时语音交互**: 集成语音识别(VAD)和语音合成(TTS)功能
- **语义搜索**: 使用LanceDB向量数据库实现精准职业推荐
- **响应式设计**: 现代化UI设计，支持移动端访问

## 📁 项目结构

```
cs-career-guide/
├── backend/                    # 后端Django项目
│   ├── ai_integration/         # AI集成模块
│   ├── career_evaluation/      # 职业测评模块
│   ├── career_paths/           # 职业路径模块
│   ├── company_reviews/        # 企业评价模块
│   └── cs_career_guide/        # Django配置
├── frontend/                   # 前端Vue项目
│   ├── src/
│   │   ├── components/         # 组件
│   │   ├── views/              # 页面视图
│   │   ├── api/                # API接口
│   │   └── stores/             # 状态管理
│   └── public/                 # 静态资源
└── README.md                   # 项目文档
```

## 📊 适用人群

- 计算机学院本科生
- 计算机相关专业学生
- 希望进入IT行业的求职者
- 需要职业规划指导的技术人员

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！
