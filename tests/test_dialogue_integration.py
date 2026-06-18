"""Tests for Sprint 8F: Dialogue Integration — GameScreen ↔ DialogueSystem ↔ DialogueUI."""
from __future__ import annotations

import pygame

from main import GameStateManager
from ui.dialogue_ui import DialogueUI
from ui.game_screen import GameScreen


# ── helpers ────────────────────────────────────────────────────────────────────


def make_game() -> tuple[GameStateManager, GameScreen]:
    manager = GameStateManager()
    screen = GameScreen(manager)
    manager.push(screen)
    return manager, screen


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


def open_dialogue(manager: GameStateManager, screen: GameScreen) -> DialogueUI:
    screen.handle_event(key_event(pygame.K_t))
    ui = manager.current
    assert isinstance(ui, DialogueUI)
    return ui


# ── Loading ──────────────────────────────────────────────────────────────────────


class TestLoading:
    def test_dialogues_loaded_into_game(self) -> None:
        _, screen = make_game()
        # стартовый диалог уровня доступен и запускается
        screen._start_dialogue("ranger_intro")
        assert screen.dialogue_system.is_active is True

    def test_loaded_dialogue_has_correct_start_node(self) -> None:
        _, screen = make_game()
        screen._start_dialogue("ranger_intro")
        node = screen.dialogue_system.current_node
        assert node is not None
        assert node.id == "greet"


# ── Opening ──────────────────────────────────────────────────────────────────────


class TestOpening:
    def test_t_opens_dialogue_ui(self) -> None:
        manager, screen = make_game()
        screen.handle_event(key_event(pygame.K_t))
        assert isinstance(manager.current, DialogueUI)

    def test_t_pushes_one_screen(self) -> None:
        manager, screen = make_game()
        assert manager.depth == 1
        screen.handle_event(key_event(pygame.K_t))
        assert manager.depth == 2

    def test_t_starts_dialogue(self) -> None:
        manager, screen = make_game()
        open_dialogue(manager, screen)
        assert screen.dialogue_system.is_active is True

    def test_ui_uses_game_dialogue_system(self) -> None:
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        # UI продвигает тот же экземпляр системы, что хранит GameScreen
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))  # выбор второго варианта -> silent
        node = screen.dialogue_system.current_node
        assert node is not None
        assert node.id == "silent"


# ── Closing ──────────────────────────────────────────────────────────────────────


class TestClosing:
    def test_completing_dialogue_returns_to_game(self) -> None:
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_RETURN))  # greet -> survivor (выбор 0)
        # survivor: единственный вариант с next_id="" -> завершение диалога
        ui.handle_event(key_event(pygame.K_RETURN))
        assert screen.dialogue_system.is_active is False
        assert manager.depth == 1
        assert isinstance(manager.current, GameScreen)

    def test_esc_closes_ui_returns_to_game(self) -> None:
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert manager.depth == 1
        assert isinstance(manager.current, GameScreen)

    def test_esc_does_not_end_dialogue_state(self) -> None:
        # ESC закрывает только оверлей; владелец состояния — DialogueSystem
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert screen.dialogue_system.is_active is True


# ── Behavior ───────────────────────────────────────────────────────────────────────


class TestBehavior:
    def test_reopening_works(self) -> None:
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_RETURN))  # -> survivor
        ui.handle_event(key_event(pygame.K_RETURN))  # -> end
        assert screen.dialogue_system.is_active is False
        # повторное открытие перезапускает диалог
        ui2 = open_dialogue(manager, screen)
        assert screen.dialogue_system.is_active is True
        node = screen.dialogue_system.current_node
        assert node is not None and node.id == "greet"
        assert ui2 is not ui

    def test_missing_dialogue_is_safe(self) -> None:
        manager, screen = make_game()
        screen._start_dialogue("does_not_exist")
        assert screen.dialogue_system.is_active is False
        assert manager.depth == 1  # ничего не запушено

    def test_no_state_manager_is_safe(self) -> None:
        screen = GameScreen(state_manager=None)
        screen.handle_event(key_event(pygame.K_t))  # не должно падать
        assert screen.dialogue_system.is_active is False

    def test_inactive_dialogue_does_not_break_game_update(self) -> None:
        _, screen = make_game()
        screen.update(0.016)  # игра обновляется без активного диалога
        screen.draw(surface())
        assert screen.dialogue_system.is_active is False


# ── Integration (full scenario) ─────────────────────────────────────────────────


class TestFullScenario:
    def test_game_to_dialogue_to_terminal_to_return(self) -> None:
        manager, screen = make_game()

        # T -> DialogueUI открыт, диалог на узле выбора
        ui = open_dialogue(manager, screen)
        ui.draw(surface())
        node = screen.dialogue_system.current_node
        assert node is not None and node.id == "greet"

        # выбор второго варианта -> терминальный узел 'silent'
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))
        node = screen.dialogue_system.current_node
        assert node is not None and node.id == "silent"
        assert node.is_terminal is True
        ui.draw(surface())

        # ENTER на терминальном узле завершает диалог и возвращает в игру
        ui.handle_event(key_event(pygame.K_RETURN))
        assert screen.dialogue_system.is_active is False
        assert manager.depth == 1
        assert isinstance(manager.current, GameScreen)

        # игра продолжает работать
        screen.update(0.016)
        screen.draw(surface())
