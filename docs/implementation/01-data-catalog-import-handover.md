# 成员1：授权题库导入交接

日期：2026-11-15

状态：数据与导入代码已合入主项目；**尚未导入运行数据库**，等待有 staff Token 或服务器/数据库访问权限的同学执行。本文只描述导入操作，不把 CI 通过写成线上数据已导入。

## 1. 已完成

- PR [#37](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/37)：943 道小林coding Java 后端面试题，文件为 `data/career-platform/xiaolincoding-questions.json`，记录带 `source`、`source_url`、`collected_at`、`dedupe_key`，当前标记 `permission_status=allowed`、`is_demo=false`。
- PR [#38](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/38)：幂等导入入口与测试。
  - `backend/company_reviews/management/commands/import_catalog.py`
  - `data/career-platform/import_catalog_via_api.py`
  - `backend/tests/test_catalog_import.py` 新增 943 条导入、二次幂等、目录查询和 `DjangoQuestionRetriever` 检索断言
- 主项目 `master` 合并提交：`1c7c816`。
- CI：PR #37、#38 全绿；本地 catalog 固定验收 4 项 + 导入测试 7 项通过。
- 合并后的 master 流水线 `43722555711` 检查已通过，镜像发布/部署进行中；截至本文撰写时未确认线上运行版本。实际线上版本以 Actions 和部署记录为准。

## 2. 数据会进入哪些功能

- **目录题库查询**：`GET /api/career-platform/catalog/questions/`，按 `role`、`topic`、`difficulty` 精确筛选；前端 `/career-platform/catalog` 展示来源和采集时间。
- **练习页** `/career-platform/practice`：正式检索由 `DjangoQuestionRetriever` 读取 `allowed` 的 `InterviewQuestion`，选中后创建练习会话。
- **成员4 RAG**：逐题检索、参考要点和来源证据使用同一批数据库记录。
- **成员2评估**：评估和检索基线需在导入后重跑，不能沿用旧 Top-K/分数。
- **App 端**：复用同一套 API，见 `docs/app-api.md`。
- **索引说明**：当前题库不使用 LanceDB 向量索引；`career_platform_questions_v1` 只是契约索引名，`index_notifier` 未配置，ORM 是检索权威来源。导入结果中的 `index_notification=not_configured` 是预期值。

## 3. 交接前必须确认

- [ ] **授权**：943 条题标记 `allowed` 的依据是成员1声明已获原作者授权；书面凭证不在仓库。导入前请核对授权范围与凭证。
  - 若授权未落实：先把 `permission_status` 改为 `pending`（JSON 或数据库），或只做 dry-run；`pending` 不会进入正式查询和 RAG。
- [ ] **目标环境**：确认 base URL/数据库连接，避免误导入本地或他人环境。
- [ ] **备份**：线上 SQLite/MySQL 先备份。导入本身幂等，但回滚删除仍需要备份。
- [ ] **权限**：执行人需要 `is_staff=true` 账号的 Token，或服务器/数据库访问权限。

## 4. 导入方式 A：HTTP API（推荐，不依赖新镜像）

要求：已部署后端可达，持有 staff Token。现有 `catalog/imports/` 接口已支持本数据集，不需要等待新镜像。

```bash
export CATALOG_IMPORT_TOKEN='<staff-token>'
python data/career-platform/import_catalog_via_api.py \
  data/career-platform/xiaolincoding-questions.json --dry-run
python data/career-platform/import_catalog_via_api.py \
  data/career-platform/xiaolincoding-questions.json --commit
```

- 默认 base URL 为 `http://123.207.252.243/api`，可用 `--base-url` 覆盖。
- HTTP 明文仅用于当前演示环境；正式环境应使用 HTTPS。
- Token 只从环境变量读取，脚本不回显、不跟随重定向；不要提交到仓库。
- 预期：第一次 `created=943`；再次执行 `created=0 unchanged=943`；`index_notification=not_configured`。

## 5. 导入方式 B：服务器管理命令（需要新镜像和数据库访问）

```bash
docker cp data/career-platform/xiaolincoding-questions.json <backend-container>:/tmp/
docker compose exec -T backend python manage.py import_catalog /tmp/xiaolincoding-questions.json --dry-run
docker compose exec -T backend python manage.py import_catalog /tmp/xiaolincoding-questions.json --commit
```

- 默认 dry-run；`--commit` 才写库；可用 `--kind questions` 只导入题库。
- 命令复用 `CatalogService`，按 `dedupe_key` 幂等，单批最多 1000 条。
- 优先使用第一个 staff 用户；没有 staff 用户时使用管理命令系统 actor，并打印警告。

## 6. 导入后验收

```bash
# 方式 A：API 查询（替换 Token）
curl -H "Authorization: Token $CATALOG_IMPORT_TOKEN" \
  "http://123.207.252.243/api/career-platform/catalog/questions/?role=Java后端&topic=集合&page_size=1"

# 服务器/Django shell
python manage.py shell -c \
"from career_platform.models import InterviewQuestion; \
 print(InterviewQuestion.objects.filter(dedupe_key__startswith='xl-').count()); \
 print(InterviewQuestion.objects.filter(permission_status='allowed', topic='集合').count())"
```

- `dedupe_key` 前缀 `xl-` 的数量应为 **943**。
- `catalog/questions/` 返回 `count > 0`，结果含 `source`、`source_url`、`collected_at`。
- 练习页用 `role=Java后端`、`topic=集合` 和任意难度发起检索，应能选到题目并创建会话。
- 成员4 `DjangoQuestionRetriever` 查询 `ArrayList` 应返回结果，`origin=catalog`。
- 成员2需重跑评估/检索基线；旧 Top-K 或分数不能复用。

## 7. 回滚

仅在确认需要撤销时执行，先备份：

```bash
python manage.py shell -c \
"from career_platform.models import InterviewQuestion; \
 qs=InterviewQuestion.objects.filter(dedupe_key__startswith='xl-'); \
 print('to delete', qs.count()); qs.delete()"
```

- 只删除本数据集（`xl-` 前缀）；不要按题目文本或其他来源批量删除。
- 已创建的练习会话使用快照；删除题目不会改写历史快照，但会影响后续检索。
- 回滚后把实际数量、执行人、时间和原因追加到 `docs/deployment-status.md` 或对应发布记录。

## 8. 已知限制

- 难度和主题为 `rule-based-v1` 自动分类，未逐题人审；建议抽检后再扩大使用。
- 未执行真实 MySQL、浏览器、真实模型或 RAG/评估基线重跑。
- `java2top.cn` 未采集（本机不可达且其源仓库无许可证）。
- 导入是否成功以数据库计数和实际接口结果为准，不以 CI 通过代替。

## 9. 交接清单

- [ ] 核对授权凭证；未落实则先把数据改为 `pending` 或只做 dry-run。
- [ ] dry-run 结果为 943。
- [ ] `--commit` 后 `dedupe_key` 前缀 `xl-` 计数为 943。
- [ ] 目录查询、练习页检索、成员4文本检索各验证一次。
- [ ] 通知成员2重跑评估基线、成员4重跑检索验收。
- [ ] 在 `docs/deployment-status.md` 或发布记录登记导入时间、执行人、环境、结果和限制。
