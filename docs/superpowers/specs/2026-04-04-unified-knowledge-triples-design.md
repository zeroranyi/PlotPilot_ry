# 统一知识三元组与检索真源 — 设计说明

**日期**：2026-04-04  
**状态**：已定稿（开发阶段，不保留旧兼容包袱）  
**目标**：人物关系、地点关系、章节推断、Bible 自动生成、人工编辑 —— **同一持久化模型、同一套读写与检索入口**，去掉并行分叉逻辑。

---

## 1. 问题陈述

当前存在多套「关系/三元组」语义：

- **故事知识 `facts`**：`KnowledgeService` + `SqliteKnowledgeRepository`，API `GET/PUT /api/v1/novels/{id}/knowledge`，前端知识库与关系图主要读此路径。
- **`TripleRepository` + `domain.bible.triple.Triple`**：自动 Bible、章节推断等写入，API `/api/v1/knowledge-graph/...`，使用 **与现网 `schema.sql` 中 `triples` 表不一致的列集合**（如 `subject_id`/`object_id`），易造成 **同表名、不同形状** 的幻觉分裂。
- **Bible 实体上的 `relationships` / `connections`**：仍是 **设定侧** 数据，可保留；但 **凡是「可检索、可出图、可推断」的断言** 必须 **投影/同步为三元组行**，避免「设定有一套、图谱又一套」。

用户要求：**真正一统**、便于 **后续检索（含置信度、来源、章节溯源）**、**易扩展**。

---

## 2. 真源定义（Single Source of Truth）

**唯一真源**：SQLite 中 **`triples` 表**（与 `schema.sql` 对齐的 **主谓宾字符串行**），在应用层对应 **`domain.knowledge.knowledge_triple.KnowledgeTriple`**（及 API DTO）。

- **叙事与检索**：一律以「主语 / 谓词 / 宾语」字符串为 **稳定对外语义**（便于展示、向量检索、关键词检索）。
- **溯源与质量**：用 **显式列 + 子表 `triple_attr` / `triple_tags` / `triple_more_chapters`** 承载扩展字段（与 [SQLite 关系模型](./2026-04-04-sqlite-relationship-model.md) 一致），**库内不用 TEXT 存 JSON**；避免再开第二套仓储类写同一张表。

**`StoryKnowledge`** 继续作为 **聚合根**：`facts` 列表即该小说全部三元组；`premise_lock`、`chapters` 等保持现有职责。

---

## 3. 数据模型扩展（开发期可直接改库，无迁移顾虑）

在 `triples` 主行（`subject`, `predicate`, `object`, `chapter_number`, `note`, `entity_type`, `importance`, `location_type`, `description`, `first_appearance`）及子表（`triple_more_chapters`, `triple_tags`, `triple_attr`）基础上，下列字段 **建列以便索引与检索**（扩展键值仍落在 `triple_attr`，非 JSON 列）：

| 列名 | 类型 | 说明 |
|------|------|------|
| `confidence` | REAL NULL | 推断/生成置信度；人工默认可 1.0 或 NULL |
| `source_type` | TEXT NULL | `manual` \| `bible_generated` \| `chapter_inferred` \| `ai_generated`（`auto_inferred` 仅 API 兼容，持久化映射为 `chapter_inferred`） |
| `subject_entity_id` | TEXT NULL | 可选：绑定 Bible 人物/地点等实体 id，便于与设定对齐 |
| `object_entity_id` | TEXT NULL | 同上 |

**规则**：

- **检索与图谱绘制**：默认仍用 `subject` / `predicate` / `object`；`entity_type` / `importance` 等用于 UI 分面。
- **推断与 Bible 写入**：必须写 `source_type` + `confidence`（推断可 0~1）；主出处用 `chapter_number`（外键至 `chapters`），**额外**章节用 `triple_more_chapters`；应用层 DTO 仍可用 `chapter_id` / `related_chapters` 命名，入库时映射到列与子表。
- **扩展**：未预见标量进 `triple_attr`（`attr_value` 一律 TEXT），避免无限制加列。
- **章节元素 ↔ 推断三元组**：规范化表 `triple_provenance`（`rule_id`、`story_node_id`、`chapter_element_id`）；叙事知识 PUT 采用**分源合并**，保留 `chapter_inferred` / `bible_generated` / `ai_generated`，避免整本删库式覆盖。

**废弃**：`domain.bible.triple.Triple` 作为 **持久化模型** 废弃；若需过渡，仅在内存中转换为 `KnowledgeTriple` 后写入，不再调用 `TripleRepository.save`。

---

## 4. 写入路径收敛（所有入口统一到 Knowledge 层）

| 来源 | 现行问题 | 目标行为 |
|------|----------|----------|
| 自动 Bible 人物/地点关系 | 写 `TripleRepository` | 生成 `KnowledgeTriple`（填 `entity_type`、`source_type=bible_generated`、`confidence`），经 **`KnowledgeService` 或 `SqliteKnowledgeRepository` 的 upsert/merge** 写入 `triples` |
| 章节知识图谱推断 | 写 `TripleRepository` | 同上，`source_type=chapter_inferred`，带章节与置信度 |
| 前端知识库 PUT | 已写 `triples` | 保持；DTO 增加新字段透传 |
| `knowledge-graph` HTTP 路由 | 独立读 `TripleRepository` | **删除或改为** 调用 `KnowledgeService` / 仓储查询同一表；避免双读 |

**合并策略（实现时选定一种并写单测）**：

- **按 `id` upsert**（推荐）：所有写入方生成稳定 id（如 UUID 或 `bible-{novel}-{hash}`），前端整表保存仍以客户端 id 为准。
- **或** 按 `(novel_id, subject, predicate, object, source_type)` 去重合并 —— 推断场景需注意重复推断，优先 **id + 软删除** 或 **版本号**，此处实现计划再细化。

---

## 5. API 与检索

- **主 API**：`GET/PUT /api/v1/novels/{novel_id}/knowledge` 为 **完整读写面**；响应/请求体中的 fact 包含 `confidence`、`source_type`、可选 `subject_entity_id` / `object_entity_id`。
- **搜索**：`GET .../knowledge/search`（或后续专用检索服务）**只索引/查询上述同一表**（或同一投影）；过滤条件支持 `source_type`、`min_confidence`、章节范围等。
- **旧 `knowledge-graph` 路由**：开发阶段可直接 **删除** 或 **301 式内部转发** 到 knowledge 查询，**不再维护第二套序列化**。

---

## 6. 前端

- `KnowledgeTriple` TypeScript 类型与后端对齐，表单可选展示/编辑 `source_type`（只读展示推断来源亦可）。
- 关系图组件 **仅依赖** `getKnowledge().facts`，不再假设「未标 `entity_type` 就无图」；必要时由后端写入时带好 `entity_type`。

---

## 7. 测试与验收

- 单元测试：`KnowledgeService` merge、推断/Bible 写入后 **同 novel 单次 GET** 可见全部 facts，且 `source_type` / `confidence` 正确。
- 集成测试：Bible `characters` 阶段完成后，**不经过** `TripleRepository`，`GET knowledge` 中可查到人物关系事实。
- 手工：前端知识库保存后，推断任务再跑，**不丢**人工 fact（合并策略需满足）。

---

## 8. 非目标（本设计不展开）

- Bible `relationships` 列表 UI 是否与表格双向绑定（可后续再做「从设定一键生成三元组」）。
- 向量库选型与同步频率（检索增强可在同一表之上挂载）。

---

## 9. 下一步

按本 spec 调用 **writing-plans** 产出实现计划（改 schema、改 DTO、删/并 `TripleRepository` 调用点、改 `AutoBibleGenerator` / `KnowledgeGraphService`、对齐 API 与前端类型）。
