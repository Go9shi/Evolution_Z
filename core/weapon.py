from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from data.weapon_config import WeaponConfig

if TYPE_CHECKING:
    from entities.bullet import Bullet


class Weapon(ABC):
    """Абстрактный базовый класс оружия. Управляет кулдауном и делегирует выстрел подклассам."""

    def __init__(self, config: WeaponConfig) -> None:
        self._config: WeaponConfig = config
        self._cooldown: float = 0.0

    @property
    def can_fire(self) -> bool:
        """Готово ли оружие к выстрелу (кулдаун истёк)."""
        return self._cooldown <= 0.0

    def update(self, dt: float) -> None:
        """Уменьшить кулдаун на dt секунд."""
        self._cooldown = max(0.0, self._cooldown - dt)

    @abstractmethod
    def fire(self, pos: pygame.Vector2, direction: pygame.Vector2) -> list[Bullet]:
        """Произвести выстрел. Возвращает список созданных пуль (пустой при кулдауне)."""
