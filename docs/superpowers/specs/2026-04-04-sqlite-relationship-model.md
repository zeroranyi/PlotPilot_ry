# SQLite 关系模型（无库内 JSON 列）

## 原则

- **不在 SQLite 用 TEXT 存 JSON 串** 表示业务结构（`related_chapters` / `tags` / `attributes` 等一律关系化）。
- HTTP/API 仍可收发 JSON 体；入库时拆成行。
- Bible 等若仍用 `data/bibles/*.json` 文件，与「库内无 JSON 列」不矛盾；若要求**全盘**无 JSON 文件，需另开迁移将 Bible 落表。

## 表与关联

```
novels
  ├─< chapters (novel_id, number) UNIQUE
  ├─< knowledge (novel_id)
  │     └─< chapter_summaries (knowledge_id, chapter_number)
  └─< triples (novel_id, chapter_number → chapters)
        ├─< triple_more_chapters (triple_id, novel_id, chapter_number)
        ├─< triple_tags (triple_id, tag)
        ├─< triple_attr (triple_id, attr_key, attr_value TEXT)
        └─< triple_provenance (triple_id, novel_id, story_node_id, chapter_element_id, rule_id, role)
```

- `triples.chapter_number`：主出处章节号，复合外键 `(novel_id, chapter_number) → chapters`。
- `triple_more_chapters`：**额外**关联章（不含与主章重复时由写入逻辑跳过）。
- `triple_tags`：一标签一行。
- `triple_attr`：扩展键值，**值均为 TEXT**（数字、布尔先 `str()`）。
- `triple_provenance`：**推断/证据链**，把三元组与 `story_nodes`（章节结构节点）、可选 `chapter_elements` 行关联；`rule_id` 标明规则（如 `coappearance`、`character_location`）。`GET .../knowledge` 在每条 fact 上附带 `provenance`；叙事知识 **PUT 合并**时不删除 `chapter_inferred` / `bible_generated` / `ai_generated` 来源行（除非同 id 被 payload 覆盖）。
- **去重**：部分唯一索引 `(triple_id, rule_id, story_node_id, chapter_element_id)`（`chapter_element_id` 非空）与 `(triple_id, rule_id, IFNULL(story_node_id,''))`（元素为空），插入使用 `INSERT OR IGNORE` + 批内去重。
- **HTTP（知识图谱）**：`GET /api/v1/knowledge-graph/novels/{novel_id}/chapters/by-number/{n}/inference-evidence`；`DELETE .../inference` 按章撤销；`DELETE /api/v1/knowledge-graph/novels/{novel_id}/inferred-triples/{triple_id}` 单条撤销（仅 `chapter_inferred`）。

## 已移除的库内 JSON 列

原 `triples.related_chapters` / `tags` / `attributes` TEXT(JSON) → 由上表替代。
