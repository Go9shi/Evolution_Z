"""Tests for Sprint 10B: Rifle and Shotgun weapons (polymorphism over the Weapon base)."""
from __future__ import annotations

import json

import pygame

from core.weapon import Weapon
from data.weapon_config import WeaponConfig
from entities.weapons.pistol import Pistol
from entities.weapons.rifle import Rifle
from entities.weapons.shotgun import Shotgun
from settings import DATA_DIR


# ── helpers ───────────────────────────────────────────────────────────────────


def load_config(name: str) -> WeaponConfig:
    """Загрузить конфиг оружия из weapons.json (как GameScreen._load_weapon_config)."""
    with open(DATA_DIR / "weapons.json", encoding="utf-8") as f:
        raw: dict[str, dict] = json.load(f)
    return WeaponConfig(**raw[name])


def rifle_config() -> WeaponConfig:
    return WeaponConfig(damage=12.0, fire_rate=6.0, bullet_speed=480.0, bullet_range=420.0, bullet_size=4)


def shotgun_config() -> WeaponConfig:
    return WeaponConfig(
        damage=8.0, fire_rate=1.0, bullet_speed=380.0, bullet_range=220.0,
        bullet_size=4, pellet_count=6, spread_degrees=30.0,
    )


ORIGIN = pygame.Vector2(100.0, 100.0)
RIGHT = pygame.Vector2(1.0, 0.0)


# ── Backward compatibility ──────────────────────────────────────────────────────


class TestConfigCompat:
    def test_single_shot_defaults(self) -> None:
        # Старый 5-полевой конфиг по-прежнему валиден (новые поля имеют дефолты).
        cfg = WeaponConfig(damage=25.0, fire_rate=2.0, bullet_speed=400.0, bullet_range=350.0, bullet_size=5)
        assert cfg.pellet_count == 1
        assert cfg.spread_degrees == 0.0

    def test_all_three_weapons_load_from_json(self) -> None:
        for name in ("pistol", "rifle", "shotgun"):
            assert isinstance(load_config(name), WeaponConfig)


# ── Rifle ─────────────────────────────────────────────────────────────────────


class TestRifle:
    def test_is_weapon(self) -> None:
        assert isinstance(Rifle(rifle_config()), Weapon)

    def test_fires_single_bullet(self) -> None:
        bullets = Rifle(rifle_config()).fire(ORIGIN, RIGHT)
        assert len(bullets) == 1

    def test_bullet_origin_is_player(self) -> None:
        bullet = Rifle(rifle_config()).fire(ORIGIN, RIGHT)[0]
        assert bullet.origin_tag == "player"

    def test_zero_direction_is_noop(self) -> None:
        assert Rifle(rifle_config()).fire(ORIGIN, pygame.Vector2(0.0, 0.0)) == []

    def test_cooldown_after_fire(self) -> None:
        rifle = Rifle(rifle_config())
        rifle.fire(ORIGIN, RIGHT)
        assert rifle.can_fire is False
        assert rifle.fire(ORIGIN, RIGHT) == []  # кулдаун активен

    def test_fires_again_after_cooldown(self) -> None:
        rifle = Rifle(rifle_config())
        rifle.fire(ORIGIN, RIGHT)
        rifle.update(1.0 / rifle_config().fire_rate + 0.01)
        assert rifle.can_fire is True
        assert len(rifle.fire(ORIGIN, RIGHT)) == 1

    def test_damage_bonus_applied(self) -> None:
        rifle = Rifle(rifle_config())
        rifle.add_damage_bonus(5.0)
        bullet = rifle.fire(ORIGIN, RIGHT)[0]
        assert bullet.damage == rifle_config().damage + 5.0

    def test_higher_fire_rate_than_pistol(self) -> None:
        assert load_config("rifle").fire_rate > load_config("pistol").fire_rate

    def test_lower_damage_than_pistol(self) -> None:
        assert load_config("rifle").damage < load_config("pistol").damage


# ── Shotgun ─────────────────────────────────────────────────────────────────────


class TestShotgun:
    def test_is_weapon(self) -> None:
        assert isinstance(Shotgun(shotgun_config()), Weapon)

    def test_fires_multiple_bullets(self) -> None:
        bullets = Shotgun(shotgun_config()).fire(ORIGIN, RIGHT)
        assert len(bullets) == shotgun_config().pellet_count
        assert len(bullets) > 1  # явно несколько дробинок

    def test_pellets_have_spread(self) -> None:
        bullets = Shotgun(shotgun_config()).fire(ORIGIN, RIGHT)
        # Дробинки летят в разных направлениях → разные позиции после шага.
        for bullet in bullets:
            bullet.update(0.1, [])
        positions = {(round(b.pos.x, 2), round(b.pos.y, 2)) for b in bullets}
        assert len(positions) == len(bullets)

    def test_all_pellets_origin_player(self) -> None:
        bullets = Shotgun(shotgun_config()).fire(ORIGIN, RIGHT)
        assert all(b.origin_tag == "player" for b in bullets)

    def test_pellet_damage_from_config(self) -> None:
        bullets = Shotgun(shotgun_config()).fire(ORIGIN, RIGHT)
        assert all(b.damage == shotgun_config().damage for b in bullets)

    def test_zero_direction_is_noop(self) -> None:
        assert Shotgun(shotgun_config()).fire(ORIGIN, pygame.Vector2(0.0, 0.0)) == []

    def test_cooldown_after_fire(self) -> None:
        shotgun = Shotgun(shotgun_config())
        shotgun.fire(ORIGIN, RIGHT)
        assert shotgun.can_fire is False
        assert shotgun.fire(ORIGIN, RIGHT) == []  # кулдаун блокирует второй залп

    def test_fires_again_after_cooldown(self) -> None:
        shotgun = Shotgun(shotgun_config())
        shotgun.fire(ORIGIN, RIGHT)
        shotgun.update(1.0 / shotgun_config().fire_rate + 0.01)
        assert len(shotgun.fire(ORIGIN, RIGHT)) == shotgun_config().pellet_count


# ── Полиморфизм ──────────────────────────────────────────────────────────────────


class TestPolymorphism:
    def test_uniform_fire_interface(self) -> None:
        # Все виды оружия вызываются единообразно через Weapon.fire (полиморфизм).
        weapons: list[Weapon] = [
            Pistol(load_config("pistol")),
            Rifle(load_config("rifle")),
            Shotgun(load_config("shotgun")),
        ]
        for weapon in weapons:
            bullets = weapon.fire(ORIGIN, RIGHT)
            assert len(bullets) >= 1
