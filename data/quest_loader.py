import json
from pathlib import Path
from typing import Any, Callable

from data.quest_data import KillZombieObjective, Objective, Quest

_REQUIRED_QUEST_FIELDS: tuple[str, ...] = ("id", "title", "description", "reward_xp", "objectives")


class QuestLoadError(Exception):
    """Ошибка чтения или валидации данных квестов из JSON."""


def _build_kill_zombie(raw: dict[str, Any]) -> Objective:
    """Построить KillZombieObjective из словаря. Требует поле target_count."""
    if "target_count" not in raw:
        raise QuestLoadError("Objective 'kill_zombie' requires field 'target_count'")
    return KillZombieObjective(target_count=raw["target_count"])


# Диспетчер построителей целей по типу. Новый тип Objective — одна строка здесь.
_OBJECTIVE_BUILDERS: dict[str, Callable[[dict[str, Any]], Objective]] = {
    "kill_zombie": _build_kill_zombie,
}


def load_quests(path: Path) -> list[Quest]:
    """Прочитать JSON-файл квестов, валидировать и вернуть готовые Quest-объекты.

    Поднимает QuestLoadError при отсутствии файла, повреждённом JSON,
    неизвестном типе цели или отсутствии обязательных полей.
    """
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise QuestLoadError(f"Cannot read quests file: {path}") from exc

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise QuestLoadError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict) or "quests" not in data:
        raise QuestLoadError("Quests file must be an object with a 'quests' key")

    quests_raw = data["quests"]
    if not isinstance(quests_raw, list):
        raise QuestLoadError("'quests' must be a list")

    return [_build_quest(entry) for entry in quests_raw]


def _build_quest(raw: Any) -> Quest:
    """Построить один Quest из словаря, проверив обязательные поля."""
    if not isinstance(raw, dict):
        raise QuestLoadError("Each quest must be an object")

    missing = [field for field in _REQUIRED_QUEST_FIELDS if field not in raw]
    if missing:
        raise QuestLoadError(f"Quest is missing required fields: {missing}")

    objectives_raw = raw["objectives"]
    if not isinstance(objectives_raw, list):
        raise QuestLoadError(f"Quest '{raw['id']}' field 'objectives' must be a list")

    objectives = [_build_objective(obj) for obj in objectives_raw]
    return Quest(
        id=raw["id"],
        title=raw["title"],
        description=raw["description"],
        reward_xp=raw["reward_xp"],
        objectives=objectives,
    )


def _build_objective(raw: Any) -> Objective:
    """Построить одну цель по её типу через диспетчер построителей."""
    if not isinstance(raw, dict) or "type" not in raw:
        raise QuestLoadError("Each objective must be an object with a 'type' field")

    obj_type = raw["type"]
    builder = _OBJECTIVE_BUILDERS.get(obj_type)
    if builder is None:
        raise QuestLoadError(f"Unknown objective type: {obj_type!r}")

    return builder(raw)
