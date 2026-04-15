# 智能检索与上下文管理（Phase 2）— 叙事事件溯源

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `aitext` SQLite 中落地「静态基座 + 演化事件流」，提供按章节重放得到实体动态属性的查询能力，对应规格 **模块二**。

**Architecture:** 新增 `entity_base`（实体不变属性）与 `narrative_events`（章节挂载事件，`mutations` 为 TEXT 存 JSON 数组，与 part2 示例一致）。领域层提供纯函数式重放；基础设施层提供 `SqliteNarrativeEventRepository` / `SqliteEntityBaseRepository`。不修改正文存储模型。

**Tech Stack:** SQLite、`schema.sql` + `connection.py` 幂等迁移、Python 3、pytest。

**前置：** [Phase 1](./2026-04-05-intelligent-retrieval-context-management-phase1.md) 不阻塞本阶段；但与 Phase 4/6 集成前需完成本阶段。

**与仓库约定：** `schema.sql` 头部注释反对随意 JSON 列。若评审要求规范化，将 `mutations` 拆为子表 `narrative_event_mutations`（本计划以 **TEXT JSON** 为默认以贴合 part2 伪代码；拆表可作为 Task 6 替代实现）。

**仓库对齐：** 2026-04-05 核对，本 Phase 任务（含可选 GET 实体状态 API）已全部勾选；路径以仓库根为准。

---

## 文件结构

| 路径 | 职责 |
|------|------|
| `aitext/infrastructure/persistence/database/schema.sql` | `CREATE TABLE entity_base`, `narrative_events` + 索引 |
| `aitext/infrastructure/persistence/database/connection.py` | 可选 `_ensure_narrative_tables` 对旧库 ALTER（若用迁移函数而非仅 schema.sql） |
| `aitext/domain/novel/value_objects/narrative_mutation.py` | `MutationAction` 枚举 + 单条 mutation 校验 |
| `aitext/domain/novel/services/narrative_state_replay.py` | `replay_entity_state(base_attrs, events) -> dict` |
| `aitext/domain/novel/repositories/narrative_event_repository.py` | 抽象仓储接口 |
| `aitext/domain/novel/repositories/entity_base_repository.py` | 抽象仓储接口 |
| `aitext/infrastructure/persistence/database/sqlite_narrative_event_repository.py` | SQLite 实现 |
| `aitext/infrastructure/persistence/database/sqlite_entity_base_repository.py` | SQLite 实现 |
| `aitext/interfaces/api/v1/narrative_events.py`（可选） | `GET .../entities/{id}/state?chapter=` 调试 API |

测试：`tests/unit/domain/novel/services/test_narrative_state_replay.py`、`tests/integration/infrastructure/persistence/database/test_sqlite_narrative_events.py`

---

### Task 1: DDL 与最小迁移

- [x] **Step 1: 失败测试** — 集成测试连接内存库，断言表存在（先写 `test_narrative_events_table_exists`，运行失败）。

- [x] **Step 2: schema 片段**

```sql
-- entity_base：静态基座（core_attributes 为 JSON 文本）
CREATE TABLE IF NOT EXISTS entity_base (
  id TEXT PRIMARY KEY,
  novel_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  name TEXT NOT NULL,
  core_attributes TEXT NOT NULL DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_entity_base_novel ON entity_base(novel_id, entity_type);

CREATE TABLE IF NOT EXISTS narrative_events (
  event_id TEXT PRIMARY KEY,
  novel_id TEXT NOT NULL,
  chapter_number INTEGER NOT NULL,
  event_summary TEXT NOT NULL DEFAULT '',
  mutations TEXT NOT NULL DEFAULT '[]',
  timestamp_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_narrative_events_novel_chapter
  ON narrative_events(novel_id, chapter_number);
```

- [x] **Step 3:** 将上述追加到 `schema.sql`，跑现有测试 + 新集成测试至 PASS。

- [x] **Step 4: Commit** — `feat(db): add entity_base and narrative_events for event sourcing`

---

### Task 2: 重放纯函数（TDD）

- [x] **Step 1: 测试**

```python
# tests/unit/domain/novel/services/test_narrative_state_replay.py
from domain.novel.services.narrative_state_replay import replay_entity_state


def test_replay_add_and_remove():
    base = {"魔法": "水系"}
    events = [
        {"mutations": [{"attribute": "魔法", "action": "add", "value": "火系"}]},
        {"mutations": [{"attribute": "临时", "action": "add", "value": "x"}, {"attribute": "临时", "action": "remove", "value": ""}]},
    ]
    state = replay_entity_state(base, events)
    assert state["魔法"] == "火系"
    assert "临时" not in state
```

- [x] **Step 2: 实现** `replay_entity_state`：逐事件解析 `mutations` 列表，`add` 设键，`remove` 删键（忽略未知 action 时记录 debug）。

- [x] **Step 3:** `pytest tests/unit/domain/novel/services/test_narrative_state_replay.py -v` → PASS。

- [x] **Step 4: Commit**

---

### Task 3: SQLite 仓储

- [x] **Step 1:** 定义 `NarrativeEventRepository` 方法：`list_up_to_chapter(novel_id, max_chapter_inclusive)`、`append_event(...)`（Phase 2 至少实现 list + 测试插入 helper）。

- [x] **Step 2:** `SqliteNarrativeEventRepository` 使用 `get_database()` 与参数化查询；`mutations` 用 `json.loads` / `json.dumps`。

- [x] **Step 3:** 集成测试：插入 novel + 两条事件，查询列表顺序为 `chapter_number ASC`。

- [x] **Step 4: Commit**

---

### Task 4: 组合查询 `get_entity_state_at_chapter`

- [x] **Step 1:** 应用服务 `NarrativeEntityStateService`（`application/services/narrative_entity_state_service.py`）：`get_state(entity_id, chapter)` = 读 base + list 事件过滤 `chapter_number <= chapter` + `replay_entity_state`。

- [x] **Step 2:** 单元测试 Mock 仓储，断言调用顺序与重放结果。

- [x] **Step 3: Commit**

---

### Task 5（可选）: 只读 API

- [x] `GET /api/v1/novels/{novel_id}/entities/{entity_id}/state?chapter=52` 返回 JSON 状态字典，供前端设定面板与后续冲突检测使用。

---

## Self-review

- **规格模块二** 静态基座 + 事件流 + 重放：已映射到 Task 1–4。  
- **性能**：单小说事件量级规格称 <5k，SQLite 全表扫可接受；若瓶颈再加分页或按 entity 索引（后续）。  
- **缺口**：事件与 Bible 角色 id 对齐策略需在 Phase 4 与冲突检测一起定（`entity_base.id` 与 `Character` id 映射表或同名约定）。
