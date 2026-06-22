"""Tests for Sprint 8E.1: DialogueLoader — JSON → Dialogue objects with validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data.dialogue_data import Dialogue
from data.dialogue_loader import DialogueLoadError, load_dialogues
from settings import DATA_DIR
from systems.dialogue import DialogueSystem


# ── helpers ────────────────────────────────────────────────────────────────────


def write_json(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "dialogues.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_text(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "dialogues.json"
    path.write_text(text, encoding="utf-8")
    return path


_VALID_PAYLOAD = {
    "dialogues": [
        {
            "id": "ranger_intro",
            "start_id": "greet",
            "nodes": [
                {
                    "id": "greet",
                    "speaker": "Ranger",
                    "text": "Are you infected?",
                    "choices": [
                        {"text": "No.", "next_id": "survivor"},
                        {"text": "...", "next_id": "silent"},
                    ],
                },
                {
                    "id": "survivor",
                    "speaker": "Ranger",
                    "text": "Take this.",
                    "choices": [{"text": "Thanks.", "next_id": ""}],
                },
                {"id": "silent", "speaker": "Ranger", "text": "Suit yourself."},
            ],
        }
    ]
}


# ── successful load ──────────────────────────────────────────────────────────────


class TestSuccessfulLoad:
    def test_returns_list_of_dialogues(self, tmp_path: Path) -> None:
        result = load_dialogues(write_json(tmp_path, _VALID_PAYLOAD))
        assert len(result) == 1
        assert isinstance(result[0], Dialogue)

    def test_dialogue_fields(self, tmp_path: Path) -> None:
        dialogue = load_dialogues(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert dialogue.id == "ranger_intro"
        assert dialogue.start_id == "greet"

    def test_nodes_built_as_map(self, tmp_path: Path) -> None:
        dialogue = load_dialogues(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert set(dialogue.nodes) == {"greet", "survivor", "silent"}
        assert dialogue.nodes["greet"].speaker == "Ranger"
        assert dialogue.nodes["greet"].text == "Are you infected?"

    def test_choices_built(self, tmp_path: Path) -> None:
        dialogue = load_dialogues(write_json(tmp_path, _VALID_PAYLOAD))[0]
        greet = dialogue.nodes["greet"]
        assert len(greet.choices) == 2
        assert greet.choices[0].text == "No."
        assert greet.choices[0].next_id == "survivor"

    def test_terminal_node_has_no_choices(self, tmp_path: Path) -> None:
        dialogue = load_dialogues(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert dialogue.nodes["silent"].is_terminal is True

    def test_missing_next_id_defaults_empty(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [
                {
                    "id": "d",
                    "start_id": "a",
                    "nodes": [
                        {"id": "a", "speaker": "X", "text": "Bye", "choices": [{"text": "Leave"}]}
                    ],
                }
            ]
        }
        dialogue = load_dialogues(write_json(tmp_path, payload))[0]
        assert dialogue.nodes["a"].choices[0].next_id == ""

    def test_loaded_dialogue_runs_in_system(self, tmp_path: Path) -> None:
        dialogue = load_dialogues(write_json(tmp_path, _VALID_PAYLOAD))[0]
        system = DialogueSystem()
        system.start(dialogue)
        system.choose(0)  # -> survivor
        assert system.current_node is not None
        assert system.current_node.id == "survivor"


# ── multiple dialogues ───────────────────────────────────────────────────────────


class TestMultipleDialogues:
    def test_loads_all(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [
                {"id": "d1", "start_id": "a", "nodes": [{"id": "a", "speaker": "X", "text": "1"}]},
                {"id": "d2", "start_id": "b", "nodes": [{"id": "b", "speaker": "Y", "text": "2"}]},
            ]
        }
        result = load_dialogues(write_json(tmp_path, payload))
        assert [d.id for d in result] == ["d1", "d2"]

    def test_empty_dialogues_list_returns_empty(self, tmp_path: Path) -> None:
        result = load_dialogues(write_json(tmp_path, {"dialogues": []}))
        assert result == []


# ── error handling ───────────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DialogueLoadError):
            load_dialogues(tmp_path / "does_not_exist.json")

    def test_corrupt_json_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_text(tmp_path, "{ not valid json "))

    def test_not_object_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, [1, 2, 3]))

    def test_missing_dialogues_key_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, {"items": []}))

    def test_dialogues_not_list_raises(self, tmp_path: Path) -> None:
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, {"dialogues": {}}))

    def test_missing_dialogue_field_raises(self, tmp_path: Path) -> None:
        payload = {"dialogues": [{"id": "d", "nodes": []}]}  # no start_id
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_nodes_not_list_raises(self, tmp_path: Path) -> None:
        payload = {"dialogues": [{"id": "d", "start_id": "a", "nodes": {}}]}
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_missing_node_field_raises(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [{"id": "d", "start_id": "a", "nodes": [{"id": "a", "speaker": "X"}]}]
        }  # node missing 'text'
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_choice_without_text_raises(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [
                {
                    "id": "d",
                    "start_id": "a",
                    "nodes": [
                        {"id": "a", "speaker": "X", "text": "?", "choices": [{"next_id": "a"}]}
                    ],
                }
            ]
        }
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_choices_not_list_raises(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [
                {
                    "id": "d",
                    "start_id": "a",
                    "nodes": [{"id": "a", "speaker": "X", "text": "?", "choices": "nope"}],
                }
            ]
        }
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_dangling_start_id_raises(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [
                {"id": "d", "start_id": "ghost", "nodes": [{"id": "a", "speaker": "X", "text": "?"}]}
            ]
        }
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_dangling_choice_reference_raises(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [
                {
                    "id": "d",
                    "start_id": "a",
                    "nodes": [
                        {
                            "id": "a",
                            "speaker": "X",
                            "text": "?",
                            "choices": [{"text": "go", "next_id": "ghost"}],
                        }
                    ],
                }
            ]
        }
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_duplicate_node_ids_raises(self, tmp_path: Path) -> None:
        payload = {
            "dialogues": [
                {
                    "id": "d",
                    "start_id": "a",
                    "nodes": [
                        {"id": "a", "speaker": "X", "text": "1"},
                        {"id": "a", "speaker": "Y", "text": "2"},
                    ],
                }
            ]
        }
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))

    def test_empty_dialogue_no_nodes_raises(self, tmp_path: Path) -> None:
        payload = {"dialogues": [{"id": "d", "start_id": "a", "nodes": []}]}
        with pytest.raises(DialogueLoadError):
            load_dialogues(write_json(tmp_path, payload))


# ── real data file ───────────────────────────────────────────────────────────────


class TestRealDataFile:
    def test_ships_dialogues_json_loads(self) -> None:
        dialogues = load_dialogues(DATA_DIR / "dialogues.json")
        assert len(dialogues) >= 1
        for dialogue in dialogues:
            assert dialogue.start_id in dialogue.nodes

    def test_ships_dialogue_runs_to_end(self) -> None:
        dialogue = load_dialogues(DATA_DIR / "dialogues.json")[0]
        system = DialogueSystem()
        system.start(dialogue)
        system.choose(1)  # silent branch (terminal)
        system.advance()  # terminal -> end
        assert system.is_active is False
