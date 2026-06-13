from __future__ import annotations

from typing import Any, Callable

import pygame

from settings import SCREEN_H, SCREEN_W, TITLE
from ui.base_screen import BaseScreen
from ui.game_screen import GameScreen

_COL_BG = (12, 14, 20)
_COL_TITLE = (210, 90, 90)
_COL_SELECTED = (120, 220, 255)
_COL_NORMAL = (170, 170, 175)
_COL_DISABLED = (90, 90, 95)
_COL_HINT = (110, 110, 110)

_NEW_GAME = "New Game"
_CONTINUE = "Continue"
_QUIT = "Quit"
_ITEMS: tuple[str, ...] = (_NEW_GAME, _CONTINUE, _QUIT)


class MainMenuScreen(BaseScreen):
    """Главное меню: New Game / Continue / Quit. UP/DOWN — выбор, ENTER — подтвердить.

    New Game и Continue заменяют меню на GameScreen через стек экранов (игра остаётся
    на глубине 1, ESC-выход работает как раньше). Continue использует существующий
    SaveSystem через `GameScreen.load_game` и активен только при наличии файла сейва.
    Quit вызывает переданный колбэк завершения приложения (паттерн on_close проекта).
    """

    def __init__(self, state_manager: Any, on_quit: Callable[[], None]) -> None:
        self._state_manager = state_manager
        self._on_quit = on_quit
        self._selected_index: int = 0
        self._font_title = pygame.font.SysFont("monospace", 48, bold=True)
        self._font_item = pygame.font.SysFont("monospace", 28)
        self._font_hint = pygame.font.SysFont("monospace", 16)

    @property
    def selected_index(self) -> int:
        """Индекс выделенного пункта меню."""
        return self._selected_index

    def handle_event(self, event: pygame.event.Event) -> None:
        """UP/DOWN — навигация по пунктам (циклическая); ENTER — активировать пункт."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_UP:
            self._move(-1)
        elif event.key == pygame.K_DOWN:
            self._move(1)
        elif event.key == pygame.K_RETURN:
            self._activate()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка меню; недоступный Continue (нет сейва) показывается приглушённым."""
        surface.fill(_COL_BG)
        title = self._font_title.render(TITLE, True, _COL_TITLE)
        surface.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 3)))

        has_save = self._has_save()
        y = SCREEN_H // 2
        for i, item in enumerate(_ITEMS):
            color = _COL_SELECTED if i == self._selected_index else _COL_NORMAL
            if item == _CONTINUE and not has_save:
                color = _COL_DISABLED
            arrow = "> " if i == self._selected_index else "  "
            text = self._font_item.render(f"{arrow}{item}", True, color)
            surface.blit(text, text.get_rect(center=(SCREEN_W // 2, y)))
            y += 44

        hint = "UP / DOWN: navigate      ENTER: select      ESC: quit"
        hint_surf = self._font_hint.render(hint, True, _COL_HINT)
        surface.blit(hint_surf, (SCREEN_W // 2 - hint_surf.get_width() // 2, SCREEN_H - 50))

    # ── actions ──────────────────────────────────────────────────────────────

    def _activate(self) -> None:
        item = _ITEMS[self._selected_index]
        if item == _NEW_GAME:
            self._new_game()
        elif item == _CONTINUE:
            self._continue()
        else:
            self._on_quit()

    def _new_game(self) -> None:
        """Начать новую игру: заменить меню свежим GameScreen (без загрузки сейва)."""
        if self._state_manager is None:
            return
        self._state_manager.pop()
        self._state_manager.push(GameScreen(self._state_manager))

    def _continue(self) -> None:
        """Продолжить: при наличии сейва открыть GameScreen и восстановить состояние."""
        if self._state_manager is None or not self._has_save():
            return
        self._state_manager.pop()
        screen = GameScreen(self._state_manager)
        self._state_manager.push(screen)
        screen.load_game()

    def _move(self, delta: int) -> None:
        self._selected_index = (self._selected_index + delta) % len(_ITEMS)

    @staticmethod
    def _has_save() -> bool:
        """Есть ли файл сохранения (единый файл GameScreen, без слотов)."""
        return GameScreen._SAVE_PATH.exists()
