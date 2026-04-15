from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CharacterId:
    """人物 ID 值对象"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Character ID cannot be empty")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CharacterId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
