"""Tests for Sprint 9E: PatientZeroBoss acid ranged special attack (Phase 2)."""
from __future__ import annotations

import pytest

from core.entity import Entity
from entities.boss import PatientZeroBoss
from entities.bullet import AcidBullet, Bullet
from settings import BOSS_ACID_COOLDOWN, BOSS_ACID_DAMAGE
from systems.combat import CombatSystem
from systems.event_bus import EventBus
from ui.game_screen import GameScreen


# ── helpers ───────────────────────────────────────────────────────────────────


def make_boss(x: float = 300.0, y: float = 300.0, max_health: int = 100) -> PatientZeroBoss:
    return PatientZeroBoss(x, y, max_health)


def make_player(x: float = 600.0, y: float = 300.0, hp: int = 100) -> Entity:
    """Лёгкий стенд игрока (как в test_boss_ai): Entity с pos/take_damage/health."""
    return Entity(x, y, hp)


def to_phase2(boss: PatientZeroBoss) -> None:
    """Перевести босса во вторую фазу (HP ниже 50%), не убивая его."""
    boss.take_damage(boss.health.maximum * 0.6)
    assert boss.phase == 2
    assert boss.is_alive


# ── Создание ──────────────────────────────────────────────────────────────────


class TestCreation:
    def test_pending_bullets_starts_empty(self) -> None:
        assert make_boss().collect_spawned_bullets() == []

    def test_collect_spawned_bullets_exists(self) -> None:
        assert hasattr(make_boss(), "collect_spawned_bullets")

    def test_can_spit_initially(self) -> None:
        assert make_boss().can_spit is True

    def test_collect_returns_list(self) -> None:
        assert isinstance(make_boss().collect_spawned_bullets(), list)


# ── Спавн снарядов ──────────────────────────────────────────────────────────────


class TestSpawn:
    def test_phase1_does_not_spit(self) -> None:
        boss = make_boss()
        player = make_player()
        assert boss.phase == 1
        boss.update(0.1, [], player)
        assert boss.collect_spawned_bullets() == []

    def test_phase2_spits(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], make_player())
        bullets = boss.collect_spawned_bullets()
        assert len(bullets) == 1
        assert isinstance(bullets[0], AcidBullet)

    def test_no_player_does_not_spit(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], None)
        assert boss.collect_spawned_bullets() == []

    def test_dead_boss_does_not_spit(self) -> None:
        boss = make_boss()
        boss.take_damage(boss.health.maximum)  # мёртв → 0% HP попало бы в phase 2
        assert not boss.is_alive
        boss.update(0.1, [], make_player())
        assert boss.collect_spawned_bullets() == []

    def test_collect_drains_queue(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], make_player())
        boss.collect_spawned_bullets()
        assert boss.collect_spawned_bullets() == []

    def test_zero_direction_does_not_crash(self) -> None:
        boss = make_boss(300.0, 300.0)
        to_phase2(boss)
        same_pos = make_player(300.0, 300.0)  # цель в точке босса → нет-оп
        boss.spit_acid(same_pos)
        assert boss.collect_spawned_bullets() == []


# ── Направление ──────────────────────────────────────────────────────────────────


class TestDirection:
    def _spit_bullet(self, boss: PatientZeroBoss, player: Entity) -> Bullet:
        boss.spit_acid(player)
        bullets = boss.collect_spawned_bullets()
        assert len(bullets) == 1
        return bullets[0]

    def test_flies_down_toward_player(self) -> None:
        boss = make_boss(300.0, 300.0)
        to_phase2(boss)
        bullet = self._spit_bullet(boss, make_player(300.0, 500.0))
        bullet.update(0.1, [])
        assert bullet.pos.y > 300.0
        assert bullet.pos.x == pytest.approx(300.0)

    def test_flies_right_toward_player(self) -> None:
        boss = make_boss(300.0, 300.0)
        to_phase2(boss)
        bullet = self._spit_bullet(boss, make_player(700.0, 300.0))
        bullet.update(0.1, [])
        assert bullet.pos.x > 300.0
        assert bullet.pos.y == pytest.approx(300.0)

    def test_direction_is_normalized_diagonal(self) -> None:
        boss = make_boss(300.0, 300.0)
        to_phase2(boss)
        bullet = self._spit_bullet(boss, make_player(500.0, 500.0))  # 45° вниз-вправо
        bullet.update(0.1, [])
        dx = bullet.pos.x - 300.0
        dy = bullet.pos.y - 300.0
        assert dx > 0 and dy > 0
        assert dx == pytest.approx(dy)  # нормализованный вектор → равные компоненты


# ── Кулдаун ──────────────────────────────────────────────────────────────────────


class TestCooldown:
    def test_second_shot_blocked_within_cooldown(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        player = make_player()
        boss.update(0.1, [], player)
        assert len(boss.collect_spawned_bullets()) == 1
        boss.update(0.1, [], player)  # кулдаун активен
        assert boss.collect_spawned_bullets() == []

    def test_shoots_again_after_cooldown(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        player = make_player()
        boss.update(0.1, [], player)
        boss.collect_spawned_bullets()
        boss.update(BOSS_ACID_COOLDOWN + 0.1, [], player)  # кулдаун истёк
        assert len(boss.collect_spawned_bullets()) == 1


# ── Интеграция с GameScreen / CombatSystem ───────────────────────────────────────


class TestIntegration:
    def test_gamescreen_collects_boss_bullets(self) -> None:
        screen = GameScreen()
        to_phase2(screen._boss)
        # Игрок в радиусе обнаружения босса — иначе кислота не стреляет (Sprint 9G).
        screen._player.pos.update(screen._boss.pos.x + 50.0, screen._boss.pos.y)
        screen.update(0.016)
        assert len(screen._combat.bullets) >= 1  # пуля босса попала в CombatSystem

    def test_acid_bullet_damages_player(self) -> None:
        # Реальный Player из GameScreen (faction='player', есть rect для коллизий).
        screen = GameScreen()
        player = screen._player
        boss = screen._boss
        to_phase2(boss)
        # Поставить босса рядом с игроком, чтобы кислота быстро долетела.
        boss.pos.x = player.pos.x + 30.0
        boss.pos.y = player.pos.y
        boss.spit_acid(player)
        combat = CombatSystem()
        combat.add_bullets(boss.collect_spawned_bullets())

        before = player.health.current
        for _ in range(20):
            combat.update(0.05, [], [player])
            if player.health.current < before:
                break
        assert player.health.current < before

    def test_melee_still_works(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 300.0)  # в пределах melee-радиуса, phase 1
        before = player.health.current
        boss.update(0.1, [], player)
        assert player.health.current == before - 20.0  # BOSS_DAMAGE
        assert boss.collect_spawned_bullets() == []  # phase 1 — без кислоты

    def test_acid_origin_tag_is_enemy(self) -> None:
        boss = make_boss(300.0, 300.0)
        to_phase2(boss)
        boss.spit_acid(make_player(500.0, 300.0))
        bullet = boss.collect_spawned_bullets()[0]
        assert bullet.origin_tag == "enemy"
        assert bullet.damage == BOSS_ACID_DAMAGE


# ── Регрессии ─────────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_boss_defeated_still_emits_once(self) -> None:
        events: list[dict] = []
        EventBus.on("boss_defeated", events.append)
        boss = make_boss()
        boss.take_damage(boss.health.maximum)
        boss.take_damage(10)  # повторный урон по трупу — без повторного события
        assert len(events) == 1

    def test_victory_still_triggers(self) -> None:
        screen = GameScreen()
        screen._boss.take_damage(screen._boss.health.maximum)
        assert screen.victory is True

    def test_game_over_still_triggers(self) -> None:
        screen = GameScreen()
        screen._player.take_damage(screen._player.health.maximum)
        assert screen.game_over is True

    def test_phase1_update_unchanged_no_bullets(self) -> None:
        # Регрессия 9D: в фазе 1 поведение прежнее (melee/преследование, без снарядов).
        boss = make_boss(300.0, 300.0)
        player = make_player(600.0, 300.0)  # вне атаки (>70), в радиусе обнаружения (<400) → погоня
        start_x = boss.pos.x
        boss.update(0.1, [], player)
        assert boss.pos.x > start_x  # двигался к игроку
        assert boss.collect_spawned_bullets() == []
