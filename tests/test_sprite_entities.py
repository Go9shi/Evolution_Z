"""Tests for Sprint 12A: extend sprite pipeline to Bullet / FoodItem / QuestItem (with fallback)."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from entities.bullet import AcidBullet, Bullet
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from systems.asset_loader import AssetLoader

_RED = (255, 0, 0)


# ── helpers ───────────────────────────────────────────────────────────────────


def make_png(path: Path, color: tuple[int, int, int] = _RED, size: int = 16) -> Path:
    surf = pygame.Surface((size, size))
    surf.fill(color)
    pygame.image.save(surf, str(path))
    return path


@pytest.fixture
def sprites_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("systems.asset_loader.SPRITES_DIR", tmp_path)
    AssetLoader.clear()
    return tmp_path


def bullet() -> Bullet:
    return Bullet(
        x=100.0, y=100.0, velocity=pygame.Vector2(0.0, 0.0),
        damage=5.0, max_range=200.0, size=6, origin_tag="player",
    )


def food() -> FoodItem:
    return FoodItem(100.0, 100.0, "canned_beans", "Beans", "desc", 25.0)


def quest() -> QuestItem:
    return QuestItem(100.0, 100.0, "vaccine_component_alpha", "Alpha", "desc")


def center_pixel(obj, surf: pygame.Surface) -> tuple[int, ...]:  # type: ignore[no-untyped-def]
    obj.draw(surf, pygame.Vector2(0, 0))
    return tuple(surf.get_at((int(obj.pos.x), int(obj.pos.y)))[:3])


# ── SPRITE-идентификаторы ────────────────────────────────────────────────────────


class TestSpriteIds:
    def test_bullet_sprite_id(self) -> None:
        assert Bullet.SPRITE == "bullet"

    def test_acid_bullet_sprite_id(self) -> None:
        assert AcidBullet.SPRITE == "acid_bullet"

    def test_food_sprite_id(self) -> None:
        assert FoodItem.SPRITE == "item_food"

    def test_quest_sprite_id(self) -> None:
        assert QuestItem.SPRITE == "item_quest"


# ── Спрайт при наличии PNG ───────────────────────────────────────────────────────


class TestSpriteRendering:
    def test_bullet_uses_sprite(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "bullet.png")
        assert center_pixel(bullet(), pygame.Surface((200, 200))) == _RED

    def test_acid_bullet_uses_sprite(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "acid_bullet.png")
        b = AcidBullet(
            x=100.0, y=100.0, velocity=pygame.Vector2(0.0, 0.0),
            damage=5.0, max_range=200.0, size=6, origin_tag="enemy",
        )
        assert center_pixel(b, pygame.Surface((200, 200))) == _RED

    def test_food_uses_sprite(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "item_food.png")
        assert center_pixel(food(), pygame.Surface((200, 200))) == _RED

    def test_quest_uses_sprite(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "item_quest.png")
        assert center_pixel(quest(), pygame.Surface((200, 200))) == _RED


# ── Fallback при отсутствии PNG ──────────────────────────────────────────────────


class TestFallback:
    def test_bullet_fallback(self, sprites_dir: Path) -> None:
        surf = pygame.Surface((200, 200))
        surf.fill((0, 0, 0))
        assert center_pixel(bullet(), surf) == Bullet.COLOR

    def test_food_fallback(self, sprites_dir: Path) -> None:
        surf = pygame.Surface((200, 200))
        surf.fill((0, 0, 0))
        assert center_pixel(food(), surf) == FoodItem.COLOR

    def test_quest_fallback(self, sprites_dir: Path) -> None:
        surf = pygame.Surface((200, 200))
        surf.fill((0, 0, 0))
        assert center_pixel(quest(), surf) == QuestItem.COLOR

    def test_no_assets_in_project(self) -> None:
        # В проекте PNG нет → все новые id дают None (рендер по fallback).
        for name in ("bullet", "acid_bullet", "item_food", "item_quest"):
            assert AssetLoader.get(name) is None

    def test_draw_does_not_crash_without_assets(self) -> None:
        surf = pygame.Surface((200, 200))
        bullet().draw(surf, pygame.Vector2(0, 0))
        food().draw(surf, pygame.Vector2(0, 0))
        quest().draw(surf, pygame.Vector2(0, 0))
