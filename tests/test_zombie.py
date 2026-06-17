import pytest
import pygame

from data.enemy_data import EnemyData
from core.entity import Entity
from entities.zombie import AIState, RunnerZombie, WalkerZombie, Zombie
from systems.event_bus import EventBus


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def walker_data() -> EnemyData:
    return EnemyData(
        max_health=80,
        speed=60.0,
        damage=15.0,
        attack_range=40.0,
        detection_range=180.0,
        attack_cooldown=1.5,
        width=32,
        height=32,
        xp_reward=10,
    )


@pytest.fixture
def runner_data() -> EnemyData:
    return EnemyData(
        max_health=30,
        speed=140.0,
        damage=8.0,
        attack_range=36.0,
        detection_range=240.0,
        attack_cooldown=0.8,
        width=28,
        height=28,
        xp_reward=15,
    )


@pytest.fixture
def walker(walker_data) -> WalkerZombie:
    return WalkerZombie(200.0, 200.0, walker_data)


@pytest.fixture
def runner(runner_data) -> RunnerZombie:
    return RunnerZombie(200.0, 200.0, runner_data)


@pytest.fixture
def dummy_target() -> Entity:
    """Простая Entity для тестов атаки."""
    return Entity(500.0, 500.0, 100)


# Позиции относительно зомби на (200, 200)
FAR_POS = pygame.Vector2(900.0, 900.0)      # вне detection_range (989px > 240)
NEAR_POS = pygame.Vector2(300.0, 200.0)     # в detection_range (100px < 180), вне attack_range (> 40)
ATTACK_POS = pygame.Vector2(210.0, 200.0)  # в attack_range (10px < 40)


# ── EnemyData ──────────────────────────────────────────────────────────────

def test_enemy_data_fields(walker_data):
    assert walker_data.max_health == 80
    assert walker_data.speed == 60.0
    assert walker_data.damage == 15.0
    assert walker_data.attack_range == 40.0
    assert walker_data.detection_range == 180.0
    assert walker_data.attack_cooldown == 1.5
    assert walker_data.width == 32
    assert walker_data.height == 32
    assert walker_data.xp_reward == 10


# ── Zombie init / hierarchy ────────────────────────────────────────────────

def test_walker_is_alive_on_spawn(walker):
    assert walker.is_alive
    assert walker.active


def test_walker_health_from_config(walker, walker_data):
    assert walker.health.current == walker_data.max_health


def test_walker_is_subclass_of_entity(walker):
    assert isinstance(walker, Entity)


def test_runner_is_subclass_of_zombie(runner):
    assert isinstance(runner, Zombie)


# ── detection helpers ──────────────────────────────────────────────────────

def test_detect_player_within_range(walker):
    assert walker._detect_player(NEAR_POS) is True


def test_no_detect_player_outside_range(walker):
    assert walker._detect_player(FAR_POS) is False


def test_in_attack_range_true(walker):
    assert walker._in_attack_range(ATTACK_POS) is True


def test_in_attack_range_false(walker):
    assert walker._in_attack_range(NEAR_POS) is False


# ── WalkerZombie AI states ─────────────────────────────────────────────────

def test_walker_patrols_when_player_far(walker):
    player = Entity(FAR_POS.x, FAR_POS.y, 100)
    walker.update(dt=0.1, walls=[], player=player)
    assert walker.state == AIState.PATROL


def test_walker_chases_when_player_detected(walker):
    player = Entity(NEAR_POS.x, NEAR_POS.y, 100)
    walker.update(dt=0.1, walls=[], player=player)
    assert walker.state == AIState.CHASE


def test_walker_attacks_when_in_range(walker):
    player = Entity(ATTACK_POS.x, ATTACK_POS.y, 100)
    walker.update(dt=0.1, walls=[], player=player)
    assert walker.state == AIState.ATTACK


# ── RunnerZombie AI states ─────────────────────────────────────────────────

def test_runner_patrols_when_player_far(runner):
    player = Entity(FAR_POS.x, FAR_POS.y, 100)
    runner.update(dt=0.1, walls=[], player=player)
    assert runner.state == AIState.PATROL


def test_runner_chases_when_detected(runner):
    player = Entity(NEAR_POS.x, NEAR_POS.y, 100)
    runner.update(dt=0.1, walls=[], player=player)
    assert runner.state == AIState.CHASE


# ── attack ─────────────────────────────────────────────────────────────────

def test_walker_attack_damages_target(walker, dummy_target):
    before = dummy_target.health.current
    walker.attack(dummy_target)
    assert dummy_target.health.current == pytest.approx(before - walker._data.damage)


def test_attack_fires_zombie_attacked_event(walker, dummy_target):
    events: list[dict] = []
    EventBus.on("zombie_attacked", events.append)
    walker.attack(dummy_target)
    assert len(events) == 1
    assert events[0]["attacker"] is walker
    assert events[0]["target"] is dummy_target


def test_attack_sets_cooldown(walker, dummy_target):
    assert walker.can_attack is True
    walker.attack(dummy_target)
    walker._attack_timer = walker._data.attack_cooldown  # simulate what update_ai sets
    assert walker.can_attack is False


def test_cooldown_expires_over_time(walker, dummy_target):
    walker._attack_timer = walker._data.attack_cooldown
    assert walker.can_attack is False
    walker.update(dt=walker._data.attack_cooldown, walls=[], player=None)
    assert walker.can_attack is True


# ── death ──────────────────────────────────────────────────────────────────

def test_zombie_dies_on_lethal_damage(walker):
    walker.take_damage(9999.0)
    assert not walker.is_alive
    assert not walker.active


def test_entity_died_event_on_lethal(walker):
    events: list[dict] = []
    EventBus.on("entity_died", events.append)
    walker.take_damage(9999.0)
    assert len(events) == 1
    assert events[0]["entity"] is walker


# ── polymorphism ───────────────────────────────────────────────────────────

def test_runner_faster_than_walker(walker_data, runner_data):
    assert runner_data.speed > walker_data.speed


def test_both_enemies_share_update_interface(walker, runner):
    player = Entity(FAR_POS.x, FAR_POS.y, 100)
    # Единый вызов для обоих — ни одного isinstance
    for enemy in [walker, runner]:
        enemy.update(dt=0.1, walls=[], player=player)
    assert walker.state == AIState.PATROL
    assert runner.state == AIState.PATROL


# ── integration ────────────────────────────────────────────────────────────

def test_walker_update_deals_damage_to_player(walker_data):
    """Полный цикл: update() обнаруживает игрока в attack_range и вызывает attack()."""
    from data.player_data import PlayerData
    from entities.player import Player

    player = Player(
        ATTACK_POS.x,
        ATTACK_POS.y,
        PlayerData(max_health=100, speed=0.0, width=32, height=32),
    )
    zombie = WalkerZombie(200.0, 200.0, walker_data)
    hp_before = player.health.current

    zombie.update(dt=0.1, walls=[], player=player)

    assert player.health.current < hp_before
