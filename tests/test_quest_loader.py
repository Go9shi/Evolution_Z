"""Tests for Sprint 8C: QuestLoader — JSON → Quest objects with validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data.quest_data import KillZombieObjective, Quest, QuestStatus
from data.quest_loader import QuestLoadError, load_quests
from settings import DATA_DIR
from systems.event_bus import EventBus
from systems.experience import ExperienceComponent, required_xp
from systems.quest_system import QuestSystem


# ── helpers ────────────────────────────────────────────────────────────────────


class FakeEntity:
    """Минимальная сущность-зомби для прогона прогресса без pygame."""

    def __init__(self, faction: str = "enemy") -> None:
        self.faction = faction


def write_json(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "quests.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_text(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "quests.json"
    path.write_text(text, encoding="utf-8")
    return path


_VALID_PAYLOAD = {
    "quests": [
        {
            "id": "clear_bunker_a1",
            "title": "Clear Bunker A1",
            "description": "Eliminate 4 zombies.",
            "reward_xp": 100,
            "objectives": [{"type": "kill_zombie", "target_count": 4}],
        }
    ]
}


# ── successful load ────────────────────────────────────────────────────────────


class TestSuccessfulLoad:
    def test_returns_list(self, tmp_path: Path) -> None:
        quests = load_quests(write_json(tmp_path, _VALID_PAYLOAD))
        assert isinstance(quests, list)

    def test_loads_one_quest(self, tmp_path: Path) -> None:
        quests = load_quests(write_json(tmp_path, _VALID_PAYLOAD))
        assert len(quests) == 1

    def test_loads_multiple_quests(self, tmp_path: Path) -> None:
        payload = {
            "quests": [
                {
                    "id": "q1", "title": "T1", "description": "D1", "reward_xp": 50,
                    "objectives": [{"type": "kill_zombie", "target_count": 2}],
                },
                {
                    "id": "q2", "title": "T2", "description": "D2", "reward_xp": 70,
                    "objectives": [{"type": "kill_zombie", "target_count": 3}],
                },
            ]
        }
        quests = load_quests(write_json(tmp_path, payload))
        assert len(quests) == 2


# ── Quest creation ─────────────────────────────────────────────────────────────


class TestQuestCreation:
    def test_is_quest_instance(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert isinstance(quest, Quest)

    def test_quest_fields(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert quest.id == "clear_bunker_a1"
        assert quest.title == "Clear Bunker A1"
        assert quest.description == "Eliminate 4 zombies."
        assert quest.reward_xp == 100

    def test_quest_default_status_available(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert quest.status == QuestStatus.AVAILABLE


# ── KillZombieObjective creation ───────────────────────────────────────────────


class TestObjectiveCreation:
    def test_objective_is_kill_zombie(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert isinstance(quest.objectives[0], KillZombieObjective)

    def test_objective_target_count(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        obj = quest.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.target_count == 4

    def test_objective_starts_incomplete(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert not quest.objectives[0].is_complete

    def test_multiple_objectives_in_one_quest(self, tmp_path: Path) -> None:
        payload = {
            "quests": [{
                "id": "q", "title": "T", "description": "D", "reward_xp": 10,
                "objectives": [
                    {"type": "kill_zombie", "target_count": 2},
                    {"type": "kill_zombie", "target_count": 5},
                ],
            }]
        }
        quest = load_quests(write_json(tmp_path, payload))[0]
        assert len(quest.objectives) == 2


# ── empty quest list ───────────────────────────────────────────────────────────


class TestEmptyList:
    def test_empty_quests_returns_empty_list(self, tmp_path: Path) -> None:
        assert load_quests(write_json(tmp_path, {"quests": []})) == []

    def test_quest_with_empty_objectives(self, tmp_path: Path) -> None:
        payload = {
            "quests": [{
                "id": "q", "title": "T", "description": "D", "reward_xp": 10,
                "objectives": [],
            }]
        }
        quest = load_quests(write_json(tmp_path, payload))[0]
        assert quest.objectives == []


# ── missing file ───────────────────────────────────────────────────────────────


class TestMissingFile:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(QuestLoadError):
            load_quests(tmp_path / "does_not_exist.json")


# ── corrupted JSON ─────────────────────────────────────────────────────────────


class TestCorruptedJson:
    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        with pytest.raises(QuestLoadError):
            load_quests(write_text(tmp_path, "{ this is not json"))

    def test_non_object_root_raises(self, tmp_path: Path) -> None:
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, [1, 2, 3]))

    def test_missing_quests_key_raises(self, tmp_path: Path) -> None:
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, {"foo": "bar"}))

    def test_quests_not_a_list_raises(self, tmp_path: Path) -> None:
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, {"quests": {"id": "x"}}))


# ── unknown objective type ─────────────────────────────────────────────────────


class TestUnknownObjectiveType:
    def test_unknown_type_raises(self, tmp_path: Path) -> None:
        payload = {
            "quests": [{
                "id": "q", "title": "T", "description": "D", "reward_xp": 10,
                "objectives": [{"type": "collect_item", "amount": 3}],
            }]
        }
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, payload))

    def test_objective_without_type_raises(self, tmp_path: Path) -> None:
        payload = {
            "quests": [{
                "id": "q", "title": "T", "description": "D", "reward_xp": 10,
                "objectives": [{"target_count": 3}],
            }]
        }
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, payload))

    def test_kill_zombie_without_target_count_raises(self, tmp_path: Path) -> None:
        payload = {
            "quests": [{
                "id": "q", "title": "T", "description": "D", "reward_xp": 10,
                "objectives": [{"type": "kill_zombie"}],
            }]
        }
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, payload))


# ── missing required fields ────────────────────────────────────────────────────


class TestMissingFields:
    @pytest.mark.parametrize("field", ["id", "title", "description", "reward_xp", "objectives"])
    def test_missing_quest_field_raises(self, tmp_path: Path, field: str) -> None:
        quest = dict(_VALID_PAYLOAD["quests"][0])
        del quest[field]
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, {"quests": [quest]}))

    def test_quest_not_object_raises(self, tmp_path: Path) -> None:
        with pytest.raises(QuestLoadError):
            load_quests(write_json(tmp_path, {"quests": ["not an object"]}))


# ── Sprint 8D: narrative metadata ───────────────────────────────────────────────


_NARRATIVE_PAYLOAD = {
    "quests": [
        {
            "id": "clear_bunker_a1",
            "title": "Clear Bunker A1",
            "description": "Eliminate infected units.",
            "lore_text": "Emergency transmission from Bunker A1...",
            "location": "Bunker A1",
            "category": "main_story",
            "reward_xp": 100,
            "objectives": [{"type": "kill_zombie", "target_count": 4}],
        }
    ]
}


class TestNarrativeMetadataLoaded:
    """Новые narrative-поля загружаются из JSON в модель Quest."""

    def test_lore_text_loaded(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _NARRATIVE_PAYLOAD))[0]
        assert quest.lore_text == "Emergency transmission from Bunker A1..."

    def test_location_loaded(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _NARRATIVE_PAYLOAD))[0]
        assert quest.location == "Bunker A1"

    def test_category_loaded(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _NARRATIVE_PAYLOAD))[0]
        assert quest.category == "main_story"

    def test_core_fields_still_loaded_alongside_metadata(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _NARRATIVE_PAYLOAD))[0]
        assert quest.id == "clear_bunker_a1"
        assert quest.reward_xp == 100
        assert quest.objectives[0].is_complete is False


class TestNarrativeMetadataOptional:
    """Отсутствие narrative-полей не ломает загрузку — поля получают пустые значения."""

    def test_missing_metadata_loads_successfully(self, tmp_path: Path) -> None:
        # _VALID_PAYLOAD не содержит lore_text/location/category
        quests = load_quests(write_json(tmp_path, _VALID_PAYLOAD))
        assert len(quests) == 1

    def test_missing_lore_text_defaults_empty(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert quest.lore_text == ""

    def test_missing_location_defaults_empty(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert quest.location == ""

    def test_missing_category_defaults_empty(self, tmp_path: Path) -> None:
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        assert quest.category == ""

    def test_partial_metadata_loads(self, tmp_path: Path) -> None:
        payload = {
            "quests": [{
                "id": "q", "title": "T", "description": "D", "reward_xp": 10,
                "location": "Bunker B3",
                "objectives": [{"type": "kill_zombie", "target_count": 1}],
            }]
        }
        quest = load_quests(write_json(tmp_path, payload))[0]
        assert quest.location == "Bunker B3"
        assert quest.lore_text == ""
        assert quest.category == ""

    def test_metadata_not_required_field(self, tmp_path: Path) -> None:
        # narrative-поля не входят в обязательные: квест без них валиден
        for field in ("lore_text", "location", "category"):
            assert field not in _VALID_PAYLOAD["quests"][0]


class TestBackwardCompatibility:
    """Старые квесты (формат до 8D) продолжают загружаться и работать в цикле."""

    def test_old_quest_completes_and_grants_xp(self, tmp_path: Path) -> None:
        exp = ExperienceComponent()
        qs = QuestSystem(exp)
        quest = load_quests(write_json(tmp_path, _VALID_PAYLOAD))[0]
        qs.accept_quest(quest)
        for _ in range(4):
            EventBus.emit("entity_died", {"entity": FakeEntity("enemy")})
        assert quest.status == QuestStatus.COMPLETED
        assert exp.current_xp == 100


# ── integration: real game JSON loads and works ────────────────────────────────


class TestRealQuestFileIntegration:
    """Проверяет, что реальный assets/data/quests.json загружается и работает в цикле."""

    def test_real_file_loads(self) -> None:
        quests = load_quests(DATA_DIR / "quests.json")
        assert len(quests) >= 1

    def test_real_starter_quest_fields(self) -> None:
        quests = load_quests(DATA_DIR / "quests.json")
        starter = quests[0]
        assert starter.id == "clear_bunker_a1"
        assert starter.reward_xp == 100
        obj = starter.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.target_count == 4

    def test_real_starter_quest_has_narrative_metadata(self) -> None:
        starter = load_quests(DATA_DIR / "quests.json")[0]
        assert starter.location == "Bunker A1"
        assert starter.category == "main_story"
        assert starter.lore_text != ""

    def test_loaded_quest_completes_and_grants_xp(self) -> None:
        exp = ExperienceComponent()
        qs = QuestSystem(exp)
        starter = load_quests(DATA_DIR / "quests.json")[0]
        qs.accept_quest(starter)
        for _ in range(4):
            EventBus.emit("entity_died", {"entity": FakeEntity("enemy")})
        assert starter.status == QuestStatus.COMPLETED
        assert exp.current_xp == 100
        # required_xp(1) == 100 → награды квеста хватает ровно на 2-й уровень
        assert exp.current_level == 2
        assert required_xp(1) == 100
