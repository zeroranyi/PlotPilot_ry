import pytest
from domain.novel.value_objects.tension_level import TensionLevel


def test_tension_level_enum_values():
    """测试 TensionLevel 枚举值"""
    assert TensionLevel.LOW == 1
    assert TensionLevel.MEDIUM == 2
    assert TensionLevel.HIGH == 3
    assert TensionLevel.PEAK == 4


def test_tension_level_comparison():
    """测试 TensionLevel 比较操作"""
    assert TensionLevel.LOW < TensionLevel.MEDIUM
    assert TensionLevel.MEDIUM < TensionLevel.HIGH
    assert TensionLevel.HIGH < TensionLevel.PEAK
    assert TensionLevel.PEAK > TensionLevel.LOW


def test_tension_level_equality():
    """测试 TensionLevel 相等性"""
    assert TensionLevel.LOW == TensionLevel.LOW
    assert TensionLevel.MEDIUM != TensionLevel.HIGH


def test_tension_level_from_value():
    """测试从值创建 TensionLevel"""
    assert TensionLevel(1) == TensionLevel.LOW
    assert TensionLevel(2) == TensionLevel.MEDIUM
    assert TensionLevel(3) == TensionLevel.HIGH
    assert TensionLevel(4) == TensionLevel.PEAK
