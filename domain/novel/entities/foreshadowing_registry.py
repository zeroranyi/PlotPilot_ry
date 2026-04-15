# domain/novel/entities/foreshadowing_registry.py
from typing import List, Optional
from dataclasses import replace

from domain.shared.base_entity import BaseEntity
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.foreshadowing import (
    Foreshadowing,
    ForeshadowingStatus
)
from domain.novel.entities.subtext_ledger_entry import SubtextLedgerEntry
from domain.shared.exceptions import InvalidOperationError


class ForeshadowingRegistry(BaseEntity):
    """伏笔注册表实体"""

    def __init__(self, id: str, novel_id: NovelId):
        super().__init__(id)
        self.novel_id = novel_id
        self._foreshadowings: List[Foreshadowing] = []
        self._subtext_entries: List[SubtextLedgerEntry] = []

    @property
    def foreshadowings(self) -> List[Foreshadowing]:
        """返回伏笔列表的副本"""
        return self._foreshadowings.copy()

    def register(self, foreshadowing: Foreshadowing) -> None:
        """注册新伏笔，检查重复"""
        if any(f.id == foreshadowing.id for f in self._foreshadowings):
            raise InvalidOperationError(
                f"Foreshadowing with id '{foreshadowing.id}' already exists"
            )
        self._foreshadowings.append(foreshadowing)

    def mark_resolved(self, foreshadowing_id: str, resolved_in_chapter: int) -> None:
        """标记伏笔为已解决，创建新的不可变对象"""
        for i, foreshadowing in enumerate(self._foreshadowings):
            if foreshadowing.id == foreshadowing_id:
                # 创建新的不可变 Foreshadowing 对象
                resolved_foreshadowing = replace(
                    foreshadowing,
                    status=ForeshadowingStatus.RESOLVED,
                    resolved_in_chapter=resolved_in_chapter
                )
                self._foreshadowings[i] = resolved_foreshadowing
                return

        raise InvalidOperationError(
            f"Foreshadowing with id '{foreshadowing_id}' not found"
        )

    def get_by_id(self, foreshadowing_id: str) -> Optional[Foreshadowing]:
        """通过 ID 获取伏笔"""
        for foreshadowing in self._foreshadowings:
            if foreshadowing.id == foreshadowing_id:
                return foreshadowing
        return None

    def get_unresolved(self) -> List[Foreshadowing]:
        """获取所有未解决的伏笔（PLANTED 状态）"""
        return [
            f for f in self._foreshadowings
            if f.status == ForeshadowingStatus.PLANTED
        ]

    def get_ready_to_resolve(self, current_chapter: int) -> List[Foreshadowing]:
        """获取准备解决的伏笔"""
        return [
            f for f in self._foreshadowings
            if f.status == ForeshadowingStatus.PLANTED
            and f.suggested_resolve_chapter is not None
            and f.suggested_resolve_chapter <= current_chapter
        ]

    @property
    def subtext_entries(self) -> List[SubtextLedgerEntry]:
        """返回潜台词账本条目列表的副本"""
        return self._subtext_entries.copy()

    def add_subtext_entry(self, entry: SubtextLedgerEntry) -> None:
        """添加潜台词账本条目，检查重复"""
        if any(e.id == entry.id for e in self._subtext_entries):
            raise InvalidOperationError(
                f"SubtextLedgerEntry with id '{entry.id}' already exists"
            )
        self._subtext_entries.append(entry)

    def update_subtext_entry(self, entry_id: str, updated_entry: SubtextLedgerEntry) -> None:
        """更新潜台词账本条目"""
        for i, entry in enumerate(self._subtext_entries):
            if entry.id == entry_id:
                self._subtext_entries[i] = updated_entry
                return

        raise InvalidOperationError(
            f"SubtextLedgerEntry with id '{entry_id}' not found"
        )

    def remove_subtext_entry(self, entry_id: str) -> None:
        """删除潜台词账本条目"""
        for i, entry in enumerate(self._subtext_entries):
            if entry.id == entry_id:
                self._subtext_entries.pop(i)
                return

        raise InvalidOperationError(
            f"SubtextLedgerEntry with id '{entry_id}' not found"
        )

    def get_subtext_entry_by_id(self, entry_id: str) -> Optional[SubtextLedgerEntry]:
        """通过 ID 获取潜台词账本条目"""
        for entry in self._subtext_entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_pending_subtext_entries(self) -> List[SubtextLedgerEntry]:
        """获取所有待消费的潜台词账本条目"""
        return [
            e for e in self._subtext_entries
            if e.status == "pending"
        ]

    def get_overdue_foreshadowings(self, current_chapter: int) -> List[Foreshadowing]:
        """获取已过期的伏笔（预期回收章节已过但尚未回收）"""
        return [
            f for f in self._foreshadowings
            if f.status == ForeshadowingStatus.PLANTED
            and f.suggested_resolve_chapter is not None
            and f.suggested_resolve_chapter < current_chapter
        ]

    def get_upcoming_foreshadowings(self, current_chapter: int, window: int = 3) -> List[Foreshadowing]:
        """获取即将到期的伏笔（在指定窗口内预期回收）"""
        return [
            f for f in self._foreshadowings
            if f.status == ForeshadowingStatus.PLANTED
            and f.suggested_resolve_chapter is not None
            and current_chapter <= f.suggested_resolve_chapter <= current_chapter + window
        ]

    def get_overdue_subtext_entries(self, current_chapter: int) -> List[SubtextLedgerEntry]:
        """获取已过期的潜台词条目"""
        return [
            e for e in self._subtext_entries
            if e.status == "pending"
            and hasattr(e, 'suggested_resolve_chapter')
            and e.suggested_resolve_chapter is not None
            and e.suggested_resolve_chapter < current_chapter
        ]

    def get_upcoming_subtext_entries(self, current_chapter: int, window: int = 3) -> List[SubtextLedgerEntry]:
        """获取即将到期的潜台词条目"""
        return [
            e for e in self._subtext_entries
            if e.status == "pending"
            and hasattr(e, 'suggested_resolve_chapter')
            and e.suggested_resolve_chapter is not None
            and current_chapter <= e.suggested_resolve_chapter <= current_chapter + window
        ]

