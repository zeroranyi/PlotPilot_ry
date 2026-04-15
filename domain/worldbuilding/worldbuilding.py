"""
Domain entity for Worldbuilding (世界观构建)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Worldbuilding:
    """世界观构建实体 - 基于专业小说家的5维度框架"""

    id: str
    novel_id: str

    # 1. 核心法则与底层逻辑 (The Rules)
    power_system: str = ""           # 力量体系/科技树
    physics_rules: str = ""          # 物理规律
    magic_tech: str = ""             # 魔法/科技机制

    # 2. 地理与生态环境 (Geography & Ecology)
    terrain: str = ""                # 地形
    climate: str = ""                # 气候
    resources: str = ""              # 资源分布
    ecology: str = ""                # 生态链

    # 3. 社会结构与权力分配 (Society & Power)
    politics: str = ""               # 政治体制
    economy: str = ""                # 经济模式
    class_system: str = ""           # 阶级系统

    # 4. 历史、信仰与文化 (History & Culture)
    history: str = ""                # 关键历史事件
    religion: str = ""               # 宗教信仰
    taboos: str = ""                 # 文化禁忌

    # 5. 沉浸感细节 (Daily Life)
    food_clothing: str = ""          # 衣食住行
    language_slang: str = ""         # 俚语口音
    entertainment: str = ""          # 娱乐方式

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def core_rules(self) -> dict:
        return {
            "power_system": self.power_system,
            "physics_rules": self.physics_rules,
            "magic_tech": self.magic_tech,
        }

    @property
    def geography(self) -> dict:
        return {
            "terrain": self.terrain,
            "climate": self.climate,
            "resources": self.resources,
            "ecology": self.ecology,
        }

    @property
    def society(self) -> dict:
        return {
            "politics": self.politics,
            "economy": self.economy,
            "class_system": self.class_system,
        }

    @property
    def culture(self) -> dict:
        return {
            "history": self.history,
            "religion": self.religion,
            "taboos": self.taboos,
        }

    @property
    def daily_life(self) -> dict:
        return {
            "food_clothing": self.food_clothing,
            "language_slang": self.language_slang,
            "entertainment": self.entertainment,
        }

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "novel_id": self.novel_id,

            # Core Rules
            "core_rules": {
                "power_system": self.power_system,
                "physics_rules": self.physics_rules,
                "magic_tech": self.magic_tech,
            },

            # Geography
            "geography": {
                "terrain": self.terrain,
                "climate": self.climate,
                "resources": self.resources,
                "ecology": self.ecology,
            },

            # Society
            "society": {
                "politics": self.politics,
                "economy": self.economy,
                "class_system": self.class_system,
            },

            # Culture
            "culture": {
                "history": self.history,
                "religion": self.religion,
                "taboos": self.taboos,
            },

            # Daily Life
            "daily_life": {
                "food_clothing": self.food_clothing,
                "language_slang": self.language_slang,
                "entertainment": self.entertainment,
            },

            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }
