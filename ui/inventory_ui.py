from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from settings import SCREEN_H, SCREEN_W
from ui.base_screen import BaseScreen

if TYPE_CHECKING:
    from core.item import Item
    from systems.inventory import Inventory

_COL_BG = (16, 20, 24)
_COL_TITLE = (180, 230, 200)
_COL_COUNT = (140, 180, 200)
_COL_SELECTED = (120, 255, 180)
_COL_NORMAL = (170, 170, 180)
_COL_DESC = (140, 140, 150)
_COL_HINT = (110, 110, 110)

_WRAP_WIDTH = 64  # символов в строке описания до переноса


class InventoryUI(BaseScreen):
    """Текстовый оверлей инвентаря. UP/DOWN — навигация, ESC — закрыть.

    Только для чтения: отображает предметы через публичный API Inventory
    (`items`), не хранит и не кэширует список — данные читаются напрямую.
    """

    def __init__(self, inventory: Inventory, on_close: Callable[[], None]) -> None:
        self._inventory = inventory
        self._on_close = on_close
        self._selected_index: int = 0
        self._font_title = pygame.font.SysFont("monospace", 30, bold=True)
        self._font_body = pygame.font.SysFont("monospace", 22)
        self._font_hint = pygame.font.SysFont("monospace", 16)

    @property
    def selected_index(self) -> int:
        """Индекс выделенного предмета в списке."""
        return self._selected_index

    def handle_event(self, event: pygame.event.Event) -> None:
        """UP/DOWN — навигация по предметам; ESC — закрыть."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._on_close()
        elif event.key == pygame.K_UP:
            self._move_selection(-1)
        elif event.key == pygame.K_DOWN:
            self._move_selection(1)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка полупрозрачного оверлея со списком предметов инвентаря."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.set_alpha(220)
        overlay.fill(_COL_BG)
        surface.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        y = 60

        title_surf = self._font_title.render("─── INVENTORY ───", True, _COL_TITLE)
        surface.blit(title_surf, (cx - title_surf.get_width() // 2, y))
        y += 44

        count_text = f"{self._inventory.count}/{self._inventory.capacity}"
        count_surf = self._font_hint.render(count_text, True, _COL_COUNT)
        surface.blit(count_surf, (cx - count_surf.get_width() // 2, y))
        y += 40

        items = self._inventory.items
        if not items:
            empty_surf = self._font_body.render("Inventory is empty.", True, _COL_HINT)
            surface.blit(empty_surf, (cx - empty_surf.get_width() // 2, y))
        else:
            self._draw_items(surface, items, cx - 320, y)

        hint = "UP / DOWN: navigate      ESC: close"
        hint_surf = self._font_hint.render(hint, True, _COL_HINT)
        surface.blit(hint_surf, (cx - hint_surf.get_width() // 2, SCREEN_H - 50))

    def _draw_items(
        self, surface: pygame.Surface, items: list[Item], left_x: int, y: int
    ) -> None:
        selected = self._selected_index % len(items)
        for i, item in enumerate(items):
            is_selected = i == selected
            color = _COL_SELECTED if is_selected else _COL_NORMAL
            arrow = "▶ " if is_selected else "  "
            header = self._font_body.render(f"{arrow}{item.name}", True, color)
            surface.blit(header, (left_x, y))
            y += 32

            if is_selected:
                for line in self._wrap(item.description, _WRAP_WIDTH):
                    line_surf = self._font_hint.render(f"      {line}", True, _COL_DESC)
                    surface.blit(line_surf, (left_x, y))
                    y += 22
            y += 8

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        """Разбить текст на строки не длиннее width символов по словам."""
        words = text.split()
        if not words:
            return [""]
        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            if len(current) + 1 + len(word) <= width:
                current = f"{current} {word}"
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def _move_selection(self, delta: int) -> None:
        count = len(self._inventory.items)
        if count == 0:
            self._selected_index = 0
            return
        self._selected_index = (self._selected_index + delta) % count
