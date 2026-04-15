# 智能检索与上下文管理（Phase 3）— 向量检索与触发词召回

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将规格 **模块三** 的「向量补充（Top-N）」与「触发词条件召回」接入现有 `ContextBuilder`；**模块四** 中与「章节 ±10 窗口」相关的规则筛选落地。替换 `dependencies.get_vector_store()` 当前返回 `None` 的可选路径。

**Architecture:**  
- 复用已有 `aitext/infrastructure/ai/qdrant_vector_store.py` 与 `domain/ai/services/vector_store.py`。  
- 新增 `OpenAIEmbeddingService` 或复用 `test_openai_embedding_service` 对应实现类，对大纲文本 embedding。  
- `ContextBuilder._build_layer2_smart_retrieval`：在 `vector_store` 非空时 `asyncio.run` 或把工作流升级为 async（**推荐**：仅 `retrieve_context` 与 `generate_chapter` 内对向量调用使用 `asyncio.get_event_loop().run_until_complete` 的隔离封装 `VectorRetrievalFacade.sync_search` 以避免全栈 async 大爆炸）。  
- 触发词：`application/services/trigger_keyword_catalog.py` 内置规格表格（战斗→武器/技能等），由 `SceneDirectorAnalysis.trigger_keywords` 与大纲中文关键词并集驱动。

**Tech Stack:** Qdrant、`qdrant-client`、OpenAI embeddings（与现有测试一致）、FastAPI。

**前置：** [Phase 1](./2026-04-05-intelligent-retrieval-context-management-phase1.md) 完成；与 Phase 2 无硬依赖。

**仓库对齐摘要：** Task 2、4 及 collection 约定、索引服务类已完成；Task 1（`trigger_keyword_catalog.py`）与 Task 5（Bible 联动）仍为占位/TODO；Task 3 中「章节保存自动索引」建议在业务保存路径上再确认是否已调用 `ChapterIndexingService` / `IndexingService`。

---

## 文件结构

| 路径 | 职责 |
|------|------|
| `aitext/application/services/trigger_keyword_catalog.py` | `expand_triggers(keywords: List[str]) -> Set[str]` |
| `aitext/application/services/vector_retrieval_facade.py` | 同步包装 async `VectorStore.search` + collection 命名 |
| `aitext/interfaces/api/dependencies.py` | `get_vector_store()` 按环境变量返回 `QdrantVectorStore` 或 `None` |
| `aitext/application/services/context_builder.py` | Layer2 合并向量 hits；按章节窗口过滤 payload |
| `aitext/infrastructure/persistence/database/sqlite_chapter_repository.py` | 若需 `list_by_novel_in_range` 可扩展 |

测试：`tests/unit/application/services/test_trigger_keyword_catalog.py`、`tests/integration/infrastructure/ai/test_qdrant_vector_store.py`（已有则扩展）

---

### Task 1: 触发词目录（纯函数）

- [ ] **Step 1: 测试**

```python
# tests/unit/application/services/test_trigger_keyword_catalog.py
from application.services.trigger_keyword_catalog import expand_triggers


def test_combat_maps_to_weapon_skill():
    assert "武器" in expand_triggers(["战斗"]) or "weapon" in expand_triggers(["combat"])
```

（按实际中文键调整断言。）

- [ ] **Step 2: 实现** 规格表格的最小字典 + 默认空集。

- [ ] **Step 3: Commit** — `feat(context): add trigger keyword expansion for smart retrieval`

---

### Task 2: 依赖注入接入 Qdrant

- [x] **Step 1:** 环境变量 `QDRANT_HOST`/`QDRANT_PORT`（默认 localhost:6333），未设置时保持 `None`。  
- [x] **Step 2:** `get_vector_store()` 返回 `QdrantVectorStore(...)` 或 `None`。  
- [x] **Step 3:** 文档字符串说明本地启动 Qdrant 的命令（不写新 README 文件，注释即可）。  
- [x] **Step 4: Commit**

---

### Task 3: Collection 约定与索引写入任务（可选独立 PR）

- [x] 约定 collection 名：`novel_{novel_id}_chunks`，payload 含 `chapter_number`, `text`, `kind`（chapter_summary | bible_snippet）。  
- [x] 提供 CLI 或 `application/services/chapter_indexing_service.py` 在章节保存时将摘要 embedding 写入（与现有 indexing 服务对齐搜索）。  
  - *注：`ChapterIndexingService` / `IndexingService` 已实现并有测试；是否在「章节保存」主流程中自动调用需在业务集成路径上单独确认。*

---

### Task 4: ContextBuilder Layer2 向量分支

- [x] **Step 1: 测试** — Mock `VectorStore.search` 返回 2 条 payload，断言 `build_context` 或 `build_structured_context` 的 layer2 文本包含 payload 片段。

- [x] **Step 2: 实现**  
  - 若 `vector_store` 为 `None`，行为与 Phase 1 一致。  
  - 非空：用 `outline` 调 embedding → `search(limit=5)` → 过滤 `abs(hit_chapter - current) <= 10`（规格 ±10 章）。  
  - 将结果块追加到 Layer2，仍受 token 预算与 `_truncate_text` 约束。

- [x] **Step 3: Commit**

---

### Task 5: 触发词与 Bible 切片联动（YAGNI 边界）

- [ ] 仅当 Layer2 中存在「世界观规则/技能」等结构化段时，用 `expand_triggers(scene_director.trigger_keywords)` 从 `bible_dto` 或 knowledge triples 中选段；若无对应 API，本 Task 可只追加占位 TODO 注释与空实现测试跳过——**禁止**无测试的大段空逻辑。

---

## Self-review

- **模块三** 向量 Top-5、±10 章：Task 4。  
- **触发词**：Task 1、5。  
- **模块四 30% 设定占比**：在 Phase 1 已有分层比例；Phase 3 可在 `build_structured_context` 增加 `settings_token_ratio` 断言式单测（可选）。  
- **异步策略**：若全栈改 async 成本过高，维持同步 `build_context` + facade 内 `asyncio.run` 的显式边界（文档警告勿在已有 event loop 内嵌套）。
