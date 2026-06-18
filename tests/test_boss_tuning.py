"""Tests for Sprint 9G: Boss Encounter Tuning — XP reward, detection-gated specials, minion pruning."""
from __future__ import annotations

from core.entity import Entity
from data.enemy_data import EnemyData
from entities.boss import PatientZeroBoss
from entities.zombie import WalkerZombie
from settings import (
    BOSS_DETECTION_RANGE,
    BOSS_SUMMON_COOLDOWN,
    BOSS_SUMMON_MAX,
    BOSS_XP_REWARD,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def walker_config() -> EnemyData:
    return EnemyData(
        max_health=80, speed=60.0, damage=15.0, attack_range=40.0,
        detection_range=180.0, attack_cooldown=1.5, width=32, height=32, xp_reward=10,
    )


def make_boss(x: float = 300.0, y: float = 300.0, hp: int = 100, *, minions: bool = False) -> PatientZeroBoss:
    return PatientZeroBoss(x, y, hp, walker_config() if minions else None)


def make_player(x: float, y: float = 300.0, hp: int = 100) -> Entity:
    return Entity(x, y, hp)


def to_phase2(boss: PatientZeroBoss) -> None:
    boss.take_damage(boss.health.maximum * 0.6)
    assert boss.phase == 2
    assert boss.is_alive


# Игрок заведомо вне / внутри радиуса обнаружения босса (центр 300, 300).
_FAR_X = 300.0 + BOSS_DETECTION_RANGE + 200.0
_NEAR_X = 300.0 + BOSS_DETECTION_RANGE / 2.0


# ── XP босса ──────────────────────────────────────────────────────────────────


class TestXpReward:
    def test_xp_reward_from_settings(self) -> None:
        assert make_boss().xp_reward == BOSS_XP_REWARD

    def test_xp_reward_is_positive(self) -> None:
        assert make_boss().xp_reward > 0


# ── Гейт кислоты по обнаружению ────────────────────────────────────────────────


class TestAcidGate:
    def test_acid_blocked_outside_detection(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], make_player(_FAR_X))  # игрок вне detection range
        assert boss.collect_spawned_bullets() == []

    def test_acid_fires_inside_detection(self) -> None:
        boss = make_boss()
        to_phase2(boss)
        boss.update(0.1, [], make_player(_NEAR_X))  # игрок в detection range
        assert len(boss.collect_spawned_bullets()) == 1


# ── Гейт призыва по обнаружению ────────────────────────────────────────────────


class TestSummonGate:
    def test_summon_blocked_outside_detection(self) -> None:
        boss = make_boss(minions=True)
        to_phase2(boss)
        boss.update(0.1, [], make_player(_FAR_X))
        assert boss.collect_spawned_minions() == []

    def test_summon_fires_inside_detection(self) -> None:
        boss = make_boss(minions=True)
        to_phase2(boss)
        boss.update(0.1, [], make_player(_NEAR_X))
        minions = boss.collect_spawned_minions()
        assert len(minions) == 1
        assert isinstance(minions[0], WalkerZombie)


# ── Прунинг призванных миньонов ────────────────────────────────────────────────


class TestPruning:
    def _summon_to_max(self, boss: PatientZeroBoss, player: Entity) -> list:
        collected: list = []
        for _ in range(BOSS_SUMMON_MAX):
            boss.update(BOSS_SUMMON_COOLDOWN + 0.1, [], player)
            collected.extend(boss.collect_spawned_minions())
        return collected

    def test_dead_minion_not_counted(self) -> None:
        boss = make_boss(minions=True)
        to_phase2(boss)
        # Игрок на боссе → в attack-range, босс стоит на месте и всегда обнаружен.
        player = make_player(300.0, 300.0, hp=1000)
        collected = self._summon_to_max(boss, player)
        assert len(collected) == BOSS_SUMMON_MAX
        assert boss._active_minions() == BOSS_SUMMON_MAX
        for minion in collected:
            minion.take_damage(minion.health.maximum)
        assert boss._active_minions() == 0  # мёртвые не учитываются

    def test_pruning_frees_limit_and_bounds_list(self) -> None:
        boss = make_boss(minions=True)
        to_phase2(boss)
        player = make_player(300.0, 300.0, hp=1000)
        collected = self._summon_to_max(boss, player)
        for minion in collected:
            minion.take_damage(minion.health.maximum)
        boss.update(BOSS_SUMMON_COOLDOWN + 0.1, [], player)  # слот свободен → новый призыв
        assert len(boss.collect_spawned_minions()) == 1
        assert len(boss._summoned) == 1  # прунинг убрал мёртвые ссылки, осталась 1 живая

    def test_limit_contract_unchanged(self) -> None:
        # BOSS_SUMMON_MAX по-прежнему ограничивает одновременно живых.
        boss = make_boss(minions=True)
        to_phase2(boss)
        player = make_player(300.0, 300.0, hp=1000)
        collected: list = []
        for _ in range(BOSS_SUMMON_MAX + 5):  # больше попыток, чем лимит
            boss.update(BOSS_SUMMON_COOLDOWN + 0.1, [], player)
            collected.extend(boss.collect_spawned_minions())
        assert len(collected) == BOSS_SUMMON_MAX


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_melee_still_works_inside_detection(self) -> None:
        boss = make_boss(300.0, 300.0)
        player = make_player(300.0, 300.0)  # phase 1, в melee-радиусе
        before = player.health.current
        boss.update(0.1, [], player)
        assert player.health.current < before

    def test_phase1_does_not_use_specials(self) -> None:
        boss = make_boss(300.0, 300.0, minions=True)
        boss.update(0.1, [], make_player(_NEAR_X))  # phase 1, игрок обнаружен
        assert boss.collect_spawned_bullets() == []
        assert boss.collect_spawned_minions() == []

    def test_phase_switches_at_half_health(self) -> None:
        boss = make_boss(300.0, 300.0)
        assert boss.phase == 1
        to_phase2(boss)
        assert boss.phase == 2
