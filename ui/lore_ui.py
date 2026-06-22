from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from settings import SCREEN_H, SCREEN_W
from ui.base_screen import BaseScreen

if TYPE_CHECKING:
    from data.lore_data import LoreEntry
    from systems.lore import LoreSystem

_COL_BG = (18, 16, 24)
_COL_TITLE = (200, 170, 240)
_COL_SELECTED = (180, 220, 255)
_COL_NORMAL = (170, 170, 180)
_COL_CATEGORY = (150, 140, 170)
_COL_TEXT = (140, 140, 150)
_COL_HINT = (110, 110, 110)

_WRAP_WIDTH = 64  # символов в строке текста записи до переноса


class LoreUI(BaseScreen):
    """Текстовый оверлей журнала лора. UP/DOWN — навигация, ESC — закрыть.

    Только для чтения: отображает открытые записи через публичный API LoreSystem
    (`unlocked_entries`), не хранит и не кэширует их — данные читаются напрямую.
    """

    def __init__(self, lore_system: LoreSystem, on_close: Callable[[], None]) -> None:
        self._lore_system = lore_system
        self._on_close = on_close
        self._selected_index: int = 0
        self._font_title = pygame.font.SysFont("monospace", 30, bold=True)
        self._font_body = pygame.font.SysFont("monospace", 22)
        self._font_hint = pygame.font.SysFont("monospace", 16)

    @property
    def selected_index(self) -> int:
        """Индекс выделенной записи в списке открытых."""
        return self._selected_index

    def handle_event(self, event: pygame.event.Event) -> None:
        """UP/DOWN — навигация по открытым записям; ESC — закрыть."""
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
        """Отрисовка полупрозрачного оверлея со списком открытых записей лора."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.set_alpha(220)
        overlay.fill(_COL_BG)
        surface.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        y = 60

        title_surf = self._font_title.render("─── LORE ───", True, _COL_TITLE)
        surface.blit(title_surf, (cx - title_surf.get_width() // 2, y))
        y += 60

        entries = self._lore_system.unlocked_entries
        if not entries:
            empty_surf = self._font_body.render("No lore entries discovered.", True, _COL_HINT)
            surface.blit(empty_surf, (cx - empty_surf.get_width() // 2, y))
        else:
            self._draw_entries(surface, entries, cx - 320, y)

        hint = "UP / DOWN: navigate      ESC: close"
        hint_surf = self._font_hint.render(hint, True, _COL_HINT)
        surface.blit(hint_surf, (cx - hint_surf.get_width() // 2, SCREEN_H - 50))

    def _draw_entries(
        self, surface: pygame.Surface, entries: list[LoreEntry], left_x: int, y: int
    ) -> None:
        selected = self._selected_index % len(entries)
        for i, entry in enumerate(entries):
            is_selected = i == selected
            color = _COL_SELECTED if is_selected else _COL_NORMAL
            arrow = "▶ " if is_selected else "  "
            header = self._font_body.render(f"{arrow}{entry.title}", True, color)
            surface.blit(header, (left_x, y))
            y += 32

            if entry.category:
                cat_surf = self._font_hint.render(f"      [{entry.category}]", True, _COL_CATEGORY)
                surface.blit(cat_surf, (left_x, y))
                y += 24

            for line in self._wrap(entry.text, _WRAP_WIDTH):
                line_surf = self._font_hint.render(f"      {line}", True, _COL_TEXT)
                surface.blit(line_surf, (left_x, y))
                y += 22
            y += 16

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
        count = len(self._lore_system.unlocked_entries)
        if count == 0:
            self._selected_index = 0
            return
        self._selected_index = (self._selected_index + delta) % count
