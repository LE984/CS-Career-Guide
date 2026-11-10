# 课程数据交付目录

`java-backend.json` 是成员1的目录数据交付样例，包含 2 家虚构企业、3 个虚构岗位和 30 道团队自编 Java 面试题。所有企业、岗位和题目均标记 `is_demo=true`，不代表真实招聘或真实面经。

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

## 复核记录

| 日期 | 范围 | 复核人 | 结果 |
| --- | --- | --- | --- |
| 2026-11-10 | 2 家企业、3 个岗位 | 待集成人复核 | 虚构演示数据，已标记 `is_demo=true` |
| 2026-11-10 | 30 道 Java 题 | 待集成人复核 | 团队自编，保持 `pending`；复核后逐题改为 `allowed` |

本目录不存放用户简历、秘密、外部数据抓取缓存或未经授权的个人材料。真实招聘数据须另行登记合法来源、采集时间和授权状态，不能把本目录的虚构样例当作真实来源验收。
