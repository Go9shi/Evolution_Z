"""Tests for Sprint 14C.2: Directional Animation (Variant B).

Логические направления DOWN/UP/LEFT/RIGHT поверх существующего пайплайна. Арт нарисован
для down/up/side (RIGHT=side, LEFT=side+flip). Проверяем: выбор направления по вектору,
directional-именование кадров, горизонтальный flip для LEFT и полную обратную совместимость
(без directional-PNG поведение прежнее: кадр → static SPRITE → примитив).
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from data.enemy_data import EnemyData
from data.player_data import PlayerData
from entities.boss import PatientZeroBoss
from entities.player import Player
from entities.zombie import WalkerZombie
from settings import BOSS_MAX_HEALTH
from systems.animation import (
    AnimationComponent,
    AnimState,
    Facing,
    draw_animated,
    facing_from_vector,
)
from systems.asset_loader import AssetLoader

_RED = (255, 0, 0)
_GREEN = (0, 255, 0)


def make_png(path: Path, color: tuple[int, int, int], size: int = 16) -> None:
    surf = pygame.Surface((size, size))
    surf.fill(color)
    pygame.image.save(surf, str(path))


def make_split_png(path: Path, left: tuple[int, int, int], right: tuple[int, int, int]) -> None:
    """PNG 16×16: левая половина — left, правая — right (для проверки горизонтального flip)."""
    surf = pygame.Surface((16, 16))
    surf.fill(left)
    surf.fill(right, pygame.Rect(8, 0, 8, 16))
    pygame.image.save(surf, str(path))


@pytest.fixture
def sprites_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr("systems.asset_loader.SPRITES_DIR", tmp_path)
    AssetLoader.clear()
    return tmp_path


def _player_data() -> PlayerData:
    return PlayerData(max_health=100, speed=200.0, width=32, height=32)


def _enemy_data() -> EnemyData:
    return EnemyData(
        max_health=80, speed=60.0, damage=15.0, attack_range=40.0,
        detection_range=400.0, attack_cooldown=1.5, width=32, height=32, xp_reward=10,
    )


# ── Facing enum + выбор направления ──────────────────────────────────────────


class TestFacingSelection:
    def test_enum_members(self) -> None:
        assert {f.name for f in Facing} == {"DOWN", "UP", "LEFT", "RIGHT"}

    def test_cardinal_directions(self) -> None:
        assert facing_from_vector(1, 0, Facing.DOWN) is Facing.RIGHT
        assert facing_from_vector(-1, 0, Facing.DOWN) is Facing.LEFT
        assert facing_from_vector(0, 1, Facing.DOWN) is Facing.DOWN
        assert facing_from_vector(0, -1, Facing.DOWN) is Facing.UP

    def test_dominant_axis(self) -> None:
        assert facing_from_vector(3, 1, Facing.UP) is Facing.RIGHT
        assert facing_from_vector(-3, 1, Facing.UP) is Facing.LEFT
        assert facing_from_vector(1, 3, Facing.LEFT) is Facing.DOWN
        assert facing_from_vector(1, -3, Facing.LEFT) is Facing.UP

    def test_zero_vector_keeps_current(self) -> None:
        assert facing_from_vector(0, 0, Facing.LEFT) is Facing.LEFT
        assert facing_from_vector(0, 0, Facing.UP) is Facing.UP


# ── directional-именование кадров ────────────────────────────────────────────


class TestDirectionalNaming:
    def test_default_facing_down(self) -> None:
        assert AnimationComponent("player").facing is Facing.DOWN

    def test_set_facing(self) -> None:
        comp = AnimationComponent("player")
        comp.set_facing(Facing.LEFT)
        assert comp.facing is Facing.LEFT

    def test_set_facing_keeps_frame(self) -> None:
        comp = AnimationComponent("player", fps=8.0)
        comp.play(AnimState.WALK)
        comp.update(1.0 / 8.0)
        before = comp.frame_index
        comp.set_facing(Facing.RIGHT)
        assert comp.frame_index == before

    def test_art_token_mapping(self) -> None:
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.DOWN)
        assert comp.directional_sprite == "player_walk_down_0"
        comp.set_facing(Facing.UP)
        assert comp.directional_sprite == "player_walk_up_0"
        comp.set_facing(Facing.RIGHT)
        assert comp.directional_sprite == "player_walk_side_0"
        comp.set_facing(Facing.LEFT)
        assert comp.directional_sprite == "player_walk_side_0"  # LEFT = side (flip в рендере)

    def test_flip_only_for_left(self) -> None:
        comp = AnimationComponent("player")
        for facing, flip in [
            (Facing.DOWN, False), (Facing.UP, False),
            (Facing.RIGHT, False), (Facing.LEFT, True),
        ]:
            comp.set_facing(facing)
            assert comp.flip_horizontal is flip

    def test_empty_prefix_no_directional(self) -> None:
        assert AnimationComponent("").directional_sprite is None
        assert AnimationComponent(None).directional_sprite is None


# ── рендер: directional + flip ───────────────────────────────────────────────


class TestDirectionalRender:
    def test_right_uses_side_frame(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "player_walk_side_0.png", _RED)
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.RIGHT)
        surf = pygame.Surface((40, 40))
        surf.fill((0, 0, 0))
        assert draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player") is True
        assert tuple(surf.get_at((8, 8))[:3]) == _RED

    def test_left_flips_side_frame(self, sprites_dir: Path) -> None:
        # side-кадр: левая половина красная, правая зелёная.
        make_split_png(sprites_dir / "player_walk_side_0.png", _RED, _GREEN)
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        surf = pygame.Surface((16, 16))
        # RIGHT (без flip): слева красное, справа зелёное
        comp.set_facing(Facing.RIGHT)
        draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player")
        assert tuple(surf.get_at((2, 8))[:3]) == _RED
        assert tuple(surf.get_at((13, 8))[:3]) == _GREEN
        # LEFT (flip): половины меняются местами
        comp.set_facing(Facing.LEFT)
        draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player")
        assert tuple(surf.get_at((2, 8))[:3]) == _GREEN
        assert tuple(surf.get_at((13, 8))[:3]) == _RED

    def test_down_uses_down_frame(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "player_walk_down_0.png", _GREEN)
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.DOWN)
        surf = pygame.Surface((20, 20))
        draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player")
        assert tuple(surf.get_at((8, 8))[:3]) == _GREEN


# ── обратная совместимость / fallback ────────────────────────────────────────


class TestBackwardCompatibility:
    def test_fallback_to_nondirectional_frame(self, sprites_dir: Path) -> None:
        # Directional-PNG нет, есть обычный кадр → используется он (прежнее поведение).
        make_png(sprites_dir / "player_idle_0.png", _RED)
        comp = AnimationComponent("player")
        comp.set_facing(Facing.RIGHT)  # directional player_idle_side_0 отсутствует
        surf = pygame.Surface((20, 20))
        surf.fill((0, 0, 0))
        assert draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player") is True
        assert tuple(surf.get_at((8, 8))[:3]) == _RED

    def test_fallback_to_static_sprite(self, sprites_dir: Path) -> None:
        # Ни directional, ни покадрового → статический SPRITE.
        make_png(sprites_dir / "player.png", _GREEN)
        comp = AnimationComponent("player")
        surf = pygame.Surface((20, 20))
        surf.fill((0, 0, 0))
        assert draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player") is True
        assert tuple(surf.get_at((8, 8))[:3]) == _GREEN

    def test_no_assets_returns_false(self, sprites_dir: Path) -> None:
        comp = AnimationComponent("player")
        comp.set_facing(Facing.LEFT)
        surf = pygame.Surface((20, 20))
        assert draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player") is False

    def test_current_sprite_unchanged_by_facing(self) -> None:
        # Контракт прежних тестов: current_sprite остаётся не-directional именем.
        comp = AnimationComponent("zombie_walker")
        comp.set_facing(Facing.LEFT)
        assert comp.current_sprite == "zombie_walker_idle_0"

    def test_directional_with_only_static_does_not_crash(self, sprites_dir: Path) -> None:
        comp = AnimationComponent("boss")
        comp.play(AnimState.DEATH)
        comp.set_facing(Facing.UP)
        surf = pygame.Surface((40, 40))
        draw_animated(surf, pygame.Rect(0, 0, 32, 32), comp, "boss")  # не падает


# ── интеграция с сущностями ──────────────────────────────────────────────────


class TestEntityFacing:
    def _walker_facing(self, px: float, py: float) -> Facing:
        z = WalkerZombie(100.0, 100.0, _enemy_data())
        target = Player(px, py, _player_data())
        z.update(0.05, [], target)
        return z.animation.facing

    def test_zombie_faces_right(self) -> None:
        assert self._walker_facing(220.0, 100.0) is Facing.RIGHT

    def test_zombie_faces_left(self) -> None:
        assert self._walker_facing(-20.0, 100.0) is Facing.LEFT

    def test_zombie_faces_up(self) -> None:
        assert self._walker_facing(100.0, -20.0) is Facing.UP

    def test_zombie_faces_down(self) -> None:
        assert self._walker_facing(100.0, 220.0) is Facing.DOWN

    def test_zombie_without_player_keeps_default(self) -> None:
        z = WalkerZombie(100.0, 100.0, _enemy_data())
        z.update(0.05, [], None)
        assert z.animation.facing is Facing.DOWN

    def test_boss_faces_player(self) -> None:
        b = PatientZeroBoss(100.0, 100.0, BOSS_MAX_HEALTH)
        target = Player(360.0, 100.0, _player_data())
        b.update(0.05, [], target)
        assert b.animation.facing is Facing.RIGHT

    def test_boss_faces_up(self) -> None:
        b = PatientZeroBoss(100.0, 100.0, BOSS_MAX_HEALTH)
        target = Player(100.0, -260.0, _player_data())
        b.update(0.05, [], target)
        assert b.animation.facing is Facing.UP

    def test_player_has_facing(self) -> None:
        p = Player(0.0, 0.0, _player_data())
        assert p.animation.facing is Facing.DOWN

    def test_player_draw_does_not_crash(self, sprites_dir: Path) -> None:
        p = Player(16.0, 16.0, _player_data())
        surf = pygame.Surface((64, 64))
        p.draw(surf, pygame.Vector2(0, 0))  # без PNG — примитив, не падает
