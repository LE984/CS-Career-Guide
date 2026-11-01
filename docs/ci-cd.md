# CI/CD 流水线

本分支自 2026-11-01 拆为组件交付；当前 Actions 与服务器状态须分别确认，不能沿用历史绿色结果。完整边界见[单仓库独立交付](split-delivery.md)。

## 触发与选择

push 覆盖所有分支，PR 目标为本 fork master。主题分支和 PR 仅 build-only；只有 `vacontinuejatotired/CS-Career-Guide` 的 master push/手动事件能发布。手动 `component=frontend/backend/all`，默认 all，可附加合法 `extra_tag`。

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

Platform documentation 继续以 PR base / push before 的归属表为准检查模块文档和 acceptance-record。交付编排 ci-cd.yml 被明确区分；业务代码、公共契约、固定测试/验收规则和未知 workflow 仍按原规则选择 complete。普通前端静态变更不启动 SQLite/MySQL 业务 runner，前端模块路径仍触发原业务验收。混入业务文件不会因同时有交付文件而被豁免。

本分支修改了检查器与 career-platform.yml，所以本分支自身仍需要六份实施记录及原全部业务验收。五个模块当前仍是 501 骨架；本地 17 项 complete 失败如实保留，不能靠降低固定测试标准使发布通过。交付验证和业务完成分开记录。

## 发布与记录

ACR_REGISTRY/ACR_NAMESPACE 仅 publisher 从 Variables 或同名 Secrets 读取（Variables 优先）；ALIYUN_ACR_USERNAME/ALIYUN_ACR_PASSWORD 用于登录。构建/联调不读取注册表凭据。镜像缓存 scope 仍按两端分别设置，关闭 provenance/SBOM 保留现有 ACR 兼容。

`ci/release_images.py verify/publish --component frontend` 或 backend 只需要对应归档；不指定组件的旧 CLI 保持双组件兼容。可重复 --component，但空/未知/重复选择会拒绝。每组件先推 sha-<7位SHA> 和可选版本标签，再推 latest；核对每次 manifest digest 一致。

`published-frontend-<run-id>` / `published-backend-<run-id>` 各自保存 `published-images.json`，含 components、compatibility（component-contracts / candidate-integration / not-recorded）、完整 commit、image ID、标签、digest/reference 与 complete。complete=false 是部分失败，不可部署；latest/SHA tag 可改写，精确恢复用 digest。两个 publisher 相互独立，不承诺两端发布原子性。

归档保留 1 天，普通日志 7 天，发布记录 30 天；不上传真实环境/凭据。一个 ref 的 push 发布不取消旧运行，PR 可取消旧运行；服务器激活共用独立 concurrency group 和远端文件锁。Actions 并发组不替代手工回滚协调。

## 验收与失败排查

本地离线运行 `python -m unittest discover -s ci -p 'test_*.py' -v`；Windows 的 POSIX 测试跳过，须在 Linux/WSL 或 runner 运行。前端与后端原测试命令见 development.md。Docker 构建、进程和网络结果仅以对应 commit 的 Actions 为准。

单端协议测试不证明和任意线上旧版本兼容；破坏合同的改动需兼容窗口与指定组合联调。镜像发布不证明服务器部署，容器健康不证明真实模型/浏览器验收。Watchtower 若另外启用仍可能因 latest 更新自动激活，回滚前协调入口。

常见问题：UTF-16 源改路径后转换失败时检查 backend/requirements.txt；旧 Dockerfile 根路径必须移除；gateway 缺失/前端仍有端口或共享卷时新同步拒绝；只设置旧总同步开关不会触发新分端部署；完整业务 501 失败应作为业务未完成处理，不能改成通过。
