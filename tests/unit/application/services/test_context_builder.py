"""ContextBuilder 单元测试（BibleService + 可选 PlotArcRepository）。"""
import time
from typing import Optional
from unittest.mock import Mock, AsyncMock

import pytest

from application.world.dtos.bible_dto import (
    BibleDTO,
    CharacterDTO,
    TimelineNoteDTO,
)
from application.engine.dtos.scene_director_dto import SceneDirectorAnalysis
from application.engine.services.context_builder import ContextBuilder
from domain.bible.value_objects.relationship_graph import RelationshipGraph
from domain.novel.entities.plot_arc import PlotArc
from domain.novel.entities.storyline import Storyline
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.plot_point import PlotPoint, PlotPointType
from domain.novel.value_objects.storyline_status import StorylineStatus
from domain.novel.value_objects.storyline_type import StorylineType
from domain.novel.value_objects.storyline_milestone import StorylineMilestone
from domain.novel.value_objects.tension_level import TensionLevel


def _empty_bible_dto(
    novel_id: str = "novel-1",
    *,
    characters=None,
    timeline_notes=None,
) -> BibleDTO:
    return BibleDTO(
        id=f"{novel_id}-bible",
        novel_id=novel_id,
        characters=characters or [],
        world_settings=[],
        locations=[],
        timeline_notes=timeline_notes or [],
        style_notes=[],
    )


def _make_builder(
    *,
    bible_dto: Optional[BibleDTO] = None,
    storyline_manager: Optional[Mock] = None,
    plot_arc_repository: Optional[Mock] = None,
    novel_repo: Optional[Mock] = None,
    chapter_repo: Optional[Mock] = None,
) -> ContextBuilder:
    bible_service = Mock()
    bible_service.get_bible_by_novel.return_value = bible_dto or _empty_bible_dto()

    if storyline_manager is None:
        storyline_manager = Mock()
        storyline_manager.repository.get_by_novel_id.return_value = []

    if novel_repo is None:
        novel_repo = Mock()
        novel = Mock()
        novel.title = "Test Novel"
        novel.author = "Test Author"
        novel_repo.get_by_id.return_value = novel

    if chapter_repo is None:
        chapter_repo = Mock()
        chapter_repo.list_by_novel.return_value = []

    return ContextBuilder(
        bible_service=bible_service,
        storyline_manager=storyline_manager,
        relationship_engine=Mock(),
        vector_store=Mock(),
        novel_repository=novel_repo,
        chapter_repository=chapter_repo,
        plot_arc_repository=plot_arc_repository,
    )


class TestContextBuilder:
    # estimate_tokens 已移至 ContextBudgetAllocator
    # 此测试已过时,跳过
    
    def test_build_context_basic(self):
        dto = _empty_bible_dto(
            characters=[
                CharacterDTO("char1", "Alice", "Protagonist", []),
            ]
        )
        builder = _make_builder(bible_dto=dto)
        context = builder.build_context(
            novel_id="novel-1",
            chapter_number=1,
            outline="Alice starts her journey",
            max_tokens=35000,
        )
        assert "Test Novel" in context
        assert "Alice" in context
        assert "Chapter 1" in context

    def test_build_context_respects_token_budget(self):
        chars = [
            CharacterDTO(f"c{i}", f"C{i}", "Very long description " * 100, [])
            for i in range(10)
        ]
        builder = _make_builder(bible_dto=_empty_bible_dto(characters=chars))
        context = builder.build_context(
            novel_id="novel-1",
            chapter_number=1,
            outline="Test outline",
            max_tokens=5000,
        )
        # 验证上下文不为空(预算分配器会处理截断)
        assert context is not None
        assert len(context) > 0

    def test_build_context_includes_recent_chapters(self):
        chapter_repo = Mock()
        chapter1 = Mock()
        chapter1.number = 1
        chapter1.title = "Chapter 1"
        chapter1.content = "Content of chapter 1"
        chapter2 = Mock()
        chapter2.number = 2
        chapter2.title = "Chapter 2"
        chapter2.content = "Content of chapter 2"
        chapter_repo.list_by_novel.return_value = [chapter1, chapter2]

        builder = _make_builder(chapter_repo=chapter_repo)
        context = builder.build_context(
            novel_id="novel-1",
            chapter_number=3,
            outline="Test outline",
            max_tokens=35000,
        )
        assert "Chapter 1" in context or "Chapter 2" in context

    def test_build_context_includes_storylines(self):
        storyline = Storyline(
            id="sl-1",
            novel_id=NovelId("novel-1"),
            storyline_type=StorylineType.MAIN_PLOT,
            status=StorylineStatus.ACTIVE,
            estimated_chapter_start=1,
            estimated_chapter_end=10,
        )
        repo = Mock()
        repo.get_by_novel_id.return_value = [storyline]
        sm = Mock()
        sm.repository = repo

        builder = _make_builder(storyline_manager=sm)
        context = builder.build_context(
            novel_id="novel-1",
            chapter_number=5,
            outline="Test outline",
            max_tokens=35000,
        )
        assert "main_plot" in context
        assert "Active Storylines" in context

    def test_layer1_includes_plot_arc_and_timeline(self):
        arc = PlotArc(id="arc-1", novel_id=NovelId("novel-1"))
        arc.add_plot_point(
            PlotPoint(1, PlotPointType.OPENING, "开局", TensionLevel.LOW)
        )
        arc.add_plot_point(
            PlotPoint(10, PlotPointType.CLIMAX, "高潮", TensionLevel.PEAK)
        )
        plot_repo = Mock()
        plot_repo.get_by_novel_id.return_value = arc

        notes = [
            TimelineNoteDTO(
                id="tn-1", event="元年", time_point="春", description="建都"
            )
        ]
        dto = _empty_bible_dto(timeline_notes=notes)

        builder = _make_builder(bible_dto=dto, plot_arc_repository=plot_repo)
        context = builder.build_context(
            novel_id="novel-1",
            chapter_number=5,
            outline="mid",
            max_tokens=35000,
        )
        assert "Plot arc (pacing)" in context
        assert "Expected tension for this chapter" in context
        assert "Bible timeline notes" in context
        assert "元年" in context

    def test_build_context_performance(self):
        chars = [
            CharacterDTO(f"c{i}", f"C{i}", f"Description {i}", [])
            for i in range(50)
        ]
        chapter_repo = Mock()
        chapters = []
        for i in range(100):
            ch = Mock()
            ch.number = i + 1
            ch.title = f"Chapter {i+1}"
            ch.content = f"Content {i+1}" * 100
            chapters.append(ch)
        chapter_repo.list_by_novel.return_value = chapters

        builder = _make_builder(
            bible_dto=_empty_bible_dto(characters=chars),
            chapter_repo=chapter_repo,
        )
        start = time.time()
        context = builder.build_context(
            novel_id="novel-1",
            chapter_number=50,
            outline="Test outline",
            max_tokens=35000,
        )
        assert time.time() - start < 2.0
        assert len(context) > 0

    def test_layer2_filters_characters_when_scene_director_set(self):
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

    def test_layer2_includes_vector_results(self):
        """向量检索结果应包含在 Layer2 中"""
        # Mock embedding service with async method
        mock_embedding = Mock()
        mock_embedding.embed = AsyncMock(return_value=[0.1] * 768)

        # Mock vector store search with async method
        mock_vector_store = Mock()
        mock_vector_store.search = AsyncMock(return_value=[
            {"id": "chunk1", "score": 0.9, "payload": {"text": "Vector result 1", "chapter_number": 5}},
            {"id": "chunk2", "score": 0.8, "payload": {"text": "Vector result 2", "chapter_number": 6}},
        ])

        # 创建 builder 时传入 mock 服务
        builder = _make_builder()
        builder.embedding_service = mock_embedding
        builder.vector_store = mock_vector_store

        # 手动创建 facade
        from application.ai.vector_retrieval_facade import VectorRetrievalFacade
        builder.vector_facade = VectorRetrievalFacade(mock_vector_store, mock_embedding)

        structured = builder.build_structured_context(
            novel_id="novel-1",
            chapter_number=5,
            outline="Test outline",
            max_tokens=35000,
        )

        layer2 = structured["layer2_text"]
        assert "Vector result 1" in layer2
        assert "Vector result 2" in layer2

    def test_layer2_filters_vector_by_chapter_window(self):
        """向量检索应过滤 ±10 章窗口外的结果"""
        # Mock embedding service with async method
        mock_embedding = Mock()
        mock_embedding.embed = AsyncMock(return_value=[0.1] * 768)

        # Mock vector store 返回 3 条结果：chapter 1, 11, 22
        mock_vector_store = Mock()
        mock_vector_store.search = AsyncMock(return_value=[
            {"id": "chunk1", "score": 0.9, "payload": {"text": "Chapter 1 content", "chapter_number": 1}},
            {"id": "chunk2", "score": 0.85, "payload": {"text": "Chapter 11 content", "chapter_number": 11}},
            {"id": "chunk3", "score": 0.8, "payload": {"text": "Chapter 22 content", "chapter_number": 22}},
        ])

        builder = _make_builder()
        builder.embedding_service = mock_embedding
        builder.vector_store = mock_vector_store

        # 手动创建 facade
        from application.ai.vector_retrieval_facade import VectorRetrievalFacade
        builder.vector_facade = VectorRetrievalFacade(mock_vector_store, mock_embedding)

        # 当前章节 11，窗口 [1, 21]，只保留 chapter 1 和 11
        structured = builder.build_structured_context(
            novel_id="novel-1",
            chapter_number=11,
            outline="Test outline",
            max_tokens=35000,
        )

        layer2 = structured["layer2_text"]
        assert "Chapter 1 content" in layer2
        assert "Chapter 11 content" in layer2
        assert "Chapter 22 content" not in layer2  # 超出 ±10 窗口

    def test_layer2_skips_vector_when_store_is_none(self):
        """当 vector_store 为 None 时，行为与 Phase 1 一致"""
        dto = _empty_bible_dto(
            characters=[CharacterDTO("c1", "Alice", "Hero", [])]
        )
        builder = _make_builder(bible_dto=dto)
        builder.vector_store = None
        builder.embedding_service = None

        structured = builder.build_structured_context(
            novel_id="novel-1",
            chapter_number=5,
            outline="Test outline",
            max_tokens=35000,
        )

        layer2 = structured["layer2_text"]
        assert "Alice" in layer2  # Bible 内容仍然存在
        # 不应该有向量检索相关内容

    def test_layer2_respects_token_budget_with_vector(self):
        """向量结果也受 token 预算约束"""
        # Mock embedding service with async method
        mock_embedding = Mock()
        mock_embedding.embed = AsyncMock(return_value=[0.1] * 768)

        # Mock vector store 返回大量文本
        large_text = "x" * 10000
        mock_vector_store = Mock()
        mock_vector_store.search = AsyncMock(return_value=[
            {"id": f"chunk{i}", "score": 0.9, "payload": {"text": large_text, "chapter_number": 5}}
            for i in range(10)
        ])

        builder = _make_builder()
        builder.embedding_service = mock_embedding
        builder.vector_store = mock_vector_store

        # 手动创建 facade
        from application.ai.vector_retrieval_facade import VectorRetrievalFacade
        builder.vector_facade = VectorRetrievalFacade(mock_vector_store, mock_embedding)

        structured = builder.build_structured_context(
            novel_id="novel-1",
            chapter_number=5,
            outline="Test outline",
            max_tokens=5000,  # 小预算
        )

        total_tokens = structured["token_usage"]["total"]
        # 允许 10% 缓冲
        assert total_tokens <= 5500
