# application/services/subtext_matching_service.py
from typing import Dict, List, Optional

from domain.novel.entities.subtext_ledger_entry import SubtextLedgerEntry


class SubtextMatchingService:
    """潜台词匹配服务"""

    def find_best_anchor_match(
        self,
        current_anchors: Dict[str, str],
        ledger_entries: List[SubtextLedgerEntry]
    ) -> Optional[SubtextLedgerEntry]:
        """
        查找最佳匹配的潜台词账本条目

        Args:
            current_anchors: 当前场景的感官锚点，如 {"visual": "红色围巾", "auditory": "脚步声"}
            ledger_entries: 待匹配的账本条目列表

        Returns:
            匹配度最高的条目，如果没有匹配则返回 None
        """
        # 只考虑 pending 状态的条目
        pending_entries = [e for e in ledger_entries if e.status == "pending"]

        if not pending_entries:
            return None

        best_match = None
        best_score = 0

        for entry in pending_entries:
            score = self._calculate_match_score(current_anchors, entry.sensory_anchors)
            if score > best_score:
                best_score = score
                best_match = entry

        # 如果没有任何匹配（score = 0），返回 None
        return best_match if best_score > 0 else None

    def _calculate_match_score(
        self,
        current_anchors: Dict[str, str],
        entry_anchors: Dict[str, str]
    ) -> float:
        """
        计算匹配分数（MVP 简单实现：子串匹配）

        Args:
            current_anchors: 当前场景的感官锚点
            entry_anchors: 账本条目的感官锚点

        Returns:
            匹配分数（基于匹配比例和绝对匹配数）
        """
        if not current_anchors or not entry_anchors:
            return 0.0

        total_matches = 0
        total_anchors = len(entry_anchors)

        # 遍历账本条目的每个锚点
        for anchor_type, anchor_value in entry_anchors.items():
            # 检查当前场景是否有相同类型的锚点
            if anchor_type in current_anchors:
                current_value = current_anchors[anchor_type].lower()
                entry_value = anchor_value.lower()

                # 子串匹配：任一方包含另一方
                if entry_value in current_value or current_value in entry_value:
                    total_matches += 1

        # 返回匹配比例 + 绝对匹配数作为权重
        # 这样可以在比例相同时，优先选择匹配更多锚点的条目
        match_ratio = total_matches / total_anchors if total_anchors > 0 else 0.0

        # 分数 = 匹配比例 + (绝对匹配数 * 0.01)
        # 例如：2/2 = 1.02, 1/1 = 1.01，这样 2/2 会胜出
        return match_ratio + (total_matches * 0.01)
