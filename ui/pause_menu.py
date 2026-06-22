from __future__ import annotations

from typing import Callable

import pygame

from settings import SCREEN_H, SCREEN_W
from ui.base_screen import BaseScreen

_COL_BG = (10, 12, 18)
_COL_TITLE = (210, 200, 90)
_COL_SELECTED = (120, 220, 255)
_COL_NORMAL = (170, 170, 175)
_COL_HINT = (110, 110, 110)

_RESUME = "Resume"
_SAVE = "Save Game"
_MAIN_MENU = "Main Menu"
_QUIT = "Quit"
_ITEMS: tuple[str, ...] = (_RESUME, _SAVE, _MAIN_MENU, _QUIT)


class PauseMenuScreen(BaseScreen):
    """Оверлей паузы поверх игры: Resume / Save Game / Main Menu / Quit.

    UP/DOWN — выбор (циклически), ENTER — подтвердить, ESC — Resume. Экран не владеет
    игровой логикой: каждое действие — переданный колбэк (паттерн on_close проекта),
    поэтому Save идёт через существующий GameScreen._save_game, а возврат в меню —
    через GameScreen._return_to_main_menu (cleanup стека делает GameStateManager.pop).
    """

    def __init__(
        self,
        on_resume: Callable[[], None],
        on_save: Callable[[], None],
        on_main_menu: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._actions: dict[str, Callable[[], None]] = {
            _RESUME: on_resume,
            _SAVE: on_save,
            _MAIN_MENU: on_main_menu,
            _QUIT: on_quit,
        }
        self._selected_index: int = 0
        self._font_title = pygame.font.SysFont("monospace", 36, bold=True)
        self._font_item = pygame.font.SysFont("monospace", 26)
        self._font_hint = pygame.font.SysFont("monospace", 16)

    @property
    def selected_index(self) -> int:
        """Индекс выделенного пункта меню паузы."""
        return self._selected_index

    def handle_event(self, event: pygame.event.Event) -> None:
        """UP/DOWN — навигация (циклическая); ENTER — активировать; ESC — Resume."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._actions[_RESUME]()
        elif event.key == pygame.K_UP:
            self._move(-1)
        elif event.key == pygame.K_DOWN:
            self._move(1)
        elif event.key == pygame.K_RETURN:
            self._actions[_ITEMS[self._selected_index]]()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Полупрозрачный оверлей с пунктами паузы по центру."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.set_alpha(220)
        overlay.fill(_COL_BG)
        surface.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        title = self._font_title.render("─── PAUSED ───", True, _COL_TITLE)
        surface.blit(title, title.get_rect(center=(cx, SCREEN_H // 3)))

        y = SCREEN_H // 2
        for i, item in enumerate(_ITEMS):
            color = _COL_SELECTED if i == self._selected_index else _COL_NORMAL
            arrow = "> " if i == self._selected_index else "  "
            text = self._font_item.render(f"{arrow}{item}", True, color)
            surface.blit(text, text.get_rect(center=(cx, y)))
            y += 44

        hint = "UP / DOWN: navigate      ENTER: select      ESC: resume"
        hint_surf = self._font_hint.render(hint, True, _COL_HINT)
        surface.blit(hint_surf, (cx - hint_surf.get_width() // 2, SCREEN_H - 50))

    def _move(self, delta: int) -> None:
        self._selected_index = (self._selected_index + delta) % len(_ITEMS)
