# 智能检索与上下文管理（Phase 5）— 文风金库与指纹

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地规格 **模块七** 的 MVP：**采血**（AI 原文 vs 作者改稿）、**俗套句式检测**、**指纹快照**（简化版统计特征）、生成前 prompt 片段注入与生成后标记。多 POV 独立指纹、风格迁移标为后续。

**Architecture:**  
- SQLite 表 `voice_vault` / `voice_fingerprint`（与 part2 DDL 一致，类型改为 SQLite TEXT/INT）。  
- `VoiceSampleService.append_sample(novel_id, chapter, scene_type, ai_original, author_refined)` 计算轻量 `diff_analysis`（diff 可用 `difflib` 或仅长度/编辑距离，避免重依赖）。  
- `VoiceFingerprintService.compute(samples: List[VoiceSample]) -> dict`：形容词密度、平均句长、句数（中文按标点切分近似）。  
- `cliche_scanner.py`：规格中的 `AI_CLICHE_PATTERNS` 正则列表 → `scan(text) -> List[ClicheHit]`。  
- `ContextBuilder` Layer1 或独立 `StyleConstraintBuilder` 将指纹摘要拼成短 bullet（≤1K tokens）。

**前置：** Phase 1；与 Phase 4 可并行。

**仓库对齐：** 2026-04-05 核对，本 Phase 勾选任务均已在仓库落地；**7.4 漂移监控**（`chapter_style_scores` 等）仍为 Self-review 中的延后项，未单列成可勾选 Task。

---

## 文件结构

| 路径 | 职责 |
|------|------|
| `aitext/infrastructure/persistence/database/schema.sql` | `voice_vault`, `voice_fingerprint` |
| `aitext/infrastructure/persistence/database/sqlite_voice_vault_repository.py` | CRUD |
| `aitext/application/services/voice_sample_service.py` | 采血与 diff |
| `aitext/application/services/voice_fingerprint_service.py` | 统计指纹 |
| `aitext/application/services/cliche_scanner.py` | 正则扫描 |
| `aitext/interfaces/api/v1/voice.py` | `POST .../voice/samples`, `GET .../voice/fingerprint` |
| `aitext/application/services/context_builder.py` 或调用方 | 可选注入风格约束 |

---

### Task 1: DDL

- [x] 追加 `voice_vault` / `voice_fingerprint` 表；集成测试表存在性。

---

### Task 2: cliche_scanner

- [x] **Step 1: 测试**

```python
from application.services.cliche_scanner import scan_cliches

def test_detects_bears_fire():
    hits = scan_cliches("他心中燃起熊熊怒火")
    assert hits
```

- [x] **Step 2: 实现** 规格列表子集（≥5 条正则）。  
- [x] **Step 3: Commit**

---

### Task 3: voice_vault 写入

- [x] API：`POST /api/v1/novels/{novel_id}/voice/samples`，body 含 `ai_original`, `author_refined`, `chapter_number`, `scene_type`。  
- [x] 持久化 + 返回 `sample_id`。

---

### Task 4: 指纹重算

- [x] 每累积 `N=10` 条样本触发重算（可在 `append_sample` 内计数），更新 `voice_fingerprint` 行。  
- [x] `GET .../voice/fingerprint` 返回 JSON 指纹。

---

### Task 5: 生成链路挂钩（最小）

- [x] `AutoNovelGenerationWorkflow` 在构建 prompt 前 `optional` 读取指纹摘要字符串；生成后对 `content` 运行 `scan_cliches`，写入日志或 `GenerationResult` 新字段 `style_warnings`（不自动重写 LLM，避免成本爆炸）。

---

## Self-review

- **7.1–7.3** 部分覆盖；**7.4 漂移监控**（连续 5 章 <75%）需章节历史存储匹配度，建议 Phase 5 Task 6 或延后：增加 `chapter_style_scores` 表。  
- **7.5 多风格** 未纳入本 Phase。
