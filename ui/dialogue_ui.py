from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from settings import SCREEN_H, SCREEN_W
from ui.base_screen import BaseScreen

if TYPE_CHECKING:
    from systems.dialogue import DialogueSystem

_COL_BG = (12, 14, 22)
_COL_SPEAKER = (220, 200, 90)
_COL_TEXT = (210, 210, 215)
_COL_SELECTED = (120, 220, 255)
_COL_NORMAL = (170, 170, 175)
_COL_CONTINUE = (130, 200, 140)
_COL_HINT = (110, 110, 110)
_COL_EMPTY = (110, 110, 110)


class DialogueUI(BaseScreen):
    """Текстовый оверлей диалога. UP/DOWN — выбор варианта, ENTER — подтвердить, ESC — закрыть.

    Только отображение и ввод: читает текущий узел через публичный API DialogueSystem
    и продвигает диалог его же методами (choose / advance). Не хранит копий состояния.
    """

    def __init__(self, dialogue_system: DialogueSystem, on_close: Callable[[], None]) -> None:
        self._dialogue_system = dialogue_system
        self._on_close = on_close
        self._selected_index: int = 0
        self._font_speaker = pygame.font.SysFont("monospace", 26, bold=True)
        self._font_body = pygame.font.SysFont("monospace", 22)
        self._font_hint = pygame.font.SysFont("monospace", 16)

    @property
    def selected_index(self) -> int:
        """Индекс выделенного варианта ответа в текущем узле."""
        return self._selected_index

    def handle_event(self, event: pygame.event.Event) -> None:
        """UP/DOWN — навигация по вариантам; ENTER — выбрать/продолжить; ESC — закрыть."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._on_close()
        elif event.key == pygame.K_UP:
            self._move_selection(-1)
        elif event.key == pygame.K_DOWN:
            self._move_selection(1)
        elif event.key == pygame.K_RETURN:
            self._confirm()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка полупрозрачного оверлея с репликой и вариантами ответа."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.set_alpha(220)
        overlay.fill(_COL_BG)
        surface.blit(overlay, (0, 0))

        left_x = SCREEN_W // 2 - 360
        y = SCREEN_H // 2 - 120

        node = self._dialogue_system.current_node
        if node is None:
            empty = self._font_body.render("...", True, _COL_EMPTY)
            surface.blit(empty, (left_x, y))
            return

        speaker_surf = self._font_speaker.render(f"{node.speaker}:", True, _COL_SPEAKER)
        surface.blit(speaker_surf, (left_x, y))
        y += 40

        text_surf = self._font_body.render(node.text, True, _COL_TEXT)
        surface.blit(text_surf, (left_x, y))
        y += 56

        if node.is_terminal:
            cont = self._font_body.render("▶ [ENTER] Continue", True, _COL_CONTINUE)
            surface.blit(cont, (left_x, y))
        else:
            selected = self._clamped_index(node.choices)
            for i, choice in enumerate(node.choices):
                is_selected = i == selected
                color = _COL_SELECTED if is_selected else _COL_NORMAL
                arrow = "▶ " if is_selected else "  "
                line = self._font_body.render(f"{arrow}{choice.text}", True, color)
                surface.blit(line, (left_x, y))
                y += 32

        hint = "UP / DOWN: navigate      ENTER: select      ESC: close"
        hint_surf = self._font_hint.render(hint, True, _COL_HINT)
        surface.blit(hint_surf, (SCREEN_W // 2 - hint_surf.get_width() // 2, SCREEN_H - 50))

    def _confirm(self) -> None:
        """ENTER: завершить диалог на терминальном узле или выбрать вариант ответа."""
        node = self._dialogue_system.current_node
        if node is None:
            return
        if node.is_terminal:
            self._dialogue_system.advance()
        else:
            self._dialogue_system.choose(self._clamped_index(node.choices))
        self._selected_index = 0

    def _move_selection(self, delta: int) -> None:
        node = self._dialogue_system.current_node
        count = len(node.choices) if node is not None else 0
        if count == 0:
            self._selected_index = 0
            return
        self._selected_index = (self._selected_index + delta) % count

    def _clamped_index(self, choices: list) -> int:
        """Текущий индекс, приведённый к диапазону вариантов узла."""
        if not choices:
            return 0
        return self._selected_index % len(choices)
