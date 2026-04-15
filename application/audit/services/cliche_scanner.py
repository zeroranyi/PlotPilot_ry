# application/services/cliche_scanner.py
import re
from dataclasses import dataclass
from typing import List


@dataclass
class ClicheHit:
    """俗套句式命中结果"""
    pattern: str  # 匹配的模式名称
    text: str  # 匹配的文本
    start: int  # 起始位置
    end: int  # 结束位置
    severity: str = "warning"  # 严重程度: "info" | "warning"


# AI 生成文本常见俗套句式模式
AI_CLICHE_PATTERNS = [
    # 熊熊系列
    (r"熊熊(烈火|怒火|火焰|燃烧)", "熊熊系列"),

    # 眼神系列
    (r"(眼中|眸中|目光中)闪过一丝", "眼神闪过系列"),

    # 嘴角系列
    (r"嘴角(勾起|扬起|浮现|上扬).*?[笑弧]", "嘴角笑意系列"),

    # 心理系列
    (r"(心中|内心)五味杂陈", "五味杂陈系列"),

    # 比喻系列
    (r"如同.{1,10}一般", "如同一般系列"),

    # 凌厉系列
    (r"(眼神|目光|气势).{0,3}(变得|显得|愈发)?凌厉", "凌厉系列"),

    # 复杂情绪系列
    (r"(眼神|目光|眼中).{0,5}复杂", "复杂眼神系列"),

    # 波澜系列
    (r"(内心|心中).{0,5}(泛起|涌起|掀起).{0,5}波澜", "心中波澜系列"),

    # 深邃系列
    (r"(眼神|目光|眼眸).{0,3}(深邃|幽深)", "深邃眼神系列"),

    # 一抹系列
    (r"(嘴角|脸上|眼中).{0,3}(浮现|闪过|掠过)一抹", "一抹系列"),
]


class ClicheScanner:
    """俗套句式扫描器

    使用正则表达式检测 AI 生成文本中的常见俗套句式。
    """

    def __init__(self):
        # 预编译所有正则表达式以提高性能
        self.compiled_patterns = [
            (re.compile(pattern), name)
            for pattern, name in AI_CLICHE_PATTERNS
        ]

    def scan_cliches(self, text: str) -> List[ClicheHit]:
        """扫描文本中的俗套句式

        Args:
            text: 要扫描的文本

        Returns:
            检测到的俗套句式列表，按出现位置排序
        """
        hits = []

        for compiled_pattern, pattern_name in self.compiled_patterns:
            for match in compiled_pattern.finditer(text):
                hit = ClicheHit(
                    pattern=pattern_name,
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    severity="warning"
                )
                hits.append(hit)

        # 按位置排序
        hits.sort(key=lambda h: h.start)

        return hits
