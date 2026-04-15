from enum import Enum


class TensionLevel(int, Enum):
    """张力等级"""
    LOW = 1      # 平缓
    MEDIUM = 2   # 中等
    HIGH = 3     # 紧张
    PEAK = 4     # 极度紧张
