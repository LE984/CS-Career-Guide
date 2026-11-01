# Git 与文档协作规范

## 仓库和分支

本规范适用于 fork `vacontinuejatotired/CS-Career-Guide`。`origin` 指向该 fork；`upstream` 为原项目，仅作参考，不默认向上游提 PR 或推送。

| 分支 | 用途 |
| --- | --- |
| `master` | 唯一主分支；接受已验证改动。代码 push 会触发验证，成功后发布镜像 |
| `codex/personal` | 个人长期开发分支；日常开发和 PR 来源，合并后继续保留 |
| `codex/<主题>` | 可选的短期分支；需要并行处理独立任务时从 master 创建 |
| `luochen` | 已有独立分支；不改写、不代替他人合并或删除 |

`main` 是一次误建的分支，其提交已通过整合保留在 master；今后不使用它作为主分支或日常工作分支。是否删除已合并分支按明确授权处理，不删除仍在使用的个人分支。

默认流程为 `codex/personal -> PR -> master`。用户明确授权直接合并/推送时可以执行；不得把本规范解释成必须再次请求相同授权。默认分支命名与 GitHub 设置保持 master，不自行改名。

## 开始与结束一次开发

先检查工作区与远端。若有别人的修改或未提交草稿，先记录范围，不用 reset、clean 或 stash 清场；切换/合并会覆盖文件时停止并解决冲突。

```bash
git status --short
git branch --show-current
git remote -v
git fetch origin
git switch codex/personal
git merge --ff-only origin/master
```

`--ff-only` 失败说明本地存在分叉。先查看双方提交；长期共享分支采用普通 merge 解决并测试，不对已推送历史直接 rebase 或强推。只有明确理解影响并获授权，才改写远端历史。

同一个个人分支同时只承载一个待合并主题；发现第二个独立主题时，先完成/拆分当前 PR，或从 master 创建单独的 `codex/<主题>`。不要把多个无关任务堆进一个 PR。

## Commit 注意事项

标题格式为 `type(scope): 具体变化`，scope 可省略，中文或清楚的英文均可。推荐类型：feat、fix、refactor、test、docs、build、ci、chore。内容必须与实际改动一致。

示例：

```text
refactor(interview): 提取可替换的 legacy 面试实现
fix(auth): 保留登录前的页面查询参数
docs(ops): 补充配置同步失败后的处理步骤
```

- 一次提交表达一个可解释的目的。功能、部署和纯文档可按责任拆分；接口/实现/必要测试也可以在同一提交形成完整变更。
- 避免 `update`、`fix bug`、`完成所有功能` 等不具体的标题；没有测试就不在标题或正文宣称已验证。
- 显式暂存目标路径或使用 `git add -p`；默认不使用 `git add .`、`git add -A`。暂存后检查文件名单和差异，保留无关修改在工作区。
- 不提交 `.env`、私钥、Token、真实 API Key、数据库/模型缓存、node_modules、个人构建产物或用户上传数据。样例只包含占位符；大模型/媒体资产按已有 LFS 和构建约定处理。
- 不为整理提交而重置他人修改；不把回放、模拟测试和真实模型验收混为一谈。

```bash
git add -- <明确的代码路径> <对应测试路径> <对应文档路径>
git diff --cached --name-status
git diff --cached
git diff --cached --check
git commit -m "refactor(interview): 提取面试实现边界"
git push -u origin codex/personal
```

尖括号内容是占位符，执行时替换。审查差异应在自己的可信终端完成，不把含秘密的文件或日志贴到共享讨论中。

## PR 注意事项

PR 目标明确指定本 fork 的 master，不能让 GitHub/gh 默认解析到 upstream。只有一次 merge 的历史已被 master 包含时，直接记录“已包含”，不为重复合并制造空提交。

```bash
gh pr create --repo vacontinuejatotired/CS-Career-Guide --base master --head codex/personal --title "重构模拟面试实现边界" --body-file <PR说明文件>
```

PR 描述面向没有看过聊天记录的审阅者，应包含：

1. 具体问题与改动后的行为，必要时给一个触发示例。
2. 本次范围、主要设计选择、相关接口/配置/文档变化。
3. 实际执行的验证及结果，说明使用模拟响应还是真实模型；缺少的验收写清楚。
4. 部署或兼容影响，包括环境变量、迁移、数据、回滚及发布副作用；无此类变化可简写。

一个 PR 围绕一个主题，不夹带无关格式化、性能优化或依赖升级。仅在它们是修复问题的必要条件时合并处理，并说明原因。多行说明用文件传入，避免 Shell 转义破坏 Markdown 或执行文本。

合并前核对当前 head SHA、目标分支、差异与最新必需检查，解决冲突后重新验证。检查通过只代表其覆盖范围；不能用旧提交的绿色记录代表当前 head。普通代码 PR 合并前应确认测试、双镜像冒烟、真实联调/持久化及 release-summary；纯文档按当前 workflow 的跳过规则核对。

个人长期分支优先使用保留历史的 merge，合并时不选“删除 head 分支”；如果改用 squash，需先理解后续比较与同步方式，不能直接强推整理长期分支。

```bash
# 确认检查、审阅和授权后，合并指定 PR；不要添加 --delete-branch。
gh pr merge <编号> --repo vacontinuejatotired/CS-Career-Guide --merge
# 合并后将主分支结果同步回长期个人分支。
git fetch origin
git switch codex/personal
git merge --ff-only origin/master
git push origin codex/personal
```

## CI 与发布注意事项

个人分支 push 和 PR 按变更范围执行 build-only；master 代码 push 会在验证后发布 ACR 镜像。master 手动触发 workflow 也可能发布，不可当作只读检查。

服务器 AI 同步只有 `DEPLOY_ENV_SYNC_ENABLED=true` 才执行，但服务器已有 Watchtower 时，镜像发布本身仍可能引发自动更新。合并前应了解该副作用，不把“没有手动 SSH 重建”写成“服务器一定没有更新”。CI、发布和服务器状态分别确认，见 [流水线](ci-cd.md) 与 [运维状态](deployment-status.md)。

当前纯文档识别只覆盖 README.md 和 docs/；根目录 `agent.md`、`AGENTS.md` 不在该跳过规则内，改它们会触发镜像检查。不要根据文件内容自行假定流水线会跳过。

## 开发时补多少文档

优先维护已有说明，只补能帮助使用、审查或接手的内容，不要求每个小改动写新文档。

| 改动 | 最少补充 |
| --- | --- |
| 新功能/核心流程或模块边界 | 对应功能说明：入口、行为、数据流、限制、验证方法 |
| API 路径、字段、鉴权、流式事件 | 请求/响应约定、调用方影响和兼容方式 |
| 新增/修改环境变量 | `.env.example` 与 environment.md，写默认值、作用域、是否敏感和生效时机 |
| 数据字段或迁移 | 数据含义、迁移条件、已有数据影响与恢复限制 |
| CI、镜像、部署或回滚变化 | 对应运维文档的前提、操作步骤、失败状态和实际验证范围 |
| 修复有明确触发条件的缺陷 | 测试与 PR 说明；反复出现的排障问题再补已有手册 |
| 小型样式/错别字/局部代码整理 | 通常无需独立文档；可在 PR 说明验证 |
| 新增正式文档 | 在根目录 agent.md 补索引 |

不要提交未获确认的方案冒充已实现功能。历史状态写日期与证据，实时操作前重新查询；状态文档不要硬编码未来提交号或宣称尚未执行的发布成功。
