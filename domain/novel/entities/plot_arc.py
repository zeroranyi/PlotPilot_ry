from typing import List, Optional
from domain.shared.base_entity import BaseEntity
from domain.novel.value_objects.novel_id import NovelId
from domain.novel.value_objects.plot_point import PlotPoint
from domain.novel.value_objects.tension_level import TensionLevel


class PlotArc(BaseEntity):
    """剧情弧实体"""

    def __init__(
        self,
        id: str,
        novel_id: NovelId,
        key_points: Optional[List[PlotPoint]] = None,
        slug: str = "default",
        display_name: str = "",
    ):
        super().__init__(id)
        self.novel_id = novel_id
        self.key_points: List[PlotPoint] = key_points if key_points is not None else []
        self.slug = slug or "default"
        self.display_name = display_name or ""

    def add_plot_point(self, point: PlotPoint) -> None:
        """添加剧情点，自动按章节号排序"""
        if point is None:
            raise ValueError("Plot point cannot be None")
        self.key_points.append(point)
        self.key_points.sort(key=lambda p: p.chapter_number)

    def get_expected_tension(self, chapter_number: int) -> TensionLevel:
        """获取指定章节的期望张力，使用线性插值"""
        if chapter_number < 1:
            raise ValueError("Chapter number must be positive (>= 1)")

        if not self.key_points:
            return TensionLevel.LOW

        # If before first point, return first point's tension
        if chapter_number <= self.key_points[0].chapter_number:
            return self.key_points[0].tension

        # If after last point, return last point's tension
        if chapter_number >= self.key_points[-1].chapter_number:
            return self.key_points[-1].tension

        # Find the two points to interpolate between
        for i in range(len(self.key_points) - 1):
            current_point = self.key_points[i]
            next_point = self.key_points[i + 1]

            if current_point.chapter_number <= chapter_number <= next_point.chapter_number:
                # Linear interpolation
                chapter_diff = next_point.chapter_number - current_point.chapter_number

                # Guard against division by zero
                if chapter_diff == 0:
                    return current_point.tension

                tension_diff = next_point.tension.value - current_point.tension.value
                chapter_offset = chapter_number - current_point.chapter_number

                interpolated_value = current_point.tension.value + (tension_diff * chapter_offset / chapter_diff)

                # Round to nearest tension level
                rounded_value = round(interpolated_value)

                # Clamp to valid range using TensionLevel enum bounds
                rounded_value = max(TensionLevel.LOW.value, min(TensionLevel.PEAK.value, rounded_value))

                return TensionLevel(rounded_value)

        # Fallback (should not reach here)
        return TensionLevel.LOW

    def get_next_plot_point(self, current_chapter: int) -> Optional[PlotPoint]:
        """获取当前章节之后的下一个剧情点"""
        if current_chapter < 1:
            raise ValueError("Chapter number must be positive (>= 1)")
        for point in self.key_points:
            if point.chapter_number > current_chapter:
                return point
        return None
