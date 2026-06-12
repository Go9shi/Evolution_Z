"""Tests for Sprint 9C: Boss Integration — PatientZeroBoss в игровом цикле GameScreen."""
from __future__ import annotations

import pygame

from entities.boss import PatientZeroBoss
from entities.bullet import Bullet
from entities.zombie import Zombie
from main import GameStateManager
from settings import BOSS_MAX_HEALTH
from systems.event_bus import EventBus
from ui.game_screen import GameScreen


# ── helpers ────────────────────────────────────────────────────────────────────


def make_game() -> tuple[GameStateManager, GameScreen]:
    manager = GameStateManager()
    screen = GameScreen(manager)
    manager.push(screen)
    return manager, screen


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


def player_bullet(pos: pygame.Vector2, damage: float = 50.0) -> Bullet:
    """Пуля игрока, расположенная поверх цели (скорость 0 — попадание на месте)."""
    return Bullet(
        x=pos.x, y=pos.y,
        velocity=pygame.Vector2(0.0, 0.0),
        damage=damage,
        max_range=500.0,
        size=6,
        origin_tag="player",
    )


class Recorder:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, data: dict) -> None:
        self.calls.append(data)


# ── Спавн ─────────────────────────────────────────────────────────────────────


class TestSpawn:
    def test_boss_created(self) -> None:
        _, screen = make_game()
        assert screen._boss is not None

    def test_boss_correct_type(self) -> None:
        _, screen = make_game()
        assert isinstance(screen._boss, PatientZeroBoss)

    def test_boss_active_in_world(self) -> None:
        _, screen = make_game()
        assert screen._boss.active is True

    def test_boss_has_configured_health(self) -> None:
        _, screen = make_game()
        assert screen._boss.health.maximum == BOSS_MAX_HEALTH

    def test_boss_is_enemy_faction(self) -> None:
        _, screen = make_game()
        assert screen._boss.faction == "enemy"


# ── Интеграция в игровой цикл ─────────────────────────────────────────────────


class TestGameLoopIntegration:
    def test_boss_survives_plain_update(self) -> None:
        _, screen = make_game()
        screen.update(0.016)  # без пуль босс не должен умирать/падать
        assert screen._boss.active is True

    def test_boss_takes_damage_through_combat(self) -> None:
        _, screen = make_game()
        screen._combat.add_bullets([player_bullet(screen._boss.pos, damage=50.0)])
        screen.update(0.016)
        assert screen._boss.health.current == BOSS_MAX_HEALTH - 50.0

    def test_boss_included_in_combat_targets(self) -> None:
        # Несколько кадров урона снижают HP босса через существующий путь combat.
        _, screen = make_game()
        for _ in range(3):
            screen._combat.add_bullets([player_bullet(screen._boss.pos, damage=30.0)])
            screen.update(0.016)
        assert screen._boss.health.current == BOSS_MAX_HEALTH - 90.0

    def test_boss_drawn_without_error(self) -> None:
        _, screen = make_game()
        screen.draw(surface())  # отрисовка с боссом не падает


# ── Победа ────────────────────────────────────────────────────────────────────


class TestVictory:
    def test_killing_boss_emits_boss_defeated(self) -> None:
        recorder = Recorder()
        EventBus.on("boss_defeated", recorder)
        _, screen = make_game()
        screen._boss.take_damage(BOSS_MAX_HEALTH)
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["boss"] is screen._boss

    def test_gamescreen_sets_victory_on_boss_death(self) -> None:
        _, screen = make_game()
        assert screen.victory is False
        screen._boss.take_damage(BOSS_MAX_HEALTH)
        assert screen.victory is True

    def test_victory_via_combat_path(self) -> None:
        _, screen = make_game()
        screen._combat.add_bullets([player_bullet(screen._boss.pos, damage=BOSS_MAX_HEALTH)])
        screen.update(0.016)
        assert screen._boss.active is False
        assert screen.victory is True

    def test_victory_does_not_break_update(self) -> None:
        _, screen = make_game()
        screen._boss.take_damage(BOSS_MAX_HEALTH)
        screen.update(0.016)  # игровой цикл продолжает работать после победы
        assert screen.victory is True

    def test_victory_does_not_break_draw(self) -> None:
        _, screen = make_game()
        screen._boss.take_damage(BOSS_MAX_HEALTH)
        screen.draw(surface())  # победный текст рисуется без падения
        assert screen.victory is True

    def test_dead_boss_not_redrawn_or_updated(self) -> None:
        _, screen = make_game()
        screen._boss.take_damage(BOSS_MAX_HEALTH)
        screen.update(0.016)
        screen.draw(surface())
        assert screen._boss.active is False


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_normal_zombies_still_spawned(self) -> None:
        _, screen = make_game()
        assert len(screen._enemies) > 0
        assert all(isinstance(e, Zombie) for e in screen._enemies)

    def test_killing_zombie_still_grants_xp(self) -> None:
        _, screen = make_game()
        assert screen._player.experience.current_xp == 0
        zombie = screen._enemies[0]
        zombie.take_damage(zombie.health.maximum)  # убить зомби
        assert screen._player.experience.current_xp == zombie.xp_reward
        assert zombie.xp_reward > 0

    def test_boss_death_grants_no_xp(self) -> None:
        # Босс проходит через _on_entity_died без падения; xp_reward=0 → XP не даёт.
        _, screen = make_game()
        screen._boss.take_damage(BOSS_MAX_HEALTH)
        assert screen._player.experience.current_xp == 0

    def test_zombies_pruned_when_dead_boss_kept(self) -> None:
        _, screen = make_game()
        zombie = screen._enemies[0]
        zombie.take_damage(zombie.health.maximum)
        screen.update(0.016)
        assert zombie not in screen._enemies  # мёртвый зомби удалён из списка

    def test_existing_systems_present(self) -> None:
        _, screen = make_game()
        assert screen._quest_system is not None
        assert screen._lore_system is not None
        assert screen.dialogue_system is not None

    def test_dialogue_still_opens(self) -> None:
        manager, screen = make_game()
        event = pygame.event.Event(
            pygame.KEYDOWN, {"key": pygame.K_t, "mod": 0, "unicode": "", "scancode": 0}
        )
        screen.handle_event(event)
        assert screen.dialogue_system.is_active is True
