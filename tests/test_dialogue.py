"""Tests for Sprint 8E: DialogueSystem (диалоги)."""
from __future__ import annotations

import pytest

from data.dialogue_data import Dialogue, DialogueChoice, DialogueNode
from systems.dialogue import DialogueError, DialogueSystem
from systems.event_bus import EventBus


# ── helpers ───────────────────────────────────────────────────────────────────

def make_linear_dialogue() -> Dialogue:
    """Линейный диалог из двух узлов: start → second → конец."""
    nodes = {
        "start": DialogueNode(
            id="start",
            speaker="Ranger",
            text="Stay back.",
            choices=[DialogueChoice(text="...", next_id="second")],
        ),
        "second": DialogueNode(id="second", speaker="Ranger", text="The bunker is sealed."),
    }
    return Dialogue(id="d_linear", nodes=nodes, start_id="start")


def make_branching_dialogue() -> Dialogue:
    """Ветвящийся диалог: start с двумя выборами → friendly / hostile."""
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


class EventRecorder:
    """Записывает события EventBus для проверки в тестах."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, data: dict) -> None:
        self.calls.append(data)


# ── data: DialogueChoice ────────────────────────────────────────────────────────

class TestDialogueChoice:
    def test_fields(self) -> None:
        choice = DialogueChoice(text="Yes", next_id="n2")
        assert choice.text == "Yes"
        assert choice.next_id == "n2"

    def test_next_id_defaults_empty(self) -> None:
        choice = DialogueChoice(text="Leave")
        assert choice.next_id == ""


# ── data: DialogueNode ───────────────────────────────────────────────────────────

class TestDialogueNode:
    def test_fields(self) -> None:
        node = DialogueNode(id="n1", speaker="Bob", text="Hi")
        assert node.id == "n1"
        assert node.speaker == "Bob"
        assert node.text == "Hi"

    def test_choices_default_empty(self) -> None:
        node = DialogueNode(id="n1", speaker="Bob", text="Hi")
        assert node.choices == []

    def test_is_terminal_true_without_choices(self) -> None:
        node = DialogueNode(id="n1", speaker="Bob", text="Bye")
        assert node.is_terminal is True

    def test_is_terminal_false_with_choices(self) -> None:
        node = DialogueNode(
            id="n1", speaker="Bob", text="Pick", choices=[DialogueChoice(text="a")]
        )
        assert node.is_terminal is False


# ── data: Dialogue ───────────────────────────────────────────────────────────────

class TestDialogue:
    def test_fields(self) -> None:
        dialogue = make_linear_dialogue()
        assert dialogue.id == "d_linear"
        assert dialogue.start_id == "start"
        assert "start" in dialogue.nodes
        assert "second" in dialogue.nodes


# ── DialogueSystem: initial state ────────────────────────────────────────────────

class TestInitialState:
    def test_not_active_initially(self) -> None:
        system = DialogueSystem()
        assert system.is_active is False

    def test_current_node_none_initially(self) -> None:
        system = DialogueSystem()
        assert system.current_node is None


# ── DialogueSystem: start ────────────────────────────────────────────────────────

class TestStart:
    def test_start_sets_active(self) -> None:
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        assert system.is_active is True

    def test_start_sets_current_to_start_node(self) -> None:
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        assert system.current_node is not None
        assert system.current_node.id == "start"

    def test_start_missing_start_node_raises(self) -> None:
        dialogue = Dialogue(id="bad", nodes={}, start_id="nowhere")
        system = DialogueSystem()
        with pytest.raises(DialogueError):
            system.start(dialogue)

    def test_start_emits_started_event(self) -> None:
        recorder = EventRecorder()
        EventBus.on("dialogue_started", recorder)
        dialogue = make_linear_dialogue()
        DialogueSystem().start(dialogue)
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["dialogue"] is dialogue

    def test_start_emits_node_changed_event(self) -> None:
        recorder = EventRecorder()
        EventBus.on("dialogue_node_changed", recorder)
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["node"].id == "start"


# ── DialogueSystem: advance (linear) ─────────────────────────────────────────────

class TestAdvance:
    def test_advance_moves_to_next_node(self) -> None:
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        system.advance()
        assert system.current_node is not None
        assert system.current_node.id == "second"

    def test_advance_on_terminal_ends_dialogue(self) -> None:
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        system.advance()  # -> second (terminal)
        system.advance()  # terminal -> end
        assert system.is_active is False
        assert system.current_node is None

    def test_advance_emits_node_changed(self) -> None:
        recorder = EventRecorder()
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        EventBus.on("dialogue_node_changed", recorder)
        system.advance()
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["node"].id == "second"

    def test_advance_without_active_raises(self) -> None:
        system = DialogueSystem()
        with pytest.raises(DialogueError):
            system.advance()

    def test_advance_on_multiple_choices_raises(self) -> None:
        system = DialogueSystem()
        system.start(make_branching_dialogue())
        with pytest.raises(DialogueError):
            system.advance()

    def test_advance_follows_empty_next_id_to_end(self) -> None:
        nodes = {
            "start": DialogueNode(
                id="start",
                speaker="X",
                text="Bye",
                choices=[DialogueChoice(text="Leave", next_id="")],
            )
        }
        system = DialogueSystem()
        system.start(Dialogue(id="d", nodes=nodes, start_id="start"))
        system.advance()
        assert system.is_active is False


# ── DialogueSystem: choose (branching) ───────────────────────────────────────────

class TestChoose:
    def test_choose_first_branch(self) -> None:
        system = DialogueSystem()
        system.start(make_branching_dialogue())
        system.choose(0)
        assert system.current_node is not None
        assert system.current_node.id == "friendly"

    def test_choose_second_branch(self) -> None:
        system = DialogueSystem()
        system.start(make_branching_dialogue())
        system.choose(1)
        assert system.current_node is not None
        assert system.current_node.id == "hostile"

    def test_choose_out_of_range_raises(self) -> None:
        system = DialogueSystem()
        system.start(make_branching_dialogue())
        with pytest.raises(DialogueError):
            system.choose(5)

    def test_choose_negative_index_raises(self) -> None:
        system = DialogueSystem()
        system.start(make_branching_dialogue())
        with pytest.raises(DialogueError):
            system.choose(-1)

    def test_choose_without_active_raises(self) -> None:
        system = DialogueSystem()
        with pytest.raises(DialogueError):
            system.choose(0)

    def test_choose_dangling_reference_raises(self) -> None:
        nodes = {
            "start": DialogueNode(
                id="start",
                speaker="X",
                text="?",
                choices=[DialogueChoice(text="go", next_id="ghost")],
            )
        }
        system = DialogueSystem()
        system.start(Dialogue(id="d", nodes=nodes, start_id="start"))
        with pytest.raises(DialogueError):
            system.choose(0)

    def test_choose_empty_next_id_ends_dialogue(self) -> None:
        nodes = {
            "start": DialogueNode(
                id="start",
                speaker="X",
                text="Last words?",
                choices=[DialogueChoice(text="None.", next_id="")],
            )
        }
        system = DialogueSystem()
        system.start(Dialogue(id="d", nodes=nodes, start_id="start"))
        system.choose(0)
        assert system.is_active is False


# ── DialogueSystem: end ──────────────────────────────────────────────────────────

class TestEnd:
    def test_end_clears_state(self) -> None:
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        system.end()
        assert system.is_active is False
        assert system.current_node is None

    def test_end_emits_ended_event(self) -> None:
        recorder = EventRecorder()
        system = DialogueSystem()
        dialogue = make_linear_dialogue()
        system.start(dialogue)
        EventBus.on("dialogue_ended", recorder)
        system.end()
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["dialogue"] is dialogue

    def test_end_when_inactive_is_noop(self) -> None:
        recorder = EventRecorder()
        EventBus.on("dialogue_ended", recorder)
        system = DialogueSystem()
        system.end()
        assert recorder.calls == []


# ── DialogueSystem: integration ──────────────────────────────────────────────────

class TestIntegration:
    def test_full_branching_walkthrough(self) -> None:
        events: list[str] = []
        EventBus.on("dialogue_started", lambda d: events.append("started"))
        EventBus.on("dialogue_node_changed", lambda d: events.append(f"node:{d['node'].id}"))
        EventBus.on("dialogue_ended", lambda d: events.append("ended"))

        system = DialogueSystem()
        system.start(make_branching_dialogue())
        system.choose(0)  # -> friendly (terminal)
        system.advance()  # terminal -> end

        assert events == ["started", "node:start", "node:friendly", "ended"]
        assert system.is_active is False

    def test_restart_after_end(self) -> None:
        system = DialogueSystem()
        system.start(make_linear_dialogue())
        system.end()
        system.start(make_branching_dialogue())
        assert system.is_active is True
        assert system.current_node is not None
        assert system.current_node.id == "start"
