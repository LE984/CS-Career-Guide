# CI/CD 流水线

本分支自 2026-11-01 拆为组件交付；当前 Actions 与服务器状态须分别确认，不能沿用历史绿色结果。完整边界见[单仓库独立交付](split-delivery.md)。

## 触发与选择

push 覆盖所有分支，PR 目标为本 fork master。主题分支和 PR 仅 build-only；只有 `vacontinuejatotired/CS-Career-Guide` 的 master push/手动事件且 `SPLIT_DELIVERY_RELEASE_ENABLED=true` 时能发布。新发布开关默认关闭，首次合并保持 build-only，先协调旧自动更新和服务器拓扑，再显式开启。手动 `component=frontend/backend/all`，默认 all，可附加合法 `extra_tag`。

`changes` 用完整 Git diff（含删除和跨目录移动）调用 `ci/component_changes.py`：仅 frontend/ 选前端，仅 backend/ 选后端，README.md/docs 不选镜像，共享/未知路径选两端。新主题分支与 origin/master 共同祖先比较，初始 master 选择全树；不只看最后一个提交。

## Job 依赖

```text
changes -> frontend-test -> frontend-image -> publish-frontend -> deploy-frontend
        -> backend-test  -> backend-image  -> publish-backend  -> deploy-backend
        -> delivery-checks --------------------^                 ^
        -> platform-gates ---------------------^                 |
两端均选中 -> integration（两个候选归档、真实网关/持久化、合成 SSE/IP）--^
全部结果 -> release-summary（always；严格区分 required、skipped 与 failure）
```

- frontend-test：Node 24、npm ci、全部 tests/*.test.mjs、Vite 构建与 GLB/VAD 资源检查。
- backend-test：Python 3.11、backend/requirements.txt 的 UTF-16 临时转码、原鉴权、配置、面试/ASR、迁移隔离回归与 Django check。
- delivery-checks：无应用/模型依赖的 ci 单元测试；runner 解析默认/updates/MySQL/digest Compose，验证端口、用户、只读挂载、资源与 CORS 接线。
- 各 image：自身目录上下文，多阶段构建，push=false/load=true；单镜像冒烟、导出和再次加载身份验证。前端冒烟不提供后端/DNS。后端 image 不等待前端。
- integration：仅两端同时选中时要求成功；下载两份已测试归档，无 ACR Secrets。`demo_smoke.py` 验证真实 gateway/frontend/Django、注册登录/401、static、资料、SQLite 持久化及独立重建；`gateway_smoke.py` 用合成上游验证头/query、media、SSE 首事件及两端换 IP。仅 runner 可启动 Docker。
- publish-frontend/backend：只依赖自身测试/image、delivery-checks、业务门禁及所需 integration，不等待另一 publisher。只下载对应归档，确认 commit、image ID、平台后推送同一镜像，不重新构建。共享所需 integration 被跳过/失败时不得发布。
- deploy-frontend/backend：仅对应 publisher 成功、fork/master、非 PR、总开关与对应分端开关同时为 true 时执行。输入是该次发布 digest；前端不接收模型字段。细节见[AI 同步](ai-env-sync.md)。
- release-summary：对已选组件要求 test/image 与预期发布/部署结果正确；未选组件要求全部 skipped。单端完整容器联调明确记为 SKIPPED，不能报告已通过。

## 业务门禁

Platform documentation 继续以 PR base / push before 的归属表为准检查模块文档和 acceptance-record。交付编排 ci-cd.yml 仅在前后端既有测试 Job 与基线保持一致时被区分；修改测试命令、跳过条件、continue-on-error 或删除测试仍进入原完整业务门禁。业务代码、公共契约、固定测试/验收规则和未知 workflow 仍按原规则选择 complete。普通前端静态变更不启动 SQLite/MySQL 业务 runner，前端模块路径仍触发原业务验收。混入业务文件不会因同时有交付文件而被豁免。

最初拆分 PR 修改了检查器与 career-platform.yml，因此该批改动需要六份实施记录及原全部业务验收。五个模块当前仍是 501 骨架；本地 17 项 complete 失败如实保留，不能靠降低固定测试标准使发布通过。交付验证和业务完成分开记录。

2026-11-01 用户明确授权保留并说明此既有业务失败后合并拆分 PR、更新服务器。该授权不改变测试结果或固定规则。首次合并关闭发布与自动激活，服务器操作通过手动 `Split delivery maintenance` workflow 的严格 SSH 核验通道执行；当前 `audit` 只输出镜像/容器/端口/卷等选定元数据，不读取或替换真实 `.env` 内容，不输出展开的 Compose 或容器环境值。

### SQLite/MySQL 验收失败对开发与发布的影响

两个 `Platform acceptance` job 运行 `ci/project_ci.py`：先在各自隔离数据库执行 scaffold（含迁移/鉴权/契约），再按 `platform-selection.json` 选择完整业务用例。2026-11-01 两种数据库的完整 17 项均出现 14 failures、3 errors，日志指向五模块 `501 / FEATURE_NOT_IMPLEMENTED`；不能据 job 名称将其认定为数据库连接/迁移故障。后续若出现连接或迁移异常，仍需按该次日志单独处理。

| 变更范围 | 业务验收与发布影响 |
| --- | --- |
| README.md / docs/ | 不选择应用镜像；文档检查成功不表示业务 complete 通过 |
| 普通前端静态资源、非业务交付脚本 | 按路径不启动完整业务验收；交付共享改动仍需双端镜像和网关联调 |
| 普通后端代码 | 可启动 SQLite/MySQL scaffold；具体 complete 选择以报告为准，不无条件跑五模块 |
| 五模块归属路径（含对应前端页面） | 运行选中的模块 complete；该模块 501 失败会阻止本次选中组件发布 |
| 公共契约、固定验收规则、未知 workflow 等共享归属路径 | 运行原全模块 complete；当前未完成业务会使门禁和对应发布失败 |

这些失败不停止已部署容器，也不要求切换服务器数据库。用户接受既有失败后合并的授权适用于本轮交付拆分，不自动放行未来业务发布；对应业务实现应保留固定验收并让其转绿。

## 发布与记录

ACR_REGISTRY/ACR_NAMESPACE 仅 publisher 从 Variables 或同名 Secrets 读取（Variables 优先）；ALIYUN_ACR_USERNAME/ALIYUN_ACR_PASSWORD 用于登录。构建/联调不读取注册表凭据。镜像缓存 scope 仍按两端分别设置，关闭 provenance/SBOM 保留现有 ACR 兼容。

`ci/release_images.py verify/publish --component frontend` 或 backend 只需要对应归档；不指定组件的旧 CLI 保持双组件兼容。可重复 --component，但空/未知/重复选择会拒绝。每组件先推 sha-<7位SHA> 和可选版本标签，再推 latest；核对每次 manifest digest 一致。

`published-frontend-<run-id>` / `published-backend-<run-id>` 各自保存 `published-images.json`，含 components、compatibility（component-contracts / candidate-integration / not-recorded）、完整 commit、image ID、标签、digest/reference 与 complete。complete=false 是部分失败，不可部署；latest/SHA tag 可改写，精确恢复用 digest。两个 publisher 相互独立，不承诺两端发布原子性。

归档保留 1 天，普通日志 7 天，发布记录 30 天；不上传真实环境/凭据。一个 ref 的 push 发布不取消旧运行，PR 可取消旧运行；服务器激活共用独立 concurrency group 和远端文件锁。Actions 并发组不替代手工回滚协调。

`check_build_context.py` 在 runner 用 scratch COPY 导出实际上下文，核对虚构的 .env、私钥、SQLite/media/LanceDB 或 node_modules 探针未进入上下文；正常源码与样例仍存在。该脚本拒绝在非 Actions 环境运行，本地只测其拒绝/泄漏判定。

## 验收与失败排查

本地离线运行 `python -m unittest discover -s ci -p 'test_*.py' -v`；Windows 的 POSIX 测试跳过，须在 Linux/WSL 或 runner 运行。前端与后端原测试命令见 development.md。Docker 构建、进程和网络结果仅以对应 commit 的 Actions 为准。

单端协议测试不证明和任意线上旧版本兼容；破坏合同的改动需兼容窗口与指定组合联调。镜像发布不证明服务器部署，容器健康不证明真实模型/浏览器验收。Watchtower 若另外启用仍可能因 latest 更新自动激活，回滚前协调入口。

常见问题：UTF-16 源改路径后转换失败时检查 backend/requirements.txt；旧 Dockerfile 根路径必须移除；gateway 缺失/前端仍有端口或共享卷时新同步拒绝；只设置旧总同步开关不会触发新分端部署；完整业务 501 失败应作为业务未完成处理，不能改成通过。

## 缓存与耗时定位

当前已启用 `setup-python` 的 pip 下载缓存、`setup-node` 的 npm 下载缓存，以及前后端各自的 BuildKit GHA 层缓存。pip/npm 缓存不会保留安装后的虚拟环境或 node_modules，新的 runner 仍会安装依赖和执行测试；镜像缓存命中也仍需导出、上传归档及运行容器检查。publisher 复用已验证的镜像归档，不重新构建。

2026-11-01 成功运行 [41307140743](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41307140743) 的 backend pip 日志明确显示 Cache hit / Cache restored，后端 Docker 多个依赖与应用层为 CACHED。该运行前端/后端镜像构建步骤约 17/22 秒；后端完整测试依赖安装约 90 秒，共享联调步骤约 153 秒。整个运行约 7 分钟，主要受后端检查到镜像再到共享联调的依赖链影响；这些数据是单次运行快照，不是后续时延承诺。

仅前端变更会跳过后端检查/镜像/发布/部署；仅后端变更同理。共享交付配置仍需要双端和完整网关联调，不能为加速删除必要验证。排查慢任务时先区分 cache restore、依赖安装、Docker build、镜像归档传输、联调和服务器拉取，不把总时长全部归因于缓存未命中。

首次网关维护的镜像传输与日常构建缓存不同。SSH 大归档曾超时，维护任务改为 runner 用既有 ACR 凭据发布专用 `gateway-nginx-<imageID>` 基础设施标签，按 digest 校验后由服务器拉取；不改前后端 `latest`/SHA 标签，日常单端发布不执行该步骤。只读 audit 不传入 ACR 凭据。

2026-11-01 最终安装与独立审计成功后，发布总开关和三项分端部署开关已开启。实际 digest、单端重建、保留后端与验收边界见[部署状态](deployment-status.md)；不能把启用开关理解为已经重新发布/部署 backend。
