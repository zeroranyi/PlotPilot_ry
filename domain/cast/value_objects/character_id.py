"""Character ID value object"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterId:
    """Character ID value object"""

    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Character ID cannot be empty")

    def __str__(self) -> str:
        return self.value
