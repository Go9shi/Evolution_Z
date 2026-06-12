import json
from pathlib import Path
from typing import Any

from data.dialogue_data import Dialogue, DialogueChoice, DialogueNode

_REQUIRED_DIALOGUE_FIELDS: tuple[str, ...] = ("id", "start_id", "nodes")
_REQUIRED_NODE_FIELDS: tuple[str, ...] = ("id", "speaker", "text")


class DialogueLoadError(Exception):
    """Ошибка чтения или валидации данных диалогов из JSON."""


def load_dialogues(path: Path) -> list[Dialogue]:
    """Прочитать JSON-файл диалогов, валидировать и вернуть готовые Dialogue-объекты.

    Поднимает DialogueLoadError при отсутствии файла, повреждённом JSON,
    отсутствии обязательных полей или висячих ссылках между узлами.
    """
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DialogueLoadError(f"Cannot read dialogues file: {path}") from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise DialogueLoadError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict) or "dialogues" not in data:
        raise DialogueLoadError("Dialogues file must be an object with a 'dialogues' key")

    dialogues_raw = data["dialogues"]
    if not isinstance(dialogues_raw, list):
        raise DialogueLoadError("'dialogues' must be a list")

    return [_build_dialogue(entry) for entry in dialogues_raw]


def _build_dialogue(raw: Any) -> Dialogue:
    """Построить один Dialogue из словаря, проверив поля и целостность ссылок."""
    if not isinstance(raw, dict):
        raise DialogueLoadError("Each dialogue must be an object")

    missing = [field for field in _REQUIRED_DIALOGUE_FIELDS if field not in raw]
    if missing:
        raise DialogueLoadError(f"Dialogue is missing required fields: {missing}")

    nodes_raw = raw["nodes"]
    if not isinstance(nodes_raw, list):
        raise DialogueLoadError(f"Dialogue '{raw['id']}' field 'nodes' must be a list")

    nodes = [_build_node(node, raw["id"]) for node in nodes_raw]
    node_map = {node.id: node for node in nodes}

    if len(node_map) != len(nodes):
        raise DialogueLoadError(f"Dialogue '{raw['id']}' has duplicate node ids")

    _validate_references(raw["id"], raw["start_id"], node_map)
    return Dialogue(id=raw["id"], nodes=node_map, start_id=raw["start_id"])


def _build_node(raw: Any, dialogue_id: str) -> DialogueNode:
    """Построить один DialogueNode из словаря."""
    if not isinstance(raw, dict):
        raise DialogueLoadError(f"Dialogue '{dialogue_id}' has a node that is not an object")

    missing = [field for field in _REQUIRED_NODE_FIELDS if field not in raw]
    if missing:
        raise DialogueLoadError(
            f"Dialogue '{dialogue_id}' node is missing required fields: {missing}"
        )

    choices_raw = raw.get("choices", [])
    if not isinstance(choices_raw, list):
        raise DialogueLoadError(
            f"Dialogue '{dialogue_id}' node '{raw['id']}' field 'choices' must be a list"
        )

    choices = [_build_choice(choice, dialogue_id, raw["id"]) for choice in choices_raw]
    return DialogueNode(id=raw["id"], speaker=raw["speaker"], text=raw["text"], choices=choices)


def _build_choice(raw: Any, dialogue_id: str, node_id: str) -> DialogueChoice:
    """Построить один DialogueChoice из словаря. Требует поле text; next_id опционален."""
    if not isinstance(raw, dict) or "text" not in raw:
        raise DialogueLoadError(
            f"Dialogue '{dialogue_id}' node '{node_id}' has a choice without 'text'"
        )
    return DialogueChoice(text=raw["text"], next_id=raw.get("next_id", ""))


def _validate_references(
    dialogue_id: str, start_id: str, node_map: dict[str, DialogueNode]
) -> None:
    """Проверить, что start_id и все непустые next_id ссылаются на существующие узлы."""
    if start_id not in node_map:
        raise DialogueLoadError(
            f"Dialogue '{dialogue_id}' start_id '{start_id}' does not match any node"
        )

    for node in node_map.values():
        for choice in node.choices:
            if choice.next_id and choice.next_id not in node_map:
                raise DialogueLoadError(
                    f"Dialogue '{dialogue_id}' node '{node.id}' references "
                    f"missing node '{choice.next_id}'"
                )
