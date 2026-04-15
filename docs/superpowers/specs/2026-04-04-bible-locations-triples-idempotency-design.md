# Bible 地点嵌套、三元组同步与幂等（设计）

**日期**：2026-04-04  
**状态**：设计已定稿，待实现计划（writing-plans）  
**关联**：[`2026-04-04-sqlite-relationship-model.md`](./2026-04-04-sqlite-relationship-model.md)（库内关系化、无业务 JSON 列）

## 1. 目标

- **模型友好**：LLM 输出结构浅、键稳定，便于校验与增量细化。
- **嵌套清晰**：大陆 → 城 → 家 → 屋等层级可表达，且不依赖深嵌套 JSON。
- **单一图查询真源**：检索与关系图以 SQLite `triples` 为准。
- **编辑/生成真源**：Bible 文件 `locations[]` 为地点树的人类可读与生成侧真源；入库时**幂等**投影为三元组。
- **横切幂等**：所有 Bible 写入、模型生成回写、同步管道须满足「同输入多次执行，持久化结果等价于执行一次」。

## 2. 真源与数据流

| 层级 | 职责 |
|------|------|
| Bible `data/bibles/*.json` 中 `locations[]` | 地点列表、展示名、描述、`parent_id`、稳定 `id`；用户编辑与 Auto Bible 生成均更新此结构。 |
| SQLite `triples` + 子表 | 图查询、推断、与章节溯源等；**空间父子关系**以三元组形式存在。 |
| HTTP/API | 可收发 JSON；**入库时拆行**，遵守关系模型 spec，不在库内用 TEXT JSON 列承载业务结构。 |

**禁止**引入第三套「仅内存或仅前端」的地点真源；UI 编辑应回写 Bible（或经 API 等价持久化到 Bible），再触发同步。

## 3. LLM / Bible 契约（两层 JSON）

- **形状**：`locations[]` 为**平铺数组**；可选 `edges[]` 用于非父子关系（邻接、路线等），与后续人物关系边共用「源–谓词–目标」思路。
- **每条 location 必填字段**：
  - `id`：全书内稳定标识（同一地点多次生成应**复用**该 id，仅改描述或 `parent_id`）。
  - `name`：显示名。
  - `kind`：粗粒度类型（如 `continent` / `city` / `home` / `room` 等），枚举可扩展。
  - `parent_id`：父地点的 `id`；根节点为 `null`。
- **禁止**将层级唯一表达为任意深度的嵌套对象树；提示中可用树形**示例**说明语义，但**解析契约**以平铺 + `parent_id` 为准。

## 4. 空间包含 → 三元组规范

- **谓词（canonical）**：采用 **`位于`**，方向为 **子地点 → 父地点**（与「某实体在某处」语感一致）。全库**不**再混用「包含」作为同一语义的反向重复边（避免双真源）。
- **一行语义**：`subject` = 子地点名称或规范名，`object` = 父地点名称或规范名；`predicate` = `位于`。
- **`source_type`**：自 Bible 同步写入的边使用 `bible_generated`（与现有枚举对齐）；用户仅在图编辑器中改的同类边可用 `manual` 等，合并规则见下文。
- **实体指针**：优先填充 `subject_entity_id` / `object_entity_id`（及 `entity_type` 等现有列），与 `chapter_elements.element_id` 对齐时使用**同一 `location.id`**，减少同名歧义。

## 5. 幂等同步（Bible → triples）

### 5.1 关联键

- 在 `triple_attr` 中写入 **`bible_location_id`** = Bible 中该地点的 `id`，表示「该三元组行由该 Bible 地点的**父子边**投影而来」。
- 同步时以 **`(novel_id, bible_location_id, 语义=位于父)`** 定位至多一行 containment 三元组：存在则更新 `subject`/`object`/实体指针等；不存在则插入。
- 若 `parent_id` 变为 `null`（根节点），则**删除**或**不再维护**对应的「位于」边（实现二选一须在代码中统一：推荐删除该 bible_location_id 下的 containment 行，避免脏边）。

### 5.2 语义去重

- 在应用层保证：同一小说内，同一子地点对同一父的 **`位于`** 关系**最多对应一条**业务三元组（可通过 bible_location_id 或规范化后的实体对唯一约束策略实现）。
- `triples.id` 可为内部 UUID；**幂等键**以业务键（bible_location_id + 谓词语义）为准，而非行 id。

### 5.3 与推断/手动的关系

- 同步逻辑**仅**更新或删除 `source_type = bible_generated` 且带有对应 `bible_location_id` 的 containment 行（或实现上等价的过滤条件），**不得**删除 `chapter_inferred`、`manual` 等来源的其它三元组。
- 若用户将某边改为 `manual` 且仍希望 Bible 覆盖策略，须在后续迭代中单独立规；**本期**默认：Bible 同步不覆盖 `manual` 的 containment 行（可通过缺少 `bible_location_id` 或标志位区分）。

## 6. 横切幂等（所有数据与模型生成）

- **稳定 id**：模型输出与 Bible 存储对「同一世界观实体」必须使用稳定 `id`；新增才分配新 id，细化只改属性或 `parent_id`。
- **规范化**：服务端对 `name` 做 trim；同名冲突策略（合并 / 报错）在实现计划中写清并测试。
- **重试**：可选支持 HTTP `Idempotency-Key`；至少保证仓储层 upsert 语义，避免双击保存导致重复行。
- **回归测试**：固定一份 Bible JSON，对同步入口**连续执行两次**，断言 `triples` 及关联 `triple_attr` 集合与内容一致（行数与关键字段不变）。

## 7. 与现有表与领域的一致性

- 遵守 [`2026-04-04-sqlite-relationship-model.md`](./2026-04-04-sqlite-relationship-model.md)：扩展字段用 `triple_attr` 等子表，值 TEXT。
- `story_nodes.parent_id` 表示**叙事结构**树；**地点嵌套**由 Bible + `位于` 三元组表达；二者语义不同，不混用一张表。
- 领域对象 `Triple`（`subject_id`/`object_id`）与 DB 行（`subject`/`object` + `subject_entity_id`）的映射继续由持久化层负责，本设计不新增第二套领域模型。

## 8. 人物关系（范围说明）

- **方向**：人物–人物、人物–地点等关系统一走 `triples` + 受控 `predicate` 枚举；逐步收敛 Character 上 `List[str]` 与结构化数组的分叉，避免双轨持久化。
- **本期交付**：以 **地点树 + 位于 + 幂等同步** 为主；人物关系全量迁移可作为同一实现计划内的后续任务或第二期，须在计划中拆分任务边界。

## 9. 分期

- **第一期**：扩展 Bible `locations[]` 契约（`parent_id`、稳定 `id`）、实现 Bible → `triples` 幂等同步、`位于` 谓词与 `bible_location_id`、双次同步测试、图 API 仍读 `triples`。
- **第二期**：`edges[]` 中非树关系、别名表、多轮对话 patch、更细的合并策略（manual 与 bible 冲突消解）。

## 10. 错误处理与观测

- **环检测**：若 `parent_id` 链成环，同步应失败并返回明确错误，不写部分三元组；或定义「按拓扑序截断」须在 spec 修订时显式写明（**默认：拒绝环**）。
- **孤儿节点**：`parent_id` 指向不存在的 id → 拒绝同步或降级为根（**默认：拒绝**，与数据质量一致）。
- **日志**：记录每次同步删除/更新/插入计数及 novel_id，便于排查重复写入。

## 11. 测试要点（验收）

- 双次同步幂等（见 6）。
- 根节点、`parent_id` 变更、改名后实体指针仍一致。
- 环与孤儿校验。
- `chapter_inferred` 三元组在同步后数量与内容不受影响（抽样断言）。

---

本设计经讨论确认：谓词采用 **`位于`**（子 → 父）；Bible `locations[]` 为编辑真源；`triples` 为图查询真源；幂等为横切要求。
