"""Tests for Sprint 9D: Boss AI — chase, melee attack, and two phases for PatientZeroBoss."""
from __future__ import annotations

import pygame

from core.entity import Entity
from entities.boss import PatientZeroBoss
from entities.bullet import Bullet
from settings import (
    BOSS_ATTACK_COOLDOWN,
    BOSS_DAMAGE,
    BOSS_SPEED,
    BOSS_XP_REWARD,
)
from systems.combat import CombatSystem
from systems.event_bus import EventBus


# ── helpers ───────────────────────────────────────────────────────────────────


def make_boss(x: float = 300.0, y: float = 300.0, max_health: int = 100) -> PatientZeroBoss:
    return PatientZeroBoss(x, y, max_health)


def make_player(x: float = 300.0, y: float = 300.0, hp: int = 100) -> Entity:
    """Лёгкий стенд игрока: Entity имеет pos, take_damage и health."""
    return Entity(x, y, hp)


class Recorder:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, data: dict) -> None:
        self.calls.append(data)


# ── Создание ──────────────────────────────────────────────────────────────────


class TestCreation:
    def test_starts_in_phase_1(self) -> None:
        assert make_boss().phase == 1

    def test_phase_1_speed_is_base(self) -> None:
        assert make_boss().speed == BOSS_SPEED

    def test_phase_1_cooldown_is_base(self) -> None:
        assert make_boss().attack_cooldown == BOSS_ATTACK_COOLDOWN

    def test_can_attack_initially(self) -> None:
        assert make_boss().can_attack is True


# ── Преследование ─────────────────────────────────────────────────────────────


class TestChase:
    def test_moves_toward_player(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 500.0)  # в радиусе обнаружения, вне атаки
        before = boss.pos.distance_to(player.pos)
        boss.update(0.1, [], player)
        assert boss.pos.distance_to(player.pos) < before

    def test_moves_in_correct_direction(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 500.0)
        boss.update(0.1, [], player)
        assert boss.pos.y > 300.0  # двигался вниз, к игроку

    def test_chase_over_multiple_frames(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 600.0)
        start = boss.pos.distance_to(player.pos)
        for _ in range(10):
            boss.update(0.1, [], player)
        assert boss.pos.distance_to(player.pos) < start

    def test_does_not_move_when_player_out_of_range(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(3000.0, 3000.0)  # далеко за радиусом обнаружения
        boss.update(0.1, [], player)
        assert boss.pos == pygame.Vector2(300.0, 300.0)

    def test_no_player_is_safe(self) -> None:
        boss = make_boss(300.0, 300.0)
        boss.update(0.1, [], None)  # не должно падать
        assert boss.pos == pygame.Vector2(300.0, 300.0)


# ── Ближняя атака ─────────────────────────────────────────────────────────────


class TestMeleeAttack:
    def test_player_takes_damage_in_range(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 330.0, hp=100)  # в радиусе атаки
        boss.update(0.016, [], player)
        assert player.health.current == 100 - BOSS_DAMAGE

    def test_attack_uses_boss_damage(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 300.0, hp=100)
        boss.attack(player)
        assert player.health.current == 100 - BOSS_DAMAGE

    def test_cooldown_blocks_immediate_second_hit(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 330.0, hp=200)
        boss.update(0.016, [], player)  # первая атака
        hp_after_first = player.health.current
        boss.update(0.016, [], player)  # сразу — кулдаун не истёк
        assert player.health.current == hp_after_first

    def test_can_attack_false_after_attack(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 330.0)
        boss.update(0.016, [], player)
        assert boss.can_attack is False

    def test_attacks_again_after_cooldown(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 330.0, hp=200)
        boss.update(0.016, [], player)  # атака 1
        hp_after_first = player.health.current
        boss.update(BOSS_ATTACK_COOLDOWN + 0.1, [], player)  # кулдаун истёк → атака 2
        assert player.health.current < hp_after_first

    def test_does_not_attack_out_of_range(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 500.0, hp=100)  # вне радиуса атаки
        boss.update(0.016, [], player)
        assert player.health.current == 100


# ── Фазы ──────────────────────────────────────────────────────────────────────


class TestPhases:
    def test_phase_1_above_half_health(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(40)  # 60% HP
        assert boss.phase == 1

    def test_phase_2_at_half_health(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(50)  # ровно 50%
        assert boss.phase == 2

    def test_phase_2_below_half_health(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(70)  # 30%
        assert boss.phase == 2

    def test_phase_2_faster_than_phase_1(self) -> None:
        boss = make_boss(max_health=100)
        phase1_speed = boss.speed
        boss.take_damage(60)  # → фаза 2
        assert boss.speed > phase1_speed

    def test_phase_2_lower_cooldown(self) -> None:
        boss = make_boss(max_health=100)
        phase1_cooldown = boss.attack_cooldown
        boss.take_damage(60)  # → фаза 2
        assert boss.attack_cooldown < phase1_cooldown

    def test_phase_2_chases_faster(self) -> None:
        # За один кадр в фазе 2 босс проходит больше, чем в фазе 1.
        p1_boss = make_boss(300.0, 300.0, max_health=100)
        p2_boss = make_boss(300.0, 300.0, max_health=100)
        p2_boss.take_damage(60)  # → фаза 2
        # игрок в радиусе обнаружения (300 <= 400), вне радиуса атаки
        p1_boss.update(0.1, [], make_player(300.0, 600.0))
        p2_boss.update(0.1, [], make_player(300.0, 600.0))
        assert p2_boss.pos.y > p1_boss.pos.y


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_boss_death_still_works(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(100)
        assert boss.is_alive is False
        assert boss.active is False

    def test_boss_defeated_still_emitted(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        boss = make_boss(max_health=100)
        boss.take_damage(100)
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["boss"] is boss

    def test_combat_system_still_damages_boss(self) -> None:
        boss = make_boss(100.0, 100.0, max_health=500)
        combat = CombatSystem()
        bullet = Bullet(
            x=100.0, y=100.0,
            velocity=pygame.Vector2(0.0, 0.0),
            damage=25.0,
            max_range=350.0,
            size=5,
            origin_tag="player",
        )
        combat.add_bullets([bullet])
        combat.update(0.016, [], [boss])
        assert boss.health.current == 475

    def test_xp_reward_from_settings(self) -> None:
        assert make_boss().xp_reward == BOSS_XP_REWARD

    def test_walls_block_boss_movement(self) -> None:
        # Стена между боссом и игроком не даёт боссу пройти сквозь неё.
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 500.0)
        wall = pygame.Rect(250, 360, 100, 20)  # поперёк пути вниз
        for _ in range(20):
            boss.update(0.1, [wall], player)
        assert boss.rect.bottom <= wall.top
