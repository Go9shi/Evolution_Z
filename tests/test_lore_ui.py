"""Tests for Sprint 8J: LoreUI — read-only display of unlocked lore entries."""
from __future__ import annotations

import pygame

from data.lore_data import LoreEntry
from systems.lore import LoreSystem
from ui.base_screen import BaseScreen
from ui.lore_ui import LoreUI


# ── helpers ────────────────────────────────────────────────────────────────────


def make_entry(entry_id: str = "e", title: str = "Title", category: str = "note") -> LoreEntry:
    return LoreEntry(id=entry_id, title=title, text=f"Body of {title}.", category=category)


def make_system(count: int = 0, *, unlock: bool = True) -> LoreSystem:
    """LoreSystem с count записями; при unlock=True все они открыты."""
    system = LoreSystem()
    for i in range(count):
        system.register(make_entry(entry_id=f"e{i}", title=f"Entry {i}"))
        if unlock:
            system.unlock(f"e{i}")
    return system


def make_ui(system: LoreSystem | None = None, on_close: object = None) -> LoreUI:
    if system is None:
        system = make_system()
    if on_close is None:
        on_close = lambda: None  # noqa: E731
    return LoreUI(system, on_close)  # type: ignore[arg-type]


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def mouse_event() -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (0, 0)})


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


# ── Инициализация ──────────────────────────────────────────────────────────────


class TestInit:
    def test_is_base_screen(self) -> None:
        assert isinstance(make_ui(), BaseScreen)

    def test_initial_selected_index_zero(self) -> None:
        assert make_ui().selected_index == 0

    def test_empty_system_safe(self) -> None:
        ui = make_ui(make_system(0))
        assert ui.selected_index == 0
        ui.draw(surface())  # не падает на пустом

    def test_reads_from_system_not_copy(self) -> None:
        system = make_system(0)
        ui = make_ui(system)
        system.register(make_entry("x", "Late"))
        system.unlock("x")
        # UI не кэширует — видит запись, открытую после создания UI
        assert len(ui._lore_system.unlocked_entries) == 1


# ── Навигация ──────────────────────────────────────────────────────────────────


class TestNavigation:
    def test_down_advances(self) -> None:
        ui = make_ui(make_system(3))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 1

    def test_up_goes_back(self) -> None:
        ui = make_ui(make_system(3))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 1

    def test_down_wraps_to_start(self) -> None:
        ui = make_ui(make_system(3))
        for _ in range(3):
            ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0

    def test_up_wraps_to_end(self) -> None:
        ui = make_ui(make_system(3))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 2

    def test_single_entry_navigation_stays(self) -> None:
        ui = make_ui(make_system(1))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 0

    def test_empty_navigation_safe(self) -> None:
        ui = make_ui(make_system(0))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 0

    def test_ignores_non_keydown(self) -> None:
        ui = make_ui(make_system(3))
        ui.handle_event(mouse_event())
        assert ui.selected_index == 0


# ── Закрытие ───────────────────────────────────────────────────────────────────


class TestClose:
    def test_esc_calls_on_close(self) -> None:
        calls: list[int] = []
        ui = make_ui(on_close=lambda: calls.append(1))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert calls == [1]

    def test_esc_calls_on_close_exactly_once(self) -> None:
        calls: list[int] = []
        ui = make_ui(on_close=lambda: calls.append(1))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert len(calls) == 1

    def test_navigation_does_not_close(self) -> None:
        calls: list[int] = []
        ui = make_ui(make_system(2), on_close=lambda: calls.append(1))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert calls == []


# ── Отрисовка ──────────────────────────────────────────────────────────────────


class TestDraw:
    def test_draw_empty(self) -> None:
        make_ui(make_system(0)).draw(surface())

    def test_draw_single_entry(self) -> None:
        make_ui(make_system(1)).draw(surface())

    def test_draw_multiple_entries(self) -> None:
        make_ui(make_system(4)).draw(surface())

    def test_draw_entry_without_category(self) -> None:
        system = LoreSystem()
        system.register(LoreEntry(id="e", title="T", text="Some text", category=""))
        system.unlock("e")
        make_ui(system).draw(surface())

    def test_draw_long_text_wraps(self) -> None:
        system = LoreSystem()
        long_text = "word " * 100
        system.register(LoreEntry(id="e", title="Long", text=long_text, category="log"))
        system.unlock("e")
        make_ui(system).draw(surface())  # не падает на длинном тексте

    def test_update_is_noop(self) -> None:
        make_ui(make_system(1)).update(0.016)


# ── Живые данные ───────────────────────────────────────────────────────────────


class TestLiveData:
    def test_new_unlock_appears_without_recreate(self) -> None:
        system = make_system(1)
        ui = make_ui(system)
        assert len(ui._lore_system.unlocked_entries) == 1
        system.register(make_entry("new", "New Entry"))
        system.unlock("new")
        # тот же экземпляр UI видит новую запись
        assert len(ui._lore_system.unlocked_entries) == 2
        ui.draw(surface())

    def test_registered_but_not_unlocked_not_shown(self) -> None:
        system = LoreSystem()
        system.register(make_entry("locked", "Hidden"))  # зарегистрирована, но не открыта
        ui = make_ui(system)
        assert ui._lore_system.unlocked_entries == []

    def test_ui_does_not_store_own_list(self) -> None:
        # UI не держит собственного списка записей — только ссылку на систему.
        system = make_system(2)
        ui = make_ui(system)
        assert not hasattr(ui, "_entries")
        assert not hasattr(ui, "_unlocked")


# ── Интеграция с GameScreen ────────────────────────────────────────────────────


class TestGameScreenIntegration:
    def _make_game(self):  # type: ignore[no-untyped-def]
        from main import GameStateManager
        from ui.game_screen import GameScreen

        manager = GameStateManager()
        screen = GameScreen(manager)
        manager.push(screen)
        return manager, screen

    def test_l_opens_lore_ui(self) -> None:
        manager, screen = self._make_game()
        screen.handle_event(key_event(pygame.K_l))
        assert isinstance(manager.current, LoreUI)
        assert manager.depth == 2

    def test_lore_ui_uses_game_lore_system(self) -> None:
        manager, screen = self._make_game()
        screen.handle_event(key_event(pygame.K_l))
        ui = manager.current
        assert isinstance(ui, LoreUI)
        assert ui._lore_system is screen._lore_system

    def test_esc_returns_to_game(self) -> None:
        from ui.game_screen import GameScreen

        manager, screen = self._make_game()
        screen.handle_event(key_event(pygame.K_l))
        manager.current.handle_event(key_event(pygame.K_ESCAPE))
        assert manager.depth == 1
        assert isinstance(manager.current, GameScreen)

    def test_l_noop_without_state_manager(self) -> None:
        from ui.game_screen import GameScreen

        screen = GameScreen(state_manager=None)
        screen.handle_event(key_event(pygame.K_l))  # не должно падать
