import pygame
import pytest

from core.entity import Entity
from data.enemy_data import EnemyData
from data.player_data import PlayerData
from data.spitter_data import SpitterData
from entities.bullet import AcidBullet, Bullet
from entities.player import Player
from entities.zombie import AIState, SpitterZombie, WalkerZombie, Zombie
from systems.combat import CombatSystem
from systems.event_bus import EventBus


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def spitter_data() -> SpitterData:
    return SpitterData(
        max_health=50,
        speed=70.0,
        damage=0.0,
        attack_range=200.0,
        detection_range=280.0,
        attack_cooldown=2.0,
        width=30,
        height=30,
        xp_reward=20,
        spit_damage=12.0,
        spit_speed=300.0,
        spit_range=350.0,
        safe_distance=100.0,
    )


@pytest.fixture
def spitter(spitter_data: SpitterData) -> SpitterZombie:
    return SpitterZombie(200.0, 200.0, spitter_data)


@pytest.fixture
def walker_data() -> EnemyData:
    return EnemyData(
        max_health=80, speed=60.0, damage=15.0, attack_range=40.0,
        detection_range=180.0, attack_cooldown=1.5, width=32, height=32, xp_reward=10,
    )


@pytest.fixture
def player_entity() -> Entity:
    return Entity(500.0, 200.0, 100)


# Позиции относительно спиттера на (200, 200); detection=280, attack=200, safe=100
FAR_POS = pygame.Vector2(900.0, 900.0)      # dist ~989px > 280 → PATROL
CHASE_POS = pygame.Vector2(450.0, 200.0)   # dist 250px: detected, > attack_range → CHASE
ATTACK_POS = pygame.Vector2(350.0, 200.0)  # dist 150px: detected, in attack_range, > safe → ATTACK
CLOSE_POS = pygame.Vector2(250.0, 200.0)   # dist 50px < safe_distance → REPOSITION


# ── SpitterData ────────────────────────────────────────────────────────────


def test_spitter_data_inherits_enemy_data(spitter_data: SpitterData) -> None:
    assert isinstance(spitter_data, EnemyData)


def test_spitter_data_base_fields(spitter_data: SpitterData) -> None:
    assert spitter_data.max_health == 50
    assert spitter_data.attack_range == pytest.approx(200.0)
    assert spitter_data.detection_range == pytest.approx(280.0)


def test_spitter_data_extra_fields(spitter_data: SpitterData) -> None:
    assert spitter_data.spit_damage == pytest.approx(12.0)
    assert spitter_data.spit_speed == pytest.approx(300.0)
    assert spitter_data.spit_range == pytest.approx(350.0)
    assert spitter_data.safe_distance == pytest.approx(100.0)


# ── AcidBullet ─────────────────────────────────────────────────────────────


def test_acid_bullet_inherits_bullet() -> None:
    b = AcidBullet(0.0, 0.0, pygame.Vector2(1, 0), 12.0, 350.0, 6, "enemy")
    assert isinstance(b, Bullet)


def test_acid_bullet_color_differs_from_bullet() -> None:
    assert AcidBullet.COLOR != Bullet.COLOR


def test_acid_bullet_origin_tag_is_enemy() -> None:
    b = AcidBullet(0.0, 0.0, pygame.Vector2(1, 0), 12.0, 350.0, 6, "enemy")
    assert b.origin_tag == "enemy"


def test_acid_bullet_damage() -> None:
    b = AcidBullet(0.0, 0.0, pygame.Vector2(1, 0), 12.0, 350.0, 6, "enemy")
    assert b.damage == pytest.approx(12.0)


def test_acid_bullet_moves_on_update() -> None:
    b = AcidBullet(0.0, 0.0, pygame.Vector2(300.0, 0.0), 12.0, 350.0, 6, "enemy")
    b.update(dt=0.1)
    assert b.pos.x == pytest.approx(30.0)


# ── SpitterZombie hierarchy & faction ─────────────────────────────────────


def test_spitter_is_zombie(spitter: SpitterZombie) -> None:
    assert isinstance(spitter, Zombie)


def test_spitter_is_entity(spitter: SpitterZombie) -> None:
    assert isinstance(spitter, Entity)


def test_spitter_faction_is_enemy(spitter: SpitterZombie) -> None:
    assert spitter.faction == "enemy"


def test_spitter_alive_on_spawn(spitter: SpitterZombie) -> None:
    assert spitter.is_alive
    assert spitter.active


# ── AI state machine ───────────────────────────────────────────────────────


def test_spitter_patrols_when_player_far(spitter: SpitterZombie) -> None:
    player = Entity(FAR_POS.x, FAR_POS.y, 100)
    spitter.update(dt=0.1, walls=[], player=player)
    assert spitter.state == AIState.PATROL


def test_spitter_chases_when_detected_outside_ranges(spitter: SpitterZombie) -> None:
    player = Entity(CHASE_POS.x, CHASE_POS.y, 100)
    spitter.update(dt=0.1, walls=[], player=player)
    assert spitter.state == AIState.CHASE


def test_spitter_attacks_at_optimal_range(spitter: SpitterZombie) -> None:
    player = Entity(ATTACK_POS.x, ATTACK_POS.y, 100)
    spitter.update(dt=0.1, walls=[], player=player)
    assert spitter.state == AIState.ATTACK


def test_spitter_repositions_when_player_too_close(spitter: SpitterZombie) -> None:
    player = Entity(CLOSE_POS.x, CLOSE_POS.y, 100)
    spitter.update(dt=0.1, walls=[], player=player)
    assert spitter.state == AIState.REPOSITION


# ── attack / collect_spawned_bullets ──────────────────────────────────────


def test_spitter_attack_appends_acid_bullet(spitter: SpitterZombie, player_entity: Entity) -> None:
    spitter.attack(player_entity)
    bullets = spitter.collect_spawned_bullets()
    assert len(bullets) == 1
    assert isinstance(bullets[0], AcidBullet)


def test_spitter_collect_drains_queue(spitter: SpitterZombie, player_entity: Entity) -> None:
    spitter.attack(player_entity)
    spitter.collect_spawned_bullets()
    assert spitter.collect_spawned_bullets() == []


def test_spitter_attack_emits_zombie_attacked(spitter: SpitterZombie, player_entity: Entity) -> None:
    events: list[dict] = []
    EventBus.on("zombie_attacked", events.append)
    spitter.attack(player_entity)
    assert len(events) == 1
    assert events[0]["attacker"] is spitter


def test_spitter_attack_respects_cooldown(spitter: SpitterZombie) -> None:
    player = Entity(ATTACK_POS.x, ATTACK_POS.y, 100)
    spitter.update(dt=0.1, walls=[], player=player)   # fires, sets cooldown
    spitter.collect_spawned_bullets()
    spitter.update(dt=0.1, walls=[], player=player)   # cooldown active — no new bullet
    assert spitter.collect_spawned_bullets() == []


def test_spitter_attack_zero_direction_does_not_crash(spitter: SpitterZombie) -> None:
    same_pos = Entity(spitter.pos.x, spitter.pos.y, 100)
    spitter.attack(same_pos)  # direction.length_squared() == 0 → early return
    assert spitter.collect_spawned_bullets() == []


# ── Walker base returns empty bullets ─────────────────────────────────────


def test_walker_collect_spawned_bullets_is_empty(walker_data: EnemyData) -> None:
    walker = WalkerZombie(0.0, 0.0, walker_data)
    assert walker.collect_spawned_bullets() == []


# ── Faction filter in CombatSystem ────────────────────────────────────────


def test_acid_bullet_hits_player_via_combat() -> None:
    cfg = PlayerData(max_health=100, speed=0.0, width=32, height=32)
    player = Player(200.0, 200.0, cfg)
    hp_before = player.health.current

    b = AcidBullet(200.0, 200.0, pygame.Vector2(1, 0), 12.0, 350.0, 6, "enemy")
    combat = CombatSystem()
    combat.add_bullets([b])
    combat.update(dt=0.01, walls=[], targets=[player])

    assert player.health.current == pytest.approx(hp_before - 12.0)
    assert b.active is False


def test_acid_bullet_skips_zombie_via_combat(walker_data: EnemyData) -> None:
    walker = WalkerZombie(200.0, 200.0, walker_data)
    hp_before = walker.health.current

    b = AcidBullet(200.0, 200.0, pygame.Vector2(1, 0), 12.0, 350.0, 6, "enemy")
    combat = CombatSystem()
    combat.add_bullets([b])
    combat.update(dt=0.01, walls=[], targets=[walker])

    assert walker.health.current == pytest.approx(hp_before)
    assert b.active is True


# ── Integration: full update cycle ────────────────────────────────────────


def test_spitter_update_at_attack_range_produces_bullet(spitter: SpitterZombie) -> None:
    """Полный цикл: spitter.update() → attack() → collect_spawned_bullets() → AcidBullet."""
    player = Entity(ATTACK_POS.x, ATTACK_POS.y, 100)
    spitter.update(dt=0.1, walls=[], player=player)
    bullets = spitter.collect_spawned_bullets()
    assert len(bullets) == 1
    assert isinstance(bullets[0], AcidBullet)
    assert bullets[0].origin_tag == "enemy"
