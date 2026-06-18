"""Tests for Sprint 10F: EventBus cleanup / GameScreen teardown — no subscriber accumulation."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from main import GameStateManager
from systems.event_bus import EventBus
from ui.game_screen import GameScreen
from ui.main_menu import MainMenuScreen

# GameScreen(4) + Player(1) + QuestSystem(1)
EXPECTED_SUBS = 6


# ── helpers ───────────────────────────────────────────────────────────────────


def total_subs() -> int:
    """Суммарное число активных подписчиков EventBus (по всем событиям)."""
    return sum(len(callbacks) for callbacks in EventBus._listeners.values())


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def write_save(xp: int) -> None:
    """Создать файл сейва, не оставив подписчиков (throwaway убирается cleanup)."""
    throwaway = GameScreen()
    throwaway._player.add_xp(xp)
    throwaway._save_game()
    throwaway.cleanup()


@pytest.fixture
def save_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "savegame.json"
    monkeypatch.setattr(GameScreen, "_SAVE_PATH", path)
    return path


# ── Подписки ─────────────────────────────────────────────────────────────────


class TestSubscriptions:
    def test_gamescreen_registers_subscriptions(self) -> None:
        assert total_subs() == 0  # conftest очищает шину
        GameScreen()
        assert total_subs() == EXPECTED_SUBS

    def test_entity_died_has_two_listeners(self) -> None:
        GameScreen()
        assert len(EventBus._listeners["entity_died"]) == 2  # GameScreen + QuestSystem


# ── Cleanup ──────────────────────────────────────────────────────────────────


class TestCleanup:
    def test_cleanup_removes_all_subscriptions(self) -> None:
        screen = GameScreen()
        screen.cleanup()
        assert total_subs() == 0

    def test_cleanup_is_idempotent(self) -> None:
        screen = GameScreen()
        screen.cleanup()
        screen.cleanup()  # повторно — без ошибки
        assert total_subs() == 0


# ── Повторное создание ──────────────────────────────────────────────────────────


class TestRecreate:
    def test_recreate_after_cleanup_does_not_grow(self) -> None:
        first = GameScreen()
        first.cleanup()
        GameScreen()
        assert total_subs() == EXPECTED_SUBS

    def test_many_cycles_stay_clean(self) -> None:
        for _ in range(5):
            screen = GameScreen()
            screen.cleanup()
        assert total_subs() == 0


# ── pop() вызывает cleanup ───────────────────────────────────────────────────────


class TestPopTriggersCleanup:
    def test_pop_cleans_up_gamescreen(self) -> None:
        manager = GameStateManager()
        manager.push(GameScreen())
        assert total_subs() == EXPECTED_SUBS
        manager.pop()
        assert total_subs() == 0

    def test_pop_of_plain_screen_is_safe(self) -> None:
        from ui.base_screen import BaseScreen

        manager = GameStateManager()
        manager.push(BaseScreen())
        manager.pop()  # BaseScreen.cleanup — нет-оп, без ошибки
        assert manager.depth == 0


# ── F9: повторные загрузки ───────────────────────────────────────────────────────


class TestF9NoAccumulation:
    def test_repeated_f9_keeps_subscriber_count(self, save_path: Path) -> None:
        write_save(100)
        screen = GameScreen()
        assert total_subs() == EXPECTED_SUBS
        for _ in range(5):
            screen.handle_event(key_event(pygame.K_F9))
            assert total_subs() == EXPECTED_SUBS

    def test_f9_does_not_leak_player_or_quest(self, save_path: Path) -> None:
        write_save(100)
        screen = GameScreen()
        for _ in range(3):
            screen.load_game()
        assert len(EventBus._listeners["player_level_up"]) == 1
        assert len(EventBus._listeners["entity_died"]) == 2


# ── Continue / New Game: без накопления ──────────────────────────────────────────


class TestMenuNoAccumulation:
    def test_repeated_continue_does_not_accumulate(self, save_path: Path) -> None:
        write_save(50)
        manager = GameStateManager()
        for _ in range(3):
            menu = MainMenuScreen(manager, lambda: None)
            manager.push(menu)
            menu.handle_event(key_event(pygame.K_DOWN))    # → Continue
            menu.handle_event(key_event(pygame.K_RETURN))  # pop меню + push GameScreen
            assert total_subs() == EXPECTED_SUBS
            manager.pop()  # снять GameScreen → cleanup
        assert total_subs() == 0

    def test_repeated_new_game_does_not_accumulate(self) -> None:
        manager = GameStateManager()
        for _ in range(3):
            menu = MainMenuScreen(manager, lambda: None)
            manager.push(menu)
            menu.handle_event(key_event(pygame.K_RETURN))  # New Game
            assert total_subs() == EXPECTED_SUBS
            manager.pop()
        assert total_subs() == 0


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_quest_progress_still_works(self) -> None:
        screen = GameScreen()
        quest = screen._quests["clear_bunker_a1"]
        screen._quest_system.accept_quest(quest)
        screen._enemies[0].take_damage(screen._enemies[0].health.maximum)  # entity_died
        assert quest.objectives[0].progress == "1/4"

    def test_dialogue_still_works(self) -> None:
        manager = GameStateManager()
        screen = GameScreen(manager)
        manager.push(screen)
        screen.handle_event(key_event(pygame.K_t))
        assert screen.dialogue_system.is_active is True

    def test_victory_still_works(self) -> None:
        screen = GameScreen()
        screen._boss.take_damage(screen._boss.health.maximum)
        assert screen.victory is True

    def test_game_over_still_works(self) -> None:
        screen = GameScreen()
        screen._player.take_damage(screen._player.health.maximum)
        assert screen.game_over is True

    def test_f9_kill_grants_xp_once(self, save_path: Path) -> None:
        write_save(0)
        screen = GameScreen()
        screen.load_game()  # F9 → старые подписки сняты
        before = screen._player.experience.current_xp
        enemy = screen._enemies[0]
        enemy.take_damage(enemy.health.maximum)
        assert screen._player.experience.current_xp == before + enemy.xp_reward
