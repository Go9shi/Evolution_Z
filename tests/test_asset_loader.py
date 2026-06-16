"""Tests for Sprint 11C: sprite rendering pipeline — AssetLoader cache + entity/tile fallback."""
from __future__ import annotations

import json
from pathlib import Path

import pygame
import pytest

from data.enemy_data import EnemyData
from data.player_data import PlayerData
from entities.boss import PatientZeroBoss
from entities.player import Player
from entities.zombie import WalkerZombie
from settings import DATA_DIR, TILE_SIZE
from systems.asset_loader import AssetLoader
from systems.game_world import GameWorld

_RED = (255, 0, 0)


# ── helpers ───────────────────────────────────────────────────────────────────


def make_png(path: Path, color: tuple[int, int, int] = _RED, size: int = 8) -> Path:
    """Создать сплошной PNG-спрайт (без видеорежима — pygame.image.save работает)."""
    surf = pygame.Surface((size, size))
    surf.fill(color)
    pygame.image.save(surf, str(path))
    return path


@pytest.fixture
def sprites_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Подменить SPRITES_DIR на пустую временную папку (изоляция + чистый кэш)."""
    monkeypatch.setattr("systems.asset_loader.SPRITES_DIR", tmp_path)
    AssetLoader.clear()
    return tmp_path


def player() -> Player:
    cfg = PlayerData(**json.load(open(DATA_DIR / "player.json", encoding="utf-8")))
    return Player(100.0, 100.0, cfg)


def walker() -> WalkerZombie:
    data = EnemyData(
        max_health=80, speed=60.0, damage=15.0, attack_range=40.0,
        detection_range=180.0, attack_cooldown=1.5, width=32, height=32, xp_reward=10,
    )
    return WalkerZombie(100.0, 100.0, data)


# ── AssetLoader ────────────────────────────────────────────────────────────────


class TestAssetLoader:
    def test_loads_png(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "foo.png")
        assert isinstance(AssetLoader.get("foo"), pygame.Surface)

    def test_caches_same_object(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "foo.png")
        assert AssetLoader.get("foo") is AssetLoader.get("foo")  # без повторной загрузки

    def test_missing_file_returns_none(self, sprites_dir: Path) -> None:
        assert AssetLoader.get("nope") is None  # не падает

    def test_missing_is_negatively_cached(self, sprites_dir: Path) -> None:
        AssetLoader.get("nope")
        assert "nope" in AssetLoader._cache and AssetLoader._cache["nope"] is None

    def test_none_name_returns_none(self, sprites_dir: Path) -> None:
        assert AssetLoader.get(None) is None

    def test_clear_empties_cache(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "foo.png")
        AssetLoader.get("foo")
        AssetLoader.clear()
        assert AssetLoader._cache == {}

    def test_draw_sprite_blits_when_present(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "foo.png")
        surf = pygame.Surface((16, 16))
        assert AssetLoader.draw_sprite(surf, "foo", pygame.Rect(0, 0, 16, 16)) is True
        assert surf.get_at((4, 4))[:3] == _RED

    def test_draw_sprite_false_when_missing(self, sprites_dir: Path) -> None:
        surf = pygame.Surface((16, 16))
        assert AssetLoader.draw_sprite(surf, "nope", pygame.Rect(0, 0, 16, 16)) is False


# ── Интеграция: сущности используют спрайт ───────────────────────────────────────


class TestEntitySprites:
    def test_player_uses_sprite_when_present(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "player.png")
        p = player()
        surf = pygame.Surface((400, 400))
        p.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at(p.rect.center)[:3] == _RED  # спрайт нарисован

    def test_player_fallback_without_sprite(self, sprites_dir: Path) -> None:
        p = player()
        surf = pygame.Surface((400, 400))
        surf.fill((0, 0, 0))
        p.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at(p.rect.center)[:3] == Player.COLOR  # fallback-примитив

    def test_walker_uses_sprite_when_present(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "zombie_walker.png")
        z = walker()
        surf = pygame.Surface((400, 400))
        z.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at(z.rect.center)[:3] == _RED

    def test_walker_fallback_without_sprite(self, sprites_dir: Path) -> None:
        z = walker()
        surf = pygame.Surface((400, 400))
        surf.fill((0, 0, 0))
        z.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at(z.rect.center)[:3] == WalkerZombie.COLOR

    def test_boss_sprite_name_resolves(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "boss.png")
        boss = PatientZeroBoss(100.0, 100.0, 100)
        surf = pygame.Surface((400, 400))
        boss.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at(boss.rect.center)[:3] == _RED

    def test_boss_fallback_without_sprite(self, sprites_dir: Path) -> None:
        boss = PatientZeroBoss(100.0, 100.0, 100)
        surf = pygame.Surface((400, 400))
        surf.fill((0, 0, 0))
        boss.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at(boss.rect.center)[:3] == PatientZeroBoss.COLOR


# ── Интеграция: тайлы ────────────────────────────────────────────────────────────


class TestTileSprites:
    def test_tiles_use_sprite_when_present(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "tile_wall.png", size=TILE_SIZE)
        make_png(sprites_dir / "tile_floor.png", color=(0, 0, 255), size=TILE_SIZE)
        world = GameWorld()  # level1.tmx
        surf = pygame.Surface((800, 600))
        world.draw(surf, pygame.Vector2(0, 0))  # стена в (0,0) → красный спрайт
        assert surf.get_at((4, 4))[:3] == _RED

    def test_tiles_fallback_without_sprite(self, sprites_dir: Path) -> None:
        world = GameWorld()
        surf = pygame.Surface((800, 600))
        world.draw(surf, pygame.Vector2(0, 0))  # не падает, рисует примитивами


# ── Регрессия: отсутствие ассетов не ломает игру ─────────────────────────────────


class TestRegression:
    def test_default_sprites_dir_has_no_assets(self) -> None:
        # В проекте спрайтов нет → все get() дают None, рендер идёт по fallback.
        for name in ("player", "zombie_walker", "zombie_runner", "zombie_spitter",
                     "boss", "tile_wall", "tile_floor"):
            assert AssetLoader.get(name) is None

    def test_full_world_draw_without_assets(self) -> None:
        world = GameWorld()
        surf = pygame.Surface((800, 600))
        world.draw(surf, pygame.Vector2(0, 0))  # без ассетов — без исключений
