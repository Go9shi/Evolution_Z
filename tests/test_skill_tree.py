"""Tests for Sprint 7B: SkillTree core logic + Player integration."""
from __future__ import annotations

import pytest
import pygame

from data.player_data import PlayerData
from data.weapon_config import WeaponConfig
from entities.player import Player
from entities.weapons.pistol import Pistol
from systems.event_bus import EventBus
from systems.skill_tree import (
    DAMAGE_PER_LEVEL,
    HP_PER_LEVEL,
    HUNGER_REDUCTION_PER_LEVEL,
    MAX_SKILL_LEVEL,
    SkillTree,
    SkillType,
)


# ── helpers ────────────────────────────────────────────────────────────────────


def make_player(hunger_decay_rate: float = 10.0) -> Player:
    config = PlayerData(
        max_health=100,
        speed=200.0,
        width=32,
        height=32,
        max_hunger=100.0,
        hunger_decay_rate=hunger_decay_rate,
        hunger_damage_rate=5.0,
    )
    return Player(0.0, 0.0, config)


def make_pistol(damage: float = 25.0) -> Pistol:
    return Pistol(
        WeaponConfig(
            damage=damage,
            fire_rate=2.0,
            bullet_speed=400.0,
            bullet_range=350.0,
            bullet_size=5,
        )
    )


def make_tree() -> SkillTree:
    return SkillTree()


# ── TestSkillTreeInitial ───────────────────────────────────────────────────────


class TestSkillTreeInitial:
    def test_available_points_zero(self) -> None:
        assert make_tree().available_points == 0

    def test_all_skill_levels_zero(self) -> None:
        tree = make_tree()
        for skill in SkillType:
            assert tree.get_level(skill) == 0

    def test_can_upgrade_false_without_points(self) -> None:
        tree = make_tree()
        for skill in SkillType:
            assert tree.can_upgrade(skill) is False


# ── TestAddPoint ──────────────────────────────────────────────────────────────


class TestAddPoint:
    def test_increments_available_points(self) -> None:
        tree = make_tree()
        tree.add_point()
        assert tree.available_points == 1

    def test_multiple_calls_accumulate(self) -> None:
        tree = make_tree()
        for _ in range(3):
            tree.add_point()
        assert tree.available_points == 3


# ── TestCanUpgrade ─────────────────────────────────────────────────────────────


class TestCanUpgrade:
    def test_false_with_no_points(self) -> None:
        assert make_tree().can_upgrade(SkillType.MAX_HEALTH) is False

    def test_true_with_point_and_below_max(self) -> None:
        tree = make_tree()
        tree.add_point()
        assert tree.can_upgrade(SkillType.MAX_HEALTH) is True

    def test_false_at_max_level_even_with_points(self) -> None:
        player = make_player()
        tree = make_tree()
        for _ in range(MAX_SKILL_LEVEL):
            tree.add_point()
            tree.upgrade(SkillType.MAX_HEALTH, player)
        tree.add_point()
        assert tree.can_upgrade(SkillType.MAX_HEALTH) is False

    def test_other_skill_still_upgradeable_at_max(self) -> None:
        player = make_player()
        tree = make_tree()
        for _ in range(MAX_SKILL_LEVEL):
            tree.add_point()
            tree.upgrade(SkillType.MAX_HEALTH, player)
        tree.add_point()
        assert tree.can_upgrade(SkillType.HUNGER_EFFICIENCY) is True


# ── TestUpgrade ───────────────────────────────────────────────────────────────


class TestUpgrade:
    def test_returns_false_without_points(self) -> None:
        assert make_tree().upgrade(SkillType.MAX_HEALTH, make_player()) is False

    def test_returns_true_on_success(self) -> None:
        tree = make_tree()
        tree.add_point()
        assert tree.upgrade(SkillType.MAX_HEALTH, make_player()) is True

    def test_consumes_one_point(self) -> None:
        player = make_player()
        tree = make_tree()
        tree.add_point()
        tree.add_point()
        tree.upgrade(SkillType.MAX_HEALTH, player)
        assert tree.available_points == 1

    def test_increases_skill_level(self) -> None:
        player = make_player()
        tree = make_tree()
        tree.add_point()
        tree.upgrade(SkillType.MAX_HEALTH, player)
        assert tree.get_level(SkillType.MAX_HEALTH) == 1

    def test_returns_false_at_max_level(self) -> None:
        player = make_player()
        tree = make_tree()
        for _ in range(MAX_SKILL_LEVEL):
            tree.add_point()
            tree.upgrade(SkillType.MAX_HEALTH, player)
        tree.add_point()
        assert tree.upgrade(SkillType.MAX_HEALTH, player) is False

    def test_failed_upgrade_does_not_consume_point(self) -> None:
        tree = make_tree()
        tree.upgrade(SkillType.MAX_HEALTH, make_player())
        assert tree.available_points == 0


# ── TestUpgradeMaxHealth ──────────────────────────────────────────────────────


class TestUpgradeMaxHealth:
    def test_increases_maximum_hp(self) -> None:
        player = make_player()
        tree = make_tree()
        tree.add_point()
        tree.upgrade(SkillType.MAX_HEALTH, player)
        assert player.health.maximum == pytest.approx(100 + HP_PER_LEVEL)

    def test_increases_current_hp_at_full_health(self) -> None:
        player = make_player()
        tree = make_tree()
        tree.add_point()
        tree.upgrade(SkillType.MAX_HEALTH, player)
        assert player.health.current == pytest.approx(100 + HP_PER_LEVEL)

    def test_current_hp_increases_at_partial_hp(self) -> None:
        player = make_player()
        player.health.take_damage(50)  # 50/100
        tree = make_tree()
        tree.add_point()
        tree.upgrade(SkillType.MAX_HEALTH, player)
        # current: min(50 + HP_PER_LEVEL, 120) = 70; maximum: 120
        assert player.health.maximum == pytest.approx(100 + HP_PER_LEVEL)
        assert player.health.current == pytest.approx(50 + HP_PER_LEVEL)

    def test_multiple_upgrades_stack(self) -> None:
        player = make_player()
        tree = make_tree()
        for _ in range(3):
            tree.add_point()
            tree.upgrade(SkillType.MAX_HEALTH, player)
        assert player.health.maximum == pytest.approx(100 + 3 * HP_PER_LEVEL)


# ── TestUpgradeHungerEfficiency ───────────────────────────────────────────────


class TestUpgradeHungerEfficiency:
    def test_reduces_hunger_decay_rate(self) -> None:
        player = make_player(hunger_decay_rate=10.0)
        tree = make_tree()
        tree.add_point()
        tree.upgrade(SkillType.HUNGER_EFFICIENCY, player)
        player.hunger.update(1.0)
        expected = 100.0 - (10.0 - HUNGER_REDUCTION_PER_LEVEL)
        assert player.hunger.current == pytest.approx(expected)

    def test_multiple_upgrades_stack(self) -> None:
        player = make_player(hunger_decay_rate=10.0)
        tree = make_tree()
        for _ in range(2):
            tree.add_point()
            tree.upgrade(SkillType.HUNGER_EFFICIENCY, player)
        player.hunger.update(1.0)
        expected = 100.0 - (10.0 - 2 * HUNGER_REDUCTION_PER_LEVEL)
        assert player.hunger.current == pytest.approx(expected)

    def test_decay_rate_does_not_go_below_zero(self) -> None:
        # decay_rate=0.3, reduction=0.5 → max(0.0, 0.3-0.5) = 0.0
        player = make_player(hunger_decay_rate=0.3)
        tree = make_tree()
        tree.add_point()
        tree.upgrade(SkillType.HUNGER_EFFICIENCY, player)
        player.hunger.update(1.0)
        assert player.hunger.current == pytest.approx(100.0)  # no hunger loss


# ── TestUpgradePistolDamage ───────────────────────────────────────────────────


class TestUpgradePistolDamage:
    def test_increases_bullet_damage(self) -> None:
        player = make_player()
        pistol = make_pistol(damage=25.0)
        player.equip(pistol)

        bullets_before = player.fire(pygame.Vector2(1, 0))
        assert bullets_before[0].damage == pytest.approx(25.0)

        player.skill_tree.add_point()
        player.skill_tree.upgrade(SkillType.PISTOL_DAMAGE, player)

        pistol.update(9999.0)  # reset cooldown
        bullets_after = player.fire(pygame.Vector2(1, 0))
        assert bullets_after[0].damage == pytest.approx(25.0 + DAMAGE_PER_LEVEL)

    def test_multiple_upgrades_stack(self) -> None:
        player = make_player()
        pistol = make_pistol(damage=25.0)
        player.equip(pistol)

        for _ in range(3):
            player.skill_tree.add_point()
            player.skill_tree.upgrade(SkillType.PISTOL_DAMAGE, player)
            pistol.update(9999.0)

        bullets = player.fire(pygame.Vector2(1, 0))
        assert bullets[0].damage == pytest.approx(25.0 + 3 * DAMAGE_PER_LEVEL)

    def test_no_weapon_upgrade_records_level_without_crashing(self) -> None:
        player = make_player()  # no weapon equipped
        player.skill_tree.add_point()
        result = player.skill_tree.upgrade(SkillType.PISTOL_DAMAGE, player)
        assert result is True
        assert player.skill_tree.get_level(SkillType.PISTOL_DAMAGE) == 1


# ── TestMultipleSkills ────────────────────────────────────────────────────────


class TestMultipleSkills:
    def test_upgrades_are_independent(self) -> None:
        player = make_player()
        tree = make_tree()
        tree.add_point()
        tree.upgrade(SkillType.MAX_HEALTH, player)
        tree.add_point()
        tree.upgrade(SkillType.HUNGER_EFFICIENCY, player)

        assert tree.get_level(SkillType.MAX_HEALTH) == 1
        assert tree.get_level(SkillType.HUNGER_EFFICIENCY) == 1
        assert tree.get_level(SkillType.PISTOL_DAMAGE) == 0

    def test_each_upgrade_costs_one_point(self) -> None:
        player = make_player()
        tree = make_tree()
        for _ in range(3):
            tree.add_point()
        tree.upgrade(SkillType.MAX_HEALTH, player)
        tree.upgrade(SkillType.HUNGER_EFFICIENCY, player)
        assert tree.available_points == 1

    def test_max_level_per_skill_respected_independently(self) -> None:
        player = make_player()
        tree = make_tree()
        for _ in range(MAX_SKILL_LEVEL):
            tree.add_point()
            tree.upgrade(SkillType.MAX_HEALTH, player)
        # HUNGER_EFFICIENCY still upgradeable
        tree.add_point()
        assert tree.can_upgrade(SkillType.HUNGER_EFFICIENCY) is True
        assert tree.can_upgrade(SkillType.MAX_HEALTH) is False


# ── TestSkillUpgradeEvent ─────────────────────────────────────────────────────


class TestSkillUpgradeEvent:
    def test_emits_skill_upgraded_on_success(self) -> None:
        received: list[dict] = []
        EventBus.on("skill_upgraded", received.append)
        player = make_player()
        player.skill_tree.add_point()
        player.skill_tree.upgrade(SkillType.MAX_HEALTH, player)
        assert len(received) == 1

    def test_event_contains_skill_and_level(self) -> None:
        received: list[dict] = []
        EventBus.on("skill_upgraded", received.append)
        player = make_player()
        player.skill_tree.add_point()
        player.skill_tree.upgrade(SkillType.MAX_HEALTH, player)
        assert received[0]["skill"] == SkillType.MAX_HEALTH
        assert received[0]["level"] == 1

    def test_no_event_on_failed_upgrade(self) -> None:
        received: list[dict] = []
        EventBus.on("skill_upgraded", received.append)
        make_tree().upgrade(SkillType.MAX_HEALTH, make_player())
        assert len(received) == 0


# ── TestPlayerSkillTreeIntegration ───────────────────────────────────────────


class TestPlayerSkillTreeIntegration:
    def test_player_has_skill_tree(self) -> None:
        assert isinstance(make_player().skill_tree, SkillTree)

    def test_level_up_grants_one_skill_point(self) -> None:
        player = make_player()
        player.add_xp(100)  # required_xp(1) = 100 → level 2
        assert player.skill_tree.available_points == 1

    def test_multiple_level_ups_grant_multiple_points(self) -> None:
        player = make_player()
        # 350 XP → level 2 (xp≥100) then level 3 (xp≥300); two player_level_up events
        player.add_xp(350)
        assert player.skill_tree.available_points == 2

    def test_no_level_up_no_skill_point(self) -> None:
        player = make_player()
        player.add_xp(50)  # below required_xp(1)=100
        assert player.skill_tree.available_points == 0

    def test_skill_point_spendable_after_level_up(self) -> None:
        player = make_player()
        player.add_xp(100)
        result = player.skill_tree.upgrade(SkillType.MAX_HEALTH, player)
        assert result is True
        assert player.skill_tree.available_points == 0
