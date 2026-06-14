"""Tests for Sprint 9F: PatientZeroBoss minion summon (Phase 2)."""
from __future__ import annotations

import pygame

from core.entity import Entity
from data.enemy_data import EnemyData
from entities.boss import PatientZeroBoss
from entities.bullet import Bullet
from entities.zombie import AIState, WalkerZombie
from settings import BOSS_DAMAGE, BOSS_SUMMON_COOLDOWN, BOSS_SUMMON_MAX
from systems.event_bus import EventBus
from ui.game_screen import GameScreen


# ── helpers ───────────────────────────────────────────────────────────────────


def walker_config() -> EnemyData:
    """Конфиг walker, как в enemies.json — для инъекции боссу в тестах."""
    return EnemyData(
        max_health=80, speed=60.0, damage=15.0, attack_range=40.0,
        detection_range=180.0, attack_cooldown=1.5, width=32, height=32, xp_reward=10,
    )


def make_boss(x: float = 300.0, y: float = 300.0, hp: int = 100, *, minions: bool = True) -> PatientZeroBoss:
    return PatientZeroBoss(x, y, hp, walker_config() if minions else None)


def make_player(x: float = 600.0, y: float = 300.0, hp: int = 100) -> Entity:
    return Entity(x, y, hp)


def _colocated_player(boss: PatientZeroBoss) -> Entity:
    """Игрок на позиции босса: в attack-range → босс стоит на месте и всегда обнаружен
    (Sprint 9G: спецатаки гейтятся _detect_player). Высокий HP — переживает melee за цикл."""
    return Entity(boss.pos.x, boss.pos.y, 100_000)


def to_phase2(boss: PatientZeroBoss) -> None:
    """Перевести босса во вторую фазу (HP ниже 50%), не убивая."""
    boss.take_damage(boss.health.maximum * 0.6)
    assert boss.phase == 2
    assert boss.is_alive


# ── Создание ──────────────────────────────────────────────────────────────────


class TestCreation:
    def test_pending_minions_starts_empty(self) -> None:
        assert make_boss().collect_spawned_minions() == []

    def test_collect_spawned_minions_exists(self) -> None:
        assert hasattr(make_boss(), "collect_spawned_minions")

    def test_collect_drains_queue(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], make_player())
        boss.collect_spawned_minions()
        assert boss.collect_spawned_minions() == []

    def test_can_summon_with_config(self) -> None:
        assert make_boss(minions=True).can_summon is True

    def test_cannot_summon_without_config(self) -> None:
        assert make_boss(minions=False).can_summon is False


# ── Фазы ──────────────────────────────────────────────────────────────────────


class TestPhases:
    def test_phase1_does_not_summon(self) -> None:
        boss = make_boss()
        assert boss.phase == 1
        boss.update(0.1, [], make_player())
        assert boss.collect_spawned_minions() == []

    def test_phase2_summons(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], make_player())
        minions = boss.collect_spawned_minions()
        assert len(minions) == 1
        assert isinstance(minions[0], WalkerZombie)

    def test_no_config_does_not_summon_in_phase2(self) -> None:
        boss = make_boss(minions=False)
        to_phase2(boss)
        boss.update(0.1, [], make_player())
        assert boss.collect_spawned_minions() == []

    def test_no_player_does_not_summon(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], None)
        assert boss.collect_spawned_minions() == []

    def test_dead_boss_does_not_summon(self) -> None:
        boss = make_boss()
        boss.take_damage(boss.health.maximum)  # мёртв → 0% HP попало бы в phase 2
        assert not boss.is_alive
        boss.update(0.1, [], make_player())
        assert boss.collect_spawned_minions() == []


# ── Кулдаун ──────────────────────────────────────────────────────────────────


class TestCooldown:
    def test_second_summon_blocked_within_cooldown(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        player = make_player()
        boss.update(0.1, [], player)
        assert len(boss.collect_spawned_minions()) == 1
        boss.update(0.1, [], player)  # кулдаун активен
        assert boss.collect_spawned_minions() == []

    def test_summons_again_after_cooldown(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        player = make_player()
        boss.update(0.1, [], player)
        boss.collect_spawned_minions()
        boss.update(BOSS_SUMMON_COOLDOWN + 0.1, [], player)  # кулдаун истёк
        assert len(boss.collect_spawned_minions()) == 1


# ── Лимиты ────────────────────────────────────────────────────────────────────


class TestLimits:
    def _summon_repeatedly(self, boss: PatientZeroBoss, player: Entity, times: int) -> list:
        collected: list = []
        for _ in range(times):
            boss.update(BOSS_SUMMON_COOLDOWN + 0.1, [], player)
            collected.extend(boss.collect_spawned_minions())
        return collected

    def test_respects_max_simultaneous(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        collected = self._summon_repeatedly(boss, _colocated_player(boss), 6)
        assert len(collected) == BOSS_SUMMON_MAX
        assert boss._active_minions() == BOSS_SUMMON_MAX

    def test_not_infinite(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        collected = self._summon_repeatedly(boss, _colocated_player(boss), 20)  # много попыток
        assert len(collected) == BOSS_SUMMON_MAX  # не растёт бесконечно

    def test_slot_frees_when_minion_dies(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        player = _colocated_player(boss)
        collected = self._summon_repeatedly(boss, player, 6)
        assert len(collected) == BOSS_SUMMON_MAX
        collected[0].take_damage(collected[0].health.maximum)  # один миньон гибнет
        boss.update(BOSS_SUMMON_COOLDOWN + 0.1, [], player)
        assert len(boss.collect_spawned_minions()) == 1  # освободился слот


# ── Интеграция с GameScreen ──────────────────────────────────────────────────


class TestIntegration:
    def _summon_one(self, screen: GameScreen) -> WalkerZombie:
        """Перевести босса в phase 2, обновить экран, вернуть призванного миньона."""
        to_phase2(screen._boss)
        # Игрок в радиусе обнаружения босса — иначе призыв не происходит (Sprint 9G).
        screen._player.pos.update(screen._boss.pos.x + 50.0, screen._boss.pos.y)
        before = {id(e) for e in screen._enemies}
        screen.update(0.016)
        new = [e for e in screen._enemies if id(e) not in before]
        assert len(new) == 1
        assert isinstance(new[0], WalkerZombie)
        return new[0]

    def test_gamescreen_gains_new_enemy(self) -> None:
        screen = GameScreen()
        before = len(screen._enemies)
        self._summon_one(screen)
        assert len(screen._enemies) == before + 1

    def test_new_enemy_participates_in_update(self) -> None:
        screen = GameScreen()
        minion = self._summon_one(screen)
        # Поставить игрока в радиус атаки миньона → его update_ai сменит state.
        screen._player.pos.update(minion.pos.x + 30.0, minion.pos.y)
        screen.update(0.016)
        assert minion.state in (AIState.CHASE, AIState.ATTACK)

    def test_new_enemy_participates_in_draw(self) -> None:
        screen = GameScreen()
        minion = self._summon_one(screen)
        screen.draw(pygame.Surface((1280, 720)))  # не падает
        assert minion in screen._enemies

    def test_new_enemy_participates_in_combat(self) -> None:
        screen = GameScreen()
        minion = self._summon_one(screen)
        bullet = Bullet(
            x=minion.pos.x, y=minion.pos.y, velocity=pygame.Vector2(0.0, 0.0),
            damage=10.0, max_range=100.0, size=5, origin_tag="player",
        )
        screen._combat.add_bullets([bullet])
        before = minion.health.current
        screen.update(0.016)
        assert minion.health.current < before  # пуля игрока попала по призванному


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_melee_still_works(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 300.0)  # в melee-радиусе, phase 1
        before = player.health.current
        boss.update(0.1, [], player)
        assert player.health.current == before - BOSS_DAMAGE
        assert boss.collect_spawned_minions() == []  # phase 1 — без призыва

    def test_acid_still_works(self) -> None:
        boss = make_boss(300.0, 300.0)
        to_phase2(boss)
        boss.update(0.1, [], make_player())
        assert len(boss.collect_spawned_bullets()) == 1  # кислота фазы 2 не сломана

    def test_boss_defeated_still_emits_once(self) -> None:
        events: list[dict] = []
        EventBus.on("boss_defeated", events.append)
        boss = make_boss()
        boss.take_damage(boss.health.maximum)
        boss.take_damage(10)  # по трупу — без повторного события
        assert len(events) == 1

    def test_victory_still_triggers(self) -> None:
        screen = GameScreen()
        screen._boss.take_damage(screen._boss.health.maximum)
        assert screen.victory is True

    def test_game_over_still_triggers(self) -> None:
        screen = GameScreen()
        screen._player.take_damage(screen._player.health.maximum)
        assert screen.game_over is True
