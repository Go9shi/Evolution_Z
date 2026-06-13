from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import SCREEN_W

if TYPE_CHECKING:
    from entities.player import Player
    from systems.quest_system import QuestSystem

_PAD = 12
_BAR_W = 220
_BAR_H = 18
_GROUP_GAP = 26
_LABEL_DX = 8

_COL_BAR_BG = (40, 40, 48)
_COL_BORDER = (15, 15, 20)
_COL_HP = (210, 60, 60)
_COL_HUNGER = (210, 160, 60)
_COL_XP = (90, 170, 230)
_COL_TEXT = (230, 230, 235)
_COL_QUEST_TITLE = (220, 220, 90)
_COL_QUEST_PROGRESS = (150, 200, 255)

_QUEST_PANEL_W = 320


class HUD:
    """Постоянный игровой оверлей: HP, голод, уровень/XP, трекер активных квестов.

    Чистый UI-слой: не хранит игрового состояния и не кэширует объекты — каждый кадр
    читает данные из переданных в draw() player и quest_system через их публичный API.
    Не является BaseScreen и не участвует в GameStateManager (рисуется поверх GameScreen).
    """

    def __init__(self) -> None:
        self._font = pygame.font.SysFont("monospace", 16)
        self._font_small = pygame.font.SysFont("monospace", 14)

    def draw(self, surface: pygame.Surface, player: Player, quest_system: QuestSystem) -> None:
        """Отрисовать HUD по актуальным данным игрока и системы квестов."""
        self._draw_status(surface, player)
        self._draw_quests(surface, quest_system)

    # ── статус игрока (слева сверху) ─────────────────────────────────────────

    def _draw_status(self, surface: pygame.Surface, player: Player) -> None:
        y = _PAD
        health = player.health
        self._draw_bar(
            surface, _PAD, y, health.percentage, _COL_HP,
            f"HP {int(health.current)}/{int(health.maximum)}",
        )
        y += _GROUP_GAP
        self._draw_bar(
            surface, _PAD, y, player.hunger.percentage, _COL_HUNGER, "Hunger",
        )
        y += _GROUP_GAP
        exp = player.experience
        total_for_next = exp.current_xp + exp.xp_to_next_level
        fraction = exp.current_xp / total_for_next if total_for_next > 0 else 0.0
        self._draw_bar(
            surface, _PAD, y, fraction, _COL_XP,
            f"Lv {exp.current_level}  XP {exp.current_xp}/{total_for_next}",
        )

    def _draw_bar(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        fraction: float,
        fill: tuple[int, int, int],
        label: str,
    ) -> None:
        """Нарисовать полоску с долей fraction (клампится в 0..1) и подпись справа."""
        clamped = max(0.0, min(1.0, fraction))
        pygame.draw.rect(surface, _COL_BAR_BG, (x, y, _BAR_W, _BAR_H))
        pygame.draw.rect(surface, fill, (x, y, int(_BAR_W * clamped), _BAR_H))
        pygame.draw.rect(surface, _COL_BORDER, (x, y, _BAR_W, _BAR_H), 1)
        text = self._font.render(label, True, _COL_TEXT)
        surface.blit(text, (x + _BAR_W + _LABEL_DX, y))

    # ── трекер квестов (справа сверху) ───────────────────────────────────────

    def _draw_quests(self, surface: pygame.Surface, quest_system: QuestSystem) -> None:
        quests = quest_system.active_quests
        if not quests:
            return
        x = SCREEN_W - _PAD - _QUEST_PANEL_W
        y = _PAD
        header = self._font.render("QUESTS", True, _COL_QUEST_TITLE)
        surface.blit(header, (x, y))
        y += 22
        for quest in quests:
            title = self._font_small.render(quest.title, True, _COL_QUEST_TITLE)
            surface.blit(title, (x, y))
            y += 18
            for objective in quest.objectives:
                line = self._font_small.render(f"  {objective.progress}", True, _COL_QUEST_PROGRESS)
                surface.blit(line, (x, y))
                y += 18
            y += 6
