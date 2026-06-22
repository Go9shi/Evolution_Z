"""Tests for Sprint 10A: PatientZeroBoss patrol outside combat."""
from __future__ import annotations

import pygame

from core.entity import Entity
from data.enemy_data import EnemyData
from entities.boss import PatientZeroBoss
from settings import (
    BOSS_DETECTION_RANGE,
    BOSS_PATROL_RADIUS,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def walker_config() -> EnemyData:
    return EnemyData(
        max_health=80, speed=60.0, damage=15.0, attack_range=40.0,
        detection_range=180.0, attack_cooldown=1.5, width=32, height=32, xp_reward=10,
    )


def make_boss(x: float = 300.0, y: float = 300.0, hp: int = 100, *, minions: bool = False) -> PatientZeroBoss:
    return PatientZeroBoss(x, y, hp, walker_config() if minions else None)


def far_player(boss: PatientZeroBoss) -> Entity:
    """Игрок заведомо вне радиуса обнаружения босса (→ патруль)."""
    return Entity(boss.pos.x + BOSS_DETECTION_RANGE + 500.0, boss.pos.y, 100)


def near_player(boss: PatientZeroBoss) -> Entity:
    """Игрок внутри радиуса обнаружения, вне melee (→ преследование)."""
    return Entity(boss.pos.x + BOSS_DETECTION_RANGE / 2.0, boss.pos.y, 100)


def to_phase2(boss: PatientZeroBoss) -> None:
    boss.take_damage(boss.health.maximum * 0.6)
    assert boss.phase == 2
    assert boss.is_alive


# ── Создание ──────────────────────────────────────────────────────────────────


class TestPatrolSetup:
    def test_anchor_is_spawn(self) -> None:
        boss = make_boss(300.0, 400.0)
        assert boss._patrol_anchor == pygame.Vector2(300.0, 400.0)

    def test_has_several_points(self) -> None:
        assert len(make_boss()._patrol_points) >= 3  # «несколько точек»

    def test_first_target_is_anchor_plus_first_point(self) -> None:
        boss = make_boss(300.0, 300.0)
        assert boss.patrol_target == boss._patrol_anchor + boss._patrol_points[0]


# ── Движение патруля ───────────────────────────────────────────────────────────


class TestPatrolMovement:
    def test_moves_when_player_undetected(self) -> None:
        boss = make_boss(300.0, 300.0)
        start = pygame.Vector2(boss.pos)
        boss.update(0.1, [], far_player(boss))
        assert boss.pos != start

    def test_moves_toward_first_waypoint(self) -> None:
        boss = make_boss(300.0, 300.0)
        target = pygame.Vector2(boss.patrol_target)
        before = boss.pos.distance_to(target)
        boss.update(0.1, [], far_player(boss))
        assert boss.pos.distance_to(target) < before

    def test_stays_near_anchor(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = far_player(boss)
        for _ in range(200):
            boss.update(0.1, [], player)
        # Патруль не уводит босса дальше радиуса (+допуск шага) от якоря.
        assert boss.pos.distance_to(boss._patrol_anchor) <= BOSS_PATROL_RADIUS + 50.0

    def test_advances_through_waypoints(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = far_player(boss)
        seen = {boss._patrol_index}
        for _ in range(400):
            boss.update(0.1, [], player)
            seen.add(boss._patrol_index)
        assert len(seen) >= 2  # обходит несколько точек циклически

    def test_no_player_does_not_patrol(self) -> None:
        boss = make_boss(300.0, 300.0)
        start = pygame.Vector2(boss.pos)
        boss.update(0.1, [], None)
        assert boss.pos == start


# ── Переходы патруль ↔ бой ─────────────────────────────────────────────────────


class TestPatrolCombatTransitions:
    def test_detection_stops_patrol_and_chases(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = near_player(boss)  # обнаружен, вне атаки
        before = boss.pos.distance_to(player.pos)
        boss.update(0.1, [], player)
        assert boss.pos.distance_to(player.pos) < before  # двигался к игроку, не к точке

    def test_returns_to_patrol_after_losing_player(self) -> None:
        boss = make_boss(300.0, 300.0)
        boss.update(0.1, [], near_player(boss))  # бой (преследование)
        pos_after_chase = pygame.Vector2(boss.pos)
        boss.update(0.1, [], far_player(boss))  # игрок потерян → патруль
        assert boss.pos != pos_after_chase  # снова движется (патруль возобновлён)


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_melee_still_works(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = Entity(300.0, 330.0, 100)  # в melee-радиусе
        before = player.health.current
        boss.update(0.016, [], player)
        assert player.health.current < before

    def test_acid_still_fires_when_detected(self) -> None:
        boss = make_boss(300.0, 300.0)
        to_phase2(boss)
        boss.update(0.1, [], near_player(boss))
        assert len(boss.collect_spawned_bullets()) == 1

    def test_summon_still_fires_when_detected(self) -> None:
        boss = make_boss(300.0, 300.0, minions=True)
        to_phase2(boss)
        boss.update(0.1, [], near_player(boss))
        assert len(boss.collect_spawned_minions()) == 1

    def test_patrol_does_not_spawn_specials(self) -> None:
        boss = make_boss(300.0, 300.0, minions=True)
        to_phase2(boss)
        boss.update(0.1, [], far_player(boss))  # вне обнаружения
        assert boss.collect_spawned_bullets() == []
        assert boss.collect_spawned_minions() == []

    def test_phase_switch_unaffected_by_patrol(self) -> None:
        boss = make_boss(300.0, 300.0)
        boss.update(0.1, [], far_player(boss))  # патрулирует в фазе 1
        assert boss.phase == 1
        to_phase2(boss)
        boss.update(0.1, [], far_player(boss))  # патрулирует в фазе 2
        assert boss.phase == 2

    def test_boss_defeated_still_emits(self) -> None:
        from systems.event_bus import EventBus
        events: list[dict] = []
        EventBus.on("boss_defeated", events.append)
        boss = make_boss(300.0, 300.0)
        boss.take_damage(boss.health.maximum)
        assert len(events) == 1

    def test_patrol_respects_walls(self) -> None:
        boss = make_boss(300.0, 300.0)
        # Стена вплотную справа (по направлению к первой точке) не пропускает босса.
        wall = pygame.Rect(int(boss.pos.x) + 20, int(boss.pos.y) - 40, 20, 80)
        for _ in range(50):
            boss.update(0.1, [wall], far_player(boss))
        assert not boss.rect.colliderect(wall)
