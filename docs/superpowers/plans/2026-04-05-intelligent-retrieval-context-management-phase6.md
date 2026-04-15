# 智能检索与上下文管理（Phase 6）— 全局大修、沙盘、卡文破局

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将规格 **全局大修工具**、**沙盘试读**、**卡文破局（张力弹弓）** 落为 **可测 API 与工作流骨架**；完整「局部重渲染」「叙事心电图」需前端与大量产品交互，本阶段以 **后端契约 + 纯函数/任务队列占位** 为主。

**Architecture:**  
- **事件断点扫描**：输入 `novel_id`、目标人设标签（如 `trait: 热血→冷酷`）、读取 Phase 2 `narrative_events` 的 `mutations` / 元数据字段 `motivation`（需在 Phase 2 Task 扩展 payload 或单独 `event_tags` 表）。输出 `List[LogicBreakpoint]`（`event_id`, `chapter`, `reason`）。  
- **对话式修复**：`POST .../macro-refactor/proposals`  body 含 `event_id` + 作者意图 → 调场记 LLM 返回建议 JSON → `PATCH .../narrative_events/{event_id}` 更新摘要与 mutations（权限与版本控制 YAGNI：单用户本地）。  
- **局部重渲染**：`POST .../chapters/{n}/rerender-segments` body 含 `paragraph_spans` 或 `event_ids` → 调 `AutoNovelGenerationWorkflow` 子例仅重写范围（若当前无 span API，则 MVP 为整章重写开关 + `dry_run`）。  
- **沙盘**：`novel_branches` 表或在 `novels` 上 `sandbox_fork_of` 字段；试读 API 返回聚合对白/动作列表（LLM 从章节抽取或简化正则，MVP 用 LLM 一次生成摘要列表）。  
- **卡文破局**：`POST /api/v1/writer-block/slingshot` body `{ "seed_image": "..." }` → LLM 返回 3 条 `what_if` 字符串 + 可选 `backbone_events`（3 条骨架）；无状态，不持久化。

**前置：** Phase 2（大修核心）；Phase 1（场记 LLM）；Phase 4 可选（冲突提示）。

**Celery：** 仅当「重渲染整章」超时再引入；本 Phase 默认同步 + 前端 loading。

**仓库对齐摘要：** Task 1–5 已勾选；事件补丁为 `POST /api/v1/novels/{id}/macro-refactor/apply`（非计划中的 `PATCH .../narrative-events/...`）。卡文端点为 `POST /api/v1/novels/{id}/writer-block/tension-slingshot` + `TensionAnalyzer`（非文根 `POST /api/v1/writer-block/slingshot`）。Task 6 实际为 `GET .../sandbox/dialogue-whitelist`。

---

## 文件结构

| 路径 | 职责 |
|------|------|
| `aitext/application/dtos/macro_refactor_dto.py` | `LogicBreakpoint`, `RefactorProposalRequest` |
| `aitext/application/services/macro_refactor_scanner.py` | `scan_breakpoints(...)` |
| `aitext/interfaces/api/v1/macro_refactor.py` | scan / propose / patch 事件 |
| `aitext/interfaces/api/v1/writer_block.py` | slingshot 端点 |
| `aitext/application/services/writer_block_service.py` | LLM 调用与 JSON 形状 |
| `aitext/infrastructure/persistence/database/schema.sql` | 可选 `novel_branches`, `event_tags` |

---

### Task 1: 事件元数据扩展

- [x] 为 `narrative_events` 增加可选列 `tags TEXT`（JSON 数组）或关联表 `event_tag(event_id, key, value)`。  
- [x] 迁移 + 测试。

---

### Task 2: scan_breakpoints

- [x] **Step 1: 测试** — 造事件 `{"动机":"冲动"}` ×3，扫描目标 `冷酷` 得 3 条 breakpoint（规则用字符串包含或键值匹配 MVP）。  
- [x] **Step 2: 实现** `MacroRefactorScanner`。  
- [x] **Step 3: API** `GET /api/v1/novels/{id}/macro-refactor/breakpoints?trait=...`  
- [x] **Step 4: Commit**

---

### Task 3: Refactor 提案 LLM

- [x] `POST .../macro-refactor/proposals` 返回自然语言 + 结构化 `suggested_mutations`；单测 Mock LLM。

---

### Task 4: 应用补丁

- [x] `PATCH .../narrative-events/{event_id}` 更新事件；集成测试断点修复后重放状态变化。  
  - *仓库实现：`POST /api/v1/novels/{id}/macro-refactor/apply` + `MutationApplier`。*

---

### Task 5: 卡文张力弹弓

- [x] **Step 1: 测试** — 集成/单测针对 `TensionAnalyzer`（非文内 `WriterBlockService` 命名）。  
- [x] **Step 2: Prompt** — LLM 张力诊断与建议（JSON/结构化由 DTO 约束）。  
- [x] **Step 3: 路由** `POST /api/v1/novels/{novel_id}/writer-block/tension-slingshot`  
- [x] **Step 4: Commit**

---

### Task 6（可选）: 沙盘对白列表

- [x] `GET /api/v1/novels/{id}/sandbox/dialogue-strip?branch=main` 返回 `List[{chapter, text, kind}]`，内部调用 LLM 或占位返回空列表并 `501` 开关（feature flag）。  
  - *仓库实现：`GET .../sandbox/dialogue-whitelist`（`SandboxDialogueService`）；与计划路径名不同，能力对白列表/试读向。*

---

## Self-review

- **全局大修** 主路径：Task 1–4。  
- **卡文破局**：Task 5。  
- **沙盘音轨/心电图**：Task 6 或前端图表 + 本 API 提供数据。  
- **合并主时间线**：需分支模型与冲突解决 UI，建议在 `novel_branches` 落地后再写 Phase 6b 计划。
