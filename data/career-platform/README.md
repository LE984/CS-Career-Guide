# 课程数据交付目录

`java-backend.json` 是成员1的目录数据交付样例，包含 2 家虚构企业、3 个虚构岗位和 30 道团队自编 Java 面试题。所有企业、岗位和题目均标记 `is_demo=true`，不代表真实招聘或真实面经。

`xiaolincoding-questions.json` 是成员1经授权采集并清洗的 Java 后端面试题库，包含 943 道题，详见下文“小林coding 授权题库”。

## 文件结构

```json
{
  "status": "demo-pending-review",
  "dataset_version": "java-demo-2026-11-10",
  "reviewed_by": "",
  "review_notes": "审核说明",
  "companies": [],
  "jobs": [],
  "questions": []
}
```

`companies`、`jobs`、`questions` 可直接分别作为 `POST /api/career-platform/catalog/imports/` 的 `records` 数组导入，`kind` 对应 `companies`、`jobs`、`questions`。导入顺序应为企业 → 岗位 → 题库；岗位通过 `company` 名称关联已导入企业。

## 来源、许可与审核

- 企业、岗位：虚构演示数据，`permission_status=allowed`，靠 `is_demo=true` 明示不是真实招聘；来源统一写为“团队创作：成员1”。
- 题库：30 道题均为团队自编，当前 `permission_status=pending`。按约定 pending 不进入公开查询和正式检索；须由集成人逐题复核来源、参考要点和授权状态，确认后改为 `allowed` 再导入。
- 每条记录都带 `source`、`collected_at`、`permission_status`、`is_demo` 和稳定的 `dedupe_key`。测试 fixture 位于 `backend/career_platform/tests/fixtures`，均标记 `test_only`，不能复制成正式题库，也不能把 6 道契约题算作 30 道交付。

## 导入与去重

```bash
curl -X POST /api/career-platform/catalog/imports/ \
  -H "Authorization: Token <staff-token>" \
  -H "Content-Type: application/json" \
  -d '{"kind":"questions","records":[...],"dry_run":false}'
```

- `dry_run=true` 只校验并返回预计的新增、更新和未变化数量，不写数据库。
- 服务端优先使用记录自带的 `dedupe_key`；省略时按来源和稳定标识生成，重复导入会更新或保持原记录，不会新增重复行。
- 任一记录校验失败时整批返回 400，错误定位到 `records[行号].字段`，整批零写入。
- 公开查询只返回 `permission_status=allowed` 的记录；岗位还会排除已过 `valid_until` 的记录。

## 小林coding 授权题库（2026-11-15）

`xiaolincoding-questions.json` 包含 943 道 Java 后端相关面试题，来源为 xiaolincoding.com/interview/ 的 16 个公开主题页。文件顶层保留 `authorization`、`counts` 和 `questions`；导入时只取 `questions` 数组作为 `records`。

- 授权：成员1声明已获原作者授权，记录标记 `permission_status=allowed`、`is_demo=false`。书面凭证由成员1保存，未随公开仓库提交；集成人合并前须核对授权范围与凭证，不能仅凭本文件或 `source_url` 认定许可。
- 来源与时间：每条记录带 `source`、`source_url`、`collected_at`（2026-11-15 UTC）和 `tags`（来源页、栏目、授权采集）。
- 范围：Java、集合、JVM、并发、Spring、数据库、Redis、计算机网络、操作系统、消息队列、分布式、数据结构与算法、Docker、Git、Linux、系统设计；排除 C++/Go/Python、测试开发、性能测试、广告页和学习路径页。java2top.cn 因本机不可访问且其源仓库无许可证未采集。
- 清洗：离线解析公开 HTML，移除导航、图片、广告和公众号推广，保留代码块、列表和表格文本；不登录、不处理验证码、不绕过访问控制，抓取限速 2 秒/页。
- 分类：`topic` 使用 16 个规范主题，便于按 role/topic/difficulty 精确筛选；`difficulty` 为 `rule-based-v1` 规则分类，需人工复核。
- 去重：规范化题干 SHA-256 生成 `dedupe_key`；跨页面重复保留答案更长者，并在 `tags` 写 `另见:<url>`。943 条记录无重复 key 或重复题干。
- 验证：运行 `python data/career-platform/validate_xiaolincoding.py data/career-platform/xiaolincoding-questions.json`，943/943 通过 `backend/career_platform/catalog/source.py` 的字段校验原语；`xiaolincoding-questions-report.json` 记录逐页数量、跳过项和跨页重复。未导入实际数据库，未重跑 RAG 或成员2评估基线。
- 敏感信息：扫描未发现真实密钥或个人信息；命中项均为示例占位值（`example@example.com`、`13800138000`、示例密码 `root`）。

## 复核记录

| 日期 | 范围 | 复核人 | 结果 |
| --- | --- | --- | --- |
| 2026-11-10 | 2 家企业、3 个岗位 | 待集成人复核 | 虚构演示数据，已标记 `is_demo=true` |
| 2026-11-10 | 30 道 Java 题 | 待集成人复核 | 团队自编，保持 `pending`；复核后逐题改为 `allowed` |
| 2026-11-15 | 943 道小林coding面试题 | 成员1声明已获作者授权；待集成人复核凭证 | 已标记 `allowed`；难度/主题为规则分类，待人工抽检 |

本目录不存放用户简历、秘密或原始抓取缓存；也不存放未经授权的个人材料。经授权的公开题库以清洗后的 JSON 交付，并在上文登记来源、采集时间、授权声明和复核状态。真实招聘数据须另行登记合法来源、采集时间和授权状态，不能把本目录的样例当作真实来源验收。
