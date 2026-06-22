"""Tests for Sprint 9A: InventoryUI — read-only display of inventory items."""
from __future__ import annotations

import pygame

from entities.items.quest_item import QuestItem
from systems.inventory import Inventory
from ui.base_screen import BaseScreen
from ui.inventory_ui import InventoryUI


# ── helpers ────────────────────────────────────────────────────────────────────


def make_item(index: int = 0) -> QuestItem:
    return QuestItem(0.0, 0.0, f"item{index}", f"Item {index}", f"Description {index}.")


def make_inventory(count: int = 0, capacity: int = 20) -> Inventory:
    inv = Inventory(capacity=capacity)
    for i in range(count):
        inv.add_item(make_item(i))
    return inv


def make_ui(inventory: Inventory | None = None, on_close: object = None) -> InventoryUI:
    if inventory is None:
        inventory = make_inventory()
    if on_close is None:
        on_close = lambda: None  # noqa: E731
    return InventoryUI(inventory, on_close)  # type: ignore[arg-type]


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

    def test_empty_inventory_safe(self) -> None:
        ui = make_ui(make_inventory(0))
        assert ui.selected_index == 0
        ui.draw(surface())  # не падает на пустом

    def test_reads_from_inventory_not_copy(self) -> None:
        inv = make_inventory(0)
        ui = make_ui(inv)
        inv.add_item(make_item(99))
        # UI не кэширует — видит предмет, добавленный после создания UI
        assert len(ui._inventory.items) == 1


# ── Навигация ──────────────────────────────────────────────────────────────────


class TestNavigation:
    def test_down_advances(self) -> None:
        ui = make_ui(make_inventory(3))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 1

    def test_up_goes_back(self) -> None:
        ui = make_ui(make_inventory(3))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 1

    def test_down_wraps_to_start(self) -> None:
        ui = make_ui(make_inventory(3))
        for _ in range(3):
            ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0

    def test_up_wraps_to_end(self) -> None:
        ui = make_ui(make_inventory(3))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 2

    def test_single_item_navigation_stays(self) -> None:
        ui = make_ui(make_inventory(1))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 0

    def test_empty_navigation_safe(self) -> None:
        ui = make_ui(make_inventory(0))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 0

    def test_ignores_non_keydown(self) -> None:
        ui = make_ui(make_inventory(3))
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
        ui = make_ui(make_inventory(2), on_close=lambda: calls.append(1))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert calls == []


# ── Отрисовка ──────────────────────────────────────────────────────────────────


class TestDraw:
    def test_draw_empty(self) -> None:
        make_ui(make_inventory(0)).draw(surface())

    def test_draw_single_item(self) -> None:
        make_ui(make_inventory(1)).draw(surface())

    def test_draw_multiple_items(self) -> None:
        make_ui(make_inventory(5)).draw(surface())

    def test_draw_after_navigation(self) -> None:
        ui = make_ui(make_inventory(5))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.draw(surface())

    def test_draw_long_description_wraps(self) -> None:
        inv = Inventory()
        long_desc = "word " * 100
        inv.add_item(QuestItem(0.0, 0.0, "x", "Long", long_desc))
        make_ui(inv).draw(surface())  # не падает на длинном описании

    def test_update_is_noop(self) -> None:
        make_ui(make_inventory(1)).update(0.016)


# ── Живые данные ───────────────────────────────────────────────────────────────


class TestLiveData:
    def test_new_item_appears_without_recreate(self) -> None:
        inv = make_inventory(1)
        ui = make_ui(inv)
        assert len(ui._inventory.items) == 1
        inv.add_item(make_item(2))
        # тот же экземпляр UI видит новый предмет
        assert len(ui._inventory.items) == 2
        ui.draw(surface())

    def test_removed_item_disappears(self) -> None:
        inv = make_inventory(0)
        item = make_item(0)
        inv.add_item(item)
        ui = make_ui(inv)
        inv.remove_item(item)
        assert ui._inventory.items == []

    def test_ui_does_not_store_own_list(self) -> None:
        # UI не держит собственного списка предметов — только ссылку на инвентарь.
        ui = make_ui(make_inventory(2))
        assert not hasattr(ui, "_items")


# ── Интеграция с GameScreen ────────────────────────────────────────────────────


class TestGameScreenIntegration:
    def _make_game(self):  # type: ignore[no-untyped-def]
        from main import GameStateManager
        from ui.game_screen import GameScreen

        manager = GameStateManager()
        screen = GameScreen(manager)
        manager.push(screen)
        return manager, screen

    def test_i_opens_inventory_ui(self) -> None:
        manager, screen = self._make_game()
        screen.handle_event(key_event(pygame.K_i))
        assert isinstance(manager.current, InventoryUI)
        assert manager.depth == 2

    def test_inventory_ui_uses_player_inventory(self) -> None:
        manager, screen = self._make_game()
        screen.handle_event(key_event(pygame.K_i))
        ui = manager.current
        assert isinstance(ui, InventoryUI)
        assert ui._inventory is screen._player.inventory

    def test_esc_returns_to_game(self) -> None:
        from ui.game_screen import GameScreen

        manager, screen = self._make_game()
        screen.handle_event(key_event(pygame.K_i))
        manager.current.handle_event(key_event(pygame.K_ESCAPE))
        assert manager.depth == 1
        assert isinstance(manager.current, GameScreen)

    def test_i_noop_without_state_manager(self) -> None:
        from ui.game_screen import GameScreen

        screen = GameScreen(state_manager=None)
        screen.handle_event(key_event(pygame.K_i))  # не должно падать
