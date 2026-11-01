# 项目文档索引

本文件是项目导航入口；自动化协作规则见 [AGENTS.md](AGENTS.md)。阅读时按任务选择相关文档，无需每次遍历全部运维历史。

## 新成员与日常开发

| 文档 | 什么时候读 |
| --- | --- |
| [README](README.md) | 了解项目目标、技术栈和功能入口 |
| [开发指南](docs/development.md) | 定位代码、准备本地环境、选择测试方式 |
| [Git 与文档协作规范](docs/git-workflow.md) | 分支开发、commit、PR、合并及文档更新 |
| [环境变量配置](docs/environment.md) | 增加或修改配置、理解前后端配置边界 |

## 业务实现与验收

五人开发先读 [公共约定](docs/implementation/00-shared-contracts.md)，再读对应专用文档：

- [成员1：数据目录](docs/implementation/01-data-catalog.md)：来源、导入、岗位/企业/题库与专项验收。
- [成员2：评估调优](docs/implementation/02-evaluation.md)：数据集拆分、指标、策略和对照。
- [成员3：简历优化](docs/implementation/03-resume-optimization.md)：证据、编辑确认和版本冲突。
- [成员4：面试RAG](docs/implementation/04-interview-rag.md)：检索、来源、反馈和记录交接。
- [成员5：练习记录](docs/implementation/05-practice-records.md)：快照、幂等、总结与重试。

| 文档 | 内容与边界 |
| --- | --- |
| [当前需求方案与五人分工](docs/career_platform_plan.md) | 唯一有效的需求与分工依据；制定实施计划、拆分模块及约定接口前先读，内容是待开发目标 |
| [统一登录门槛](docs/authentication-gate.md) | 前端路由与后端鉴权、Token 行为、隔离测试 |
| [模拟面试重构](docs/interview-refactor.md) | legacy 主链路、交互与简历观览；ASR/TTS 和浏览器录音的验收边界 |

新业务模块有独立接口、数据模型或流程约定时，在 docs 下增加短文档并补到本表。需求提案和实现说明分别标注，未提交的个人草稿不作为团队事实来源。

为各成员准备需求文档前，先以最新 `origin/master` 和部署状态核对现有能力；旧个人分支可能落后，方案中列出的 MySQL、RAG、模型评估和逐题记录均需逐项确认，不直接当作已实现。

## 发布与运维

| 文档 | 什么时候读 |
| --- | --- |
| [部署与运维总览](docs/deployment.md) | 理解整条发布链路与运维入口 |
| [验收状态与接手记录](docs/deployment-status.md) | 核对带日期的证据、未完成事项；执行前刷新当前状态 |
| [CI/CD 流水线](docs/ci-cd.md) | 分支触发规则、测试、构建、发布、失败排查 |
| [AI 环境同步](docs/ai-env-sync.md) | 模型/SSH 配置、白名单、自动重建及安全边界 |
| [Docker 镜像](docs/docker-images.md) | 镜像组成、运行依赖、构建参数 |
| [服务器拉取部署](docs/server-pull.md) | 部署账号、服务器前提、存储与手动操作 |
| [宿主机保护边界](docs/host-protection.md) | 权限、资源与尚未隔离验收的风险 |
| [Watchtower 与回滚](docs/watchtower-rollback.md) | 更新入口协调、成对 digest 回滚、失败处理 |
| [前端部署排障](docs/troubleshooting-frontend.md) | 端口、Nginx 和访问异常 |

## 文档维护约定

接口、配置、数据结构、核心业务或部署行为改变时，同一个 PR 更新相关文档。优先修改现有说明，只有存在独立主题时才新增文件；不要为每个 commit 生成一份流水账。

文档应说明问题、当前行为、主要入口、使用/验证方法及已知限制。计划与已验证结果分开，不能把 CI 通过写成真实模型或生产验收成功。密钥、真实环境文件、用户数据与未脱敏日志不得入库。

本索引只维护链接和定位信息，配置值与运行状态在对应专题中维护，避免多处复制后失去一致性。
