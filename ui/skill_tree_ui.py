from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from settings import SCREEN_H, SCREEN_W
from systems.skill_tree import MAX_SKILL_LEVEL, SkillType
from ui.base_screen import BaseScreen

if TYPE_CHECKING:
    from entities.player import Player

_SKILL_LABELS: dict[SkillType, str] = {
    SkillType.MAX_HEALTH: "Max Health        (+20 HP per level)",
    SkillType.HUNGER_EFFICIENCY: "Hunger Efficiency  (-0.5 decay/s per level)",
    SkillType.PISTOL_DAMAGE: "Pistol Damage      (+5 dmg per level)",
}

_SKILLS: list[SkillType] = list(SkillType)

_COL_BG = (15, 15, 25)
_COL_TITLE = (220, 220, 60)
_COL_POINTS = (100, 255, 100)
_COL_SELECTED = (100, 200, 255)
_COL_NORMAL = (180, 180, 180)
_COL_MAXED = (100, 100, 100)
_COL_HINT = (110, 110, 110)
_COL_BAR_FILLED = (80, 160, 255)
_COL_BAR_EMPTY = (50, 50, 70)


class SkillTreeUI(BaseScreen):
    """Текстовый оверлей дерева навыков. UP/DOWN — навигация, ENTER — прокачка, ESC — закрыть."""

    def __init__(self, player: Player, on_close: Callable[[], None]) -> None:
        self._player = player
        self._on_close = on_close
        self._selected_index: int = 0
        self._font_title = pygame.font.SysFont("monospace", 30, bold=True)
        self._font_body = pygame.font.SysFont("monospace", 22)
        self._font_hint = pygame.font.SysFont("monospace", 16)

    @property
    def selected_skill(self) -> SkillType:
        """Текущий выделенный навык."""
        return _SKILLS[self._selected_index]

    def handle_event(self, event: pygame.event.Event) -> None:
        """UP/DOWN — навигация; ENTER — прокачать выбранный навык; ESC — закрыть."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._on_close()
        elif event.key == pygame.K_UP:
            self._selected_index = (self._selected_index - 1) % len(_SKILLS)
        elif event.key == pygame.K_DOWN:
            self._selected_index = (self._selected_index + 1) % len(_SKILLS)
        elif event.key == pygame.K_RETURN:
            self._player.skill_tree.upgrade(self.selected_skill, self._player)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка полупрозрачного оверлея с деревом навыков."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.set_alpha(220)
        overlay.fill(_COL_BG)
        surface.blit(overlay, (0, 0))

        cx = SCREEN_W // 2
        y = 70

        title_surf = self._font_title.render("─── SKILL TREE ───", True, _COL_TITLE)
        surface.blit(title_surf, (cx - title_surf.get_width() // 2, y))
        y += 52

        pts = self._player.skill_tree.available_points
        pts_color = _COL_POINTS if pts > 0 else _COL_HINT
        pts_surf = self._font_body.render(f"Available skill points: {pts}", True, pts_color)
        surface.blit(pts_surf, (cx - pts_surf.get_width() // 2, y))
        y += 50

        left_x = cx - 300

        for i, skill in enumerate(_SKILLS):
            level = self._player.skill_tree.get_level(skill)
            is_selected = i == self._selected_index
            is_maxed = level >= MAX_SKILL_LEVEL

            if is_maxed:
                color = _COL_MAXED
            elif is_selected:
                color = _COL_SELECTED
            else:
                color = _COL_NORMAL

            arrow = "▶ " if is_selected else "  "
            label = _SKILL_LABELS[skill]
            line = f"{arrow}{label}"
            text_surf = self._font_body.render(line, True, color)
            surface.blit(text_surf, (left_x, y))

            # уровень-бар справа
            bar_x = left_x + 480
            bar_y = y + 4
            bar_w, bar_h = 16, 16
            gap = 4
            for j in range(MAX_SKILL_LEVEL):
                rect = pygame.Rect(bar_x + j * (bar_w + gap), bar_y, bar_w, bar_h)
                bar_color = _COL_BAR_FILLED if j < level else _COL_BAR_EMPTY
                pygame.draw.rect(surface, bar_color, rect)

            lvl_label = self._font_hint.render(f"{level}/{MAX_SKILL_LEVEL}", True, color)
            surface.blit(lvl_label, (bar_x + MAX_SKILL_LEVEL * (bar_w + gap) + 8, bar_y))

            y += 48

        y += 16
        hint = "UP / DOWN: navigate      ENTER: upgrade      ESC: close"
        hint_surf = self._font_hint.render(hint, True, _COL_HINT)
        surface.blit(hint_surf, (cx - hint_surf.get_width() // 2, y))
