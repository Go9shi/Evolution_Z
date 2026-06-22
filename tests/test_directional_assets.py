"""Tests for Sprint 14C.3: импортированные directional-ассеты.

Проверяют, что реальные directional-PNG разложены по контракту `<prefix>_<state>_<token>_<i>`
(token ∈ down/up/side), что AnimationComponent находит их, что LEFT использует side-кадр
(через flip, без отдельного left-арта) и что базовые кадры + fallback сохранены.
Работают с реальным assets/sprites (проект отгружает спрайты, импорт через tools.import_sprites).
"""
from __future__ import annotations

import pygame

from systems.animation import AnimationComponent, AnimState, Facing, draw_animated
from systems.asset_loader import AssetLoader

_ZOMBIE_PREFIXES = ("zombie_walker", "zombie_runner", "zombie_spitter", "boss")


# ── импортированные directional-PNG ──────────────────────────────────────────


class TestDirectionalAssetsImported:
    def test_player_walk_directions_loaded(self) -> None:
        for token in ("down", "up", "side"):
            assert AssetLoader.get(f"player_walk_{token}_0") is not None

    def test_player_idle_directions_loaded(self) -> None:
        for token in ("down", "up"):
            assert AssetLoader.get(f"player_idle_{token}_0") is not None

    def test_player_attack_directions_loaded(self) -> None:
        for token in ("down", "up", "side"):
            assert AssetLoader.get(f"player_attack_{token}_0") is not None

    def test_zombie_rig_walk_directions_loaded(self) -> None:
        for prefix in _ZOMBIE_PREFIXES:
            for token in ("down", "up", "side"):
                assert AssetLoader.get(f"{prefix}_walk_{token}_0") is not None, prefix

    def test_boss_attack_side_loaded(self) -> None:
        assert AssetLoader.get("boss_attack_side_0") is not None

    def test_walk_side_has_full_layout_count(self) -> None:
        # walk = 4 кадра по _DEFAULT_LAYOUT → side_0..3 должны существовать.
        for i in range(4):
            assert AssetLoader.get(f"player_walk_side_{i}") is not None


# ── базовые кадры и отсутствие left-арта ─────────────────────────────────────


class TestBaseFramesPreserved:
    def test_old_frames_still_exist(self) -> None:
        for name in ("player_walk_0", "zombie_walker_walk_0", "boss_death_0", "player_idle_0"):
            assert AssetLoader.get(name) is not None

    def test_no_left_art_created(self) -> None:
        # LEFT строится отражением side → отдельных left-кадров быть не должно.
        for name in ("player_walk_left_0", "zombie_walker_walk_left_0", "boss_attack_left_0"):
            assert AssetLoader.get(name) is None

    def test_static_sprites_present(self) -> None:
        for name in ("player", "zombie_walker", "boss", "item_food", "tile_floor"):
            assert AssetLoader.get(name) is not None


# ── AnimationComponent находит directional-кадр ──────────────────────────────


class TestComponentResolvesDirectional:
    def test_right_resolves_to_side(self) -> None:
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.RIGHT)
        assert comp.directional_sprite == "player_walk_side_0"
        assert AssetLoader.get(comp.directional_sprite) is not None

    def test_left_uses_side_with_flip(self) -> None:
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.LEFT)
        assert comp.directional_sprite == "player_walk_side_0"  # тот же side-кадр
        assert comp.flip_horizontal is True
        assert AssetLoader.get(comp.directional_sprite) is not None

    def test_down_and_up_resolve(self) -> None:
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.DOWN)
        assert AssetLoader.get(comp.directional_sprite) is not None
        comp.set_facing(Facing.UP)
        assert AssetLoader.get(comp.directional_sprite) is not None

    def test_draw_uses_directional_asset(self) -> None:
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.RIGHT)
        surf = pygame.Surface((40, 40))
        assert draw_animated(surf, pygame.Rect(0, 0, 32, 32), comp, "player") is True

    def test_draw_left_renders(self) -> None:
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        comp.set_facing(Facing.LEFT)
        surf = pygame.Surface((40, 40))
        assert draw_animated(surf, pygame.Rect(0, 0, 32, 32), comp, "player") is True


# ── fallback сохранён ────────────────────────────────────────────────────────


class TestFallbackPreserved:
    def test_player_idle_side_falls_back_to_base(self) -> None:
        # У игрока нет idle-side → directional отсутствует, но базовый idle есть.
        assert AssetLoader.get("player_idle_side_0") is None
        comp = AnimationComponent("player")
        comp.play(AnimState.IDLE)
        comp.set_facing(Facing.RIGHT)
        surf = pygame.Surface((40, 40))
        # directional None → база player_idle_0 → True
        assert draw_animated(surf, pygame.Rect(0, 0, 32, 32), comp, "player") is True

    def test_zombie_has_no_idle_directional(self) -> None:
        # У зомби нет папки idle → directional idle отсутствует (уходит в static/primitive).
        assert AssetLoader.get("zombie_walker_idle_down_0") is None

    def test_death_directional_absent_uses_base(self) -> None:
        # death не направленный → directional нет, базовые death-кадры есть.
        assert AssetLoader.get("boss_death_side_0") is None
        assert AssetLoader.get("boss_death_0") is not None
