from dataclasses import dataclass

import pygame


@dataclass
class TriggerZone:
    """Зона-триггер из TMX object-слоя `triggers` (Sprint 13B). Только данные + флаг active.

    При входе игрока в `rect` эмитится `event_name` через EventBus (логику держит GameScreen).
    Single activation: после первой активации `active=False`, повторный вход не эмитит снова.
    """

    trigger_id: str
    event_name: str
    x: float
    y: float
    width: float
    height: float
    active: bool = True

    @property
    def rect(self) -> pygame.Rect:
        """AABB зоны для проверки входа игрока."""
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
