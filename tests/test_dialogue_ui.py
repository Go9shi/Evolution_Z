"""Tests for Sprint 8E.2: DialogueUI — display and input over DialogueSystem."""
from __future__ import annotations

import pygame

from data.dialogue_data import Dialogue, DialogueChoice, DialogueNode
from systems.dialogue import DialogueSystem
from ui.base_screen import BaseScreen
from ui.dialogue_ui import DialogueUI


# ── helpers ────────────────────────────────────────────────────────────────────


def make_branching_dialogue() -> Dialogue:
    nodes = {
        "start": DialogueNode(
            id="start",
            speaker="Survivor",
            text="Friend or foe?",
            choices=[
                DialogueChoice(text="Friend.", next_id="friendly"),
                DialogueChoice(text="Foe.", next_id="hostile"),
            ],
        ),
        "friendly": DialogueNode(id="friendly", speaker="Survivor", text="Welcome."),
        "hostile": DialogueNode(id="hostile", speaker="Survivor", text="Then die."),
    }
    return Dialogue(id="d_branch", nodes=nodes, start_id="start")


def make_single_choice_dialogue() -> Dialogue:
    nodes = {
        "start": DialogueNode(
            id="start",
            speaker="X",
            text="Continue?",
            choices=[DialogueChoice(text="Onward.", next_id="end_node")],
        ),
        "end_node": DialogueNode(id="end_node", speaker="X", text="Done."),
    }
    return Dialogue(id="d_single", nodes=nodes, start_id="start")


def started_system(dialogue: Dialogue | None = None) -> DialogueSystem:
    system = DialogueSystem()
    system.start(dialogue if dialogue is not None else make_branching_dialogue())
    return system


class CloseSpy:
    """Считает вызовы on_close."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


def make_ui(system: DialogueSystem | None = None, on_close: object = None) -> DialogueUI:
    if system is None:
        system = started_system()
    if on_close is None:
        on_close = lambda: None  # noqa: E731
    return DialogueUI(system, on_close)  # type: ignore[arg-type]


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


# ── Initialization ───────────────────────────────────────────────────────────────


class TestInitialization:
    def test_is_base_screen(self) -> None:
        assert isinstance(make_ui(), BaseScreen)

    def test_initial_selected_index_zero(self) -> None:
        assert make_ui().selected_index == 0

    def test_empty_dialogue_inactive_system(self) -> None:
        # система без start: current_node is None — UI создаётся и не падает
        ui = DialogueUI(DialogueSystem(), lambda: None)
        assert ui.selected_index == 0
        ui.draw(surface())


# ── Navigation ───────────────────────────────────────────────────────────────────


class TestNavigation:
    def test_down_advances(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 1

    def test_up_from_zero_wraps_to_last(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 1  # 2 варианта → (0-1) % 2 == 1

    def test_down_wraps_around(self) -> None:
        ui = make_ui()
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0

    def test_single_choice_navigation_stays(self) -> None:
        ui = make_ui(started_system(make_single_choice_dialogue()))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 0

    def test_navigation_on_terminal_node_stays_zero(self) -> None:
        system = started_system()
        system.choose(0)  # -> friendly (terminal)
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0

    def test_navigation_inactive_system_safe(self) -> None:
        ui = DialogueUI(DialogueSystem(), lambda: None)
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0

    def test_non_keydown_ignored(self) -> None:
        ui = make_ui()
        ui.handle_event(pygame.event.Event(pygame.KEYUP, {"key": pygame.K_DOWN}))
        assert ui.selected_index == 0


# ── Selection ────────────────────────────────────────────────────────────────────


class TestSelection:
    def test_enter_selects_first_choice(self) -> None:
        system = started_system()
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_RETURN))
        assert system.current_node is not None
        assert system.current_node.id == "friendly"

    def test_enter_selects_second_choice(self) -> None:
        system = started_system()
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))
        assert system.current_node is not None
        assert system.current_node.id == "hostile"

    def test_selection_resets_index_after_transition(self) -> None:
        system = started_system()
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_DOWN))  # index -> 1
        ui.handle_event(key_event(pygame.K_RETURN))  # choose hostile
        assert ui.selected_index == 0

    def test_enter_on_terminal_ends_dialogue(self) -> None:
        system = started_system()
        system.choose(0)  # -> friendly (terminal)
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_RETURN))
        assert system.is_active is False

    def test_enter_inactive_system_safe(self) -> None:
        system = DialogueSystem()
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_RETURN))  # no crash
        assert system.is_active is False


# ── Close ────────────────────────────────────────────────────────────────────────


class TestClose:
    def test_esc_calls_on_close(self) -> None:
        spy = CloseSpy()
        ui = make_ui(on_close=spy)
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert spy.calls == 1

    def test_esc_calls_on_close_exactly_once(self) -> None:
        spy = CloseSpy()
        ui = make_ui(on_close=spy)
        ui.handle_event(key_event(pygame.K_ESCAPE))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert spy.calls == 1

    def test_esc_does_not_end_dialogue(self) -> None:
        # ESC закрывает только UI; владелец состояния — DialogueSystem
        system = started_system()
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert system.is_active is True


# ── Drawing ──────────────────────────────────────────────────────────────────────


class TestDrawing:
    def test_draw_does_not_raise(self) -> None:
        make_ui().draw(surface())

    def test_draw_terminal_node(self) -> None:
        system = started_system()
        system.choose(1)  # -> hostile (terminal)
        DialogueUI(system, lambda: None).draw(surface())

    def test_draw_inactive_system(self) -> None:
        DialogueUI(DialogueSystem(), lambda: None).draw(surface())

    def test_draw_empty_choice_text(self) -> None:
        nodes = {
            "start": DialogueNode(
                id="start",
                speaker="X",
                text="",
                choices=[DialogueChoice(text="", next_id="")],
            )
        }
        system = DialogueSystem()
        system.start(Dialogue(id="d", nodes=nodes, start_id="start"))
        DialogueUI(system, lambda: None).draw(surface())

    def test_update_does_not_raise(self) -> None:
        make_ui().update(0.016)


# ── Integration ──────────────────────────────────────────────────────────────────


class TestIntegration:
    def test_full_walkthrough(self) -> None:
        system = started_system()
        ui = DialogueUI(system, lambda: None)

        # start: на узле выбора
        assert system.current_node is not None
        assert system.current_node.id == "start"

        # навигация на второй вариант и выбор
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))
        assert system.current_node is not None
        assert system.current_node.id == "hostile"  # терминальный

        # ENTER на терминальном узле завершает диалог
        ui.draw(surface())
        ui.handle_event(key_event(pygame.K_RETURN))
        assert system.is_active is False
        assert system.current_node is None

    def test_linear_walkthrough_single_choice(self) -> None:
        system = started_system(make_single_choice_dialogue())
        ui = DialogueUI(system, lambda: None)
        ui.handle_event(key_event(pygame.K_RETURN))  # -> end_node (terminal)
        assert system.current_node is not None
        assert system.current_node.id == "end_node"
        ui.handle_event(key_event(pygame.K_RETURN))  # terminal -> end
        assert system.is_active is False
