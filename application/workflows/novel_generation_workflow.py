"""小说生成工作流

协调多个应用服务完成完整的小说生成流程。
这是对旧 pipeline/runner.py 的重构，使用新的 DDD 架构。
"""
import logging
from typing import List, Optional
from application.core.services.novel_service import NovelService
from application.core.services.chapter_service import ChapterService
from application.world.services.bible_service import BibleService
from application.engine.services.ai_generation_service import AIGenerationService
from application.core.dtos.novel_dto import NovelDTO
from application.core.dtos.chapter_dto import ChapterDTO
from domain.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


class NovelGenerationWorkflow:
    """小说生成工作流

    协调多个服务完成完整的小说生成流程。
    替代旧的 pipeline/runner.py 功能。
    """

    def __init__(
        self,
        novel_service: NovelService,
        chapter_service: ChapterService,
        bible_service: BibleService,
        ai_generation_service: AIGenerationService
    ):
        """初始化工作流

        Args:
            novel_service: 小说服务
            chapter_service: 章节服务
            bible_service: Bible 服务
            ai_generation_service: AI 生成服务
        """
        self.novel_service = novel_service
        self.chapter_service = chapter_service
        self.bible_service = bible_service
        self.ai_generation_service = ai_generation_service

    async def run_full_generation(
        self,
        novel_id: str,
        title: str,
        author: str,
        target_chapters: int,
        outlines: List[str],
        premise: Optional[str] = None
    ) -> NovelDTO:
        """运行完整的小说生成流程

        这是主要的工作流方法，协调整个小说生成过程：
        1. 创建小说
        2. 创建 Bible
        3. 逐章生成内容
        4. 更新小说状态为完成

        Args:
            novel_id: 小说 ID
            title: 标题
            author: 作者
            target_chapters: 目标章节数
            outlines: 章节大纲列表
            premise: 小说前提（可选）

        Returns:
            生成完成的小说 DTO

        Raises:
            ValueError: 如果参数无效
            RuntimeError: 如果生成过程失败
        """
        logger.info(f"Starting full generation for novel: {title} (ID: {novel_id})")

        # 验证输入
        if len(outlines) != target_chapters:
            raise ValueError(
                f"Outline count ({len(outlines)}) does not match target chapters ({target_chapters})"
            )

        # 1. 创建小说
        logger.info(f"Creating novel: {title}")
        novel = self.novel_service.create_novel(
            novel_id=novel_id,
            title=title,
            author=author,
            target_chapters=target_chapters
        )

        # 2. 创建 Bible
        logger.info(f"Creating Bible for novel: {novel_id}")
        bible_id = f"{novel_id}-bible"
        self.bible_service.create_bible(
            bible_id=bible_id,
            novel_id=novel_id
        )

        # 3. 逐章生成
        for i, outline in enumerate(outlines, 1):
            logger.info(f"Generating chapter {i}/{target_chapters}")

            try:
                # 生成章节内容
                content = await self.ai_generation_service.generate_chapter(
                    novel_id=novel_id,
                    chapter_number=i,
                    outline=outline
                )

                # 添加章节到小说
                chapter_id = f"{novel_id}-chapter-{i}"
                novel = self.novel_service.add_chapter(
                    novel_id=novel_id,
                    chapter_id=chapter_id,
                    number=i,
                    title=f"第{i}章",
                    content=content
                )

                logger.info(f"Chapter {i} completed")

            except Exception as e:
                logger.error(f"Failed to generate chapter {i}: {str(e)}")
                raise RuntimeError(f"Chapter {i} generation failed: {str(e)}") from e

        # 4. 更新小说阶段为完成
        logger.info(f"Marking novel as completed: {novel_id}")
        novel = self.novel_service.update_novel_stage(
            novel_id=novel_id,
            stage="completed"
        )

        logger.info(f"Full generation completed for novel: {title}")
        return novel

    async def generate_single_chapter(
        self,
        novel_id: str,
        chapter_number: int,
        outline: str
    ) -> str:
        """生成单个章节

        用于单独生成或重新生成某一章节。

        Args:
            novel_id: 小说 ID
            chapter_number: 章节编号
            outline: 章节大纲

        Returns:
            生成的章节内容

        Raises:
            EntityNotFoundError: 如果小说不存在
            RuntimeError: 如果生成失败
        """
        logger.info(f"Generating single chapter {chapter_number} for novel {novel_id}")

        # 验证小说存在
        novel = self.novel_service.get_novel(novel_id)
        if novel is None:
            raise EntityNotFoundError("Novel", novel_id)

        # 生成章节
        try:
            content = await self.ai_generation_service.generate_chapter(
                novel_id=novel_id,
                chapter_number=chapter_number,
                outline=outline
            )
            logger.info(f"Single chapter {chapter_number} generated successfully")
            return content
        except Exception as e:
            logger.error(f"Failed to generate chapter {chapter_number}: {str(e)}")
            raise RuntimeError(f"Chapter generation failed: {str(e)}") from e

    async def regenerate_chapter(
        self,
        novel_id: str,
        chapter_number: int,
        outline: str
    ) -> ChapterDTO:
        """重新生成已存在的章节

        Args:
            novel_id: 小说 ID
            chapter_number: 章节编号
            outline: 新的章节大纲

        Returns:
            更新后的章节 DTO

        Raises:
            EntityNotFoundError: 如果小说或章节不存在
            RuntimeError: 如果生成失败
        """
        logger.info(f"Regenerating chapter {chapter_number} for novel {novel_id}")

        # 生成新内容
        content = await self.generate_single_chapter(
            novel_id=novel_id,
            chapter_number=chapter_number,
            outline=outline
        )

        # 更新章节内容
        chapter_id = f"{novel_id}-chapter-{chapter_number}"
        chapter = self.chapter_service.update_chapter_content(
            chapter_id=chapter_id,
            content=content
        )

        logger.info(f"Chapter {chapter_number} regenerated successfully")
        return chapter

    def get_generation_progress(self, novel_id: str) -> dict:
        """获取生成进度

        Args:
            novel_id: 小说 ID

        Returns:
            包含进度信息的字典

        Raises:
            EntityNotFoundError: 如果小说不存在
        """
        novel = self.novel_service.get_novel(novel_id)
        if novel is None:
            raise EntityNotFoundError("Novel", novel_id)

        stats = self.novel_service.get_novel_statistics(novel_id)

        return {
            "novel_id": novel_id,
            "title": novel.title,
            "stage": novel.stage,
            "target_chapters": novel.target_chapters,
            "completed_chapters": stats["completed_chapters"],
            "total_chapters": stats["total_chapters"],
            "total_words": stats["total_words"],
            "progress_percentage": (
                stats["completed_chapters"] / novel.target_chapters * 100
                if novel.target_chapters > 0 else 0
            )
        }
