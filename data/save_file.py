from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SaveData:
    """Снимок сохраняемого состояния игры. Хранит только данные, не игровые объекты.

    Минимальный вертикальный срез (Sprint 10A): прогресс игрока (XP/уровень), уровни
    навыков, id предметов инвентаря, id активных/завершённых квестов, id открытого лора.
    Сериализуется в JSON через `to_dict` / `from_dict`.
    """

    player_xp: int = 0
    player_level: int = 1
    skill_levels: dict[str, int] = field(default_factory=dict)
    inventory_item_ids: list[str] = field(default_factory=list)
    active_quest_ids: list[str] = field(default_factory=list)
    completed_quest_ids: list[str] = field(default_factory=list)
    unlocked_lore_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Преобразовать в JSON-совместимый словарь."""
        return {
            "player": {"xp": self.player_xp, "level": self.player_level},
            "skills": dict(self.skill_levels),
            "inventory": list(self.inventory_item_ids),
            "quests": {
                "active": list(self.active_quest_ids),
                "completed": list(self.completed_quest_ids),
            },
            "lore": list(self.unlocked_lore_ids),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SaveData:
        """Построить SaveData из словаря. Отсутствующие/битые ключи дают пустые значения."""
        player = raw.get("player")
        if not isinstance(player, dict):
            player = {}
        quests = raw.get("quests")
        if not isinstance(quests, dict):
            quests = {}
        skills_raw = raw.get("skills")
        if not isinstance(skills_raw, dict):
            skills_raw = {}

        return cls(
            player_xp=int(player.get("xp", 0)),
            player_level=int(player.get("level", 1)),
            skill_levels={str(k): int(v) for k, v in skills_raw.items()},
            inventory_item_ids=list(raw.get("inventory", []) or []),
            active_quest_ids=list(quests.get("active", []) or []),
            completed_quest_ids=list(quests.get("completed", []) or []),
            unlocked_lore_ids=list(raw.get("lore", []) or []),
        )
