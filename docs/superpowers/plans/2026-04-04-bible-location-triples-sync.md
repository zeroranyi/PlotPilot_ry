# Bible 地点嵌套 → 三元组幂等同步 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Bible `locations[]`（含 `parent_id`、稳定 `id`）作为编辑真源，幂等同步为 SQLite `triples` 中 `predicate=位于` 的 `bible_generated` 边，并满足设计文档 [`2026-04-04-bible-locations-triples-idempotency-design.md`](../specs/2026-04-04-bible-locations-triples-idempotency-design.md)。

**Architecture:** 纯函数校验 + 小型应用服务 `BibleLocationTripleSyncService` 计算待写入/待删除的三元组；通过现有 `TripleRepository` / `SqliteKnowledgeRepository.save_triple` 路径写入；稳定 `triples.id` 使用 `uuid.uuid5` 由 `(novel_id, bible_location_id, 位于)` 派生；`triple_attr.bible_location_id` 作为业务键；不覆盖 `source_type != bible_generated` 的已有行。

**Tech Stack:** Python 3.11+、SQLite、现有 FastAPI / `Triple` 领域模型、`pytest`。

**关联规范:** [`2026-04-04-sqlite-relationship-model.md`](../specs/2026-04-04-sqlite-relationship-model.md)（子表扩展、无库内 JSON 业务列）。

---

## 文件结构（将创建 / 修改）

| 路径 | 职责 |
|------|------|
| `domain/bible/entities/location.py` | `Location` 增加可选 `parent_id: str \| None`（缺省 `None`，兼容旧 JSON）。 |
| `infrastructure/persistence/mappers/bible_mapper.py` | `locations` 序列化/反序列化 `parent_id`。 |
| `application/dtos/bible_dto.py` | `LocationDTO` 增加 `parent_id`。 |
| `interfaces/api/v1/bible.py` | `LocationData` 增加可选 `parent_id`。 |
| `application/services/bible_service.py` | 构建 `Location` 时传入 `parent_id`。 |
| `application/services/bible_location_triple_sync.py`（新建） | 校验树、环、孤儿；计算 upsert/delete；调用 `TripleRepository`。 |
| `infrastructure/persistence/database/triple_repository.py` | 增加按 `bible_location_id` 查询/列举待删 id 的辅助方法（避免业务层拼 SQL）。 |
| `application/services/auto_bible_generator.py` | 地点 prompt 与默认结构含 `parent_id`、稳定 `id`；生成后调用同步。 |
| `interfaces/api/dependencies.py` 或 `bible.py` | 在 Bible 保存成功后注入并调用同步（见任务 6）。 |
| `web-app/src/components/BiblePanel.vue`（可选） | 表格或 JSON 编辑支持 `parent_id`（可第二期）。 |
| `tests/unit/application/services/test_bible_location_triple_sync.py`（新建） | 校验、幂等、环、孤儿、不碰 `chapter_inferred`。 |

---

### Task 1: 领域与持久化 — `Location.parent_id`

**Files:**
- Modify: `domain/bible/entities/location.py`
- Modify: `infrastructure/persistence/mappers/bible_mapper.py`（`to_dict` / `from_dict` 中 `locations`）
- Modify: `application/dtos/bible_dto.py`（`LocationDTO` + `from_domain`）
- Modify: `application/services/bible_service.py`（`update_bible` 里 `Location(...)`）
- Test: `tests/unit/domain/bible/test_bible.py` 或新建 `tests/unit/domain/bible/test_location_parent.py`

- [ ] **Step 1: 修改 `Location` 数据类**

```python
# domain/bible/entities/location.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Location:
    id: str
    name: str
    description: str
    location_type: str
    connections: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None

    def __post_init__(self):
        if not self.id or not self.id.strip():
            raise ValueError("Location id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Location name cannot be empty")
```

- [ ] **Step 2: BibleMapper 读写 `parent_id`**

在 `to_dict` 的每个 location 字典增加 `"parent_id": loc.parent_id`（若为 `None` 可省略或显式 `null`）。  
在 `from_dict` 中：`parent_id=loc_data.get("parent_id")`，缺省为 `None`。

- [ ] **Step 3: DTO 与 BibleService**

`LocationDTO` 增加 `parent_id: Optional[str] = None`；`from_domain` 传入 `location.parent_id`。  
`bible_service.update_bible` 中：`Location(..., parent_id=getattr(loc_data, "parent_id", None))`（若 API 用 dataclass/Pydantic 则 `loc_data.parent_id`）。

- [ ] **Step 4: 运行相关单测**

Run: `pytest tests/unit/domain/bible/ -q`  
Expected: PASS（按需为新字段补一条「带 parent_id 反序列化」的断言）。

- [ ] **Step 5: Commit**

```bash
git add domain/bible/entities/location.py infrastructure/persistence/mappers/bible_mapper.py application/dtos/bible_dto.py application/services/bible_service.py tests/
git commit -m "feat(bible): Location.parent_id in domain and mapper"
```

---

### Task 2: API 契约 — `LocationData.parent_id`

**Files:**
- Modify: `interfaces/api/v1/bible.py`（`LocationData`）
- Test: `tests/integration/interfaces/api/v1/test_bible_api.py`（扩展或新增用例）

- [ ] **Step 1: Pydantic 模型**

```python
# interfaces/api/v1/bible.py — LocationData
from typing import Optional

class LocationData(BaseModel):
    id: str = Field(..., description="地点 ID")
    name: str = Field(..., description="地点名称")
    description: str = Field(..., description="地点描述")
    location_type: str = Field(..., description="地点类型")
    parent_id: Optional[str] = Field(default=None, description="父地点 id，根为 null")
```

- [ ] **Step 2: 集成测试 — PUT/POST 带回 parent_id**

构造 `BulkUpdateBibleRequest`，`locations` 含两条：`child.parent_id == parent.id`，调用更新接口后 `GET` Bible，断言 JSON 中 `locations[1].parent_id` 一致。

Run: `pytest tests/integration/interfaces/api/v1/test_bible_api.py -q --tb=short`  
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(api): LocationData.parent_id for bible bulk update"
```

---

### Task 3: 常量与纯校验 — `bible_location_tree.py`

**Files:**
- Create: `domain/bible/bible_location_tree.py`（或 `application/services/bible_location_triple_sync.py` 内嵌函数，二选一；推荐独立小模块便于单测）
- Test: `tests/unit/domain/bible/test_bible_location_tree.py`

- [ ] **Step 1: 失败用例测试（先写测）**

```python
# tests/unit/domain/bible/test_bible_location_tree.py
import pytest
from domain.bible.bible_location_tree import validate_location_forest


def test_rejects_orphan_parent():
    locs = [
        {"id": "a", "name": "A", "parent_id": "missing"},
    ]
    with pytest.raises(ValueError, match="orphan|parent"):
        validate_location_forest(locs)


def test_rejects_cycle():
    locs = [
        {"id": "a", "name": "A", "parent_id": "b"},
        {"id": "b", "name": "B", "parent_id": "a"},
    ]
    with pytest.raises(ValueError, match="cycle"):
        validate_location_forest(locs)
```

Run: `pytest tests/unit/domain/bible/test_bible_location_tree.py -v`  
Expected: FAIL（模块未实现）。

- [ ] **Step 2: 实现校验**

```python
# domain/bible/bible_location_tree.py
from typing import Any, Dict, List, Set


def validate_location_forest(locations: List[Dict[str, Any]]) -> None:
    """校验 id 唯一、parent_id 存在或为 None、无环。失败抛 ValueError。"""
    ids: Set[str] = set()
    for loc in locations:
        lid = (loc.get("id") or "").strip()
        if not lid:
            raise ValueError("location id empty")
        if lid in ids:
            raise ValueError(f"duplicate location id: {lid}")
        ids.add(lid)
    for loc in locations:
        pid = loc.get("parent_id")
        if pid is None or pid == "":
            continue
        if pid not in ids:
            raise ValueError(f"orphan parent_id references missing id: {pid}")
    # 环检测：沿 parent 走，步数 > len 则环
    for loc in locations:
        lid = loc["id"].strip()
        seen: Set[str] = set()
        cur: str | None = lid
        steps = 0
        while cur is not None and cur != "":
            if cur in seen:
                raise ValueError("location parent_id cycle detected")
            seen.add(cur)
            parent = None
            for x in locations:
                if x["id"].strip() == cur:
                    p = x.get("parent_id")
                    parent = p.strip() if isinstance(p, str) and p.strip() else None
                    break
            cur = parent
            steps += 1
            if steps > len(locations) + 1:
                raise ValueError("location parent_id cycle detected")
```

Run: `pytest tests/unit/domain/bible/test_bible_location_tree.py -v`  
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add domain/bible/bible_location_tree.py tests/unit/domain/bible/test_bible_location_tree.py
git commit -m "feat(bible): validate location parent_id forest (no cycle, no orphan)"
```

---

### Task 4: `TripleRepository` 辅助查询

**Files:**
- Modify: `infrastructure/persistence/database/triple_repository.py`
- Test: `tests/integration/infrastructure/persistence/database/test_triple_repository_bible_loc.py`（新建，需临时 DB）

- [ ] **Step 1: 新增方法签名与实现**

在 `TripleRepository` 中增加（同步 `async` 风格与现有方法一致，若类中均为 `async def` 则保持一致）：

```python
BIBLE_LOCATION_ATTR_KEY = "bible_location_id"
CONTAINMENT_PREDICATE = "位于"

async def get_containment_row_meta_by_bible_location_id(
    self, novel_id: str, bible_location_id: str
) -> Optional[dict]:
    """返回 {"id": str, "source_type": str} 或 None。JOIN triple_attr。"""
    row = self._db.fetch_one(
        """
        SELECT t.id, t.source_type
        FROM triples t
        INNER JOIN triple_attr a ON a.triple_id = t.id AND a.attr_key = ?
        WHERE t.novel_id = ? AND t.predicate = ? AND a.attr_value = ?
        LIMIT 1
        """,
        (BIBLE_LOCATION_ATTR_KEY, novel_id, CONTAINMENT_PREDICATE, bible_location_id),
    )
    return dict(row) if row else None


async def list_bible_generated_containment_triple_ids(
    self, novel_id: str,
) -> List[str]:
    """所有 bible_generated + 位于 + 带 bible_location_id 的三元组 id。"""
    rows = self._db.fetch_all(
        """
        SELECT DISTINCT t.id
        FROM triples t
        INNER JOIN triple_attr a ON a.triple_id = t.id AND a.attr_key = ?
        WHERE t.novel_id = ? AND t.predicate = ? AND t.source_type = 'bible_generated'
        """,
        (BIBLE_LOCATION_ATTR_KEY, novel_id, CONTAINMENT_PREDICATE),
    )
    return [r["id"] for r in rows]
```

- [ ] **Step 2: 单测占位**  
若集成测试成本高，可仅在 Task 5 用 `BibleLocationTripleSyncService` 的集成测试覆盖；本任务至少 `pytest` 全 suite 无语法错误。

Run: `pytest tests/unit/infrastructure/persistence/database/ -q` 或全量  
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(triples): query bible_location_id containment rows"
```

---

### Task 5: `BibleLocationTripleSyncService`

**Files:**
- Create: `application/services/bible_location_triple_sync.py`
- Modify: `domain/bible/triple.py`（仅在使用处构造 `Triple`；无需改枚举）
- Test: `tests/unit/application/services/test_bible_location_triple_sync.py`

- [ ] **Step 1: 稳定 triple id**

```python
import uuid

def stable_containment_triple_id(novel_id: str, bible_location_id: str) -> str:
    ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    return str(uuid.uuid5(ns, f"aitext/{novel_id}/bible_location/{bible_location_id}/位于"))
```

- [ ] **Step 2: 同步逻辑（核心）**

伪代码要求（实现时写成类方法）：

1. `validate_location_forest(locations)`  
2. `id_to_name = {trim(id): trim(name)}`  
3. 对每个 `loc`，若 `parent_id` 为空：若存在 `bible_generated` 且 `bible_location_id==loc.id` 的 `位于` 行则 `delete`；若已有行且 `source_type != bible_generated` 则 **跳过**。  
4. 对每个 `loc` 有 `parent_id`：构造 `Triple(novel_id=..., subject_id=child_id, object_id=parent_id, subject_type='location', object_type='location', predicate='位于', source_type=BIBLE_GENERATED, attributes={'bible_location_id': loc.id})`，`subject`/`object` 列使用 **名称**（与现有 `_triple_to_fact_dict` 一致：`subject_id` 同时写入 `subject` 字段）。  
5. **Upsert 前**：`get_containment_row_meta_by_bible_location_id`；若 `source_type` 为 `manual` 等，**跳过**该 `loc`。  
6. **删除多余**：`list_bible_generated_containment_triple_ids` 得到集合 `T`；当前 bible 中所有 **有父** 的 `loc.id` 集合为 `S`；对 `loc` 根节点曾在库中有的 containment：已由步骤 3 删除；另：若 `T` 中某 `triple_attr` 的 `bible_location_id` 已不在本次 `locations` 的 id 集合中，则 `delete` 该三元组。

名称与 id：现有 `_triple_to_fact_dict` 将 `Triple.subject_id` 同时写入 `subject` 与 `subject_entity_id`。**第一期推荐**：`Triple.subject_id` / `object_id` 均用 **location.id**，名称写入 `description` 或 `triple_attr`（如 `subject_name`、`object_name`），避免改动映射层；若要与 spec「文本列为名称」完全一致，在 Task 5 中扩展 `_triple_to_fact_dict`：当 `attributes` 含 `subject_label`/`object_label` 时用其作为 dict 的 `subject`/`object` 字段值，同时保留 `subject_entity_id`/`object_entity_id` 为 id。

- [ ] **Step 3: 幂等测试**

```python
# tests/unit/application/services/test_bible_location_triple_sync.py
# 使用 pytest + 临时 sqlite 文件路径，构造 TripleRepository，写两条 location 后 sync 两次；
# 断言 triples 表中 predicate=位于 且 bible_generated 的行数不变。
```

Run: `pytest tests/unit/application/services/test_bible_location_triple_sync.py -v`  
Expected: PASS

- [ ] **Step 4: chapter_inferred 不删**

在测试中先插入一条 `source_type=chapter_inferred` 的 `位于`（无 `bible_location_id`），同步后仍存在。

- [ ] **Step 5: Commit**

```bash
git add application/services/bible_location_triple_sync.py tests/unit/application/services/test_bible_location_triple_sync.py infrastructure/persistence/database/triple_repository.py
git commit -m "feat(sync): idempotent Bible locations to 位于 triples"
```

---

### Task 6: 挂载点 — 保存 Bible 与自动生成后调用同步

**Files:**
- Modify: `application/services/bible_service.py`（在 `save` 后调用，或通过 `FileBibleRepository` 装饰器；**推荐**在 `BibleService.update_bible` 末尾、`bible_repository.save(bible)` 之后注入 `sync_service.sync(novel_id, locations_dicts)`）
- Modify: `interfaces/api/dependencies.py`（构造 `BibleLocationTripleSyncService` 所需 `TripleRepository`）
- Modify: `application/services/auto_bible_generator.py`（`_save_to_bible` 或 `generate_and_save` 成功保存地点后调用同步）

- [ ] **Step 1: BibleService 注入可选 `location_triple_sync`**

若 `None`（测试无 DB）则跳过。接口示例：

```python
def sync_after_save(self, novel_id: str, bible: Bible) -> None:
    if self._location_triple_sync is None:
        return
    locs = [
        {
            "id": loc.id.strip(),
            "name": loc.name.strip(),
            "parent_id": loc.parent_id.strip() if loc.parent_id else None,
        }
        for loc in bible.locations
    ]
    self._location_triple_sync.sync_from_locations(novel_id, locs)
```

在 `update_bible` 成功 `save` 后调用 `sync_after_save`。

- [ ] **Step 2: AutoBibleGenerator**  
在写入 locations 到 Bible 并 `save` 之后，用同一 `novel_id` 与刚写入的 `locations` 列表调用同步（避免重复读文件可用内存中的 `bible_data["locations"]`，需已含 `id`/`parent_id`）。

- [ ] **Step 3: 手动跑一轮 API**

启动服务后更新 Bible（带 `parent_id`），查询 knowledge graph 或直连 DB 确认 `位于` 行存在。

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(bible): run location-triple sync after bible save and auto-generate"
```

---

### Task 7: Auto Bible 提示词与默认 JSON — `parent_id` + 稳定 `id`

**Files:**
- Modify: `application/services/auto_bible_generator.py`（`_generate_locations` 的 prompt 与解析后补全 `id`/`parent_id`）

- [ ] **Step 1: Prompt 片段**  
要求模型输出 `locations` 数组，每项含 `id`（稳定 slug）、`name`、`description`、`location_type`、`parent_id`（根为 `null`）；示例含大陆→城→室内三级。

- [ ] **Step 2: 后处理**  
若某条缺 `id`，用 `f"loc-{index}"` 或 `uuid4` 仅作兜底并打日志；优先保证 `parent_id` 引用存在。

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(auto-bible): locations prompt with parent_id and stable ids"
```

---

### Task 8: 前端（可选，第一期可省略）

**Files:**
- Modify: `web-app/src/components/BiblePanel.vue`、`web-app/src/api/bible.ts` 类型

- [ ] **Step 1:** 在保存 payload 中透传 `parent_id`（若 UI 暂不编辑，至少保留从 API load 的字段不被 strip）。  
- [ ] **Step 2:** `pnpm test` / `npm run build` 通过则 Commit `fix(web): preserve location parent_id in bible payload`。

---

## Self-review（对照 spec）

| Spec 章节 | 对应任务 |
|-----------|----------|
| 真源 Bible / triples | Task 1–2、6 |
| 两层 JSON、`parent_id` | Task 1–2、7 |
| 谓词 `位于`、bible_generated | Task 4–5 |
| triple_attr `bible_location_id` | Task 4–5 |
| 幂等、不覆盖 manual / 不删 inferred | Task 5 |
| 环、孤儿 | Task 3、5 |
| 第一期不含 edges[] 非树 | 未实现 Task 8 外不引入 |

**占位符扫描:** 本计划无 TBD/TODO 式步骤；具体 SQL 与类名以仓库为准，若 `Triple` 构造函数参数名不同，实现时按 `domain/bible/triple.py` 实际字段调整。

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-04-bible-location-triples-sync.md`. Two execution options:**

1. **Subagent-Driven（推荐）** — 每个 Task 单独子代理，任务间人工检查，迭代快。  
2. **Inline Execution** — 本会话内按 Task 顺序执行，用 executing-plans 式检查点批量推进。

你想用哪一种？
