from __future__ import annotations

from typing import TYPE_CHECKING

from systems.event_bus import EventBus

if TYPE_CHECKING:
    from core.item import Item
    from entities.player import Player


class Inventory:
    """Инвентарь игрока. Хранит предметы и делегирует использование через item.use(player)."""

    def __init__(self, capacity: int = 20) -> None:
        self._items: list[Item] = []
        self._capacity: int = capacity

    @property
    def items(self) -> list[Item]:
        """Копия списка предметов в инвентаре."""
        return list(self._items)

    @property
    def capacity(self) -> int:
        """Максимальное количество предметов."""
        return self._capacity

    @property
    def count(self) -> int:
        """Текущее количество предметов."""
        return len(self._items)

    def is_full(self) -> bool:
        """True если инвентарь заполнен до предела."""
        return self.count >= self._capacity

    def contains(self, item: Item) -> bool:
        """Есть ли данный предмет в инвентаре."""
        return item in self._items

    def add_item(self, item: Item) -> bool:
        """Добавить предмет. Возвращает False если инвентарь полон."""
        if self.is_full():
            return False
        self._items.append(item)
        EventBus.emit("inventory_item_added", {"item": item})
        return True

    def remove_item(self, item: Item) -> bool:
        """Удалить конкретный предмет. Возвращает False если предмет не найден."""
        if item not in self._items:
            return False
        self._items.remove(item)
        EventBus.emit("inventory_item_removed", {"item": item})
        return True

    def use_item(self, item: Item, player: Player) -> bool:
        """Использовать предмет на игроке. Удаляет из инвентаря если item.use() вернул True."""
        if item not in self._items:
            return False
        consumed = item.use(player)
        if consumed:
            self._items.remove(item)
            EventBus.emit("item_used", {"item": item})
        return consumed
