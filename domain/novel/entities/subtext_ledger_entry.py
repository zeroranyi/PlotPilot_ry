# domain/novel/entities/subtext_ledger_entry.py
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class SubtextLedgerEntry:
    """潜台词账本条目（不可变值对象）"""

    id: str
    chapter: int
    character_id: str
    hidden_clue: str
    sensory_anchors: Dict[str, str]  # {"visual": "红色围巾", "auditory": "脚步声"}
    status: str  # "pending" | "consumed"
    consumed_at_chapter: Optional[int] = None
    # 预期回收章节范围（写入时由 LLM 或人工设定）
    suggested_resolve_chapter: Optional[int] = None  # 建议回收章节
    resolve_chapter_window: Optional[int] = None  # 宽容窗口（建议章节 ± window 内可接受）
    importance: str = "medium"  # "low" | "medium" | "high" | "critical"
    created_at: datetime = None

    def __post_init__(self):
        # 设置默认创建时间
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.utcnow())

        # 验证 status
        if self.status not in ("pending", "consumed"):
            raise ValueError(f"Invalid status: {self.status}. Must be 'pending' or 'consumed'")

        # 验证 consumed 状态的一致性
        if self.status == "consumed" and self.consumed_at_chapter is None:
            raise ValueError("consumed_at_chapter must be set when status is 'consumed'")

        if self.status == "pending" and self.consumed_at_chapter is not None:
            raise ValueError("consumed_at_chapter must be None when status is 'pending'")

        # 验证 importance
        valid_importance = ("low", "medium", "high", "critical")
        if self.importance not in valid_importance:
            raise ValueError(f"Invalid importance: {self.importance}. Must be one of {valid_importance}")

        # 验证回收章节的合理性
        if self.suggested_resolve_chapter is not None and self.suggested_resolve_chapter < self.chapter:
            raise ValueError("suggested_resolve_chapter must be >= chapter (埋设章节)")
