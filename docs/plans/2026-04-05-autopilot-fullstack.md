# 百万字全托管写作引擎：全栈实现计划 v2

> **范围**：Task 1～11 为状态机与护城河闭环；**Task 12～18** 为对话整合后的战役三（快照/角色/节奏/检索/UI）。  
> **目标**：把现有骨架代码焊接成可在无人值守深夜安全运行的闭环系统。  
> **原则**：不画新架构，只接线。事务最小化、幂等性、防雪崩、防暴走。

---

## 北极星、原则与四维度体检（整合纪要）

以下节选自产品/艺术/工程/UX 对齐讨论，作为 **战役二（同步状态机）之后** 的延伸目标与验收语境；实现时以本文件后续 **Task 12+** 为开发清单。

### 终极目标

打造具备自纠错能力的 **全自动文学引擎**：可规模化生成，且具备起承转合、逻辑闭环与人类情感共鸣。前端长期形态是 **「世界观测控制台」**，而非传统富文本编辑器。

### 三大原则

| 原则 | 含义 |
|------|------|
| **数据即真理** | 不信任模型上下文记忆；设定、情绪、伏笔必须落库为可查询字段。 |
| **宏观控场，微观放权** | 人/策略只定「死谁、去哪、拿什么」；对话、环境、战术描写交给模型扩展。 |
| **节奏大于逻辑** | 网文优先情绪曲线；避免高潮注水、过渡段狂推主线。 |

### 四维度：隐患与对策摘要

**小说家**

- 配角 NPC 化 → 口头禅 + 待机动作等「毛边」字段，并在 Prompt 中约束使用频率（见 Task 14）。
- 情绪无沉淀 → 角色 `mental_state` + `reason` 锚点，后续章节强制注入（见 Task 13）。

**工程（百万字规模）**

- 向量检索噪声 → 后续可加重：时间衰减权重 + 知识图谱三元组校验（见 Task 17，可选）。
- 限流/错误死循环 → 本计划 Task 3 熔断 + 连续失败挂起；可扩展 Webhook/邮件告警（与运维配置挂钩）。

**产品**

- 全自动失控 → `PAUSED_FOR_REVIEW` 关键节点拦截（本计划 Task 2/4/8 已覆盖流程）。
- 无法回溯 → **C+ 语义化快照**（Task 12）：自动防灾 + 手动分歧点，禁止正文深拷贝。

**UI/UX**

- 终端式正文流 + 右侧思考日志、剧情树、张力/文风/伏笔仪表盘 → 在 Task 10/11 基础上演进（Task 18）。

### 实现优先级结论（与本文 Task 1～11 的关系）

- **先做版本兜底（Task 12）**，再强化单章节拍质量（Task 16 与既有 Task 2/4 对齐）：没有安全网时，自动重写/漂移修复都是高风险操作。
- 既有 v2 中 `_handle_writing` 已具备 `magnify_outline_to_beats` 与节拍级幂等；Task 16 侧重 **4 节拍 JSON 契约、提示词质量与断点续写验收**，而非从零造轮子。

---

## 整体思路

蓝图里有 8 步工作流，各模块已有但 **AutopilotDaemon 里都是 TODO 占位**，链路断开。  
本次工作在原 7 个 Task 基础上，额外补充 **4 个"护城河"Task**，共 **11 个核心 Task**；再将对话中确定的 **战役三与内容质量项** 固化为 **Task 12～18**（可与 1～11 并行排期，但建议 12 在「自动修复类功能」之前落地）。

| # | Task | 关键文件 | 优先级 |
|---|------|---------|--------|
| 1 | Schema 迁移：新增护城河字段 | `schema.sql` + migration | **P0** |
| 2 | AutopilotDaemon 完整实现 | `autopilot_daemon.py` | **P0** |
| 3 | 熔断器 + 指数退避 | `circuit_breaker.py`（新建） | **P0** |
| 4 | 节拍级幂等落库 | `autopilot_daemon.py` | **P0** |
| 5 | BackgroundTaskService 真实执行 | `background_task_service.py` | P1 |
| 6 | start_daemon.py 全依赖注入 | `scripts/start_daemon.py` | P1 |
| 7 | LLMClient 补 stream_generate | `llm_client.py` | P1 |
| 8 | Autopilot API 路由 | `autopilot_routes.py`（新建） | P1 |
| 9 | main.py 注册路由 | `interfaces/main.py` | P1 |
| 10 | 前端自动驾驶监控面板 | `AutopilotPanel.vue`（新建） | P2 |
| 11 | 前端实时生成流（SSE 打字机） | `AutopilotStream.vue`（新建） | P2 |
| 12 | **C+ 语义化快照（Git-like，禁止正文深拷贝）** | `novel_snapshot` 模型 + `snapshot_service.py` + `autopilot_daemon` 钩子 | **P0（战役三）** |
| 13 | **角色心理锚点（枚举 v1）** | `bible_characters` / Character 模型 + `context_intelligence` / `ContextAssemblyService` | P1 |
| 14 | **配角活化：口头禅 + 待机动作** | 同上 + Prompt 频率约束 | P1 |
| 15 | **宏观缓冲章（幕级规划入口）** | `planning_service` / `ContinuousPlanningService` | P1 |
| 16 | **微观节拍放大器强化（4 节拍契约 + 幂等）** | `autopilot_daemon.py`（与 Task 2/4 迭代） | P1 |
| 17 | **检索降噪（可选）：向量时间衰减 + 图谱校验** | 检索管线 + 图谱存储 | P2 |
| 18 | **控制台 UI 演进** | `AutopilotPanel.vue` / 新时间线视图 | P2 |

---

## Task 1：Schema 迁移 — 新增护城河字段

### 文件
- **修改**：`infrastructure/persistence/database/schema.sql`
- **新建**：`infrastructure/persistence/database/migrations/add_autopilot_v2_fields.sql`

### 思路

需要给 `novels` 表新增 5 个字段，支撑成本控制、人工审阅、熔断恢复：

```sql
-- migrations/add_autopilot_v2_fields.sql
ALTER TABLE novels ADD COLUMN max_auto_chapters INTEGER DEFAULT 50;
ALTER TABLE novels ADD COLUMN current_auto_chapters INTEGER DEFAULT 0;
ALTER TABLE novels ADD COLUMN last_chapter_tension INTEGER DEFAULT 0;
ALTER TABLE novels ADD COLUMN consecutive_error_count INTEGER DEFAULT 0;
ALTER TABLE novels ADD COLUMN current_beat_index INTEGER DEFAULT 0;
```

同时 `schema.sql` 的 `CREATE TABLE novels` 里也要加上这 5 列，保证新建数据库时一并创建。

`connection.py` 的 `_ensure_database_exists` 里调用 schema.sql 已经有幂等 `CREATE TABLE IF NOT EXISTS`，但 `ALTER TABLE` 不幂等。处理方法：

```python
def _apply_migrations(conn: sqlite3.Connection) -> None:
    """逐列 PRAGMA 检测，缺则补列（幂等）"""
    cur = conn.execute("PRAGMA table_info(novels)")
    cols = {row[1] for row in cur.fetchall()}
    migrations = {
        "max_auto_chapters":      "ALTER TABLE novels ADD COLUMN max_auto_chapters INTEGER DEFAULT 50",
        "current_auto_chapters":  "ALTER TABLE novels ADD COLUMN current_auto_chapters INTEGER DEFAULT 0",
        "last_chapter_tension":   "ALTER TABLE novels ADD COLUMN last_chapter_tension INTEGER DEFAULT 0",
        "consecutive_error_count":"ALTER TABLE novels ADD COLUMN consecutive_error_count INTEGER DEFAULT 0",
        "current_beat_index":     "ALTER TABLE novels ADD COLUMN current_beat_index INTEGER DEFAULT 0",
    }
    for col, sql in migrations.items():
        if col not in cols:
            conn.execute(sql)
    conn.commit()
```

在 `DatabaseConnection._ensure_database_exists()` 末尾加一行：`_apply_migrations(conn)`

### NovelStage 枚举补充

在 `domain/novel/entities/novel.py` 的 `NovelStage` 里加一个状态：

```python
class NovelStage(str, Enum):
    PLANNING = "planning"
    MACRO_PLANNING = "macro_planning"
    ACT_PLANNING = "act_planning"
    WRITING = "writing"
    AUDITING = "auditing"
    REVIEWING = "reviewing"
    PAUSED_FOR_REVIEW = "paused_for_review"   # ← 新增：幕完成，等待人工确认
    COMPLETED = "completed"
```

`Novel` 实体加 5 个新属性（构造函数 + 属性赋值），`SqliteNovelRepository.save()` 和 `get_by_id()` 等方法同步加上这 5 列的读写。

---

## Task 2：AutopilotDaemon 完整实现

### 文件
- **修改**：`application/engine/services/autopilot_daemon.py`

### 构造函数改造

```python
from application.blueprint.services.continuous_planning_service import ContinuousPlanningService
from infrastructure.persistence.database.story_node_repository import StoryNodeRepository
from infrastructure.persistence.database.sqlite_chapter_repository import SqliteChapterRepository
from application.engine.services.circuit_breaker import CircuitBreaker  # Task 3 新建

class AutopilotDaemon:
    def __init__(
        self,
        novel_repository,
        llm_service,                    # AnthropicProvider
        context_builder,                # ContextBuilder（完整版）
        background_task_service,
        planning_service: ContinuousPlanningService,
        story_node_repo: StoryNodeRepository,
        chapter_repository: SqliteChapterRepository,
        poll_interval: int = 5,
        voice_drift_service=None,
        circuit_breaker: CircuitBreaker = None,   # Task 3
    ):
        ...
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
```

### `run_forever` — 事务最小化原则

**核心原则**：数据库写操作只发生在"读状态"和"更新状态"这两个瞬间，LLM 请求期间绝不持有数据库写锁。

```python
def run_forever(self):
    logger.info("🚀 Autopilot Daemon Started")
    while True:
        # 熔断器检查
        if self.circuit_breaker.is_open():
            wait = self.circuit_breaker.wait_seconds()
            logger.warning(f"熔断器打开，暂停 {wait}s")
            time.sleep(wait)
            continue

        try:
            active_novels = self._get_active_novels()   # 快速只读查询
            for novel in active_novels:
                asyncio.run(self._process_novel(novel))
        except Exception as e:
            logger.error(f"Daemon 顶层异常: {e}", exc_info=True)

        time.sleep(self.poll_interval)
```

### `_process_novel` — 全流程

```python
async def _process_novel(self, novel: Novel):
    try:
        if novel.current_stage == NovelStage.MACRO_PLANNING:
            await self._handle_macro_planning(novel)
        elif novel.current_stage == NovelStage.ACT_PLANNING:
            await self._handle_act_planning(novel)
        elif novel.current_stage == NovelStage.WRITING:
            await self._handle_writing(novel)
        elif novel.current_stage == NovelStage.AUDITING:
            await self._handle_auditing(novel)
        elif novel.current_stage == NovelStage.PAUSED_FOR_REVIEW:
            return   # 人工干预点：不处理，等前端确认

        # ✅ 保存状态（最小事务：只在这里写库）
        self.novel_repository.save(novel)

        # 熔断器：成功则重置错误计数
        self.circuit_breaker.record_success()
        novel.consecutive_error_count = 0

    except Exception as e:
        logger.error(f"[{novel.novel_id}] 处理失败: {e}", exc_info=True)

        # 熔断器：记录失败
        self.circuit_breaker.record_failure()
        novel.consecutive_error_count = (novel.consecutive_error_count or 0) + 1

        if novel.consecutive_error_count >= 3:
            # 单本小说连续 3 次错误 → 挂起（不影响其他小说）
            logger.error(f"[{novel.novel_id}] 连续失败 3 次，挂起等待急救")
            novel.autopilot_status = AutopilotStatus.ERROR
        self.novel_repository.save(novel)
```

### `_handle_macro_planning`

```python
async def _handle_macro_planning(self, novel: Novel):
    target_chapters = novel.target_chapters or 30
    structure_preference = {
        "parts": 1,
        "volumes_per_part": 1,
        "acts_per_volume": 3,
        "chapters_per_act": max(target_chapters // 3, 5)
    }

    result = await self.planning_service.generate_macro_plan(
        novel_id=novel.novel_id.value,
        target_chapters=target_chapters,
        structure_preference=structure_preference
    )

    if result.get("success") and result.get("structure"):
        await self.planning_service.confirm_macro_plan_safe(
            novel_id=novel.novel_id.value,
            structure=result["structure"]
        )
    else:
        await self._create_minimal_structure(novel)

    # ⏸ 幕级大纲已就绪，进入人工审阅点
    # 作者看一眼三幕骨架，确认没偏，再点"继续"
    novel.current_stage = NovelStage.PAUSED_FOR_REVIEW
    logger.info(f"[{novel.novel_id}] 宏观规划完成，进入审阅等待")
```

### `_handle_act_planning`

```python
async def _handle_act_planning(self, novel: Novel):
    novel_id = novel.novel_id.value
    target_act_number = novel.current_act + 1  # 1-indexed

    all_nodes = await self.story_node_repo.get_by_novel(novel_id)
    act_nodes = sorted(
        [n for n in all_nodes if n.node_type.value == "act"],
        key=lambda n: n.number
    )

    target_act = next((n for n in act_nodes if n.number == target_act_number), None)

    if not target_act:
        if act_nodes:
            await self.planning_service.create_next_act_auto(
                novel_id=novel_id,
                current_act_id=act_nodes[-1].id
            )
            all_nodes = await self.story_node_repo.get_by_novel(novel_id)
            act_nodes = sorted(
                [n for n in all_nodes if n.node_type.value == "act"],
                key=lambda n: n.number
            )
            target_act = next((n for n in act_nodes if n.number == target_act_number), None)

        if not target_act:
            logger.error(f"[{novel.novel_id}] 找不到第 {target_act_number} 幕")
            novel.current_stage = NovelStage.WRITING
            return

    # 检查该幕下是否已有章节节点（避免重复规划）
    act_children = self.story_node_repo.get_children_sync(target_act.id)
    confirmed_chapters = [n for n in act_children if n.node_type.value == "chapter"]

    if not confirmed_chapters:
        plan_result = await self.planning_service.plan_act_chapters(
            act_id=target_act.id,
            custom_chapter_count=target_act.suggested_chapter_count or 5
        )
        chapters_data = plan_result.get("chapters", [])
        if chapters_data:
            await self.planning_service.confirm_act_planning(
                act_id=target_act.id,
                chapters=chapters_data
            )

    # ⏸ 幕级章节大纲就绪，再次进入人工审阅点
    novel.current_stage = NovelStage.PAUSED_FOR_REVIEW
    logger.info(f"[{novel.novel_id}] 第 {target_act_number} 幕规划完成，进入审阅等待")
```

### `_handle_writing` — 节拍级幂等落库

这是最核心的部分。关键设计：**每写完一个节拍就立刻 append 到数据库**，而不是最后一次性落库。

```python
async def _handle_writing(self, novel: Novel):
    # 1. 成本控制：达到最大章节数则自动停止
    max_chapters = novel.max_auto_chapters or 50
    if (novel.current_auto_chapters or 0) >= max_chapters:
        logger.info(f"[{novel.novel_id}] 已达成本控制上限 {max_chapters} 章，自动停止")
        novel.autopilot_status = AutopilotStatus.STOPPED
        novel.current_stage = NovelStage.PAUSED_FOR_REVIEW
        return

    # 2. 缓冲章判断（高潮后插入日常章）
    needs_buffer = (novel.last_chapter_tension or 0) >= 8
    if needs_buffer:
        logger.info(f"[{novel.novel_id}] 上章张力≥8，强制生成缓冲章")

    # 3. 找下一个未写章节
    next_chapter_node = await self._find_next_unwritten_chapter_async(novel)
    if not next_chapter_node:
        if await self._current_act_fully_written(novel):
            novel.current_act += 1
            novel.current_chapter_in_act = 0
            novel.current_stage = NovelStage.ACT_PLANNING
        else:
            novel.current_stage = NovelStage.AUDITING
        return

    chapter_num = next_chapter_node.number
    outline = next_chapter_node.outline or next_chapter_node.description or next_chapter_node.title

    if needs_buffer:
        outline = f"【缓冲章：日常过渡】{outline}。主角战后休整，与配角闲聊，展示收获，节奏轻松。"

    logger.info(f"[{novel.novel_id}] 开始写第 {chapter_num} 章：{outline[:60]}...")

    # 4. 组装上下文（不持有数据库锁，纯读操作）
    context = ""
    if self.context_builder:
        try:
            context = self.context_builder.build_context(
                novel_id=novel.novel_id.value,
                chapter_number=chapter_num,
                outline=outline,
                max_tokens=20000
            )
        except Exception as e:
            logger.warning(f"ContextBuilder 失败，降级：{e}")

    # 5. 节拍放大
    beats = []
    if self.context_builder:
        beats = self.context_builder.magnify_outline_to_beats(outline, target_chapter_words=2500)

    # 6. 🔑 节拍级幂等生成 + 增量落库
    start_beat = novel.current_beat_index or 0  # 断点续写：从上次中断的节拍继续

    chapter_content = await self._get_existing_chapter_content(novel, chapter_num) or ""

    if beats:
        for i, beat in enumerate(beats):
            if i < start_beat:
                continue  # 跳过已生成的节拍

            beat_prompt = self.context_builder.build_beat_prompt(beat, i, len(beats))
            beat_content = await self._stream_one_beat(outline, context, beat_prompt, beat)

            chapter_content += ("\n\n" if chapter_content else "") + beat_content

            # ✅ 每节拍完成后立刻写库（最小事务）
            await self._upsert_chapter_content(novel, next_chapter_node, chapter_content, status="draft")

            # 更新断点索引（写库后更新，保证原子性）
            novel.current_beat_index = i + 1
            self.novel_repository.save(novel)

            logger.info(f"  节拍 {i+1}/{len(beats)} 落库：{len(beat_content)} 字")
    else:
        # 降级：无节拍，一次生成
        beat_content = await self._stream_one_beat(outline, context, None, None)
        chapter_content += beat_content
        await self._upsert_chapter_content(novel, next_chapter_node, chapter_content, status="draft")

    # 7. 章节完成，标记 completed
    await self._upsert_chapter_content(novel, next_chapter_node, chapter_content, status="completed")

    # 8. 更新计数器，重置节拍索引
    novel.current_auto_chapters = (novel.current_auto_chapters or 0) + 1
    novel.current_chapter_in_act += 1
    novel.current_beat_index = 0
    novel.current_stage = NovelStage.AUDITING

    logger.info(f"[{novel.novel_id}] 第 {chapter_num} 章完成：{len(chapter_content)} 字")
```

**辅助方法 `_upsert_chapter_content`（最小事务）：**

```python
async def _upsert_chapter_content(self, novel, chapter_node, content: str, status: str):
    """最小事务：只更新章节内容，不涉及其他表"""
    from domain.novel.entities.chapter import Chapter, ChapterStatus
    from domain.novel.value_objects.novel_id import NovelId

    existing = self.chapter_repository.get_by_novel_and_number(
        NovelId(novel.novel_id.value), chapter_node.number
    )
    if existing:
        existing.update_content(content)
        existing.status = ChapterStatus(status)
        self.chapter_repository.save(existing)
    else:
        chapter = Chapter(
            id=chapter_node.id,
            novel_id=NovelId(novel.novel_id.value),
            number=chapter_node.number,
            title=chapter_node.title,
            content=content,
            outline=chapter_node.outline or "",
            status=ChapterStatus(status)
        )
        self.chapter_repository.save(chapter)
```

**辅助方法 `_stream_one_beat`：**

```python
async def _stream_one_beat(self, outline, context, beat_prompt, beat) -> str:
    """流式生成单个节拍（或整章），返回生成内容"""
    from domain.ai.value_objects.prompt import Prompt
    from domain.ai.services.llm_service import GenerationConfig

    system = """你是一位资深网文作家，擅长写爽文。
写作要求：
1. 严格按节拍字数和聚焦点写作
2. 必须有对话和人物互动，保持人物性格一致
3. 增加感官细节：视觉、听觉、触觉、情绪
4. 节奏控制：不要一章推进太多剧情
5. 不要写章节标题"""

    user_parts = []
    if context:
        user_parts.append(context)
    user_parts.append(f"\n【本章大纲】\n{outline}")
    if beat_prompt:
        user_parts.append(f"\n{beat_prompt}")
    user_parts.append("\n\n开始撰写：")

    max_tokens = int(beat.target_words * 1.5) if beat else 3000

    prompt = Prompt(system=system, user="\n".join(user_parts))
    config = GenerationConfig(max_tokens=max_tokens, temperature=0.85)

    content = ""
    async for chunk in self.llm_service.stream_generate(prompt, config):
        content += chunk

    return content
```

### `_handle_auditing` — 含张力打分

```python
async def _handle_auditing(self, novel: Novel):
    chapter_num = novel.current_act * 10 + novel.current_chapter_in_act  # 刚写完的章节

    from domain.novel.value_objects.novel_id import NovelId
    from domain.novel.value_objects.chapter_id import ChapterId

    chapter = self.chapter_repository.get_by_novel_and_number(
        NovelId(novel.novel_id.value), chapter_num
    )
    if not chapter:
        novel.current_stage = NovelStage.WRITING
        return

    content = chapter.content or ""
    chapter_id = ChapterId(chapter.id)

    # 1. 提交后台异步任务（不阻塞）
    for task_type in [TaskType.VOICE_ANALYSIS, TaskType.GRAPH_UPDATE, TaskType.FORESHADOW_EXTRACT]:
        self.background_task_service.submit_task(
            task_type=task_type,
            novel_id=novel.novel_id,
            chapter_id=chapter_id,
            payload={"content": content, "chapter_number": chapter_num}
        )

    # 2. 张力打分（轻量 LLM 调用，~200 token）
    tension = await self._score_tension(content)
    novel.last_chapter_tension = tension
    logger.info(f"[{novel.novel_id}] 章节 {chapter_num} 张力值：{tension}/10")

    # 3. 文风漂移检测（同步）
    drift_too_high = False
    if self.voice_drift_service and content:
        try:
            result = self.voice_drift_service.score_chapter(
                novel_id=novel.novel_id.value,
                chapter_number=chapter_num,
                content=content
            )
            similarity = result.get("similarity_score")
            drift_alert = result.get("drift_alert", False)
            logger.info(f"[{novel.novel_id}] 文风相似度：{similarity}，告警：{drift_alert}")
            drift_too_high = drift_alert
        except Exception as e:
            logger.warning(f"文风检测失败（跳过）：{e}")

    # 4. 文风漂移 → 删章重写
    if drift_too_high:
        logger.warning(f"[{novel.novel_id}] 章节 {chapter_num} 文风漂移，删章重写")
        self.chapter_repository.delete(chapter_id)
        novel.current_chapter_in_act -= 1
        novel.current_auto_chapters = max(0, (novel.current_auto_chapters or 1) - 1)
        novel.current_beat_index = 0
        novel.current_stage = NovelStage.WRITING
        return

    novel.current_stage = NovelStage.WRITING

    # 5. 全书完成检测
    chapters = self.chapter_repository.list_by_novel(NovelId(novel.novel_id.value))
    completed = [c for c in chapters if c.status.value == "completed"]
    if len(completed) >= novel.target_chapters:
        logger.info(f"[{novel.novel_id}] 🎉 全书完成！共 {len(completed)} 章")
        novel.autopilot_status = AutopilotStatus.STOPPED
        novel.current_stage = NovelStage.COMPLETED
```

**辅助方法 `_score_tension`（轻量 LLM 调用）：**

```python
async def _score_tension(self, content: str) -> int:
    """给章节打张力分（1-10），用于判断是否插入缓冲章"""
    if not content or len(content) < 200:
        return 5  # 默认中等张力

    snippet = content[:500]  # 只取前 500 字，节省 token

    try:
        from domain.ai.value_objects.prompt import Prompt
        from domain.ai.services.llm_service import GenerationConfig

        prompt = Prompt(
            system="你是小说节奏分析师，只输出一个 1-10 的整数，不要解释。",
            user=f"""根据以下章节开头，打分当前剧情的张力值（1=日常/轻松，10=生死对决/高潮）：

{snippet}

张力分（只输出数字）："""
        )
        config = GenerationConfig(max_tokens=5, temperature=0.1)
        result = await self.llm_service.generate(prompt, config)
        raw = result.content.strip() if hasattr(result, "content") else str(result).strip()
        score = int(''.join(filter(str.isdigit, raw[:3])))
        return max(1, min(10, score))
    except Exception:
        return 5  # 解析失败，返回默认值
```

---

## Task 3：熔断器（Circuit Breaker）

### 文件
- **新建**：`application/engine/services/circuit_breaker.py`

### 思路

防止 API 宕机时 Daemon 把所有小说都变成 ERROR 状态。三种状态：
- **CLOSED（正常）**：放行所有请求
- **OPEN（断开）**：拒绝请求，等待 `reset_timeout` 秒后进入 HALF_OPEN
- **HALF_OPEN（试探）**：放行一次请求，成功则 CLOSED，失败则重回 OPEN

```python
"""熔断器：防止 API 雪崩导致所有小说同时进入 ERROR"""
import time
import logging
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class BreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,    # 连续失败 5 次后断开
        reset_timeout: int = 120,       # 断开后 120 秒尝试恢复
        half_open_max_calls: int = 1,  # 试探阶段最多放行 1 次
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = BreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._lock = Lock()

    def is_open(self) -> bool:
        with self._lock:
            if self._state == BreakerState.OPEN:
                if time.time() - self._last_failure_time > self.reset_timeout:
                    logger.info("[CircuitBreaker] → HALF_OPEN，开始试探")
                    self._state = BreakerState.HALF_OPEN
                    self._success_count = 0
                    return False  # 放行试探
                return True  # 仍在断开期
            return False

    def wait_seconds(self) -> float:
        """还需等待多少秒"""
        elapsed = time.time() - self._last_failure_time
        return max(0.0, self.reset_timeout - elapsed)

    def record_success(self):
        with self._lock:
            if self._state == BreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    logger.info("[CircuitBreaker] → CLOSED，恢复正常")
                    self._state = BreakerState.CLOSED
                    self._failure_count = 0
            elif self._state == BreakerState.CLOSED:
                self._failure_count = 0  # 成功重置计数

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == BreakerState.HALF_OPEN:
                logger.warning("[CircuitBreaker] 试探失败 → OPEN")
                self._state = BreakerState.OPEN
            elif self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"[CircuitBreaker] 连续失败 {self._failure_count} 次 → OPEN，"
                    f"暂停 {self.reset_timeout}s"
                )
                self._state = BreakerState.OPEN

    @property
    def state(self) -> str:
        return self._state.value
```

---

## Task 4：节拍级幂等落库

节拍幂等逻辑已在 Task 2 的 `_handle_writing` 里详细描述。

关键设计要点总结：

| 问题 | 解法 |
|------|------|
| 写到第 3 节拍时崩溃 | `novel.current_beat_index` 记录已完成节拍号，重启时跳过 |
| 重启后章节内容丢失 | 每节拍完成立刻 `_upsert_chapter_content(status="draft")` |
| 章节最终标记混淆 | 四个节拍全部完成后再改 `status="completed"` |
| 节拍索引和章节内容不同步 | 先写章节内容，再更新 `current_beat_index` 并 `novel_repository.save()` |

---

## Task 5：BackgroundTaskService 真实执行

### 文件
- **修改**：`application/engine/services/background_task_service.py`

### 架构改造：加后台工作线程

```python
import threading, queue

class BackgroundTaskService:
    def __init__(
        self,
        voice_drift_service=None,
        llm_service=None,
        foreshadowing_repo=None,
        triple_repository=None,
    ):
        self.voice_drift_service = voice_drift_service
        self.llm_service = llm_service
        self.foreshadowing_repo = foreshadowing_repo
        self.triple_repository = triple_repository

        self._queue = queue.Queue(maxsize=200)  # 防队列无限增长
        self._worker = threading.Thread(target=self._worker_loop, daemon=True, name="bg-task-worker")
        self._worker.start()

    def submit_task(self, task_type, novel_id, chapter_id, payload):
        try:
            task = BackgroundTask(
                task_id=str(uuid.uuid4()),
                task_type=task_type,
                novel_id=novel_id,
                chapter_id=chapter_id,
                payload=payload
            )
            self._queue.put_nowait(task)
        except queue.Full:
            logger.warning("后台任务队列已满，丢弃任务")

    def _worker_loop(self):
        while True:
            try:
                task = self._queue.get(timeout=2)
                self._execute_with_retry(task)
                self._queue.task_done()
            except queue.Empty:
                continue

    def _execute_with_retry(self, task, max_retries=2):
        for attempt in range(max_retries + 1):
            try:
                self._execute_task(task)
                return
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"[BG] 任务最终失败 {task.task_type}：{e}")
                else:
                    wait = 2 ** attempt  # 指数退避：1s, 2s
                    time.sleep(wait)
```

### VOICE_ANALYSIS 处理器

```python
def _handle_voice_analysis(self, task):
    if not self.voice_drift_service:
        return
    content = task.payload.get("content", "")
    chapter_number = task.payload.get("chapter_number", 0)
    if not content:
        return
    self.voice_drift_service.score_chapter(
        novel_id=task.novel_id.value,
        chapter_number=chapter_number,
        content=content
    )
    logger.info(f"[BG] 文风分析完成：第 {chapter_number} 章")
```

### GRAPH_UPDATE 处理器

用 LLM 提取三元组写入 `triples` 表：

```python
def _handle_graph_update(self, task):
    if not self.llm_service or not self.triple_repository:
        return
    content = task.payload.get("content", "")[:2000]
    chapter_number = task.payload.get("chapter_number", 0)
    if not content:
        return

    import asyncio, uuid
    from domain.ai.value_objects.prompt import Prompt
    from domain.ai.services.llm_service import GenerationConfig

    prompt = Prompt(
        system="你是信息抽取专家，只输出指定格式内容，不要解释。",
        user=f"""从以下小说章节提取人物关系三元组。
格式：主体|关系|客体（每行一条，最多8条）
只提取文中明确描述的动作或关系。

章节内容：
{content}

三元组："""
    )
    config = GenerationConfig(max_tokens=400, temperature=0.2)
    result = asyncio.run(self.llm_service.generate(prompt, config))
    raw = result.content if hasattr(result, "content") else str(result)

    for line in raw.strip().split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 3 and all(parts):
            subject, predicate, obj = parts
            try:
                self.triple_repository.save({
                    "id": str(uuid.uuid4()),
                    "novel_id": task.novel_id.value,
                    "subject": subject,
                    "predicate": predicate,
                    "object": obj,
                    "chapter_number": chapter_number,
                    "source_type": "autopilot_extract",
                    "confidence": 0.7,
                })
            except Exception:
                pass  # 重复三元组忽略
    logger.info(f"[BG] 图谱更新完成：第 {chapter_number} 章")
```

### FORESHADOW_EXTRACT 处理器

```python
def _handle_foreshadow_extract(self, task):
    if not self.llm_service or not self.foreshadowing_repo:
        return
    content = task.payload.get("content", "")[:2000]
    chapter_number = task.payload.get("chapter_number", 0)
    if not content:
        return

    import asyncio
    from domain.ai.value_objects.prompt import Prompt
    from domain.ai.services.llm_service import GenerationConfig

    prompt = Prompt(
        system="你是小说分析专家，专门识别叙事伏笔。只输出格式内容，不要解释。",
        user=f"""从以下章节提取潜在伏笔（悬而未决的情节/暗示/物品/对话）。
格式：伏笔内容|触发关键词（每行一条，最多4条）

章节：
{content}

伏笔："""
    )
    config = GenerationConfig(max_tokens=300, temperature=0.3)
    result = asyncio.run(self.llm_service.generate(prompt, config))
    raw = result.content if hasattr(result, "content") else str(result)

    for line in raw.strip().split("\n"):
        parts = line.strip().split("|")
        if parts and parts[0].strip():
            foreshadow_content = parts[0].strip()
            trigger = parts[1].strip() if len(parts) > 1 else ""
            try:
                self.foreshadowing_repo.create(
                    novel_id=task.novel_id.value,
                    content=foreshadow_content,
                    chapter_number=chapter_number,
                    trigger_keywords=[trigger] if trigger else [],
                    status="pending"
                )
            except Exception:
                pass
    logger.info(f"[BG] 伏笔提取完成：第 {chapter_number} 章")
```

---

## Task 6：start_daemon.py 全依赖注入

### 文件
- **修改**：`scripts/start_daemon.py`

### 完整代码

```python
"""启动自动驾驶守护进程（v2，全依赖注入 + 护城河）"""
import sys, logging, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.paths import get_db_path, DATA_DIR
from infrastructure.persistence.database.connection import get_database
from infrastructure.persistence.database.sqlite_novel_repository import SqliteNovelRepository
from infrastructure.persistence.database.sqlite_chapter_repository import SqliteChapterRepository
from infrastructure.persistence.database.story_node_repository import StoryNodeRepository
from infrastructure.persistence.database.chapter_element_repository import ChapterElementRepository
from infrastructure.persistence.database.sqlite_foreshadowing_repository import SqliteForeshadowingRepository

from application.engine.services.autopilot_daemon import AutopilotDaemon
from application.engine.services.background_task_service import BackgroundTaskService
from application.engine.services.circuit_breaker import CircuitBreaker
from application.blueprint.services.continuous_planning_service import ContinuousPlanningService

# 复用 API 层的工厂函数，保证与 FastAPI 层使用同一套配置
from interfaces.api.dependencies import (
    get_llm_service, get_context_builder, get_bible_service,
    get_foreshadowing_repository, get_novel_repository, get_chapter_repository,
)

(DATA_DIR / "logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(str(DATA_DIR / "logs" / "autopilot_daemon.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def build_daemon() -> AutopilotDaemon:
    db_path = get_db_path()
    db = get_database(db_path)

    novel_repo = SqliteNovelRepository(db)
    chapter_repo = SqliteChapterRepository(db)
    story_node_repo = StoryNodeRepository(db_path)
    chapter_element_repo = ChapterElementRepository(db_path)
    foreshadow_repo = SqliteForeshadowingRepository(db)

    llm_service = get_llm_service()
    context_builder = get_context_builder()

    planning_service = ContinuousPlanningService(
        story_node_repo=story_node_repo,
        chapter_element_repo=chapter_element_repo,
        llm_service=llm_service,
        bible_service=get_bible_service(),
        chapter_repository=chapter_repo,
    )

    # VoiceDriftService（可选，失败则跳过）
    voice_drift_service = None
    try:
        from infrastructure.persistence.database.sqlite_voice_vault_repository import SqliteVoiceVaultRepository
        from infrastructure.persistence.database.sqlite_voice_fingerprint_repository import SQLiteVoiceFingerprintRepository
        from application.analyst.services.voice_drift_service import VoiceDriftService
        score_repo = SqliteVoiceVaultRepository(db)
        fingerprint_repo = SQLiteVoiceFingerprintRepository(db)
        voice_drift_service = VoiceDriftService(score_repo, fingerprint_repo)
        logger.info("VoiceDriftService 已启用")
    except Exception as e:
        logger.warning(f"VoiceDriftService 初始化失败，文风检测已禁用：{e}")

    # TripleRepository（可选）
    triple_repo = None
    try:
        from infrastructure.persistence.database.triple_repository import TripleRepository
        triple_repo = TripleRepository(db_path)
        logger.info("TripleRepository 已启用")
    except Exception as e:
        logger.warning(f"TripleRepository 不可用，图谱提取已禁用：{e}")

    bg_service = BackgroundTaskService(
        voice_drift_service=voice_drift_service,
        llm_service=llm_service,
        foreshadowing_repo=foreshadow_repo,
        triple_repository=triple_repo,
    )

    circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        reset_timeout=120,
    )

    return AutopilotDaemon(
        novel_repository=novel_repo,
        llm_service=llm_service,
        context_builder=context_builder,
        background_task_service=bg_service,
        planning_service=planning_service,
        story_node_repo=story_node_repo,
        chapter_repository=chapter_repo,
        poll_interval=5,
        voice_drift_service=voice_drift_service,
        circuit_breaker=circuit_breaker,
    )


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🚀 Autopilot Daemon v2 Starting")
    logger.info("=" * 80)

    daemon = build_daemon()
    try:
        daemon.run_forever()
    except KeyboardInterrupt:
        logger.info("守护进程已停止（KeyboardInterrupt）")
    except Exception as e:
        logger.error(f"守护进程异常退出：{e}", exc_info=True)
        raise
```

---

## Task 7：LLMClient 补 stream_generate

### 文件
- **修改**：`infrastructure/ai/llm_client.py`

```python
from typing import AsyncIterator

async def stream_generate(
    self,
    prompt,          # Prompt 对象或 str
    config=None,
    **kwargs
) -> AsyncIterator[str]:
    """流式生成，代理到底层 provider"""
    from domain.ai.value_objects.prompt import Prompt as PromptVO
    from domain.ai.services.llm_service import GenerationConfig

    if isinstance(prompt, str):
        prompt_obj = PromptVO(
            system="你是一个专业的小说创作助手。",
            user=prompt
        )
    else:
        prompt_obj = prompt

    if config is None:
        config = GenerationConfig(
            max_tokens=kwargs.get("max_tokens", 3000),
            temperature=kwargs.get("temperature", 0.85)
        )

    async for chunk in self.provider.stream_generate(prompt_obj, config):
        yield chunk
```

---

## Task 8：Autopilot API 路由

### 文件
- **新建**：`interfaces/api/v1/engine/autopilot_routes.py`

### 端点完整实现

```python
"""自动驾驶控制 API（v2：含审阅确认 + SSE 生成流）"""
import asyncio, json, logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from domain.novel.entities.novel import AutopilotStatus, NovelStage
from domain.novel.value_objects.novel_id import NovelId
from interfaces.api.dependencies import get_novel_repository, get_chapter_repository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/autopilot", tags=["autopilot"])


class StartRequest(BaseModel):
    max_auto_chapters: Optional[int] = 50  # 本次托管最大章节数


@router.post("/{novel_id}/start")
async def start_autopilot(novel_id: str, body: StartRequest = StartRequest()):
    """启动自动驾驶"""
    repo = get_novel_repository()
    novel = repo.get_by_id(NovelId(novel_id))
    if not novel:
        raise HTTPException(404, "小说不存在")

    novel.autopilot_status = AutopilotStatus.RUNNING
    novel.max_auto_chapters = body.max_auto_chapters
    novel.current_auto_chapters = novel.current_auto_chapters or 0
    novel.consecutive_error_count = 0

    # 如果是全新小说，从宏观规划开始
    fresh_stages = {NovelStage.PLANNING, NovelStage.MACRO_PLANNING}
    if novel.current_stage in fresh_stages:
        novel.current_stage = NovelStage.MACRO_PLANNING

    # 如果之前处于审阅等待，恢复为写作
    if novel.current_stage == NovelStage.PAUSED_FOR_REVIEW:
        novel.current_stage = NovelStage.ACT_PLANNING

    repo.save(novel)
    return {
        "success": True,
        "message": f"自动驾驶已启动，目标 {body.max_auto_chapters} 章",
        "autopilot_status": novel.autopilot_status.value,
        "current_stage": novel.current_stage.value,
    }


@router.post("/{novel_id}/stop")
async def stop_autopilot(novel_id: str):
    """停止自动驾驶"""
    repo = get_novel_repository()
    novel = repo.get_by_id(NovelId(novel_id))
    if not novel:
        raise HTTPException(404, "小说不存在")
    novel.autopilot_status = AutopilotStatus.STOPPED
    repo.save(novel)
    return {"success": True, "message": "自动驾驶已停止"}


@router.post("/{novel_id}/resume")
async def resume_from_review(novel_id: str):
    """从人工审阅点恢复（PAUSED_FOR_REVIEW → RUNNING）"""
    repo = get_novel_repository()
    novel = repo.get_by_id(NovelId(novel_id))
    if not novel:
        raise HTTPException(404, "小说不存在")
    if novel.current_stage != NovelStage.PAUSED_FOR_REVIEW:
        raise HTTPException(400, f"当前不在审阅等待状态（当前：{novel.current_stage.value}）")

    novel.autopilot_status = AutopilotStatus.RUNNING
    novel.current_stage = NovelStage.ACT_PLANNING
    repo.save(novel)
    return {"success": True, "message": "已恢复，开始规划下一幕章节"}


@router.get("/{novel_id}/status")
async def get_autopilot_status(novel_id: str):
    """获取完整运行状态"""
    novel_repo = get_novel_repository()
    chapter_repo = get_chapter_repository()

    novel = novel_repo.get_by_id(NovelId(novel_id))
    if not novel:
        raise HTTPException(404, "小说不存在")

    chapters = chapter_repo.list_by_novel(NovelId(novel_id))
    total_words = sum(c.word_count.value for c in chapters if c.word_count)
    completed = [c for c in chapters if c.status.value == "completed"]

    return {
        "autopilot_status": novel.autopilot_status.value,
        "current_stage": novel.current_stage.value,
        "current_act": novel.current_act,
        "current_chapter_in_act": novel.current_chapter_in_act,
        "current_beat_index": getattr(novel, "current_beat_index", 0),
        "current_auto_chapters": getattr(novel, "current_auto_chapters", 0),
        "max_auto_chapters": getattr(novel, "max_auto_chapters", 50),
        "last_chapter_tension": getattr(novel, "last_chapter_tension", 0),
        "consecutive_error_count": getattr(novel, "consecutive_error_count", 0),
        "total_words": total_words,
        "completed_chapters": len(completed),
        "target_chapters": novel.target_chapters,
        "progress_pct": round(len(completed) / novel.target_chapters * 100, 1) if novel.target_chapters else 0,
        "needs_review": novel.current_stage.value == "paused_for_review",
    }


@router.get("/{novel_id}/events")
async def autopilot_events(novel_id: str):
    """SSE 实时状态推送（每 3 秒）"""
    novel_repo = get_novel_repository()
    chapter_repo = get_chapter_repository()

    async def event_generator():
        while True:
            try:
                novel = novel_repo.get_by_id(NovelId(novel_id))
                if not novel:
                    break
                chapters = chapter_repo.list_by_novel(NovelId(novel_id))
                total_words = sum(c.word_count.value for c in chapters if c.word_count)
                completed = [c for c in chapters if c.status.value == "completed"]

                data = {
                    "autopilot_status": novel.autopilot_status.value,
                    "current_stage": novel.current_stage.value,
                    "current_act": novel.current_act,
                    "current_beat_index": getattr(novel, "current_beat_index", 0),
                    "completed_chapters": len(completed),
                    "total_words": total_words,
                    "target_chapters": novel.target_chapters,
                    "needs_review": novel.current_stage.value == "paused_for_review",
                    "consecutive_error_count": getattr(novel, "consecutive_error_count", 0),
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                terminal_states = {"stopped", "error", "completed"}
                if novel.autopilot_status.value in terminal_states and \
                   novel.current_stage.value != "paused_for_review":
                    break

                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"SSE error: {e}")
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

---

## Task 9：main.py 注册路由

### 文件
- **修改**：`interfaces/main.py`

```python
from interfaces.api.v1.engine import generation, context_intelligence, autopilot_routes

# Engine module routes
app.include_router(generation.router, prefix="/api/v1")
app.include_router(context_intelligence.router, prefix="/api/v1")
app.include_router(autopilot_routes.router, prefix="/api/v1")   # ← 新增
```

---

## Task 10：前端自动驾驶监控面板

### 文件
- **新建**：`frontend/src/components/autopilot/AutopilotPanel.vue`

### 设计要点

- 状态灯：绿脉冲（运行中）/ 橙闪（审阅等待）/ 红（出错）/ 灰（停止）
- 橙色「审阅等待」时，显示「查看大纲 → 确认继续」按钮，调用 `/resume`
- 进度条：`completed_chapters / target_chapters`
- 张力指示器：`last_chapter_tension` 对应到文字描述
- 熔断警告：`consecutive_error_count >= 3` 时显示红色警告提示
- SSE 自动重连（5 秒）

```vue
<template>
  <div class="autopilot-panel">
    <!-- 状态头 -->
    <div class="ap-header">
      <span class="ap-dot" :class="dotClass"></span>
      <span class="ap-title">全托管驾驶</span>
      <span class="ap-stage-tag" :class="stageTagClass">{{ stageLabel }}</span>
    </div>

    <!-- 进度条 -->
    <n-progress
      type="line"
      :percentage="progressPct"
      :color="progressColor"
      indicator-placement="inside"
      :height="14"
      style="margin: 4px 0"
    />

    <!-- 数据格 -->
    <div class="ap-grid">
      <div class="ap-cell">
        <div class="label">已写章节</div>
        <div class="value">{{ status?.completed_chapters || 0 }} / {{ status?.target_chapters || '-' }}</div>
      </div>
      <div class="ap-cell">
        <div class="label">总字数</div>
        <div class="value">{{ formatWords(status?.total_words) }}</div>
      </div>
      <div class="ap-cell">
        <div class="label">当前幕 / 节拍</div>
        <div class="value">
          第 {{ (status?.current_act || 0) + 1 }} 幕
          <span v-if="isWriting">· {{ beatLabel }}</span>
        </div>
      </div>
      <div class="ap-cell">
        <div class="label">上章张力</div>
        <div class="value" :style="{ color: tensionColor }">{{ tensionLabel }}</div>
      </div>
    </div>

    <!-- 熔断警告 -->
    <n-alert v-if="hasErrors" type="error" :show-icon="true" style="margin: 4px 0; font-size: 12px">
      连续失败 {{ status.consecutive_error_count }} 次，守护进程可能已熔断
    </n-alert>

    <!-- 审阅等待提示 -->
    <n-alert v-if="needsReview" type="warning" style="margin: 4px 0; font-size: 12px">
      ✍️ 大纲已生成，请确认后继续写作
    </n-alert>

    <!-- 操作按钮 -->
    <n-space justify="end" size="small">
      <n-button v-if="needsReview" type="warning" size="small" :loading="toggling" @click="resume">
        确认大纲，继续写作
      </n-button>
      <n-button v-if="!isRunning && !needsReview" type="primary" size="small" :loading="toggling" @click="openStartModal">
        🚀 启动全托管
      </n-button>
      <n-button v-if="isRunning" type="error" ghost size="small" :loading="toggling" @click="stop">
        ⏹ 停止
      </n-button>
    </n-space>

    <!-- 启动配置弹窗 -->
    <n-modal v-model:show="showStartModal" title="自动驾驶配置" preset="dialog" positive-text="启动" @positive-click="start">
      <n-form>
        <n-form-item label="本次最多生成章节数（成本控制）">
          <n-input-number v-model:value="startConfig.max_auto_chapters" :min="1" :max="200" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMessage } from 'naive-ui'

const props = defineProps({ novelId: String })
const emit = defineEmits(['status-change'])
const message = useMessage()

const status = ref(null)
const toggling = ref(false)
const showStartModal = ref(false)
const startConfig = ref({ max_auto_chapters: 50 })
let eventSource = null

// 计算属性
const isRunning  = computed(() => status.value?.autopilot_status === 'running')
const needsReview = computed(() => status.value?.needs_review === true)
const isWriting  = computed(() => status.value?.current_stage === 'writing')
const hasErrors  = computed(() => (status.value?.consecutive_error_count || 0) >= 3)
const progressPct = computed(() => status.value?.progress_pct || 0)
const progressColor = computed(() => {
  if (hasErrors.value) return '#d03050'
  if (needsReview.value) return '#f0a020'
  return '#18a058'
})

const dotClass = computed(() => ({
  'dot-running': isRunning.value && !needsReview.value,
  'dot-review':  needsReview.value,
  'dot-error':   status.value?.autopilot_status === 'error',
  'dot-stopped': !isRunning.value && !needsReview.value,
}))

const stageLabel = computed(() => {
  const m = {
    macro_planning: '宏观规划', act_planning: '幕级规划',
    writing: '撰写中', auditing: '审计中',
    paused_for_review: '待审阅', completed: '已完成',
  }
  return m[status.value?.current_stage] || '待机'
})

const stageTagClass = computed(() => ({
  'tag-active':  isRunning.value && !needsReview.value,
  'tag-review':  needsReview.value,
  'tag-idle':    !isRunning.value && !needsReview.value,
}))

const beatLabel = computed(() => {
  const b = status.value?.current_beat_index || 0
  return b === 0 ? '准备' : `节拍 ${b}`
})

const tensionLabel = computed(() => {
  const t = status.value?.last_chapter_tension || 0
  if (t >= 8) return `🔥 高潮 (${t}/10)`
  if (t >= 5) return `⚡ 冲突 (${t}/10)`
  return `🌊 平缓 (${t}/10)`
})

const tensionColor = computed(() => {
  const t = status.value?.last_chapter_tension || 0
  return t >= 8 ? '#d03050' : t >= 5 ? '#f0a020' : '#18a058'
})

// 格式化
function formatWords(n) {
  if (!n) return '0'
  return n >= 10000 ? `${(n / 10000).toFixed(1)}万` : String(n)
}

// API 调用
const base = () => `/api/v1/autopilot/${props.novelId}`

async function fetchStatus() {
  const res = await fetch(`${base()}/status`)
  if (res.ok) {
    status.value = await res.json()
    emit('status-change', status.value)
  }
}

function connectSSE() {
  if (eventSource) eventSource.close()
  eventSource = new EventSource(`${base()}/events`)
  eventSource.onmessage = (e) => {
    status.value = JSON.parse(e.data)
    emit('status-change', status.value)
  }
  eventSource.onerror = () => {
    eventSource.close()
    setTimeout(connectSSE, 5000)
  }
}

function openStartModal() { showStartModal.value = true }

async function start() {
  toggling.value = true
  const res = await fetch(`${base()}/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(startConfig.value)
  })
  if (res.ok) message.success('自动驾驶已启动')
  else message.error('启动失败')
  await fetchStatus()
  toggling.value = false
}

async function stop() {
  toggling.value = true
  await fetch(`${base()}/stop`, { method: 'POST' })
  message.info('已停止')
  await fetchStatus()
  toggling.value = false
}

async function resume() {
  toggling.value = true
  const res = await fetch(`${base()}/resume`, { method: 'POST' })
  if (res.ok) message.success('已确认大纲，开始写作')
  else { const e = await res.json(); message.error(e.detail || '恢复失败') }
  await fetchStatus()
  toggling.value = false
}

onMounted(() => { fetchStatus(); connectSSE() })
onUnmounted(() => eventSource?.close())
</script>

<style scoped>
.autopilot-panel {
  background: #18181c;
  border: 1px solid #2d2d30;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 280px;
}
.ap-header { display: flex; align-items: center; gap: 8px; }
.ap-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.dot-running { background: #18a058; animation: pulse 1.4s ease-in-out infinite; }
.dot-review  { background: #f0a020; animation: pulse 0.8s ease-in-out infinite; }
.dot-error   { background: #d03050; }
.dot-stopped { background: #555; }
@keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:.4; transform:scale(.85); } }

.ap-title { font-weight: 600; color: #eee; font-size: 14px; }
.ap-stage-tag {
  margin-left: auto; font-size: 11px; padding: 2px 8px;
  border-radius: 10px; font-weight: 500;
}
.tag-active  { background: rgba(24,160,88,.2); color: #18a058; }
.tag-review  { background: rgba(240,160,32,.2); color: #f0a020; }
.tag-idle    { background: rgba(100,100,100,.2); color: #888; }

.ap-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 12px; }
.ap-cell { text-align: center; }
.ap-cell .label { font-size: 10px; color: #666; margin-bottom: 2px; }
.ap-cell .value { font-size: 14px; font-weight: 600; color: #ddd; }
</style>
```

---

## Task 11：前端实时生成流（SSE 打字机）

### 文件
- **新建**：`frontend/src/components/autopilot/AutopilotStream.vue`

### 思路

当 `current_stage === 'writing'` 时，连接到最新草稿章节，实时显示内容变化。通过轮询最新章节（每 5 秒）来实现，不需要额外后端接口。

```vue
<template>
  <div v-if="isVisible" class="ap-stream">
    <div class="stream-header">
      <span class="pulse-dot"></span>
      正在生成第 {{ chapterNumber }} 章 · 节拍 {{ beatIndex }}
      <span class="word-count">{{ wordCount }} 字</span>
    </div>
    <div ref="streamEl" class="stream-body">
      <div class="stream-text">{{ displayContent }}</div>
      <span class="cursor">▋</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  novelId: String,
  currentStage: String,
  completedChapters: Number,
})

const isVisible = computed(() => props.currentStage === 'writing')
const displayContent = ref('')
const chapterNumber = ref(0)
const beatIndex = ref(0)
const wordCount = computed(() => displayContent.value.length)
const streamEl = ref(null)

let pollTimer = null

async function fetchLatestDraft() {
  // 取最新 draft 章节的内容
  const res = await fetch(`/api/v1/novels/${props.novelId}/chapters?status=draft&limit=1`)
  if (!res.ok) return
  const data = await res.json()
  if (data.chapters?.length) {
    const ch = data.chapters[0]
    displayContent.value = ch.content || ''
    chapterNumber.value = ch.number
    // 自动滚到底
    await nextTick()
    if (streamEl.value) {
      streamEl.value.scrollTop = streamEl.value.scrollHeight
    }
  }
}

watch(() => props.currentStage, (stage) => {
  if (stage === 'writing') {
    pollTimer = setInterval(fetchLatestDraft, 5000)
    fetchLatestDraft()
  } else {
    clearInterval(pollTimer)
  }
}, { immediate: true })

onUnmounted(() => clearInterval(pollTimer))
</script>

<style scoped>
.ap-stream {
  background: #0d0d0d;
  border: 1px solid #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
  font-family: 'Courier New', monospace;
}
.stream-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 14px;
  background: #111; border-bottom: 1px solid #1a1a1a;
  font-size: 12px; color: #888;
}
.pulse-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #18a058;
  animation: pulse 1s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
.word-count { margin-left: auto; color: #555; }
.stream-body {
  height: 200px; overflow-y: auto;
  padding: 12px 16px;
}
.stream-text { color: #c8c8c8; font-size: 13px; line-height: 1.8; white-space: pre-wrap; }
.cursor { color: #18a058; animation: blink 1s step-end infinite; }
@keyframes blink { 50%{opacity:0} }
</style>
```

---

## Task 12：C+ 语义化快照系统（Git-like，轻量指针）

### 目标

小说级 **版本控制 + 平行分支**，支持回溯与「世界线分歧」。**禁止**每次快照对正文做深拷贝（避免库体积爆炸）。

### 数据模型（领域 / SQLAlchemy 方向）

新建 `NovelSnapshot`（表名可按项目惯例，如 `novel_snapshots`）：

| 字段 | 说明 |
|------|------|
| `id` | UUID |
| `novel_id` | 外键 → `Novel` |
| `parent_snapshot_id` | 可选，分支点父快照 |
| `branch_name` | 如 `main` / `experimental-save-heroine` |
| `trigger_type` | 枚举：`AUTO` / `MANUAL` |
| `name` | 短标题，如 `[Auto] 幕间结算：第一幕完`、`[Manual] 抉择点：准备杀出重围` |
| `description` | 可选长备注 |
| `chapter_pointers` | **JSON：当前快照涵盖的 chapter id 列表（只存指针，不存正文）** |
| `bible_state` | JSON：世界观/人物设定等 Bible 全量快照 |
| `foreshadow_state` | JSON：伏笔账本快照 |
| `graph_state` | JSON（可选）：知识图谱/三元组快照，与 Task 17 衔接 |
| `created_at` | 时间戳 |

**演进说明**：若后续要求「章节不可变、多版本并存」，可再引入 `chapter_versions` 表；v1 可用 **指针列表 + 回滚时按策略裁剪/重建章节行** 控制复杂度，但须在服务层文档中写明语义（软删除 vs 硬删）。

### 核心服务：`snapshot_service.py`

- `create_snapshot(novel_id, trigger_type, name, description=None, branch_name=None, parent_snapshot_id=None)`  
  - 收集当前小说下**有效**章节 id 列表。  
  - 序列化 Bible、Foreshadow（及可选 graph）。  
  - 写入 `NovelSnapshot`。  
- `list_snapshots(novel_id)` / `get_snapshot(snapshot_id)`  
- `rollback_to_snapshot(novel_id, snapshot_id)`：恢复 novel 侧状态 + 按策略处理「快照之后」的章节（产品需二选一：**隐藏/删除** 或 **迁入 orphan 分支**）。  
- `branch_from_snapshot(novel_id, snapshot_id, branch_name, description)`：从新分支指针继续生成。

### 自动触发（C+ 语义化策略）

| 触发点 | 行为 |
|--------|------|
| 状态机进入 `PAUSED_FOR_REVIEW` | 自动 `AUTO` 快照，名称带语义（幕间/重大转折前夕等） |
| Macro Refactor **应用修改前** | 自动 `[Auto] 全局重构前` |
| 每完成 **10 章**（可配置） | 滚动防灾快照 |

### 手动触发

- UI/API：`MANUAL` 快照，**强制填写备注**（世界线分歧点），用于「杀出重围 vs 招安」等实验分支。

### API 草案（与 Task 8 同风格注册）

- `POST /api/v1/novels/{novel_id}/snapshots` — 手动创建  
- `POST /api/v1/novels/{novel_id}/snapshots/auto` — 可选：显式触发滚动备份  
- `POST /api/v1/novels/{novel_id}/rollback` — body: `{ "snapshot_id": "..." }`  
- `POST /api/v1/novels/{novel_id}/snapshots/{snapshot_id}/branch` — 创建平行分支  
- `GET /api/v1/novels/{novel_id}/snapshots` — 时间线列表  

### 集成点

- `autopilot_daemon`：在切入 `PAUSED_FOR_REVIEW` 之前、以及满足「每 10 章」计数时调用 `create_snapshot`。  
- 全局重构管线：在 **apply** 前调用一次 `AUTO` 快照。

### 前端（与 Task 18 联动）

时间线视图：快照节点 → 「回溯」「从此处分支」；分支对比可后续再做（字数、张力曲线、差异摘要）。

---

## Task 13：轻量级角色心理锚点（Mental State v1）

### 目标

用低成本枚举解决「上一章大悲、下一章说笑」的断裂感；**v1 不做**完整事件驱动心理机（留作后续升级到 B/C 档）。

### 数据

在 `bible_characters`（或项目中的 `Character` 持久化表）增加：

- `mental_state`：枚举，建议 `NORMAL` / `TRAUMATIZED` / `ENRAGED` / `DEPRESSED` / `EXHAUSTED` / `CALM`（可按库内惯例收敛命名）。  
- `mental_state_reason`：短字符串（如 ≤100 字），例：`师傅刚在眼前被反派轰成渣`。

### Prompt 注入

在 `ContextAssemblyService.build_chapter_prompt()`（或等价 `context_intelligence` 组装处）：

- 拉取本章将出场角色。  
- 若 `mental_state != NORMAL`，在角色设定区追加约束，例如：  
  `[情绪锚点约束] {name} 当前心理状态为【{mental_state}】（原因：{mental_state_reason}）。对话、微表情、动作须与该状态一致。`

### 后续迭代（不在 v1 范围）

- 事件驱动表 `character_mental_states`、持续章节数、创伤源与触发词强化（对话纪要中的 C 档）。

---

## Task 14：配角活化（口头禅 + 待机动作）

### 决策

采用 **B 档**：`verbal_tic` + `idle_behavior`；**不做**完整 speech_pattern / emotional_trigger 库（避免 Context 污染，见对话纪要）。

### 数据

`bible_characters` 增加：

- `verbal_tic`：String，约 ≤50 字。  
- `idle_behavior`：String，约 ≤100 字。

### Prompt 注入

与 Task 13 一并打包进角色区，示例约束：

`[角色特征约束] {name} 说话时常带口头禅【{verbal_tic}】，并有习惯动作【{idle_behavior}】。在长对话中自然穿插以替代单调的“他说道”，但单章内同一动作重复不超过 2 次。`

---

## Task 15：宏观节奏控制器（缓冲章 / Buffer Chapters）

### 目标

上一幕若为高潮，本幕开篇强制 **1～2 章缓冲**：战利品、疗伤、震惊反应、轻量日常，**不猛推主线危机**。

### 实现位置

在幕级章纲生成入口（如 `generate_act_chapters` / `ContinuousPlanningService` 对应方法）**开头**：

1. 读取上一幕末 **2～3** 章的 outline/summary（或已有 `tension_score`）。  
2. 若无结构化张力，可用极简规则或极短 LLM 判别「是否高潮/大战」。  
3. 若判定为高潮，在向模型投喂的 system 侧注入 **【强制节奏指令】**（缓冲章要求，见北极星节）。

### 与现有计划的关系

本文件 **关键注意事项 §5** 已有「`last_chapter_tension` + prompt 软注入」；Task 15 将同一思想 **上推到幕级规划**，避免仅靠单章审计补救。实施时避免两处指令互相矛盾，优先 **单一来源** 或明确优先级（幕级 > 单章）。

---

## Task 16：微观节拍放大器强化（Beat Magnifier）

### 目标

在已有 **节拍级幂等**（Task 2 `_handle_writing` + Task 1 `current_beat_index`）上，强化 **契约与质量**：

1. **Beat 拆解**：将本章一句 outline 交给 LLM，输出 **固定长度（如 4）** 的节拍 JSON 数组，每项含场景/动作/目标字数_hint。  
2. **幂等循环**：`for idx, beat in enumerate(beats)`：若 `idx < chapter.current_beat_index` 则跳过；否则只生成当前节拍；`content += 段落`；`current_beat_index = idx + 1`；**每节拍 commit**，长事务不锁库。

### 验收要点

- 中断后可从 `current_beat_index` 续写，不重复已写入节拍。  
- 节拍 JSON 可解析、失败重试策略明确（与熔断/Task 3 一致）。

---

## Task 17（可选）：检索降噪 — 时间衰减 + 图谱校验

### 背景

百万字后纯向量检索易把无关历史片段拼进上下文，导致「精神分裂」式生成。

### 方向

- 检索打分加入 **时间衰减**（越近章节权重越高）。  
- **知识图谱三元组** gate：仅当 `[实体]-[关系]-[实体]` 与查询意图一致（或存在于当前 bible/graph 快照）时，才采纳该向量片段。

### 依赖

与 Task 12 的 `graph_state` 快照、现有图谱更新任务（Task 5 `GRAPH_UPDATE`）衔接；可排在 P2。

---

## Task 18：控制台 UI 演进（世界观测台）

### 方向（不替代 Task 10/11，在其上扩展）

- **主区**：双栏 — 左侧章节 Markdown 流，右侧实时「思考/阶段」日志（提取伏笔、文风漂移评估等）。  
- **左栏**：可生长的剧情树，当前生成节点高亮。  
- **右栏仪表盘**：张力曲线、文风偏离、未回收伏笔/未出场角色（资产雷达）。  
- **Task 12**：快照时间线、回溯与分支入口。

实现可拆多 PR：先时间线 + 只读指标，再图表细化。

---

## 关键注意事项汇总

### 1. 事务粒度原则

```
❌ 错误：  open_db_tx → LLM生成(3分钟) → commit
✅ 正确：  快速读状态 → [无锁] LLM生成 → 快速写状态
```

Daemon 里所有 DB 操作只在两个时机：
- 开头读 `novel` 状态（`get_by_id`）
- 每个节拍完成后更新章节内容 + `novel.current_beat_index`

### 2. 幂等性保证

每次 WRITING 阶段启动时，先检查 `novel.current_beat_index`，从断点继续，不从头重写。

### 3. asyncio 与线程混用

- Daemon 主线程：同步 `while True` + `asyncio.run()` 包每次处理
- BackgroundTaskService 后台线程：`asyncio.run()` 调用 LLM（每次新 loop，无冲突）
- SQLite 连接：`check_same_thread=False`，多线程读写安全

### 4. `PAUSED_FOR_REVIEW` 触发时机

| 时机 | 动作 |
|------|------|
| `MACRO_PLANNING` 完成后 | 暂停，前端显示「确认三幕骨架」提示 |
| `ACT_PLANNING` 完成后 | 暂停，前端显示「确认章节大纲」提示 |
| 达到 `max_auto_chapters` | 暂停并停止，等待人工重新设置目标 |

用户点「确认继续」→ 调用 `POST /resume` → 后端设 `stage=ACT_PLANNING, status=RUNNING`。

### 5. `last_chapter_tension` 与缓冲章

张力打分在 `AUDITING` 阶段做（很轻量，~5 token 输出）。  
下一轮 `WRITING` 开始时检查，如果 `≥ 8`，自动在 `outline` 前拼入缓冲提示语。  
不需要修改 story_node，直接在 prompt 层面"软注入"。

**幕级补强**：见 **Task 15**，在生成下一幕章纲时根据上一幕末章再注入「缓冲章」指令；与本节并存时需约定优先级，避免重复或矛盾。

### 6. 语义化快照与回滚

进入 `PAUSED_FOR_REVIEW`、全局重构应用前、每 10 章等节点应自动打快照；回滚语义（删/隐藏后续章节、分支指针）必须在 **Task 12** 服务层写清，避免与 autopilot 状态机打架。

### 7. 验证命令

```bash
# 启动 daemon
python scripts/start_daemon.py

# 通过 API 启动一本小说的自动驾驶（先记下 novel_id）
curl -X POST http://localhost:8000/api/v1/autopilot/{novel_id}/start \
  -H "Content-Type: application/json" \
  -d '{"max_auto_chapters": 5}'

# 实时监控 SSE
curl -N http://localhost:8000/api/v1/autopilot/{novel_id}/events

# 查看生成的章节
sqlite3 data/aitext.db \
  "SELECT number, title, length(content), status FROM chapters WHERE novel_id='{novel_id}' ORDER BY number;"

# 查看熔断状态（通过 daemon 日志）
tail -f data/logs/autopilot_daemon.log | grep -E "CircuitBreaker|张力|文风|伏笔"
```
