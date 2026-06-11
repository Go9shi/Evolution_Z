"""Tests for Sprint 7A: ExperienceComponent + Player XP + zombie kill integration."""
from __future__ import annotations

from data.enemy_data import EnemyData
from data.player_data import PlayerData
from entities.player import Player
from entities.zombie import WalkerZombie
from systems.event_bus import EventBus
from systems.experience import ExperienceComponent, required_xp


# ── helpers ───────────────────────────────────────────────────────────────────

def make_exp() -> ExperienceComponent:
    return ExperienceComponent()


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


def make_walker(xp_reward: int = 10) -> WalkerZombie:
    data = EnemyData(
        max_health=80,
        speed=60.0,
        damage=15.0,
        attack_range=40.0,
        detection_range=180.0,
        attack_cooldown=1.5,
        width=32,
        height=32,
        xp_reward=xp_reward,
    )
    return WalkerZombie(500.0, 500.0, data)


# ── required_xp formula ───────────────────────────────────────────────────────

class TestRequiredXp:
    def test_level_1_threshold(self) -> None:
        assert required_xp(1) == 100  # 50 * 1 * 2

    def test_level_2_threshold(self) -> None:
        assert required_xp(2) == 300  # 50 * 2 * 3

    def test_level_3_threshold(self) -> None:
        assert required_xp(3) == 600  # 50 * 3 * 4

    def test_increases_with_level(self) -> None:
        assert required_xp(2) > required_xp(1)
        assert required_xp(3) > required_xp(2)


# ── ExperienceComponent ───────────────────────────────────────────────────────

class TestExperienceComponentInitial:
    def test_initial_level_is_one(self) -> None:
        assert make_exp().current_level == 1

    def test_initial_xp_is_zero(self) -> None:
        assert make_exp().current_xp == 0

    def test_xp_to_next_level_equals_threshold_at_start(self) -> None:
        exp = make_exp()
        assert exp.xp_to_next_level == required_xp(1)


class TestExperienceComponentAddXp:
    def test_add_xp_increases_total(self) -> None:
        exp = make_exp()
        exp.add_xp(30)
        assert exp.current_xp == 30

    def test_no_level_up_below_threshold(self) -> None:
        exp = make_exp()
        result = exp.add_xp(99)
        assert result is False
        assert exp.current_level == 1

    def test_level_up_at_threshold(self) -> None:
        exp = make_exp()
        result = exp.add_xp(100)
        assert result is True
        assert exp.current_level == 2

    def test_multiple_level_ups_from_large_gain(self) -> None:
        exp = make_exp()
        result = exp.add_xp(350)
        # required_xp(1)=100 → level 2; required_xp(2)=300 ≤ 350 → level 3; required_xp(3)=600 > 350
        assert result is True
        assert exp.current_level == 3

    def test_xp_to_next_level_property(self) -> None:
        exp = make_exp()
        exp.add_xp(50)
        assert exp.xp_to_next_level == required_xp(1) - 50

    def test_xp_to_next_level_after_level_up(self) -> None:
        exp = make_exp()
        exp.add_xp(100)  # now level 2, total xp = 100
        assert exp.xp_to_next_level == required_xp(2) - 100

    def test_xp_accumulates_across_calls(self) -> None:
        exp = make_exp()
        exp.add_xp(40)
        exp.add_xp(40)
        assert exp.current_xp == 80


# ── EventBus events ───────────────────────────────────────────────────────────

class TestExperienceEvents:
    def test_emit_player_xp_gained_event(self) -> None:
        received: list[dict] = []
        EventBus.on("player_xp_gained", received.append)
        exp = make_exp()
        exp.add_xp(25)
        assert len(received) == 1
        assert received[0]["amount"] == 25
        assert received[0]["total_xp"] == 25

    def test_emit_player_level_up_event(self) -> None:
        received: list[dict] = []
        EventBus.on("player_level_up", received.append)
        exp = make_exp()
        exp.add_xp(100)
        assert len(received) == 1
        assert received[0]["level"] == 2

    def test_no_level_up_event_when_not_leveling(self) -> None:
        received: list[dict] = []
        EventBus.on("player_level_up", received.append)
        exp = make_exp()
        exp.add_xp(50)
        assert len(received) == 0

    def test_multiple_level_up_events_on_large_gain(self) -> None:
        received: list[dict] = []
        EventBus.on("player_level_up", received.append)
        exp = make_exp()
        exp.add_xp(350)  # reaches level 3
        assert len(received) == 2
        assert received[0]["level"] == 2
        assert received[1]["level"] == 3


# ── Player delegation ─────────────────────────────────────────────────────────

class TestPlayerExperience:
    def test_player_experience_property(self) -> None:
        player = make_player()
        assert isinstance(player.experience, ExperienceComponent)

    def test_player_add_xp_delegates_to_component(self) -> None:
        player = make_player()
        player.add_xp(50)
        assert player.experience.current_xp == 50

    def test_player_add_xp_returns_false_without_level_up(self) -> None:
        player = make_player()
        assert player.add_xp(10) is False

    def test_player_add_xp_returns_true_on_level_up(self) -> None:
        player = make_player()
        assert player.add_xp(100) is True


# ── Integration: zombie death → XP ───────────────────────────────────────────

class TestKillIntegration:
    """Имитирует поведение GameScreen: подписка на entity_died → add_xp."""

    def _wire_xp(self, player: Player) -> None:
        """Подписываем player на entity_died так же, как это делает GameScreen."""
        def on_entity_died(data: dict) -> None:
            entity = data["entity"]
            if entity.faction == "enemy":
                player.add_xp(entity.xp_reward)
        EventBus.on("entity_died", on_entity_died)

    def test_zombie_death_grants_xp(self) -> None:
        player = make_player()
        walker = make_walker(xp_reward=10)
        self._wire_xp(player)
        walker.take_damage(9999)
        assert player.experience.current_xp == 10

    def test_multiple_kills_accumulate_xp(self) -> None:
        player = make_player()
        self._wire_xp(player)
        for _ in range(3):
            w = make_walker(xp_reward=10)
            w.take_damage(9999)
        assert player.experience.current_xp == 30

    def test_level_up_after_kills(self) -> None:
        player = make_player()
        self._wire_xp(player)
        # required_xp(1)=100; 10 kills × 10 XP = 100 → level up
        for _ in range(10):
            w = make_walker(xp_reward=10)
            w.take_damage(9999)
        assert player.experience.current_level == 2

    def test_player_death_does_not_grant_xp(self) -> None:
        player = make_player()
        self._wire_xp(player)
        player.take_damage(9999)  # player dies, faction="player"
        assert player.experience.current_xp == 0
