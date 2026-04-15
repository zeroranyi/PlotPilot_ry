"""Novel 数据传输对象"""
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from domain.novel.entities.novel import Novel
    from domain.novel.entities.chapter import Chapter


@dataclass
class ChapterDTO:
    """章节 DTO"""
    id: str
    number: int
    title: str
    content: str
    word_count: int

    @classmethod
    def from_domain(cls, chapter: 'Chapter') -> 'ChapterDTO':
        """从领域对象创建 DTO

        Args:
            chapter: Chapter 领域对象

        Returns:
            ChapterDTO
        """
        return cls(
            id=chapter.id,
            number=chapter.number,
            title=chapter.title,
            content=chapter.content,
            word_count=chapter.word_count.value
        )


@dataclass
class NovelDTO:
    """小说 DTO

    用于在应用层和外部层之间传输数据。
    """
    id: str
    title: str
    author: str
    target_chapters: int
    stage: str
    premise: str
    chapters: List[ChapterDTO]
    total_word_count: int
    has_bible: bool = False
    has_outline: bool = False
    autopilot_status: str = "stopped"
    auto_approve_mode: bool = False
    hermes_mode: bool = False

    @classmethod
    def from_domain(cls, novel: 'Novel') -> 'NovelDTO':
        """从领域对象创建 DTO

        Args:
            novel: Novel 领域对象

        Returns:
            NovelDTO
        """
        chapters = [ChapterDTO.from_domain(chapter) for chapter in novel.chapters]
        
        _ap = getattr(novel, 'autopilot_status', 'stopped')
        autopilot_status = _ap.value if hasattr(_ap, 'value') else str(_ap)

        return cls(
            id=novel.novel_id.value,
            title=novel.title,
            author=novel.author,
            target_chapters=novel.target_chapters,
            stage=novel.stage.value,
            premise=getattr(novel, 'premise', ''),  # 兼容旧数据
            chapters=chapters,
            total_word_count=novel.get_total_word_count().value,
            autopilot_status=autopilot_status,
            auto_approve_mode=getattr(novel, 'auto_approve_mode', False),
            hermes_mode=getattr(novel, 'hermes_mode', False),
        )
