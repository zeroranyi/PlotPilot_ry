# 智能检索与上下文管理（Phase 4）— 冲突、伏笔账本、视点防火墙

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地规格 **模块五**（大纲绝对意志 + 生成后幽灵批注）、**模块六** 的潜台词账本与「一击致命」查询入口、**模块一扩展**（场记输出「表演指令」而非剧透 hidden 设定）。依赖 **Phase 2** 的实体状态重放（冲突检测）与 **Phase 1** 场记 DTO。

**Architecture:**  
- `ConflictDetectionService`：输入 `outline`、`SceneDirectorAnalysis`、可选 `entity_states: dict[str, dict]`（自 Phase 2），输出 `List[GhostAnnotation]`（Pydantic：`type`, `severity`, `message`, `entity_id?`）。**不阻断生成**；由 `GenerationResult` 或并行字段返回给 API。  
- `ForeshadowLedgerRepository`：可 **扩展** `FileForeshadowingRegistry` 的 JSON 结构，或新增 SQLite 表 `foreshadow_ledger`（part2）；与现有 `ForeshadowingRepository` 并存时明确优先级（建议：账本存「感官锚点」细粒度，registry 存粗粒度伏笔，Phase 4 先扩展文件 JSON 避免双源）。  
- **视点防火墙**：扩展 `CharacterDTO` / Bible 存储模型，支持 `public_profile` 与 `hidden_profile`（均为 TEXT JSON 或结构化子表）；`ContextBuilder` 在组装 Layer2 时根据 `scene_director.pov` 与 `chapter_number` 与 `reveal_chapter` 过滤 hidden。  
- **场记**：`SceneDirectorAnalysis` 增加可选字段 `performance_notes: List[str]`（或 `director_instructions: str`），由 LLM 生成「动作级指令」，不注入 hidden 身份词。

**前置：** Phase 1；Phase 2（冲突与实体状态）；Phase 3 非必须。

**仓库对齐：** 2026-04-05 核对，本 Phase 任务已全部勾选。幽灵批注模型在 `application/dtos/ghost_annotation.py`（非文内 `ghost_annotation_dto.py` 文件名）。

---

## 文件结构

| 路径 | 职责 |
|------|------|
| `aitext/application/dtos/ghost_annotation_dto.py` | `GhostAnnotation`, `ConflictCheckResponse` |
| `aitext/application/services/conflict_detection_service.py` | `detect(...)` 纯规则 + 可选 LLM 二次确认（YAGNI：先规则） |
| `aitext/application/dtos/scene_director_dto.py` | 扩展 `performance_notes` |
| `aitext/application/services/scene_director_service.py` | 更新 prompt 要求输出 performance 字段 |
| `aitext/application/dtos/bible_dto.py` / domain Character | `public`/`hidden`/`reveal_chapter` |
| `aitext/application/services/context_builder.py` | POV 过滤 hidden |
| `aitext/application/workflows/auto_novel_generation_workflow.py` | 生成后调用 `detect`，附加到结果 |
| `aitext/application/dtos/generation_result.py` 或 API 响应 | `ghost_annotations: List[...]` |
| `aitext/domain/novel/entities/foreshadowing_registry.py` 或新 ledger | 账本条目字段 |

测试：`tests/unit/application/services/test_conflict_detection_service.py`、`tests/unit/application/services/test_context_builder_pov_firewall.py`

---

### Task 1: GhostAnnotation DTO

- [x] Pydantic 模型 + JSON 序列化测试。

---

### Task 2: 规则型冲突检测（示例：元素体系）

- [x] **Step 1: 测试**

```python
def test_detect_setting_conflict_when_outline_contradicts_state():
    from application.services.conflict_detection_service import ConflictDetectionService

    svc = ConflictDetectionService()
    issues = svc.detect(
        outline="李明掐诀，一道火球射向敌人。",
        entity_states={"ent-1": {"魔法": "水系"}},
        name_to_entity_id={"李明": "ent-1"},
    )
    assert any(i.type == "setting_conflict" for i in issues)
```

- [x] **Step 2: 实现** 最小规则：关键词「火」+ 状态「水系」→ warning（可维护映射表，避免万能 NLP）。  
- [x] **Step 3: Commit**

---

### Task 3: 工作流挂载批注

- [x] `generate_chapter` 返回体增加 `ghost_annotations`；`generation.py` 响应模型扩展；集成测试 Mock 冲突服务。

---

### Task 4: Bible public/hidden + ContextBuilder

- [x] **Step 1:** DTO 扩展字段默认值向后兼容（旧数据无 hidden → 行为与今相同）。  
- [x] **Step 2:** `_build_layer2` 仅当 `reveal_chapter` 为空或 `chapter_number >= reveal_chapter` 时附加 hidden 文本。  
- [x] **Step 3:** 单元测试：第 10 章 POV 男主、林雪 reveal=100 → layer2 无「卧底」字样。

---

### Task 5: 场记 performance_notes

- [x] 更新 JSON schema 与 `SceneDirectorService._coerce`；前端可展示给主力模型 prompt 拼接模块（后端只存字段）。

---

### Task 6: 潜台词账本（文件型 MVP）

- [x] 在 `ForeshadowingRegistry` 或并列结构增加 `subtext_entries: List[SubtextLedgerEntry]`（`id`, `chapter`, `character_id`, `hidden_clue`, `sensory_anchors` dict, `status`, `consumed_at_chapter?`）。  
- [x] `POST /api/v1/novels/{id}/foreshadow-ledger` 增删改查最小集。  
- [x] 「感官匹配」查询：`find_best_anchor_match(current_anchors: dict) -> Optional[entry]` 纯函数 + 单元测试（字符串子串匹配即可 MVP）。

---

## Self-review

- **模块五** 执行期沉默、校对期批注：Task 2–3。  
- **模块六** 账本 + 匹配：Task 6。  
- **视点防火墙 + 情绪降维**：Task 4–5（表演指令替代直接注入 hidden）。  
- **缺口**：结算期「一键更新设定 / 笔误修正重写」需 UI + 工作流 API，可放 Phase 6 或独立小计划。
