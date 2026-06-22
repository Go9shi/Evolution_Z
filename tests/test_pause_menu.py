"""Tests for Sprint 10G: Pause Menu — Resume / Save Game / Main Menu / Quit + terminal exits."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from main import GameStateManager
from systems.event_bus import EventBus
from ui.base_screen import BaseScreen
from ui.game_screen import GameScreen
from ui.main_menu import MainMenuScreen
from ui.pause_menu import PauseMenuScreen


# ── helpers ───────────────────────────────────────────────────────────────────


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def mouse_event() -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (0, 0)})


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


def total_subs() -> int:
    """Суммарное число активных подписчиков EventBus (для проверки утечек)."""
    return sum(len(callbacks) for callbacks in EventBus._listeners.values())


def make_pause(
    on_resume: object = None,
    on_save: object = None,
    on_main_menu: object = None,
    on_quit: object = None,
) -> PauseMenuScreen:
    noop = lambda: None  # noqa: E731
    return PauseMenuScreen(
        on_resume=on_resume or noop,  # type: ignore[arg-type]
        on_save=on_save or noop,  # type: ignore[arg-type]
        on_main_menu=on_main_menu or noop,  # type: ignore[arg-type]
        on_quit=on_quit or noop,  # type: ignore[arg-type]
    )


def make_game(on_quit: object = None) -> tuple[GameStateManager, GameScreen]:
    manager = GameStateManager()
    screen = GameScreen(manager, on_quit)  # type: ignore[arg-type]
    manager.push(screen)
    return manager, screen


def current_pause(manager: GameStateManager) -> PauseMenuScreen:
    """Вернуть активный оверлей паузы с проверкой типа (сужает BaseScreen | None)."""
    pause = manager.current
    assert isinstance(pause, PauseMenuScreen)
    return pause


def kill(entity) -> None:  # type: ignore[no-untyped-def]
    entity.take_damage(entity.health.maximum)


@pytest.fixture
def save_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "savegame.json"
    monkeypatch.setattr(GameScreen, "_SAVE_PATH", path)
    return path


# ── Pause Menu (unit) ───────────────────────────────────────────────────────────


class TestPauseMenu:
    def test_is_base_screen(self) -> None:
        assert isinstance(make_pause(), BaseScreen)

    def test_first_item_selected(self) -> None:
        assert make_pause().selected_index == 0

    def test_down_advances(self) -> None:
        pause = make_pause()
        pause.handle_event(key_event(pygame.K_DOWN))
        assert pause.selected_index == 1

    def test_down_wraps(self) -> None:
        pause = make_pause()
        for _ in range(4):  # 4 пункта → полный цикл
            pause.handle_event(key_event(pygame.K_DOWN))
        assert pause.selected_index == 0

    def test_up_wraps_to_last(self) -> None:
        pause = make_pause()
        pause.handle_event(key_event(pygame.K_UP))
        assert pause.selected_index == 3

    def test_ignores_non_keydown(self) -> None:
        pause = make_pause()
        pause.handle_event(mouse_event())
        assert pause.selected_index == 0

    def test_enter_on_resume_calls_resume(self) -> None:
        calls: list[str] = []
        pause = make_pause(on_resume=lambda: calls.append("resume"))
        pause.handle_event(key_event(pygame.K_RETURN))  # Resume — индекс 0
        assert calls == ["resume"]

    def test_escape_calls_resume(self) -> None:
        calls: list[str] = []
        pause = make_pause(on_resume=lambda: calls.append("resume"))
        pause.handle_event(key_event(pygame.K_ESCAPE))
        assert calls == ["resume"]

    def test_enter_on_save_calls_save(self) -> None:
        calls: list[str] = []
        pause = make_pause(on_save=lambda: calls.append("save"))
        pause.handle_event(key_event(pygame.K_DOWN))  # → Save Game
        pause.handle_event(key_event(pygame.K_RETURN))
        assert calls == ["save"]

    def test_enter_on_main_menu_calls_callback(self) -> None:
        calls: list[str] = []
        pause = make_pause(on_main_menu=lambda: calls.append("menu"))
        pause.handle_event(key_event(pygame.K_DOWN))
        pause.handle_event(key_event(pygame.K_DOWN))  # → Main Menu
        pause.handle_event(key_event(pygame.K_RETURN))
        assert calls == ["menu"]

    def test_enter_on_quit_calls_callback(self) -> None:
        calls: list[str] = []
        pause = make_pause(on_quit=lambda: calls.append("quit"))
        pause.handle_event(key_event(pygame.K_UP))  # последний пункт → Quit
        pause.handle_event(key_event(pygame.K_RETURN))
        assert calls == ["quit"]

    def test_draw_does_not_crash(self) -> None:
        make_pause().draw(surface())

    def test_update_is_noop(self) -> None:
        make_pause().update(0.016)


# ── Integration: GameScreen ↔ Pause Menu (стек экранов) ──────────────────────────


class TestGameScreenIntegration:
    def test_escape_opens_pause_menu(self) -> None:
        manager, screen = make_game()
        screen.handle_event(key_event(pygame.K_ESCAPE))
        assert isinstance(manager.current, PauseMenuScreen)
        assert manager.depth == 2

    def test_resume_returns_to_game(self) -> None:
        manager, screen = make_game()
        screen.handle_event(key_event(pygame.K_ESCAPE))
        current_pause(manager).handle_event(key_event(pygame.K_ESCAPE))  # Resume
        assert manager.current is screen
        assert manager.depth == 1

    def test_save_game_writes_file(self, save_path: Path) -> None:
        manager, screen = make_game()
        assert not save_path.exists()
        screen.handle_event(key_event(pygame.K_ESCAPE))
        pause = current_pause(manager)
        pause.handle_event(key_event(pygame.K_DOWN))  # → Save Game
        pause.handle_event(key_event(pygame.K_RETURN))
        assert save_path.exists()

    def test_main_menu_returns_to_menu(self) -> None:
        manager, screen = make_game()
        screen.handle_event(key_event(pygame.K_ESCAPE))
        pause = current_pause(manager)
        pause.handle_event(key_event(pygame.K_DOWN))
        pause.handle_event(key_event(pygame.K_DOWN))  # → Main Menu
        pause.handle_event(key_event(pygame.K_RETURN))
        assert isinstance(manager.current, MainMenuScreen)
        assert manager.depth == 1

    def test_quit_calls_on_quit(self) -> None:
        calls: list[int] = []
        manager, screen = make_game(on_quit=lambda: calls.append(1))
        screen.handle_event(key_event(pygame.K_ESCAPE))
        pause = current_pause(manager)
        pause.handle_event(key_event(pygame.K_UP))  # → Quit
        pause.handle_event(key_event(pygame.K_RETURN))
        assert calls == [1]

    def test_no_state_manager_is_safe(self) -> None:
        screen = GameScreen()  # без менеджера
        screen.handle_event(key_event(pygame.K_ESCAPE))  # не падает, ничего не открывает


# ── Терминальные состояния → Main Menu ──────────────────────────────────────────


class TestTerminalExit:
    def test_game_over_enter_returns_to_menu(self) -> None:
        manager, screen = make_game()
        kill(screen._player)
        assert screen.game_over is True
        screen.handle_event(key_event(pygame.K_RETURN))
        assert isinstance(manager.current, MainMenuScreen)
        assert manager.depth == 1

    def test_victory_enter_returns_to_menu(self) -> None:
        manager, screen = make_game()
        kill(screen._boss)
        assert screen.victory is True
        screen.handle_event(key_event(pygame.K_RETURN))
        assert isinstance(manager.current, MainMenuScreen)
        assert manager.depth == 1

    def test_terminal_ignores_other_input(self) -> None:
        manager, screen = make_game()
        kill(screen._player)
        screen.handle_event(key_event(pygame.K_i))  # инвентарь не открывается
        screen.handle_event(mouse_event())  # выстрел не проходит
        assert manager.current is screen
        assert manager.depth == 1


# ── Регрессии: cleanup / отсутствие утечек EventBus ──────────────────────────────


class TestCleanup:
    def test_main_menu_cleans_subscriptions(self) -> None:
        assert total_subs() == 0  # conftest очищает шину
        manager, screen = make_game()
        screen.handle_event(key_event(pygame.K_ESCAPE))
        pause = current_pause(manager)
        pause.handle_event(key_event(pygame.K_DOWN))
        pause.handle_event(key_event(pygame.K_DOWN))  # → Main Menu
        pause.handle_event(key_event(pygame.K_RETURN))
        assert total_subs() == 0  # GameScreen.cleanup снял все подписки

    def test_terminal_exit_cleans_subscriptions(self) -> None:
        assert total_subs() == 0
        manager, screen = make_game()
        kill(screen._boss)  # victory
        screen.handle_event(key_event(pygame.K_RETURN))
        assert total_subs() == 0

    def test_repeated_sessions_do_not_accumulate(self) -> None:
        # Открыть игру и вернуться в меню дважды — подписки не копятся.
        for _ in range(2):
            manager, screen = make_game()
            screen._return_to_main_menu()
        assert total_subs() == 0
