"""Tests for Sprint 7C: SkillTreeUI navigation, selection, upgrade, close, display."""
from __future__ import annotations

import pygame

from data.player_data import PlayerData
from entities.player import Player
from main import GameStateManager
from systems.skill_tree import MAX_SKILL_LEVEL, SkillType
from ui.base_screen import BaseScreen
from ui.skill_tree_ui import SkillTreeUI, _SKILLS


# ── helpers ────────────────────────────────────────────────────────────────────


def make_player() -> Player:
    config = PlayerData(
        max_health=100,
        speed=200.0,
        width=32,
        height=32,
        max_hunger=100.0,
        hunger_decay_rate=0.0,
        hunger_damage_rate=5.0,
    )
    return Player(0.0, 0.0, config)


def make_ui(player: Player | None = None, on_close: object = None) -> SkillTreeUI:
    if player is None:
        player = make_player()
    if on_close is None:
        on_close = lambda: None  # noqa: E731
    return SkillTreeUI(player, on_close)  # type: ignore[arg-type]


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def mouse_event() -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (0, 0)})


# ── TestInitialState ───────────────────────────────────────────────────────────


class TestInitialState:
    def test_selected_skill_is_first(self) -> None:
        ui = make_ui()
        assert ui.selected_skill == _SKILLS[0]

    def test_selected_skill_type(self) -> None:
        ui = make_ui()
        assert isinstance(ui.selected_skill, SkillType)

    def test_first_skill_is_max_health(self) -> None:
        ui = make_ui()
        assert ui.selected_skill == SkillType.MAX_HEALTH


# ── TestNavigation ─────────────────────────────────────────────────────────────


class TestNavigation:
    def test_down_advances_selection(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_skill == _SKILLS[1]

    def test_down_twice_reaches_third(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_skill == _SKILLS[2]

    def test_down_wraps_around_to_first(self) -> None:
        ui = make_ui()
        for _ in range(len(_SKILLS)):
            ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_skill == _SKILLS[0]

    def test_up_from_start_wraps_to_last(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_skill == _SKILLS[-1]

    def test_up_after_down_returns_to_start(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_skill == _SKILLS[0]

    def test_unrelated_event_type_ignored(self) -> None:
        ui = make_ui()
        ui.handle_event(mouse_event())
        assert ui.selected_skill == _SKILLS[0]

    def test_unrelated_key_ignored(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_SPACE))
        assert ui.selected_skill == _SKILLS[0]


# ── TestClose ─────────────────────────────────────────────────────────────────


class TestClose:
    def test_esc_calls_on_close(self) -> None:
        called: list[int] = []
        ui = make_ui(on_close=lambda: called.append(1))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert len(called) == 1

    def test_esc_calls_exactly_once(self) -> None:
        called: list[int] = []
        ui = make_ui(on_close=lambda: called.append(1))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert len(called) == 2

    def test_other_keys_do_not_close(self) -> None:
        called: list[int] = []
        ui = make_ui(on_close=lambda: called.append(1))
        for k in (pygame.K_DOWN, pygame.K_UP, pygame.K_RETURN, pygame.K_SPACE):
            ui.handle_event(key_event(k))
        assert len(called) == 0


# ── TestUpgrade ───────────────────────────────────────────────────────────────


class TestUpgrade:
    def test_enter_upgrades_selected_skill(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        ui = make_ui(player)
        ui.handle_event(key_event(pygame.K_RETURN))
        assert player.skill_tree.get_level(_SKILLS[0]) == 1

    def test_enter_without_points_does_nothing(self) -> None:
        player = make_player()
        ui = make_ui(player)
        ui.handle_event(key_event(pygame.K_RETURN))
        for skill in SkillType:
            assert player.skill_tree.get_level(skill) == 0

    def test_enter_decrements_available_points(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        player.skill_tree.add_point()
        ui = make_ui(player)
        ui.handle_event(key_event(pygame.K_RETURN))
        assert player.skill_tree.available_points == 1

    def test_upgrade_second_skill_after_navigation(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        ui = make_ui(player)
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))
        assert player.skill_tree.get_level(_SKILLS[1]) == 1
        assert player.skill_tree.get_level(_SKILLS[0]) == 0

    def test_upgrade_third_skill_after_navigation(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        ui = make_ui(player)
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))
        assert player.skill_tree.get_level(_SKILLS[2]) == 1
        assert player.skill_tree.get_level(_SKILLS[0]) == 0

    def test_maxed_skill_cannot_be_upgraded_further(self) -> None:
        player = make_player()
        ui = make_ui(player)
        for _ in range(MAX_SKILL_LEVEL):
            player.skill_tree.add_point()
            ui.handle_event(key_event(pygame.K_RETURN))
        player.skill_tree.add_point()
        ui.handle_event(key_event(pygame.K_RETURN))
        assert player.skill_tree.get_level(_SKILLS[0]) == MAX_SKILL_LEVEL
        assert player.skill_tree.available_points == 1


# ── TestAvailablePoints ───────────────────────────────────────────────────────


class TestAvailablePoints:
    def test_reflects_zero_points_initially(self) -> None:
        player = make_player()
        ui = make_ui(player)
        assert ui._player.skill_tree.available_points == 0

    def test_reflects_added_points(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        player.skill_tree.add_point()
        ui = make_ui(player)
        assert ui._player.skill_tree.available_points == 2

    def test_points_decrease_after_upgrade(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        ui = make_ui(player)
        ui.handle_event(key_event(pygame.K_RETURN))
        assert player.skill_tree.available_points == 0

    def test_level_up_grants_point_visible_in_ui(self) -> None:
        player = make_player()
        ui = make_ui(player)
        player.add_xp(100)  # required_xp(1)=100 → level 2 → +1 point
        assert ui._player.skill_tree.available_points == 1


# ── TestDrawAndUpdate ─────────────────────────────────────────────────────────


class TestDrawAndUpdate:
    def test_update_does_not_raise(self) -> None:
        ui = make_ui()
        ui.update(0.016)

    def test_draw_does_not_raise(self) -> None:
        ui = make_ui()
        surface = pygame.Surface((1280, 720))
        ui.draw(surface)

    def test_draw_with_points_does_not_raise(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        ui = make_ui(player)
        surface = pygame.Surface((1280, 720))
        ui.draw(surface)

    def test_draw_with_upgraded_skill_does_not_raise(self) -> None:
        player = make_player()
        player.skill_tree.add_point()
        player.skill_tree.upgrade(SkillType.MAX_HEALTH, player)
        ui = make_ui(player)
        surface = pygame.Surface((1280, 720))
        ui.draw(surface)


# ── TestGameStateManagerDepth ─────────────────────────────────────────────────
# Регрессия: баг двойной обработки ESC (Sprint 7C).
# ESC при открытом SkillTreeUI завершал игру, т.к. main.py всегда выставлял
# _running=False на K_ESCAPE. Фикс: проверять depth <= 1 перед выходом.


class TestGameStateManagerDepth:
    def test_depth_zero_when_empty(self) -> None:
        sm = GameStateManager()
        assert sm.depth == 0

    def test_depth_one_after_single_push(self) -> None:
        sm = GameStateManager()
        sm.push(BaseScreen())
        assert sm.depth == 1

    def test_depth_two_with_overlay(self) -> None:
        sm = GameStateManager()
        sm.push(BaseScreen())
        sm.push(BaseScreen())
        assert sm.depth == 2

    def test_depth_decreases_on_pop(self) -> None:
        sm = GameStateManager()
        sm.push(BaseScreen())
        sm.push(BaseScreen())
        sm.pop()
        assert sm.depth == 1

    def test_pop_on_empty_is_safe(self) -> None:
        sm = GameStateManager()
        sm.pop()
        assert sm.depth == 0


# ── TestEscRoutingRegression ──────────────────────────────────────────────────
# Воспроизводит баг и проверяет поведение после фикса.
# main.py не тестируется напрямую (требует display), но инварианты,
# на которых строится фикс, проверяются здесь.


class TestEscRoutingRegression:
    def test_esc_pops_overlay_base_screen_remains(self) -> None:
        """ESC при открытом SkillTreeUI закрывает только UI, базовый экран остаётся."""
        sm = GameStateManager()
        base = BaseScreen()
        sm.push(base)

        player = make_player()
        ui = SkillTreeUI(player, sm.pop)
        sm.push(ui)

        assert sm.depth == 2
        ui.handle_event(key_event(pygame.K_ESCAPE))

        assert sm.depth == 1
        assert sm.current is base

    def test_depth_greater_than_one_signals_overlay_open(self) -> None:
        """depth > 1 — признак открытого оверлея; main.py НЕ должен выходить из игры."""
        sm = GameStateManager()
        sm.push(BaseScreen())  # базовый экран
        player = make_player()
        sm.push(SkillTreeUI(player, sm.pop))

        assert sm.depth > 1  # инвариант для проверки в main._handle_events

    def test_esc_on_base_screen_alone_signals_quit(self) -> None:
        """depth == 1 — только базовый экран; main.py ДОЛЖЕН выходить из игры."""
        sm = GameStateManager()
        sm.push(BaseScreen())
        assert sm.depth == 1  # инвариант: выход разрешён

    def test_tab_open_esc_close_returns_to_base(self) -> None:
        """TAB → открыть SkillTreeUI → ESC → закрыть → стек вернулся к базовому."""
        sm = GameStateManager()
        base = BaseScreen()
        sm.push(base)

        # Симулируем Tab: открываем SkillTreeUI поверх базового экрана
        player = make_player()
        ui = SkillTreeUI(player, sm.pop)
        sm.push(ui)
        assert sm.depth == 2
        assert sm.current is ui

        # ESC закрывает SkillTreeUI
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert sm.depth == 1
        assert sm.current is base

    def test_reopen_after_close_works(self) -> None:
        """После закрытия SkillTreeUI можно открыть снова."""
        sm = GameStateManager()
        base = BaseScreen()
        sm.push(base)
        player = make_player()

        # Первое открытие и закрытие
        ui1 = SkillTreeUI(player, sm.pop)
        sm.push(ui1)
        ui1.handle_event(key_event(pygame.K_ESCAPE))
        assert sm.depth == 1

        # Повторное открытие
        ui2 = SkillTreeUI(player, sm.pop)
        sm.push(ui2)
        assert sm.depth == 2
        assert sm.current is ui2

    def test_on_close_called_exactly_once_on_esc(self) -> None:
        """on_close вызывается ровно один раз на одно нажатие ESC — не дважды."""
        calls: list[int] = []
        player = make_player()
        ui = SkillTreeUI(player, lambda: calls.append(1))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert len(calls) == 1
