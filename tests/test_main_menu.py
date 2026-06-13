"""Tests for Sprint 10E: Main Menu — New Game / Continue / Quit over GameStateManager."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from main import GameStateManager
from ui.base_screen import BaseScreen
from ui.game_screen import GameScreen
from ui.main_menu import MainMenuScreen


# ── helpers ───────────────────────────────────────────────────────────────────


def make_menu(on_quit: object = None) -> tuple[GameStateManager, MainMenuScreen]:
    if on_quit is None:
        on_quit = lambda: None  # noqa: E731
    manager = GameStateManager()
    menu = MainMenuScreen(manager, on_quit)  # type: ignore[arg-type]
    manager.push(menu)
    return manager, menu


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def mouse_event() -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (0, 0)})


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


def write_save(xp: int) -> None:
    """Создать файл сохранения (через существующий путь GameScreen)."""
    throwaway = GameScreen()
    throwaway._player.add_xp(xp)
    throwaway._save_game()


@pytest.fixture
def save_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "savegame.json"
    monkeypatch.setattr(GameScreen, "_SAVE_PATH", path)
    return path


# ── Main Menu ─────────────────────────────────────────────────────────────────


class TestMenu:
    def test_is_base_screen(self) -> None:
        _, menu = make_menu()
        assert isinstance(menu, BaseScreen)

    def test_first_item_selected(self) -> None:
        _, menu = make_menu()
        assert menu.selected_index == 0

    def test_down_advances(self) -> None:
        _, menu = make_menu()
        menu.handle_event(key_event(pygame.K_DOWN))
        assert menu.selected_index == 1

    def test_down_wraps(self) -> None:
        _, menu = make_menu()
        for _ in range(3):
            menu.handle_event(key_event(pygame.K_DOWN))
        assert menu.selected_index == 0

    def test_up_wraps_to_last(self) -> None:
        _, menu = make_menu()
        menu.handle_event(key_event(pygame.K_UP))
        assert menu.selected_index == 2

    def test_ignores_non_keydown(self) -> None:
        _, menu = make_menu()
        menu.handle_event(mouse_event())
        assert menu.selected_index == 0


# ── New Game ──────────────────────────────────────────────────────────────────


class TestNewGame:
    def test_enter_starts_game(self) -> None:
        manager, menu = make_menu()
        menu.handle_event(key_event(pygame.K_RETURN))  # New Game (индекс 0)
        assert isinstance(manager.current, GameScreen)

    def test_new_game_replaces_menu(self) -> None:
        manager, menu = make_menu()
        menu.handle_event(key_event(pygame.K_RETURN))
        assert manager.depth == 1  # меню заменено, игра на глубине 1 (ESC-выход цел)


# ── Continue ──────────────────────────────────────────────────────────────────


class TestContinue:
    def test_continue_without_save_does_nothing(self, save_path: Path) -> None:
        assert not save_path.exists()
        manager, menu = make_menu()
        menu.handle_event(key_event(pygame.K_DOWN))  # → Continue
        menu.handle_event(key_event(pygame.K_RETURN))
        assert isinstance(manager.current, MainMenuScreen)  # остались в меню
        assert manager.depth == 1

    def test_continue_with_save_starts_game(self, save_path: Path) -> None:
        write_save(300)
        manager, menu = make_menu()
        menu.handle_event(key_event(pygame.K_DOWN))  # → Continue
        menu.handle_event(key_event(pygame.K_RETURN))
        assert isinstance(manager.current, GameScreen)

    def test_continue_loads_state(self, save_path: Path) -> None:
        write_save(300)
        manager, menu = make_menu()
        menu.handle_event(key_event(pygame.K_DOWN))
        menu.handle_event(key_event(pygame.K_RETURN))
        current = manager.current
        assert isinstance(current, GameScreen)
        assert current._player.experience.current_xp == 300


# ── Quit ──────────────────────────────────────────────────────────────────────


class TestQuit:
    def test_enter_on_quit_calls_callback(self) -> None:
        calls: list[int] = []
        manager, menu = make_menu(on_quit=lambda: calls.append(1))
        menu.handle_event(key_event(pygame.K_DOWN))
        menu.handle_event(key_event(pygame.K_DOWN))  # → Quit (индекс 2)
        menu.handle_event(key_event(pygame.K_RETURN))
        assert calls == [1]

    def test_quit_does_not_start_game(self) -> None:
        manager, menu = make_menu()
        menu.handle_event(key_event(pygame.K_DOWN))
        menu.handle_event(key_event(pygame.K_DOWN))
        menu.handle_event(key_event(pygame.K_RETURN))
        assert isinstance(manager.current, MainMenuScreen)


# ── Отрисовка ──────────────────────────────────────────────────────────────────


class TestDraw:
    def test_draw_without_save(self, save_path: Path) -> None:
        _, menu = make_menu()
        menu.draw(surface())  # Continue приглушён — не падает

    def test_draw_with_save(self, save_path: Path) -> None:
        write_save(100)
        _, menu = make_menu()
        menu.draw(surface())

    def test_update_is_noop(self) -> None:
        _, menu = make_menu()
        menu.update(0.016)


# ── Интеграция / стек ──────────────────────────────────────────────────────────


class TestIntegration:
    def test_menu_is_top_of_stack(self) -> None:
        manager, menu = make_menu()
        assert manager.current is menu
        assert manager.depth == 1

    def test_no_state_manager_is_safe(self) -> None:
        menu = MainMenuScreen(None, lambda: None)
        menu.handle_event(key_event(pygame.K_RETURN))  # New Game без менеджера — не падает


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_gamescreen_still_constructs_and_draws(self) -> None:
        screen = GameScreen()
        screen.draw(surface())

    def test_f9_load_still_works(self, save_path: Path) -> None:
        write_save(250)
        manager = GameStateManager()
        screen = GameScreen(manager)
        manager.push(screen)
        screen.handle_event(key_event(pygame.K_F9))
        assert screen._player.experience.current_xp == 250
