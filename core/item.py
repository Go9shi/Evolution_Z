from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from core.game_object import GameObject
from systems.asset_loader import AssetLoader

if TYPE_CHECKING:
    from entities.player import Player

_ITEM_SIZE: int = 16


class Item(GameObject, ABC):
    """Базовый класс предметов. Позиционированный объект, который можно подобрать и использовать."""

    COLOR: tuple[int, int, int] = (200, 200, 200)
    SPRITE: str | None = None  # переопределяется подклассами; None → fallback-квадрат

    def __init__(
        self,
        x: float,
        y: float,
        item_id: str,
        name: str,
        description: str,
        stackable: bool = False,
    ) -> None:
        super().__init__(x, y)
        self._item_id: str = item_id
        self._name: str = name
        self._description: str = description
        self._stackable: bool = stackable

    @property
    def item_id(self) -> str:
        """Уникальный идентификатор типа предмета."""
        return self._item_id

    @property
    def name(self) -> str:
        """Отображаемое имя предмета."""
        return self._name

    @property
    def description(self) -> str:
        """Описание предмета."""
        return self._description

    @property
    def stackable(self) -> bool:
        """Можно ли складывать предметы в стопку."""
        return self._stackable

    @property
    def rect(self) -> pygame.Rect:
        """AABB для обнаружения подбора предмета с земли."""
        half = _ITEM_SIZE // 2
        return pygame.Rect(int(self.pos.x) - half, int(self.pos.y) - half, _ITEM_SIZE, _ITEM_SIZE)

    @abstractmethod
    def use(self, player: Player) -> bool:
        """Использовать предмет на игроке. True — предмет потреблён и удаляется из инвентаря."""

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка предмета на земле спрайтом (или fallback-квадратом при отсутствии PNG)."""
        screen_rect = self.rect.move(-int(offset.x), -int(offset.y))
        if AssetLoader.draw_sprite(surface, self.SPRITE, screen_rect):
            return
        screen_x = int(self.pos.x - offset.x)
        screen_y = int(self.pos.y - offset.y)
        half = _ITEM_SIZE // 2
        pygame.draw.rect(
            surface,
            self.COLOR,
            pygame.Rect(screen_x - half, screen_y - half, _ITEM_SIZE, _ITEM_SIZE),
        )
