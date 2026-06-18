"""Tests for Sprint 14B: Animation Pipeline.

AnimationComponent — кадровая анимация поверх AssetLoader: смена состояний, продвижение
кадров по dt, циклические/одноразовые клипы, graceful fallback при отсутствии PNG, и
интеграция с сущностями (Player/Zombie/Boss) без изменения игровой логики.
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from data.enemy_data import EnemyData
from data.player_data import PlayerData
from data.spitter_data import SpitterData
from data.weapon_config import WeaponConfig
from entities.boss import PatientZeroBoss
from entities.player import Player
from entities.weapons.pistol import Pistol
from entities.zombie import AIState, RunnerZombie, SpitterZombie, WalkerZombie
from settings import BOSS_MAX_HEALTH
from systems.animation import (
    AnimationClip,
    AnimationComponent,
    AnimState,
    draw_animated,
)
from systems.asset_loader import AssetLoader

_RED = (255, 0, 0)
_FPS = 8.0
_FRAME_TIME = 1.0 / _FPS


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


def _player_data(max_health: int = 100, speed: float = 200.0) -> PlayerData:
    return PlayerData(max_health=max_health, speed=speed, width=32, height=32)


def _enemy_data() -> EnemyData:
    return EnemyData(
        max_health=80, speed=60.0, damage=15.0, attack_range=40.0,
        detection_range=180.0, attack_cooldown=1.5, width=32, height=32, xp_reward=10,
    )


def _spitter_data() -> SpitterData:
    return SpitterData(
        max_health=50, speed=70.0, damage=0.0, attack_range=200.0,
        detection_range=280.0, attack_cooldown=2.0, width=30, height=30, xp_reward=20,
        spit_damage=12.0, spit_speed=300.0, spit_range=350.0, safe_distance=100.0,
    )


def _weapon_config() -> WeaponConfig:
    return WeaponConfig(
        damage=10.0, fire_rate=5.0, bullet_speed=400.0, bullet_range=400.0, bullet_size=6
    )


def player() -> Player:
    return Player(100.0, 100.0, _player_data())


def walker() -> WalkerZombie:
    return WalkerZombie(100.0, 100.0, _enemy_data())


def runner() -> RunnerZombie:
    return RunnerZombie(100.0, 100.0, _enemy_data())


def spitter() -> SpitterZombie:
    return SpitterZombie(100.0, 100.0, _spitter_data())


def boss() -> PatientZeroBoss:
    return PatientZeroBoss(100.0, 100.0, BOSS_MAX_HEALTH)


# ── состояния ───────────────────────────────────────────────────────────────


class TestStates:
    def test_default_state_is_idle(self) -> None:
        assert AnimationComponent("player").state is AnimState.IDLE

    def test_play_switches_state(self) -> None:
        comp = AnimationComponent("player")
        comp.play(AnimState.WALK)
        assert comp.state is AnimState.WALK

    def test_play_resets_frame_and_progress(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME * 2)
        assert comp.frame_index == 2
        comp.play(AnimState.IDLE)
        assert comp.frame_index == 0

    def test_play_same_state_is_noop(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME)
        assert comp.frame_index == 1
        comp.play(AnimState.WALK)  # тот же state — без сброса
        assert comp.frame_index == 1

    def test_play_restart_forces_reset(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME)
        comp.play(AnimState.WALK, restart=True)
        assert comp.frame_index == 0

    def test_all_four_states_have_clips(self) -> None:
        comp = AnimationComponent("player")
        for state in (AnimState.IDLE, AnimState.WALK, AnimState.ATTACK, AnimState.DEATH):
            assert comp.frame_count(state) > 0


# ── продвижение кадров ────────────────────────────────────────────────────────


class TestFrameStepping:
    def test_advances_one_frame_per_frame_time(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME)
        assert comp.frame_index == 1

    def test_no_advance_below_frame_time(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME * 0.4)
        assert comp.frame_index == 0

    def test_accumulates_partial_dt(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME * 0.6)
        comp.update(_FRAME_TIME * 0.6)  # суммарно > frame_time → +1
        assert comp.frame_index == 1

    def test_multiple_frames_in_one_big_dt(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)  # walk = 4 кадра
        comp.update(_FRAME_TIME * 3)
        assert comp.frame_index == 3

    def test_zero_dt_does_not_advance(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(0.0)
        assert comp.frame_index == 0

    def test_current_sprite_name_follows_frame(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        assert comp.current_sprite == "player_walk_0"
        comp.update(_FRAME_TIME)
        assert comp.current_sprite == "player_walk_1"


# ── циклические анимации ──────────────────────────────────────────────────────


class TestLooping:
    def test_walk_loops_back_to_zero(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)  # 4 кадра: 0→1→2→3→0
        comp.update(_FRAME_TIME * 4)
        assert comp.frame_index == 0

    def test_loop_never_finishes(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME * 20)
        assert comp.is_finished is False

    def test_idle_loops(self) -> None:
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.IDLE)  # 2 кадра
        comp.update(_FRAME_TIME * 2)
        assert comp.frame_index == 0


# ── одноразовые анимации (death) ──────────────────────────────────────────────


class TestOneShot:
    def test_death_stops_on_last_frame(self) -> None:
        comp = AnimationComponent("boss", fps=_FPS)
        comp.play(AnimState.DEATH)  # 4 кадра, loop=False
        comp.update(_FRAME_TIME * 10)
        assert comp.frame_index == 3  # последний кадр

    def test_death_sets_finished(self) -> None:
        comp = AnimationComponent("boss", fps=_FPS)
        comp.play(AnimState.DEATH)
        comp.update(_FRAME_TIME * 10)
        assert comp.is_finished is True

    def test_death_does_not_wrap(self) -> None:
        comp = AnimationComponent("boss", fps=_FPS)
        comp.play(AnimState.DEATH)
        comp.update(_FRAME_TIME * 3)  # дойти до кадра 3
        comp.update(_FRAME_TIME * 3)  # дальше — стоп, не на 0
        assert comp.frame_index == 3

    def test_replay_death_resets_finished(self) -> None:
        comp = AnimationComponent("boss", fps=_FPS)
        comp.play(AnimState.DEATH)
        comp.update(_FRAME_TIME * 10)
        comp.play(AnimState.DEATH, restart=True)
        assert comp.is_finished is False and comp.frame_index == 0


# ── fallback при отсутствии кадров ────────────────────────────────────────────


class TestFallback:
    def test_empty_prefix_has_no_frames(self) -> None:
        comp = AnimationComponent("")
        assert comp.current_sprite is None
        assert comp.frame_count(AnimState.IDLE) == 0

    def test_none_prefix_has_no_frames(self) -> None:
        comp = AnimationComponent(None)
        assert comp.current_sprite is None

    def test_empty_prefix_update_is_safe(self) -> None:
        comp = AnimationComponent("")
        comp.play(AnimState.WALK)
        comp.update(_FRAME_TIME * 5)  # не должно падать
        assert comp.current_sprite is None

    def test_custom_layout_single_frame(self) -> None:
        comp = AnimationComponent(
            "x", fps=_FPS, layout={AnimState.IDLE: (1, True)}
        )
        comp.play(AnimState.IDLE)
        comp.update(_FRAME_TIME * 3)
        assert comp.frame_index == 0  # один кадр — продвигать нечего

    def test_non_positive_fps_falls_back_to_default(self) -> None:
        comp = AnimationComponent("player", fps=0.0)
        comp.play(AnimState.WALK)
        comp.update(1.0 / 8.0)  # дефолтный fps = ANIMATION_FPS = 8
        assert comp.frame_index == 1


# ── интеграция с AssetLoader ──────────────────────────────────────────────────


class TestAssetLoaderIntegration:
    def test_draw_animated_uses_frame_png(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "player_idle_0.png")
        comp = AnimationComponent("player")
        comp.play(AnimState.IDLE)
        surf = pygame.Surface((40, 40))
        surf.fill((0, 0, 0))
        assert draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player") is True
        assert tuple(surf.get_at((0, 0))[:3]) == _RED

    def test_draw_animated_falls_back_to_static_sprite(self, sprites_dir: Path) -> None:
        # Кадра анимации нет, но есть статический "player.png" → рисуется он.
        make_png(sprites_dir / "player.png")
        comp = AnimationComponent("player")
        comp.play(AnimState.IDLE)
        surf = pygame.Surface((40, 40))
        surf.fill((0, 0, 0))
        assert draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player") is True
        assert tuple(surf.get_at((0, 0))[:3]) == _RED

    def test_draw_animated_returns_false_without_any_png(self, sprites_dir: Path) -> None:
        comp = AnimationComponent("player")
        surf = pygame.Surface((40, 40))
        assert draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player") is False

    def test_frame_switch_changes_rendered_png(self, sprites_dir: Path) -> None:
        make_png(sprites_dir / "player_walk_0.png", (255, 0, 0))
        make_png(sprites_dir / "player_walk_1.png", (0, 255, 0))
        comp = AnimationComponent("player", fps=_FPS)
        comp.play(AnimState.WALK)
        surf = pygame.Surface((40, 40))
        draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player")
        assert tuple(surf.get_at((0, 0))[:3]) == (255, 0, 0)
        comp.update(_FRAME_TIME)
        draw_animated(surf, pygame.Rect(0, 0, 16, 16), comp, "player")
        assert tuple(surf.get_at((0, 0))[:3]) == (0, 255, 0)

    def test_imported_animation_frames_load(self) -> None:
        # После импорта пака (tools.import_sprites) кадры боевых сущностей резолвятся в Surface.
        for name in (
            "player_idle_0", "player_walk_0", "player_attack_0", "player_death_0",
            "zombie_walker_walk_0", "zombie_runner_walk_0", "zombie_spitter_walk_0",
            "boss_death_0",
        ):
            assert AssetLoader.get(name) is not None
        # Несуществующий кадр по-прежнему None — контракт negative-cache сохранён.
        assert AssetLoader.get("player_idle_999") is None


# ── интеграция с Entity ───────────────────────────────────────────────────────


class TestEntityIntegration:
    def test_player_has_animation(self) -> None:
        assert isinstance(player().animation, AnimationComponent)

    def test_player_idle_when_not_moving(self) -> None:
        p = player()
        p.update(0.1, [])  # без ввода клавиш → idle
        assert p.animation.state is AnimState.IDLE

    def test_player_attack_state_after_fire(self) -> None:
        p = player()
        p.equip(Pistol(_weapon_config()))
        bullets = p.fire(pygame.Vector2(1, 0))
        assert bullets  # действительно выстрелил
        p.update(0.01, [])
        assert p.animation.state is AnimState.ATTACK

    def test_player_attack_expires(self) -> None:
        p = player()
        p.equip(Pistol(_weapon_config()))
        p.fire(pygame.Vector2(1, 0))
        p.update(1.0, [])  # дольше PLAYER_ATTACK_ANIM_DURATION → attack спадает
        assert p.animation.state is AnimState.IDLE

    def test_zombie_idle_without_player(self) -> None:
        z = walker()
        z.update(0.1, [], None)
        assert z.animation.state is AnimState.IDLE

    def test_zombie_walk_when_chasing(self) -> None:
        z = walker()  # detection=180, attack=40
        target = Player(160.0, 100.0, _player_data(max_health=1, speed=0.0))  # dist 60: chase
        z.update(0.05, [], target)
        assert z.state is AIState.CHASE
        assert z.animation.state is AnimState.WALK

    def test_zombie_attack_animation_when_attacking(self) -> None:
        z = walker()
        target = Player(101.0, 100.0, _player_data(max_health=100, speed=0.0))  # dist 1: attack
        z.update(0.05, [], target)
        assert z.state is AIState.ATTACK
        assert z.animation.state is AnimState.ATTACK

    def test_runner_and_spitter_have_animation(self) -> None:
        assert isinstance(runner().animation, AnimationComponent)
        assert isinstance(spitter().animation, AnimationComponent)

    def test_entity_anim_prefix_matches_sprite(self) -> None:
        assert walker().animation.current_sprite == "zombie_walker_idle_0"
        assert runner().animation.current_sprite == "zombie_runner_idle_0"
        assert spitter().animation.current_sprite == "zombie_spitter_idle_0"

    def test_boss_has_animation(self) -> None:
        assert isinstance(boss().animation, AnimationComponent)

    def test_boss_idle_without_player(self) -> None:
        b = boss()
        b.update(0.1, [], None)
        assert b.animation.state is AnimState.IDLE

    def test_boss_walk_when_player_detected(self) -> None:
        b = boss()  # detection=400, attack=70
        target = Player(180.0, 100.0, _player_data(max_health=1, speed=0.0))  # dist 80: walk
        b.update(0.05, [], target)
        assert b.animation.state is AnimState.WALK

    def test_boss_attack_when_in_range(self) -> None:
        b = boss()
        target = Player(110.0, 100.0, _player_data(max_health=1, speed=0.0))  # dist 10: attack
        b.update(0.05, [], target)
        assert b.animation.state is AnimState.ATTACK

    def test_boss_death_state_on_lethal_damage(self) -> None:
        b = boss()
        b.take_damage(BOSS_MAX_HEALTH * 2)
        assert b.animation.state is AnimState.DEATH


# ── zero-regression: рендер без PNG = примитив ────────────────────────────────


class TestZeroRegression:
    def test_entity_draw_does_not_crash(self, sprites_dir: Path) -> None:
        surf = pygame.Surface((200, 200))
        player().draw(surf, pygame.Vector2(0, 0))
        walker().draw(surf, pygame.Vector2(0, 0))
        runner().draw(surf, pygame.Vector2(0, 0))
        spitter().draw(surf, pygame.Vector2(0, 0))
        boss().draw(surf, pygame.Vector2(0, 0))

    def test_player_fallback_color_without_png(self, sprites_dir: Path) -> None:
        # Без PNG игрок рисуется fallback-цветом COLOR (как до 14B).
        surf = pygame.Surface((64, 64))
        surf.fill((0, 0, 0))
        p = Player(16.0, 16.0, _player_data())
        p.draw(surf, pygame.Vector2(0, 0))
        assert tuple(surf.get_at((16, 16))[:3]) == Player.COLOR

    def test_clip_is_immutable(self) -> None:
        clip = AnimationClip(frames=("a", "b"), fps=8.0, loop=True)
        with pytest.raises((AttributeError, Exception)):
            clip.frames = ("c",)  # type: ignore[misc]
