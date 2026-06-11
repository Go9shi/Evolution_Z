from __future__ import annotations

from typing import TYPE_CHECKING

from core.item import Item

if TYPE_CHECKING:
    from entities.player import Player


class FoodItem(Item):
    """Еда. Восстанавливает сытость игрока при использовании."""

    COLOR: tuple[int, int, int] = (210, 175, 50)

    def __init__(
        self,
        x: float,
        y: float,
        item_id: str,
        name: str,
        description: str,
        nutrition: float,
    ) -> None:
        super().__init__(x, y, item_id, name, description, stackable=False)
        self._nutrition: float = nutrition

    @property
    def nutrition(self) -> float:
        """Количество восстанавливаемой сытости."""
        return self._nutrition

    def use(self, player: Player) -> bool:
        """Съесть еду: восстановить сытость игрока. Всегда потребляет предмет."""
        player.hunger.consume(self._nutrition)
        return True
