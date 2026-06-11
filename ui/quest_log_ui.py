from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from data.quest_data import QuestStatus
from settings import SCREEN_H, SCREEN_W
from ui.base_screen import BaseScreen

if TYPE_CHECKING:
    from systems.quest_system import QuestSystem

_COL_BG = (15, 20, 15)
_COL_TITLE = (220, 220, 60)
_COL_SELECTED = (100, 255, 150)
_COL_NORMAL = (180, 180, 180)
_COL_DESC = (140, 140, 150)
_COL_PROGRESS = (120, 200, 255)
_COL_META = (150, 170, 140)
_COL_HINT = (110, 110, 110)


class QuestLogUI(BaseScreen):
    """Текстовый оверлей журнала квестов. UP/DOWN — навигация, ESC — закрыть.

    Только для чтения: отображает активные квесты через публичный API QuestSystem,
    не хранит и не изменяет их состояние.
    """

    def __init__(self, quest_system: QuestSystem, on_close: Callable[[], None]) -> None:
        self._quest_system = quest_system
        self._on_close = on_close
        self._selected_index: int = 0
        self._font_title = pygame.font.SysFont("monospace", 30, bold=True)
        self._font_body = pygame.font.SysFont("monospace", 22)
        self._font_hint = pygame.font.SysFont("monospace", 16)

    @property
    def selected_index(self) -> int:
        """Индекс выделенного квеста в списке активных."""
        return self._selected_index

    def handle_event(self, event: pygame.event.Event) -> None:
        """UP/DOWN — навигация по активным квестам; ESC — закрыть."""
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
        """Отрисовка полупрозрачного оверлея со списком активных квестов."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.set_alpha(220)
        overlay.fill(_COL_BG)
        surface.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        y = 60

        title_surf = self._font_title.render("─── QUEST LOG ───", True, _COL_TITLE)
        surface.blit(title_surf, (cx - title_surf.get_width() // 2, y))
        y += 60

        quests = self._quest_system.active_quests
        if not quests:
            empty_surf = self._font_body.render("No active quests.", True, _COL_HINT)
            surface.blit(empty_surf, (cx - empty_surf.get_width() // 2, y))
        else:
            self._draw_quests(surface, quests, cx - 300, y)

        hint = "UP / DOWN: navigate      ESC: close"
        hint_surf = self._font_hint.render(hint, True, _COL_HINT)
        surface.blit(hint_surf, (cx - hint_surf.get_width() // 2, SCREEN_H - 50))

    def _draw_quests(self, surface: pygame.Surface, quests: list, left_x: int, y: int) -> None:
        selected = self._selected_index % len(quests)
        for i, quest in enumerate(quests):
            is_selected = i == selected
            color = _COL_SELECTED if is_selected else _COL_NORMAL
            arrow = "▶ " if is_selected else "  "
            checkbox = "[x]" if quest.status == QuestStatus.COMPLETED else "[ ]"
            header = self._font_body.render(f"{arrow}{checkbox} {quest.title}", True, color)
            surface.blit(header, (left_x, y))
            y += 32

            desc = self._font_hint.render(f"      {quest.description}", True, _COL_DESC)
            surface.blit(desc, (left_x, y))
            y += 26

            meta = self._format_meta(quest)
            if meta:
                meta_surf = self._font_hint.render(f"      {meta}", True, _COL_META)
                surface.blit(meta_surf, (left_x, y))
                y += 24

            for objective in quest.objectives:
                line = self._font_hint.render(
                    f"      Progress: {objective.progress}", True, _COL_PROGRESS
                )
                surface.blit(line, (left_x, y))
                y += 24
            y += 16

    @staticmethod
    def _format_meta(quest: object) -> str:
        """Собрать строку 'category @ location' из непустых narrative-полей квеста.

        Старые квесты без этих полей дают пустую строку — строка не отрисовывается.
        """
        category = getattr(quest, "category", "")
        location = getattr(quest, "location", "")
        parts: list[str] = []
        if category:
            parts.append(f"[{category}]")
        if location:
            parts.append(f"@ {location}")
        return " ".join(parts)

    def _move_selection(self, delta: int) -> None:
        count = len(self._quest_system.active_quests)
        if count == 0:
            self._selected_index = 0
            return
        self._selected_index = (self._selected_index + delta) % count
