"""Tests for Sprint 10D: Game Over / Lose Condition + freeze of terminal states."""
from __future__ import annotations

import pygame

from entities.bullet import Bullet
from ui.game_screen import GameScreen


# ── helpers ───────────────────────────────────────────────────────────────────


def make_screen() -> GameScreen:
    return GameScreen()


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


def kill(entity) -> None:  # type: ignore[no-untyped-def]
    entity.take_damage(entity.health.maximum)


def moving_bullet(pos: pygame.Vector2) -> Bullet:
    return Bullet(
        x=pos.x, y=pos.y,
        velocity=pygame.Vector2(200.0, 0.0),
        damage=5.0,
        max_range=500.0,
        size=5,
        origin_tag="player",
    )


# ── Базовое состояние ───────────────────────────────────────────────────────────


class TestBasicState:
    def test_game_over_false_after_creation(self) -> None:
        assert make_screen().game_over is False

    def test_victory_false_after_creation(self) -> None:
        assert make_screen().victory is False


# ── Смерть игрока ────────────────────────────────────────────────────────────────


class TestPlayerDeath:
    def test_lethal_damage_triggers_game_over(self) -> None:
        screen = make_screen()
        kill(screen._player)
        assert screen.game_over is True

    def test_non_lethal_damage_keeps_playing(self) -> None:
        screen = make_screen()
        screen._player.take_damage(screen._player.health.maximum - 1)
        assert screen.game_over is False


# ── Регрессии: чужая смерть не вызывает поражение ────────────────────────────────


class TestOtherDeaths:
    def test_zombie_death_does_not_trigger_game_over(self) -> None:
        screen = make_screen()
        kill(screen._enemies[0])
        assert screen.game_over is False

    def test_boss_death_does_not_trigger_game_over(self) -> None:
        screen = make_screen()
        kill(screen._boss)
        assert screen.game_over is False
        assert screen.victory is True  # вместо этого — победа


# ── Заморозка терминальных состояний ─────────────────────────────────────────────


class TestFreeze:
    def test_update_runs_normally_without_terminal_state(self) -> None:
        # Контроль: без терминального состояния combat двигает пулю (заморозка значима).
        screen = make_screen()
        bullet = moving_bullet(screen._player.pos)
        screen._combat.add_bullets([bullet])
        before = bullet.pos.x
        screen.update(0.1)
        assert bullet.pos.x != before

    def test_update_frozen_after_game_over(self) -> None:
        screen = make_screen()
        bullet = moving_bullet(screen._player.pos)
        screen._combat.add_bullets([bullet])
        kill(screen._player)  # game_over
        before = bullet.pos.x
        screen.update(0.1)
        assert bullet.pos.x == before  # combat не тикал

    def test_update_frozen_after_victory(self) -> None:
        screen = make_screen()
        bullet = moving_bullet(screen._player.pos)
        screen._combat.add_bullets([bullet])
        kill(screen._boss)  # victory
        before = bullet.pos.x
        screen.update(0.1)
        assert bullet.pos.x == before


# ── Отрисовка ─────────────────────────────────────────────────────────────────────


class TestDraw:
    def test_draw_with_game_over(self) -> None:
        screen = make_screen()
        kill(screen._player)
        screen.draw(surface())  # GAME OVER поверх HUD — не падает

    def test_draw_with_victory(self) -> None:
        screen = make_screen()
        kill(screen._boss)
        screen.draw(surface())


# ── Совместимость с победой ───────────────────────────────────────────────────────


class TestVictoryCompatibility:
    def test_victory_still_works(self) -> None:
        screen = make_screen()
        kill(screen._boss)
        assert screen.victory is True
        assert screen.game_over is False

    def test_game_over_and_victory_independent(self) -> None:
        # Гибель игрока не выставляет victory; гибель босса не выставляет game_over.
        screen = make_screen()
        kill(screen._player)
        assert screen.victory is False
        assert screen.game_over is True
