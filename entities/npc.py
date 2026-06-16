from __future__ import annotations

import pygame

from core.game_object import GameObject
from settings import NPC_SIZE
from systems.asset_loader import AssetLoader


class NPC(GameObject):
    """Неигровой персонаж (Sprint 13A). Стоит на карте и выдаёт диалог; в бою не участвует.

    Один и тот же класс работает на любой карте — данные (npc_id/dialogue_id/позиция)
    приходят из TMX-слоя `npcs`. Рендер — спрайт `npc_<id>` через AssetLoader, иначе
    fallback-прямоугольник.
    """

    COLOR: tuple[int, int, int] = (90, 160, 220)

    def __init__(self, x: float, y: float, npc_id: str, dialogue_id: str) -> None:
        super().__init__(x, y)
        self._npc_id: str = npc_id
        self._dialogue_id: str = dialogue_id

    @property
    def npc_id(self) -> str:
        """Идентификатор NPC."""
        return self._npc_id

    @property
    def dialogue_id(self) -> str:
        """Id диалога, который открывается при взаимодействии."""
        return self._dialogue_id

    @property
    def rect(self) -> pygame.Rect:
        """AABB для рендера (центрирован на позиции)."""
        half = NPC_SIZE // 2
        return pygame.Rect(int(self.pos.x) - half, int(self.pos.y) - half, NPC_SIZE, NPC_SIZE)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка спрайтом `npc_<id>` (или fallback-прямоугольником при отсутствии PNG)."""
        screen_rect = self.rect.move(-int(offset.x), -int(offset.y))
        if AssetLoader.draw_sprite(surface, f"npc_{self._npc_id}", screen_rect):
            return
        pygame.draw.rect(surface, self.COLOR, screen_rect)
