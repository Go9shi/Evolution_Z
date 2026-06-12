"""Tests for Sprint 9B: Patient Zero Boss Core — Entity, faction, damage, death, boss_defeated."""
from __future__ import annotations

import pygame

from core.entity import Entity
from entities.boss import Boss, PatientZeroBoss
from entities.bullet import Bullet
from settings import TILE_SIZE
from systems.combat import CombatSystem
from systems.event_bus import EventBus


# ── helpers ───────────────────────────────────────────────────────────────────


def make_boss(x: float = 300.0, y: float = 300.0, max_health: int = 500) -> PatientZeroBoss:
    return PatientZeroBoss(x, y, max_health)


class Recorder:
    """Записывает данные событий EventBus для проверок."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, data: dict) -> None:
        self.calls.append(data)


# ── Создание ──────────────────────────────────────────────────────────────────


class TestCreation:
    def test_type(self) -> None:
        assert isinstance(make_boss(), PatientZeroBoss)

    def test_inherits_boss(self) -> None:
        assert isinstance(make_boss(), Boss)

    def test_inherits_entity(self) -> None:
        assert isinstance(make_boss(), Entity)

    def test_faction_is_enemy(self) -> None:
        assert make_boss().faction == "enemy"

    def test_has_own_max_health(self) -> None:
        assert make_boss(max_health=750).health.maximum == 750

    def test_starts_at_full_health(self) -> None:
        boss = make_boss(max_health=500)
        assert boss.health.current == 500

    def test_starts_alive(self) -> None:
        assert make_boss().is_alive is True

    def test_starts_active(self) -> None:
        assert make_boss().active is True

    def test_has_rect(self) -> None:
        boss = make_boss(x=300.0, y=300.0)
        assert isinstance(boss.rect, pygame.Rect)
        assert boss.rect.center == (300, 300)

    def test_rect_size_from_settings(self) -> None:
        boss = make_boss()
        assert boss.rect.width == TILE_SIZE * 2
        assert boss.rect.height == TILE_SIZE * 2


# ── Получение урона ───────────────────────────────────────────────────────────


class TestTakeDamage:
    def test_damage_reduces_health(self) -> None:
        boss = make_boss(max_health=500)
        boss.take_damage(120)
        assert boss.health.current == 380

    def test_multiple_hits_accumulate(self) -> None:
        boss = make_boss(max_health=500)
        boss.take_damage(100)
        boss.take_damage(50)
        boss.take_damage(25)
        assert boss.health.current == 325

    def test_health_not_below_zero(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(250)  # избыточный урон
        assert boss.health.current == 0

    def test_non_lethal_damage_keeps_alive_and_active(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(40)
        assert boss.is_alive is True
        assert boss.active is True


# ── Смерть ────────────────────────────────────────────────────────────────────


class TestDeath:
    def test_deactivates_on_death(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(100)
        assert boss.active is False

    def test_dies_on_exact_damage(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(100)
        assert boss.is_alive is False

    def test_dies_on_excess_damage(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(500)
        assert boss.is_alive is False

    def test_alive_just_below_lethal(self) -> None:
        boss = make_boss(max_health=100)
        boss.take_damage(99)
        assert boss.is_alive is True
        assert boss.active is True


# ── EventBus: boss_defeated ───────────────────────────────────────────────────


class TestBossDefeatedEvent:
    def test_emitted_on_death(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        make_boss(max_health=100).take_damage(100)
        assert len(recorder.calls) == 1

    def test_data_contains_boss(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        boss = make_boss(max_health=100)
        boss.take_damage(100)
        assert recorder.calls[0]["boss"] is boss

    def test_not_emitted_on_non_lethal_damage(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        make_boss(max_health=100).take_damage(40)
        assert recorder.calls == []

    def test_emitted_exactly_once_on_repeated_damage(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        boss = make_boss(max_health=100)
        boss.take_damage(100)  # смертельный
        boss.take_damage(50)   # повторный удар по мёртвому
        boss.take_damage(50)
        assert len(recorder.calls) == 1

    def test_emitted_once_on_overkill(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        make_boss(max_health=100).take_damage(9999)
        assert len(recorder.calls) == 1

    def test_entity_died_still_emitted_for_compatibility(self) -> None:
        # Боссы следуют death-паттерну врагов: entity_died тоже эмитится (как у зомби).
        recorder = Recorder()
        EventBus.on("entity_died", recorder)
        boss = make_boss(max_health=100)
        boss.take_damage(100)
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["entity"] is boss


# ── Интеграция: CombatSystem и Entity-паттерны ────────────────────────────────


class TestCombatIntegration:
    def test_player_bullet_damages_boss(self) -> None:
        boss = make_boss(x=100.0, y=100.0, max_health=500)
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

    def test_enemy_bullet_does_not_hit_boss(self) -> None:
        # Faction-фильтр CombatSystem: снаряд врага не бьёт союзного босса (оба 'enemy').
        boss = make_boss(x=100.0, y=100.0, max_health=500)
        combat = CombatSystem()
        bullet = Bullet(
            x=100.0, y=100.0,
            velocity=pygame.Vector2(0.0, 0.0),
            damage=25.0,
            max_range=350.0,
            size=5,
            origin_tag="enemy",
        )
        combat.add_bullets([bullet])
        combat.update(0.016, [], [boss])
        assert boss.health.current == 500

    def test_combat_kills_boss_and_emits_event(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        boss = make_boss(x=100.0, y=100.0, max_health=20)
        combat = CombatSystem()
        bullet = Bullet(
            x=100.0, y=100.0,
            velocity=pygame.Vector2(0.0, 0.0),
            damage=100.0,
            max_range=350.0,
            size=5,
            origin_tag="player",
        )
        combat.add_bullets([bullet])
        combat.update(0.016, [], [boss])
        assert boss.is_alive is False
        assert boss.active is False
        assert len(recorder.calls) == 1

    def test_dead_boss_ignored_by_combat(self) -> None:
        # После смерти боссом combat больше не занимается (active=False) — урона нет.
        boss = make_boss(x=100.0, y=100.0, max_health=20)
        boss.take_damage(20)  # мёртв
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
        assert boss.health.current == 0  # без изменений, без второго boss_defeated

    def test_heal_follows_entity_pattern(self) -> None:
        boss = make_boss(max_health=500)
        boss.take_damage(200)
        boss.heal(50)
        assert boss.health.current == 350
