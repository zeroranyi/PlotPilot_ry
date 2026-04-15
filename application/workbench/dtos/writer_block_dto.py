"""Writer Block 数据传输对象"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class TensionSlingshotRequest:
    """张力弹弓请求 DTO"""
    novel_id: str
    chapter_number: int
    stuck_reason: Optional[str] = None


@dataclass
class TensionDiagnosis:
    """张力诊断结果 DTO"""
    diagnosis: str
    tension_level: str  # low/medium/high
    missing_elements: List[str]
    suggestions: List[str]
