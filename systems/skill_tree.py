from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from systems.event_bus import EventBus

if TYPE_CHECKING:
    from entities.player import Player

HP_PER_LEVEL: int = 20
HUNGER_REDUCTION_PER_LEVEL: float = 0.5
DAMAGE_PER_LEVEL: float = 5.0
MAX_SKILL_LEVEL: int = 5


class SkillType(Enum):
    """Типы навыков в дереве прокачки игрока."""

    MAX_HEALTH = auto()
    HUNGER_EFFICIENCY = auto()
    PISTOL_DAMAGE = auto()


class SkillTree:
    """Дерево навыков. Хранит очки умений и применяет бонусы к игроку при прокачке."""

    def __init__(self) -> None:
        self._available_points: int = 0
        self._skill_levels: dict[SkillType, int] = {skill: 0 for skill in SkillType}

    @property
    def available_points(self) -> int:
        """Количество доступных очков навыков."""
        return self._available_points

    def get_level(self, skill: SkillType) -> int:
        """Текущий уровень указанного навыка."""
        return self._skill_levels[skill]

    def add_point(self) -> None:
        """Добавить одно очко навыка. Вызывается при повышении уровня игрока."""
        self._available_points += 1

    def can_upgrade(self, skill: SkillType) -> bool:
        """True если есть очки и навык не достиг максимального уровня."""
        return self._available_points > 0 and self._skill_levels[skill] < MAX_SKILL_LEVEL

    def upgrade(self, skill: SkillType, player: Player) -> bool:
        """Потратить очко на прокачку навыка. Возвращает True при успехе."""
        if not self.can_upgrade(skill):
            return False
        self._available_points -= 1
        self._skill_levels[skill] += 1
        self._apply_effect(skill, player)
        EventBus.emit("skill_upgraded", {"skill": skill, "level": self._skill_levels[skill]})
        return True

    def _apply_effect(self, skill: SkillType, player: Player) -> None:
        """Применить игровой эффект навыка к игроку."""
        if skill == SkillType.MAX_HEALTH:
            player.health.increase_maximum(HP_PER_LEVEL)
        elif skill == SkillType.HUNGER_EFFICIENCY:
            player.hunger.reduce_decay_rate(HUNGER_REDUCTION_PER_LEVEL)
        elif skill == SkillType.PISTOL_DAMAGE:
            player.apply_weapon_damage_bonus(DAMAGE_PER_LEVEL)
