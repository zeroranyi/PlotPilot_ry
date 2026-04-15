"""Macro Refactor Scanner Service"""
import logging
from typing import List, Optional, Dict, Set
from domain.novel.repositories.narrative_event_repository import NarrativeEventRepository
from application.audit.dtos.macro_refactor_dto import LogicBreakpoint

logger = logging.getLogger(__name__)


class MacroRefactorScanner:
    """宏观重构扫描器 - 检测人设冲突断点"""

    # 内置人设冲突规则映射
    TRAIT_CONFLICT_RULES: Dict[str, List[str]] = {
        "冷酷": ["动机:冲动", "情绪:愤怒", "行为:鲁莽", "情绪:激动"],
        "理性": ["动机:感性", "情绪:激动", "行为:冲动"],
        "谨慎": ["行为:鲁莽", "动机:冲动", "行为:冲动"],
        "温和": ["情绪:愤怒", "行为:暴力", "情绪:激动"],
    }

    def __init__(self, event_repository: NarrativeEventRepository):
        """初始化扫描器

        Args:
            event_repository: 叙事事件仓储
        """
        self.event_repository = event_repository

    def scan_breakpoints(
        self,
        novel_id: str,
        trait: str,
        conflict_tags: Optional[List[str]] = None
    ) -> List[LogicBreakpoint]:
        """扫描人设冲突断点

        Args:
            novel_id: 小说 ID
            trait: 目标人设标签（如 "冷酷"）
            conflict_tags: 自定义冲突标签列表（如果提供，覆盖内置规则）

        Returns:
            冲突断点列表
        """
        # 确定冲突标签
        if conflict_tags is not None:
            target_conflict_tags = set(conflict_tags)
        else:
            # 使用内置规则
            target_conflict_tags = set(self.TRAIT_CONFLICT_RULES.get(trait, []))

        if not target_conflict_tags:
            logger.warning(f"No conflict rules defined for trait '{trait}' and no custom tags provided")
            return []

        # 获取所有事件（不限章节）
        events = self.event_repository.list_up_to_chapter(novel_id, 999999)

        # 扫描冲突
        breakpoints = []
        for event in events:
            event_tags = set(event.get("tags", []))

            # 检查是否有冲突标签
            conflicting_tags = event_tags & target_conflict_tags

            if conflicting_tags:
                reason = self._generate_conflict_reason(trait, list(conflicting_tags))
                breakpoint = LogicBreakpoint(
                    event_id=event["event_id"],
                    chapter=event["chapter_number"],
                    reason=reason,
                    tags=list(conflicting_tags)
                )
                breakpoints.append(breakpoint)

        logger.info(f"Scanned {len(events)} events, found {len(breakpoints)} breakpoints for trait '{trait}'")
        return breakpoints

    def _generate_conflict_reason(self, trait: str, conflicting_tags: List[str]) -> str:
        """生成冲突原因描述

        Args:
            trait: 目标人设
            conflicting_tags: 冲突标签列表

        Returns:
            冲突原因描述
        """
        tags_str = "、".join(conflicting_tags)
        return f"人设 '{trait}' 与事件标签 [{tags_str}] 冲突"
