"""Tests for Sprint 10C: HUD — read-only overlay for health, hunger, level/XP, quests."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from data.player_data import PlayerData
from data.quest_data import KillZombieObjective, Quest
from entities.player import Player
from main import GameStateManager
from systems.experience import ExperienceComponent
from systems.quest_system import QuestSystem
from ui.game_screen import GameScreen
from ui.hud import HUD


# ── helpers ───────────────────────────────────────────────────────────────────


def make_player(decay_rate: float = 0.0) -> Player:
    config = PlayerData(
        max_health=100,
        speed=200.0,
        width=32,
        height=32,
        max_hunger=100.0,
        hunger_decay_rate=decay_rate,
        hunger_damage_rate=5.0,
    )
    return Player(0.0, 0.0, config)


def make_quests(player: Player | None = None) -> QuestSystem:
    exp = player.experience if player is not None else ExperienceComponent()
    return QuestSystem(exp)


def make_quest(quest_id: str = "q", target: int = 5) -> Quest:
    return Quest(
        id=quest_id,
        title=f"Kill {target} Zombies",
        description="Thin the horde.",
        reward_xp=50,
        objectives=[KillZombieObjective(target_count=target)],
    )


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


# ── HUD ─────────────────────────────────────────────────────────────────────────


class TestHUD:
    def test_creation(self) -> None:
        assert HUD() is not None

    def test_draw_empty_state(self) -> None:
        player = make_player()
        HUD().draw(surface(), player, make_quests(player))  # без квестов — не падает

    def test_draw_full_hp(self) -> None:
        player = make_player()
        assert player.health.percentage == 1.0
        HUD().draw(surface(), player, make_quests(player))

    def test_draw_low_hp(self) -> None:
        player = make_player()
        player.take_damage(95)
        HUD().draw(surface(), player, make_quests(player))

    def test_draw_zero_hunger(self) -> None:
        player = make_player(decay_rate=100.0)
        player.hunger.update(2.0)  # 100 - 200 → 0
        assert player.hunger.percentage == 0.0
        HUD().draw(surface(), player, make_quests(player))

    def test_draw_multiple_active_quests(self) -> None:
        player = make_player()
        quests = make_quests(player)
        quests.accept_quest(make_quest("q1", target=3))
        quests.accept_quest(make_quest("q2", target=5))
        HUD().draw(surface(), player, quests)

    def test_draw_after_player_state_change(self) -> None:
        player = make_player()
        hud = HUD()
        hud.draw(surface(), player, make_quests(player))
        player.take_damage(40)
        player.add_xp(120)
        hud.draw(surface(), player, make_quests(player))  # читает изменённое состояние

    def test_hud_holds_no_game_state(self) -> None:
        # HUD не кэширует игровые объекты — читает их каждый кадр из аргументов draw.
        hud = HUD()
        assert not hasattr(hud, "_player")
        assert not hasattr(hud, "_quest_system")


# ── Интеграция с GameScreen ──────────────────────────────────────────────────────


class TestGameScreenIntegration:
    def test_gamescreen_has_hud(self) -> None:
        screen = GameScreen()
        assert isinstance(screen._hud, HUD)

    def test_gamescreen_draw_runs_with_hud(self) -> None:
        screen = GameScreen()
        screen.draw(surface())  # полный кадр с HUD — не падает

    def test_hud_reads_passed_objects_not_stored(self) -> None:
        # Один HUD рисует двух разных игроков — значит читает аргументы, а не копию.
        hud = HUD()
        a = make_player()
        b = make_player()
        b.add_xp(500)
        hud.draw(surface(), a, make_quests(a))
        hud.draw(surface(), b, make_quests(b))

    def test_after_f9_draw_still_works(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(GameScreen, "_SAVE_PATH", tmp_path / "savegame.json")
        manager = GameStateManager()
        screen = GameScreen(manager)
        manager.push(screen)

        screen._player.add_xp(450)
        screen.handle_event(key_event(pygame.K_F5))
        hud_before = screen._hud
        screen.handle_event(key_event(pygame.K_F9))  # подменяет _player/_quest_system

        assert screen._hud is hud_before  # HUD создан один раз
        screen.draw(surface())  # HUD рисует уже новые объекты — не падает
        assert screen._player.experience.current_xp == 450
