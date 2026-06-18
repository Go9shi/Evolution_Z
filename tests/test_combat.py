import pygame
import pytest

from data.enemy_data import EnemyData
from data.weapon_config import WeaponConfig
from entities.bullet import Bullet
from entities.weapons.pistol import Pistol
from entities.zombie import WalkerZombie
from systems.combat import CombatSystem
from systems.event_bus import EventBus


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def pistol_config() -> WeaponConfig:
    return WeaponConfig(
        damage=25.0,
        fire_rate=2.0,
        bullet_speed=400.0,
        bullet_range=350.0,
        bullet_size=5,
    )


@pytest.fixture
def pistol(pistol_config: WeaponConfig) -> Pistol:
    return Pistol(pistol_config)


@pytest.fixture
def bullet() -> Bullet:
    return Bullet(
        x=100.0, y=100.0,
        velocity=pygame.Vector2(400.0, 0.0),
        damage=25.0,
        max_range=350.0,
        size=5,
        origin_tag="player",
    )


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
def walker(walker_data: EnemyData) -> WalkerZombie:
    return WalkerZombie(200.0, 200.0, walker_data)


@pytest.fixture
def combat() -> CombatSystem:
    return CombatSystem()


# ── WeaponConfig ───────────────────────────────────────────────────────────

def test_weapon_config_fields(pistol_config: WeaponConfig) -> None:
    assert pistol_config.damage == 25.0
    assert pistol_config.fire_rate == 2.0
    assert pistol_config.bullet_speed == 400.0
    assert pistol_config.bullet_range == 350.0
    assert pistol_config.bullet_size == 5


def test_weapon_config_is_dataclass(pistol_config: WeaponConfig) -> None:
    from dataclasses import fields
    # 5 базовых полей + 2 дефолтных для дробовика (Sprint 10B): pellet_count, spread_degrees.
    assert len(fields(pistol_config)) == 7


# ── Bullet ─────────────────────────────────────────────────────────────────

def test_bullet_initial_state(bullet: Bullet) -> None:
    assert bullet.active is True
    assert bullet.pos.x == pytest.approx(100.0)
    assert bullet.pos.y == pytest.approx(100.0)


def test_bullet_damage_and_size_properties(bullet: Bullet) -> None:
    assert bullet.damage == pytest.approx(25.0)
    assert bullet.size == 5


def test_bullet_origin_tag(bullet: Bullet) -> None:
    assert bullet.origin_tag == "player"


def test_bullet_rect_centered_on_pos(bullet: Bullet) -> None:
    r = bullet.rect
    assert r.centerx == int(bullet.pos.x)
    assert r.centery == int(bullet.pos.y)
    assert r.width == bullet.size * 2
    assert r.height == bullet.size * 2


def test_bullet_moves_on_update(bullet: Bullet) -> None:
    bullet.update(dt=0.1)
    assert bullet.pos.x == pytest.approx(140.0)  # 100 + 400*0.1
    assert bullet.pos.y == pytest.approx(100.0)


def test_bullet_deactivates_at_max_range(bullet: Bullet) -> None:
    # dt достаточно, чтобы превысить max_range=350 за один шаг
    bullet.update(dt=1.0)
    assert bullet.active is False


def test_bullet_deactivates_on_wall_hit(bullet: Bullet) -> None:
    # Стена прямо перед пулей
    wall = pygame.Rect(110, 90, 32, 32)
    bullet.update(dt=0.1, walls=[wall])
    assert bullet.active is False


def test_bullet_passes_through_distant_wall(bullet: Bullet) -> None:
    # Стена далеко — пуля не деактивируется
    wall = pygame.Rect(600, 600, 32, 32)
    bullet.update(dt=0.1, walls=[wall])
    assert bullet.active is True


# ── Pistol ─────────────────────────────────────────────────────────────────

def test_pistol_fires_single_bullet_list(pistol: Pistol) -> None:
    bullets = pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(1, 0))
    assert len(bullets) == 1
    assert isinstance(bullets[0], Bullet)


def test_pistol_returns_empty_list_on_cooldown(pistol: Pistol) -> None:
    pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(1, 0))
    bullets = pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(1, 0))
    assert bullets == []


def test_pistol_returns_empty_list_on_zero_direction(pistol: Pistol) -> None:
    bullets = pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(0, 0))
    assert bullets == []


def test_pistol_bullet_damage_from_config(pistol: Pistol, pistol_config: WeaponConfig) -> None:
    bullets = pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(1, 0))
    assert bullets[0].damage == pytest.approx(pistol_config.damage)


def test_pistol_sets_cooldown_after_fire(pistol: Pistol) -> None:
    assert pistol.can_fire is True
    pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(1, 0))
    assert pistol.can_fire is False


def test_pistol_can_fire_after_cooldown_expires(pistol: Pistol, pistol_config: WeaponConfig) -> None:
    pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(1, 0))
    # fire_rate=2.0 → cooldown=0.5s
    pistol.update(dt=1.0 / pistol_config.fire_rate)
    assert pistol.can_fire is True


def test_pistol_bullet_velocity_matches_direction(pistol: Pistol, pistol_config: WeaponConfig) -> None:
    bullets = pistol.fire(pygame.Vector2(0, 0), pygame.Vector2(0, 1))
    b = bullets[0]
    b.update(dt=1.0, walls=None)  # move for 1s to check direction
    # Пуля должна двигаться строго вниз (x неизменен, y увеличился)
    assert b.pos.x == pytest.approx(0.0, abs=1.0)
    assert b.pos.y > 0.0


# ── CombatSystem ───────────────────────────────────────────────────────────

def test_combat_add_bullets_increases_pool(combat: CombatSystem, bullet: Bullet) -> None:
    assert len(combat.bullets) == 0
    combat.add_bullets([bullet])
    assert len(combat.bullets) == 1


def test_combat_bullet_moves_on_update(combat: CombatSystem, bullet: Bullet) -> None:
    combat.add_bullets([bullet])
    combat.update(dt=0.1, walls=[], targets=[])
    assert bullet.pos.x == pytest.approx(140.0)


def test_combat_bullet_damages_target_on_hit(
    combat: CombatSystem, walker: WalkerZombie
) -> None:
    hp_before = walker.health.current
    # Пуля спавнится прямо на позиции зомби
    b = Bullet(200.0, 200.0, pygame.Vector2(1, 0), damage=25.0, max_range=350.0, size=5, origin_tag="player")
    combat.add_bullets([b])
    combat.update(dt=0.01, walls=[], targets=[walker])
    assert walker.health.current == pytest.approx(hp_before - 25.0)


def test_combat_bullet_deactivates_on_hit(
    combat: CombatSystem, walker: WalkerZombie
) -> None:
    b = Bullet(200.0, 200.0, pygame.Vector2(1, 0), damage=25.0, max_range=350.0, size=5, origin_tag="player")
    combat.add_bullets([b])
    combat.update(dt=0.01, walls=[], targets=[walker])
    assert b.active is False


def test_combat_emits_bullet_hit_event(
    combat: CombatSystem, walker: WalkerZombie
) -> None:
    events: list[dict] = []
    EventBus.on("bullet_hit", events.append)

    b = Bullet(200.0, 200.0, pygame.Vector2(1, 0), damage=25.0, max_range=350.0, size=5, origin_tag="player")
    combat.add_bullets([b])
    combat.update(dt=0.01, walls=[], targets=[walker])

    assert len(events) == 1
    assert events[0]["target"] is walker


def test_combat_removes_inactive_bullets(combat: CombatSystem) -> None:
    # Пуля с нулевой дальностью деактивируется немедленно
    b = Bullet(0.0, 0.0, pygame.Vector2(1, 0), damage=10.0, max_range=0.001, size=5, origin_tag="player")
    combat.add_bullets([b])
    combat.update(dt=1.0, walls=[], targets=[])
    assert len(combat.bullets) == 0


def test_combat_no_hit_on_distant_target(
    combat: CombatSystem, walker: WalkerZombie
) -> None:
    hp_before = walker.health.current
    # Пуля далеко от зомби
    b = Bullet(0.0, 0.0, pygame.Vector2(1, 0), damage=25.0, max_range=350.0, size=5, origin_tag="player")
    combat.add_bullets([b])
    combat.update(dt=0.01, walls=[], targets=[walker])
    assert walker.health.current == pytest.approx(hp_before)


# ── Integration ────────────────────────────────────────────────────────────

def test_full_combat_loop_kills_walker(walker_data: EnemyData) -> None:
    """Полный цикл: Player.fire() → CombatSystem.update() → WalkerZombie умирает → entity_died."""
    from data.player_data import PlayerData
    from entities.player import Player

    died_events: list[dict] = []
    EventBus.on("entity_died", died_events.append)

    player = Player(0.0, 0.0, PlayerData(max_health=100, speed=0.0, width=32, height=32))
    player.equip(Pistol(WeaponConfig(
        damage=9999.0, fire_rate=10.0, bullet_speed=400.0, bullet_range=500.0, bullet_size=5
    )))

    # Зомби прямо перед игроком
    zombie = WalkerZombie(50.0, 0.0, walker_data)
    combat = CombatSystem()

    bullets = player.fire(pygame.Vector2(1, 0))
    combat.add_bullets(bullets)
    # dt=0.1 → bullet moves 400*0.1=40px; zombie rect x:34-66 → hit
    combat.update(dt=0.1, walls=[], targets=[zombie])

    assert not zombie.is_alive
    assert not zombie.active
    assert len(died_events) == 1
    assert died_events[0]["entity"] is zombie


def test_dead_enemy_not_double_damaged(walker_data: EnemyData) -> None:
    """Мёртвый зомби (active=False) не получает урон от пуль."""
    zombie = WalkerZombie(200.0, 200.0, walker_data)
    zombie.take_damage(9999.0)          # убиваем вручную
    assert not zombie.active

    combat = CombatSystem()
    b = Bullet(200.0, 200.0, pygame.Vector2(1, 0), damage=25.0, max_range=350.0, size=5, origin_tag="player")
    combat.add_bullets([b])
    combat.update(dt=0.01, walls=[], targets=[zombie])

    # HP не изменился (уже 0) и пуля продолжает лететь
    assert zombie.health.current == pytest.approx(0.0)
    assert b.active is True  # пуля не деактивирована — цель пропущена
