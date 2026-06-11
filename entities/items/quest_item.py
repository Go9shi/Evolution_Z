from __future__ import annotations

from typing import TYPE_CHECKING

from core.item import Item

if TYPE_CHECKING:
    from entities.player import Player


class QuestItem(Item):
    """Квестовый предмет (компонент вакцины). Хранится в инвентаре, не расходуется."""

    COLOR: tuple[int, int, int] = (80, 160, 255)

    def use(self, player: Player) -> bool:
        """Квестовые предметы не расходуются при использовании."""
        return False
