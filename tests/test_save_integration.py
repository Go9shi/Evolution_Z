"""Tests for Sprint 10B: Save Integration — F5 save / F9 load hooked into GameScreen."""
from __future__ import annotations

import json
from pathlib import Path

import pygame
import pytest

from entities.items.food_item import FoodItem
from main import GameStateManager
from systems.experience import required_xp
from systems.skill_tree import SkillType
from ui.game_screen import GameScreen

QUEST_ID = "clear_bunker_a1"
LORE_ID = "bunker_a1_origin"
FOOD_ID = "canned_beans"


# ── helpers ───────────────────────────────────────────────────────────────────


@pytest.fixture
def save_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Перенаправить единый файл сохранения GameScreen во временный каталог."""
    path = tmp_path / "savegame.json"
    monkeypatch.setattr(GameScreen, "_SAVE_PATH", path)
    return path


def make_game() -> tuple[GameStateManager, GameScreen]:
    manager = GameStateManager()
    screen = GameScreen(manager)
    manager.push(screen)
    return manager, screen


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def press(screen: GameScreen, key: int) -> None:
    screen.handle_event(key_event(key))


# ── F5: Save ──────────────────────────────────────────────────────────────────


class TestSaveHotkey:
    def test_f5_creates_save_file(self, save_path: Path) -> None:
        _, screen = make_game()
        press(screen, pygame.K_F5)
        assert save_path.exists()

    def test_f5_writes_valid_json(self, save_path: Path) -> None:
        _, screen = make_game()
        press(screen, pygame.K_F5)
        parsed = json.loads(save_path.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict)

    def test_f5_saves_current_state(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._player.add_xp(450)
        press(screen, pygame.K_F5)
        parsed = json.loads(save_path.read_text(encoding="utf-8"))
        assert parsed["player"]["xp"] == 450


# ── F9: Load ──────────────────────────────────────────────────────────────────


class TestLoadHotkey:
    def test_f9_loads_saved_state(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._player.add_xp(450)
        press(screen, pygame.K_F5)
        screen._player.add_xp(100)  # отклонить состояние от сохранённого (→ 550)
        press(screen, pygame.K_F9)
        assert screen._player.experience.current_xp == 450

    def test_f9_swaps_player_instance(self, save_path: Path) -> None:
        _, screen = make_game()
        press(screen, pygame.K_F5)
        original = screen._player
        press(screen, pygame.K_F9)
        assert screen._player is not original  # загрузка пересоздаёт игрока


# ── Интеграция: восстановление по каждой системе ───────────────────────────────


class TestIntegrationRestore:
    def test_xp_restored(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._player.add_xp(required_xp(2))
        press(screen, pygame.K_F5)
        press(screen, pygame.K_F9)
        assert screen._player.experience.current_xp == required_xp(2)
        assert screen._player.experience.current_level == 3

    def test_skills_restored(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._player.add_xp(required_xp(2))  # 2 очка
        screen._player.skill_tree.upgrade(SkillType.MAX_HEALTH, screen._player)
        press(screen, pygame.K_F5)
        press(screen, pygame.K_F9)
        assert screen._player.skill_tree.get_level(SkillType.MAX_HEALTH) == 1

    def test_inventory_restored(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._player.pickup_item(FoodItem(0.0, 0.0, FOOD_ID, "x", "y", 25.0))
        press(screen, pygame.K_F5)
        press(screen, pygame.K_F9)
        assert FOOD_ID in [item.item_id for item in screen._player.inventory.items]

    def test_quests_restored(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._quest_system.accept_quest(screen._quests[QUEST_ID])
        press(screen, pygame.K_F5)
        press(screen, pygame.K_F9)
        assert QUEST_ID in [q.id for q in screen._quest_system.active_quests]

    def test_lore_restored(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._lore_system.unlock(LORE_ID)
        press(screen, pygame.K_F5)
        press(screen, pygame.K_F9)
        assert screen._lore_system.is_unlocked(LORE_ID) is True

    def test_loaded_game_keeps_running(self, save_path: Path) -> None:
        _, screen = make_game()
        screen._player.add_xp(450)
        press(screen, pygame.K_F5)
        press(screen, pygame.K_F9)
        screen.update(0.016)  # игровой цикл продолжает работать после загрузки
        screen.draw(pygame.Surface((1280, 720)))


# ── Безопасность ──────────────────────────────────────────────────────────────


class TestSafety:
    def test_missing_file_does_not_crash(self, save_path: Path) -> None:
        _, screen = make_game()
        assert not save_path.exists()
        original = screen._player
        press(screen, pygame.K_F9)  # нет файла — нет-оп
        assert screen._player is original  # состояние не тронуто

    def test_corrupt_file_does_not_crash(self, save_path: Path) -> None:
        _, screen = make_game()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text("{ broken json", encoding="utf-8")
        original = screen._player
        press(screen, pygame.K_F9)  # битый файл — нет-оп
        assert screen._player is original

    def test_non_object_file_does_not_crash(self, save_path: Path) -> None:
        _, screen = make_game()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text("[1, 2, 3]", encoding="utf-8")
        original = screen._player
        press(screen, pygame.K_F9)
        assert screen._player is original
