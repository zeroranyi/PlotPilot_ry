# 智能检索与上下文管理（Phase 1）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **路线图：** 全部分阶段计划见同目录 [`2026-04-05-intelligent-retrieval-context-management-overview.md`](./2026-04-05-intelligent-retrieval-context-management-overview.md)（Phase 2–6）。

**Goal:** 在现有 `aitext` 后端上落地「场记智能体结构化输出 → 可选过滤 ContextBuilder Layer 2 → 分层 JSON 召回 API」，与规格文档中的场景 1（防抖由前端负责）对齐；不引入 Celery/PostgreSQL 新表。

**Architecture:** 轻量 LLM 通过既有 `LLMService`（`AnthropicProvider` / `MockProvider`）生成 JSON，经 `application/ai/llm_json_extract.py` 校验；`ContextBuilder` 在保留原 `build_context` 字符串输出的前提下，增加可选 `scene_director` 提示以缩小 Bible 角色/地点候选，并新增结构化三层输出供 `POST .../context/retrieve` 使用。向量检索在 `get_vector_store()` 仍为 `None` 时跳过，与当前依赖注入行为一致。

**Tech Stack:** Python 3、FastAPI、Pydantic v2、pytest、既有 SQLite 仓储与 `BibleService`、`ContextBuilder`、`AutoNovelGenerationWorkflow`。

**规格范围说明（必读）：**  
`2026-04-05-intelligent-retrieval-context-management-design.md` 与 `...-part2.md` 含七大模块及全局大修、卡文破局等。**本计划仅覆盖 Phase 1**：模块一（场记 JSON）、模块三的部分（规则筛选 + 与现有三层上下文对齐）、模块四（显式 token_usage 统计与分层预算）。以下需 **单独计划**（避免单 PR 不可测试交付）：叙事事件溯源表与重放、`foreshadow_ledger` / `voice_vault` SQL、冲突检测与幽灵批注闭环、视点防火墙与 hidden 设定、Celery 队列、Qdrant 在 `dependencies` 中的实装接入。

**仓库对齐：** 2026-04-05 核对，下文 `aitext/` 前缀在仓库中对应根目录下的 `application/`、`interfaces/` 等；本 Phase 任务已全部勾选。

---

## 文件结构（创建 / 修改）

| 路径 | 职责 |
|------|------|
| `aitext/application/dtos/scene_director_dto.py` | 场记请求/响应 Pydantic 模型（与 part2 API 示例字段一致） |
| `aitext/application/services/scene_director_service.py` | 调用 LLM + 解析 JSON → `SceneDirectorAnalysis` |
| `aitext/application/services/context_builder.py` | 可选场记过滤；`build_structured_context`；Layer 2 在 `vector_store` 非空时预留异步扩展点（Phase 1 可保持同步占位注释） |
| `aitext/interfaces/api/v1/context_intelligence.py` | `POST .../scene-director/analyze` 与 `POST .../context/retrieve` |
| `aitext/interfaces/main.py` | `include_router` 新路由 |
| `aitext/interfaces/api/dependencies.py` | `get_scene_director_service()`，与 `_anthropic_settings` 模式一致 |
| `aitext/application/workflows/auto_novel_generation_workflow.py`（可选） | `generate_chapter` 增加可选 `scene_director_override`，传入 `build_context` |

测试文件见各 Task。

---

### Task 1: 场记 DTO 与 JSON 契约单元测试

**Files:**
- Create: `aitext/application/dtos/scene_director_dto.py`
- Create: `aitext/tests/unit/application/dtos/test_scene_director_dto.py`

- [x] **Step 1: 编写失败测试（模型校验）**

```python
# aitext/tests/unit/application/dtos/test_scene_director_dto.py
import pytest
from pydantic import ValidationError

from application.dtos.scene_director_dto import (
    SceneDirectorAnalysis,
    SceneDirectorAnalyzeRequest,
)


def test_scene_director_analysis_accepts_valid_payload():
    m = SceneDirectorAnalysis(
        characters=["李明"],
        locations=["废弃工厂"],
        action_types=["combat"],
        trigger_keywords=["武器"],
        emotional_state="tense",
        pov="李明",
    )
    assert m.pov == "李明"


def test_outline_request_rejects_empty_outline():
    with pytest.raises(ValidationError):
        SceneDirectorAnalyzeRequest(chapter_number=1, outline="   ")
```

- [x] **Step 2: 运行测试确认失败**

Run: `cd d:\CODE\aitext && python -m pytest tests/unit/application/dtos/test_scene_director_dto.py -v`  
Expected: `ModuleNotFoundError` 或 `ImportError`（模块不存在）

- [x] **Step 3: 实现 DTO**

```python
# aitext/application/dtos/scene_director_dto.py
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SceneDirectorAnalyzeRequest(BaseModel):
    chapter_number: int = Field(ge=1)
    outline: str = Field(min_length=1)


class SceneDirectorAnalysis(BaseModel):
    characters: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    action_types: List[str] = Field(default_factory=list)
    trigger_keywords: List[str] = Field(default_factory=list)
    emotional_state: str = ""
    pov: Optional[str] = None


class SceneDirectorAnalyzeResponse(BaseModel):
    characters: List[str]
    locations: List[str]
    action_types: List[str]
    trigger_keywords: List[str]
    emotional_state: str
    pov: Optional[str]
```

- [x] **Step 4: 运行测试通过**

Run: `python -m pytest tests/unit/application/dtos/test_scene_director_dto.py -v`  
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add aitext/application/dtos/scene_director_dto.py aitext/tests/unit/application/dtos/test_scene_director_dto.py
git commit -m "feat(scene-director): add Pydantic DTOs for outline analysis API"
```

---

### Task 2: SceneDirectorService（Mock LLM）解析逻辑

**Files:**
- Create: `aitext/application/services/scene_director_service.py`
- Create: `aitext/tests/unit/application/services/test_scene_director_service.py`

- [x] **Step 1: 编写失败测试**

```python
# aitext/tests/unit/application/services/test_scene_director_service.py
import pytest
from unittest.mock import AsyncMock, Mock

from application.dtos.scene_director_dto import SceneDirectorAnalysis
from application.services.scene_director_service import SceneDirectorService
from domain.ai.services.llm_service import GenerationConfig, GenerationResult
from domain.ai.value_objects.prompt import Prompt
from domain.ai.value_objects.token_usage import TokenUsage


@pytest.mark.asyncio
async def test_analyze_outline_parses_json():
    llm = Mock()
    llm.generate = AsyncMock(
        return_value=GenerationResult(
            content='{"characters":["A"],"locations":[],"action_types":[],"trigger_keywords":[],"emotional_state":"calm","pov":"A"}',
            token_usage=TokenUsage(input_tokens=1, output_tokens=1),
        )
    )
    svc = SceneDirectorService(llm_service=llm)
    result = await svc.analyze(chapter_number=1, outline="A walks")
    assert isinstance(result, SceneDirectorAnalysis)
    assert result.characters == ["A"]
    llm.generate.assert_called_once()
```

- [x] **Step 2: 运行测试失败**

Run: `python -m pytest tests/unit/application/services/test_scene_director_service.py -v`  
Expected: ImportError / AttributeError

- [x] **Step 3: 实现服务**

```python
# aitext/application/services/scene_director_service.py
from __future__ import annotations

import logging
from typing import Optional

from application.ai.llm_json_extract import parse_llm_json_to_dict
from application.dtos.scene_director_dto import SceneDirectorAnalysis
from domain.ai.services.llm_service import GenerationConfig, LLMService
from domain.ai.value_objects.prompt import Prompt

logger = logging.getLogger(__name__)

SCENE_DIRECTOR_SYSTEM = """你是小说场记。根据给定章节大纲，只输出一个 JSON 对象，键为：
characters, locations, action_types, trigger_keywords, emotional_state, pov。
characters/locations/action_types/trigger_keywords 均为字符串数组；emotional_state 为简短英文或中文单词；pov 为视点人物名字符串或 null。
不要 markdown，不要解释。"""


class SceneDirectorService:
    def __init__(self, llm_service: LLMService, *, model: str = "claude-3-5-haiku-20241022"):
        self._llm = llm_service
        self._model = model

    async def analyze(self, chapter_number: int, outline: str) -> SceneDirectorAnalysis:
        user = f"章节号: {chapter_number}\n大纲:\n{outline.strip()}"
        prompt = Prompt(system=SCENE_DIRECTOR_SYSTEM, user=user)
        config = GenerationConfig(model=self._model, max_tokens=1024, temperature=0.2)
        raw = await self._llm.generate(prompt, config)
        data, errs = parse_llm_json_to_dict(raw.content)
        if not data:
            logger.warning("scene director JSON parse failed: %s", errs)
            return SceneDirectorAnalysis()
        return self._coerce(data)

    def _coerce(self, data: dict) -> SceneDirectorAnalysis:
        def as_str_list(key: str) -> list:
            v = data.get(key)
            if v is None:
                return []
            if isinstance(v, list):
                return [str(x) for x in v if x is not None]
            return [str(v)]

        pov = data.get("pov")
        if pov is not None:
            pov = str(pov).strip() or None

        return SceneDirectorAnalysis(
            characters=as_str_list("characters"),
            locations=as_str_list("locations"),
            action_types=as_str_list("action_types"),
            trigger_keywords=as_str_list("trigger_keywords"),
            emotional_state=str(data.get("emotional_state") or "").strip(),
            pov=pov,
        )
```

- [x] **Step 4: 运行测试通过**

Run: `python -m pytest tests/unit/application/services/test_scene_director_service.py -v`  
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add aitext/application/services/scene_director_service.py aitext/tests/unit/application/services/test_scene_director_service.py
git commit -m "feat(scene-director): add LLM-backed outline analysis service"
```

---

### Task 3: FastAPI 路由 scene-director/analyze

**Files:**
- Create: `aitext/interfaces/api/v1/context_intelligence.py`
- Modify: `aitext/interfaces/main.py`（增加 `include_router`）
- Modify: `aitext/interfaces/api/dependencies.py`（`get_scene_director_service`）
- Create: `aitext/tests/integration/interfaces/api/v1/test_context_intelligence_api.py`

- [x] **Step 1: 依赖注入**

在 `dependencies.py` 末尾附近添加：

```python
from application.services.scene_director_service import SceneDirectorService


def get_scene_director_service() -> SceneDirectorService:
    settings = _anthropic_settings(require_key=False)
    if settings:
        llm_service = AnthropicProvider(settings)
    else:
        from infrastructure.ai.providers.mock_provider import MockProvider
        llm_service = MockProvider()
    return SceneDirectorService(llm_service=llm_service)
```

- [x] **Step 2: 路由模块**

```python
# aitext/interfaces/api/v1/context_intelligence.py
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from application.dtos.scene_director_dto import (
    SceneDirectorAnalyzeRequest,
    SceneDirectorAnalyzeResponse,
)
from application.services.scene_director_service import SceneDirectorService
from interfaces.api.dependencies import get_scene_director_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novels", tags=["context-intelligence"])


@router.post("/{novel_id}/scene-director/analyze", response_model=SceneDirectorAnalyzeResponse)
async def analyze_outline(
    novel_id: str,
    body: SceneDirectorAnalyzeRequest,
    svc: SceneDirectorService = Depends(get_scene_director_service),
):
    _ = novel_id  # 预留：可按小说过滤词表；Phase 1 仅记录日志
    logger.debug("scene-director analyze novel_id=%s chapter=%s", novel_id, body.chapter_number)
    try:
        r = await svc.analyze(body.chapter_number, body.outline)
    except Exception as e:
        logger.exception("scene-director failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    return SceneDirectorAnalyzeResponse(
        characters=r.characters,
        locations=r.locations,
        action_types=r.action_types,
        trigger_keywords=r.trigger_keywords,
        emotional_state=r.emotional_state,
        pov=r.pov,
    )
```

- [x] **Step 3: main.py 注册**

```python
from interfaces.api.v1 import context_intelligence
# ...
app.include_router(context_intelligence.router, prefix="/api/v1")
```

- [x] **Step 4: 集成测试（TestClient + MockProvider）**

```python
# aitext/tests/integration/interfaces/api/v1/test_context_intelligence_api.py
from fastapi.testclient import TestClient

from interfaces.main import app


def test_scene_director_analyze_returns_json_shape():
    client = TestClient(app)
    r = client.post(
        "/api/v1/novels/test-novel/scene-director/analyze",
        json={"chapter_number": 1, "outline": "主角进入房间。"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "characters" in data and isinstance(data["characters"], list)
```

- [x] **Step 5: 运行并提交**

Run: `python -m pytest tests/integration/interfaces/api/v1/test_context_intelligence_api.py -v`  
Expected: PASS

```bash
git add aitext/interfaces/api/v1/context_intelligence.py aitext/interfaces/main.py aitext/interfaces/api/dependencies.py aitext/tests/integration/interfaces/api/v1/test_context_intelligence_api.py
git commit -m "feat(api): add POST /novels/{id}/scene-director/analyze"
```

---

### Task 4: ContextBuilder 可选场记过滤 + 结构化输出

**Files:**
- Modify: `aitext/application/services/context_builder.py`
- Modify: `aitext/tests/unit/application/services/test_context_builder.py`

- [x] **Step 1: 编写测试（仅当提供名字时过滤 Layer 2 角色）**

```python
# 在 test_context_builder.py 新增
from application.dtos.scene_director_dto import SceneDirectorAnalysis


def test_layer2_filters_characters_when_scene_director_set():
    dto = _empty_bible_dto(
        characters=[
            CharacterDTO("c1", "Alice", "Hero", []),
            CharacterDTO("c2", "Bob", "Villain", []),
        ]
    )
    builder = _make_builder(bible_dto=dto)
    hint = SceneDirectorAnalysis(characters=["Alice"], locations=[], action_types=[], trigger_keywords=[], emotional_state="", pov="Alice")
    structured = builder.build_structured_context(
        novel_id="novel-1",
        chapter_number=2,
        outline="Alice fights",
        max_tokens=35000,
        scene_director=hint,
    )
    layer2 = structured["layer2_text"]
    assert "Alice" in layer2
    assert "Bob" not in layer2
```

- [x] **Step 2: 运行失败**

Run: `python -m pytest tests/unit/application/services/test_context_builder.py::test_layer2_filters_characters_when_scene_director_set -v`  
Expected: FAIL（无 `build_structured_context`）

- [x] **Step 3: 实现要点（节选，工程师需与现有私有方法对齐）**

1. `from application.dtos.scene_director_dto import SceneDirectorAnalysis`（使用 `TYPE_CHECKING` 避免循环则可）。
2. 将 `_build_layer2_smart_retrieval` 增加可选参数 `scene_director: Optional[SceneDirectorAnalysis] = None`；在遍历 `bible_dto.characters` 时若 `scene_director` 且 `scene_director.characters` 非空，仅保留 `char.name` 出现在 `hint.characters` 中的项（地点同理）。
3. 新增：

```python
def build_structured_context(
    self,
    novel_id: str,
    chapter_number: int,
    outline: str,
    max_tokens: int = 35000,
    scene_director: Optional[SceneDirectorAnalysis] = None,
) -> dict:
    layer1_budget = int(max_tokens * 0.15)
    layer2_budget = int(max_tokens * 0.55)
    layer3_budget = int(max_tokens * 0.30)
    layer1 = self._build_layer1_core_context(novel_id, chapter_number, outline, layer1_budget)
    layer2 = self._build_layer2_smart_retrieval(
        novel_id, chapter_number, outline, layer2_budget, scene_director=scene_director
    )
    layer3 = self._build_layer3_recent_context(novel_id, chapter_number, layer3_budget)
    t1, t2, t3 = self.estimate_tokens(layer1), self.estimate_tokens(layer2), self.estimate_tokens(layer3)
    total = t1 + t2 + t3
    return {
        "layer1_text": layer1,
        "layer2_text": layer2,
        "layer3_text": layer3,
        "token_usage": {"layer1": t1, "layer2": t2, "layer3": t3, "total": total},
    }
```

4. `build_context` 内调用 `_build_layer2_smart_retrieval(..., scene_director=None)` 保持旧行为。

- [x] **Step 4: 全量 ContextBuilder 测试**

Run: `python -m pytest tests/unit/application/services/test_context_builder.py -v`  
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add aitext/application/services/context_builder.py aitext/tests/unit/application/services/test_context_builder.py
git commit -m "feat(context): optional scene-director filter and structured layer payload"
```

---

### Task 5: POST /novels/{id}/context/retrieve

**Files:**
- Modify: `aitext/interfaces/api/v1/context_intelligence.py`
- Modify: `aitext/tests/integration/interfaces/api/v1/test_context_intelligence_api.py`
- Modify: `aitext/interfaces/api/dependencies.py`（`get_context_builder` 已存在，直接 Depends）

- [x] **Step 1: Pydantic 请求/响应模型**（可放在 `scene_director_dto.py` 或同文件）

```python
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ContextRetrieveRequest(BaseModel):
    chapter_number: int = Field(ge=1)
    outline: str = Field(min_length=1)
    scene_director_result: Optional[Dict[str, Any]] = None
    max_tokens: int = Field(default=35000, ge=4096, le=120000)


class ContextRetrieveResponse(BaseModel):
    layer1: Dict[str, Any]
    layer2: Dict[str, Any]
    layer3: Dict[str, Any]
    token_usage: Dict[str, int]
```

响应体将 `layer1`/`layer2`/`layer3` 设为 `{"content": "<文本>"}`，与 part2 示例的嵌套对象对齐且便于后续扩展 `novel_metadata` 等字段。

- [x] **Step 2: 端点实现**

```python
@router.post("/{novel_id}/context/retrieve", response_model=ContextRetrieveResponse)
def retrieve_context(
    novel_id: str,
    body: ContextRetrieveRequest,
    builder: ContextBuilder = Depends(get_context_builder),
):
    from application.dtos.scene_director_dto import SceneDirectorAnalysis

    hint = None
    if body.scene_director_result:
        hint = SceneDirectorAnalysis.model_validate(body.scene_director_result)
    payload = builder.build_structured_context(
        novel_id=novel_id,
        chapter_number=body.chapter_number,
        outline=body.outline,
        max_tokens=body.max_tokens,
        scene_director=hint,
    )
    return ContextRetrieveResponse(
        layer1={"content": payload["layer1_text"]},
        layer2={"content": payload["layer2_text"]},
        layer3={"content": payload["layer3_text"]},
        token_usage=payload["token_usage"],
    )
```

- [x] **Step 3: 集成测试**

```python
def test_context_retrieve_returns_layers():
    client = TestClient(app)
    r = client.post(
        "/api/v1/novels/test-novel/context/retrieve",
        json={"chapter_number": 1, "outline": "开场。", "max_tokens": 8000},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "layer1" in body and "content" in body["layer1"]
    assert body["token_usage"]["total"] >= 0
```

- [x] **Step 4: 运行 pytest**

Run: `python -m pytest tests/integration/interfaces/api/v1/test_context_intelligence_api.py -v`

- [x] **Step 5: Commit**

```bash
git commit -am "feat(api): add POST /novels/{id}/context/retrieve with layered payload"
```

---

### Task 6（可选）: 生成工作流接入场记结果

**Files:**
- Modify: `aitext/application/workflows/auto_novel_generation_workflow.py`
- Modify: `aitext/interfaces/api/v1/generation.py`（`GenerateChapterRequest` 增加可选 `scene_director_result`）
- Modify: `aitext/tests/unit/application/workflows/test_auto_novel_generation_workflow.py`

- [x] 为 `generate_chapter` 增加可选参数 `scene_director: Optional[SceneDirectorAnalysis] = None`，在调用 `build_context` 前若项目已改为统一入口 `build_structured_context`+拼接，则同步；**最小改动**为扩展 `ContextBuilder.build_context(..., scene_director=None)` 签名并在 workflow 中传入。

- [x] 单测断言 `build_context` 以 `scene_director=` 被调用。

---

## Self-review（计划自检）

**1. Spec coverage（Phase 1）**  
- 场记 JSON 与 API：Task 1–3。  
- 知识召回分层 + token 统计：Task 4–5。  
- 规则筛选（出场人物/地点子集）：Task 4。  
- 防抖 2s、Celery、向量 Top-5、冲突批注、伏笔账本、文风金库、事件流 SQL、全局大修、卡文破局：**未在本计划** → 需后续独立计划。

**2. Placeholder scan**  
- 无 TBD；向量增强明确为 Phase 2（依赖 `get_vector_store()` 非空与异步策略）。

**3. Type consistency**  
- `SceneDirectorAnalysis` 在 DTO、Service、ContextBuilder、API 间复用同一模型；请求体字典用 `model_validate` 转换。

---

## 执行交接

**Plan complete and saved to `docs/superpowers/plans/2026-04-05-intelligent-retrieval-context-management-phase1.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — 每个 Task 派生子代理并在 Task 之间做审查，迭代快。

**2. Inline Execution** — 本会话内按 `executing-plans` 批量执行并设检查点。

**Which approach?**

---

**附：弃用说明**  
Cursor 的 `/write-plan` 命令已弃用，将在后续大版本移除。请直接要求助手使用 **superpowers `writing-plans`** 技能撰写实现计划（本文件即按该技能结构编写）。
