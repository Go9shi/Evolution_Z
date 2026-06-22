"""Tests for Sprint 10A: Save System — capture/serialize/restore minimal game state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data.lore_data import LoreEntry
from data.player_data import PlayerData
from data.quest_loader import load_quests
from data.save_file import SaveData
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from entities.player import Player
from settings import DATA_DIR
from systems.experience import required_xp
from systems.lore import LoreSystem
from systems.quest_system import QuestSystem
from systems.save_system import SaveError, SaveSystem
from systems.skill_tree import SkillType

# Реальные id из assets/data/*.json
FOOD_ID = "canned_beans"
QUEST_ITEM_ID = "vaccine_component_alpha"
QUEST_ID = "clear_bunker_a1"
LORE_ID = "bunker_a1_origin"


# ── helpers ───────────────────────────────────────────────────────────────────


def make_player() -> Player:
    config = PlayerData(
        max_health=100,
        speed=200.0,
        width=32,
        height=32,
        max_hunger=100.0,
        hunger_decay_rate=0.0,
        hunger_damage_rate=5.0,
    )
    return Player(0.0, 0.0, config)


def make_quests(player: Player) -> QuestSystem:
    return QuestSystem(player.experience)


def make_lore() -> LoreSystem:
    lore = LoreSystem()
    lore.register(LoreEntry(id=LORE_ID, title="Origin", text="Body", category="terminal"))
    return lore


def starter_quest():  # type: ignore[no-untyped-def]
    """Реальный квест уровня из quests.json (свежий экземпляр, статус AVAILABLE)."""
    return load_quests(DATA_DIR / "quests.json")[0]


def save_path(tmp_path: Path) -> Path:
    return tmp_path / "slot.json"


# ── Save ──────────────────────────────────────────────────────────────────────


class TestSave:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        player = make_player()
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())
        assert path.exists()

    def test_saved_file_is_valid_json(self, tmp_path: Path) -> None:
        player = make_player()
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())
        parsed = json.loads(path.read_text(encoding="utf-8"))  # не падает
        assert isinstance(parsed, dict)

    def test_saved_file_has_expected_sections(self, tmp_path: Path) -> None:
        player = make_player()
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())
        parsed = json.loads(path.read_text(encoding="utf-8"))
        assert set(parsed) == {"player", "skills", "inventory", "quests", "lore", "map"}


# ── SaveData (модель данных) ───────────────────────────────────────────────────


class TestSaveData:
    def test_to_from_dict_roundtrip(self) -> None:
        data = SaveData(
            player_xp=300,
            player_level=3,
            skill_levels={"MAX_HEALTH": 2},
            inventory_item_ids=[FOOD_ID],
            active_quest_ids=[QUEST_ID],
            completed_quest_ids=["other"],
            unlocked_lore_ids=[LORE_ID],
        )
        restored = SaveData.from_dict(data.to_dict())
        assert restored == data

    def test_from_dict_empty_defaults(self) -> None:
        data = SaveData.from_dict({})
        assert data == SaveData()


# ── Load + Safety ──────────────────────────────────────────────────────────────


class TestLoadSafety:
    def test_load_roundtrip(self, tmp_path: Path) -> None:
        player = make_player()
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())
        data = SaveSystem().load(path)
        assert isinstance(data, SaveData)

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(SaveError):
            SaveSystem().load(tmp_path / "nope.json")

    def test_corrupt_json_raises(self, tmp_path: Path) -> None:
        path = save_path(tmp_path)
        path.write_text("{ not valid json", encoding="utf-8")
        with pytest.raises(SaveError):
            SaveSystem().load(path)

    def test_non_object_json_raises(self, tmp_path: Path) -> None:
        path = save_path(tmp_path)
        path.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(SaveError):
            SaveSystem().load(path)

    def test_empty_save_loads_defaults(self, tmp_path: Path) -> None:
        path = save_path(tmp_path)
        path.write_text("{}", encoding="utf-8")
        data = SaveSystem().load(path)
        assert data == SaveData()

    def test_apply_empty_save_is_safe(self, tmp_path: Path) -> None:
        path = save_path(tmp_path)
        path.write_text("{}", encoding="utf-8")
        player = make_player()
        quests = make_quests(player)
        lore = make_lore()
        SaveSystem().load_into(path, player, quests, lore)  # не падает
        assert player.experience.current_xp == 0
        assert player.inventory.count == 0


# ── Experience ─────────────────────────────────────────────────────────────────


class TestExperience:
    def test_xp_restored(self, tmp_path: Path) -> None:
        player = make_player()
        player.add_xp(450)
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        assert fresh.experience.current_xp == 450

    def test_level_restored(self, tmp_path: Path) -> None:
        player = make_player()
        player.add_xp(required_xp(2))  # достигает уровня 3
        original_level = player.experience.current_level
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        assert fresh.experience.current_level == original_level
        assert original_level == 3


# ── Skill Tree ─────────────────────────────────────────────────────────────────


class TestSkillTree:
    def test_skill_levels_restored(self, tmp_path: Path) -> None:
        player = make_player()
        player.add_xp(required_xp(2))  # уровень 3 → 2 очка навыков
        assert player.skill_tree.upgrade(SkillType.MAX_HEALTH, player) is True
        assert player.skill_tree.upgrade(SkillType.HUNGER_EFFICIENCY, player) is True
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        assert fresh.skill_tree.get_level(SkillType.MAX_HEALTH) == 1
        assert fresh.skill_tree.get_level(SkillType.HUNGER_EFFICIENCY) == 1
        assert fresh.skill_tree.get_level(SkillType.PISTOL_DAMAGE) == 0

    def test_skill_effect_reapplied(self, tmp_path: Path) -> None:
        player = make_player()
        player.add_xp(required_xp(1))  # уровень 2 → 1 очко
        player.skill_tree.upgrade(SkillType.MAX_HEALTH, player)
        boosted_max = player.health.maximum
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        assert fresh.health.maximum == boosted_max

    def test_available_points_preserved(self, tmp_path: Path) -> None:
        # 2 заработанных очка, потрачено 1 → 1 свободное должно остаться после загрузки.
        player = make_player()
        player.add_xp(required_xp(2))  # 2 очка
        player.skill_tree.upgrade(SkillType.MAX_HEALTH, player)  # потрачено 1
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        assert fresh.skill_tree.available_points == 1


# ── Inventory ──────────────────────────────────────────────────────────────────


class TestInventory:
    def test_items_restored(self, tmp_path: Path) -> None:
        player = make_player()
        player.pickup_item(FoodItem(0.0, 0.0, FOOD_ID, "x", "y", 25.0))
        player.pickup_item(QuestItem(0.0, 0.0, QUEST_ITEM_ID, "x", "y"))
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        ids = [item.item_id for item in fresh.inventory.items]
        assert FOOD_ID in ids
        assert QUEST_ITEM_ID in ids

    def test_restored_food_is_usable_type(self, tmp_path: Path) -> None:
        player = make_player()
        player.pickup_item(FoodItem(0.0, 0.0, FOOD_ID, "x", "y", 25.0))
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        restored = fresh.inventory.items[0]
        assert isinstance(restored, FoodItem)

    def test_unknown_item_id_skipped(self, tmp_path: Path) -> None:
        path = save_path(tmp_path)
        SaveData(inventory_item_ids=["does_not_exist"]).to_dict()
        path.write_text(
            json.dumps(SaveData(inventory_item_ids=["does_not_exist"]).to_dict()),
            encoding="utf-8",
        )
        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        assert fresh.inventory.count == 0  # неизвестный id пропущен, без падения


# ── Quest System ───────────────────────────────────────────────────────────────


class TestQuests:
    def test_active_quest_restored(self, tmp_path: Path) -> None:
        player = make_player()
        quests = make_quests(player)
        quests.accept_quest(starter_quest())
        path = save_path(tmp_path)
        SaveSystem().save(path, player, quests, make_lore())

        fresh = make_player()
        fresh_quests = make_quests(fresh)
        SaveSystem().load_into(path, fresh, fresh_quests, make_lore())
        assert [q.id for q in fresh_quests.active_quests] == [QUEST_ID]
        assert fresh_quests.completed_quests == []

    def test_completed_quest_restored(self, tmp_path: Path) -> None:
        player = make_player()
        quests = make_quests(player)
        quest = starter_quest()
        quests.accept_quest(quest)
        quests.complete_quest(quest)  # → completed
        path = save_path(tmp_path)
        SaveSystem().save(path, player, quests, make_lore())

        fresh = make_player()
        fresh_quests = make_quests(fresh)
        SaveSystem().load_into(path, fresh, fresh_quests, make_lore())
        assert [q.id for q in fresh_quests.completed_quests] == [QUEST_ID]
        assert fresh_quests.active_quests == []

    def test_restore_does_not_regrant_quest_xp(self, tmp_path: Path) -> None:
        # Завершённый квест восстанавливается без повторной выдачи reward_xp.
        player = make_player()
        quests = make_quests(player)
        quest = starter_quest()
        quests.accept_quest(quest)
        quests.complete_quest(quest)
        saved_xp = player.experience.current_xp
        path = save_path(tmp_path)
        SaveSystem().save(path, player, quests, make_lore())

        fresh = make_player()
        SaveSystem().load_into(path, fresh, make_quests(fresh), make_lore())
        assert fresh.experience.current_xp == saved_xp


# ── Lore ───────────────────────────────────────────────────────────────────────


class TestLore:
    def test_unlocked_lore_restored(self, tmp_path: Path) -> None:
        player = make_player()
        lore = make_lore()
        lore.unlock(LORE_ID)
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), lore)

        fresh = make_player()
        fresh_lore = make_lore()  # каталог зарегистрирован
        SaveSystem().load_into(path, fresh, make_quests(fresh), fresh_lore)
        assert fresh_lore.is_unlocked(LORE_ID) is True

    def test_locked_lore_not_restored(self, tmp_path: Path) -> None:
        player = make_player()
        lore = make_lore()  # запись зарегистрирована, но НЕ открыта
        path = save_path(tmp_path)
        SaveSystem().save(path, player, make_quests(player), lore)

        fresh = make_player()
        fresh_lore = make_lore()
        SaveSystem().load_into(path, fresh, make_quests(fresh), fresh_lore)
        assert fresh_lore.unlocked_entries == []


# ── Full round-trip (интеграционный smoke) ─────────────────────────────────────


class TestFullRoundTrip:
    def test_capture_apply_capture_identical(self, tmp_path: Path) -> None:
        player = make_player()
        player.add_xp(required_xp(2))
        player.skill_tree.upgrade(SkillType.MAX_HEALTH, player)
        player.pickup_item(FoodItem(0.0, 0.0, FOOD_ID, "x", "y", 25.0))
        quests = make_quests(player)
        quests.accept_quest(starter_quest())
        lore = make_lore()
        lore.unlock(LORE_ID)

        system = SaveSystem()
        original = system.capture(player, quests, lore)

        path = save_path(tmp_path)
        system.save(path, player, quests, lore)

        fresh = make_player()
        fresh_quests = make_quests(fresh)
        fresh_lore = make_lore()
        system.load_into(path, fresh, fresh_quests, fresh_lore)
        restored = system.capture(fresh, fresh_quests, fresh_lore)

        assert restored == original
