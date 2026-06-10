import pygame
import pytest

from data.player_data import PlayerData
from entities.player import Player
from systems.event_bus import EventBus


@pytest.fixture
def config():
    return PlayerData(max_health=100, speed=200.0, width=32, height=32)


@pytest.fixture
def player(config):
    return Player(640.0, 360.0, config)


def test_rect_centered_on_spawn(player):
    assert player.rect.centerx == 640
    assert player.rect.centery == 360


def test_health_comes_from_config(config):
    p = Player(0, 0, config)
    assert p.health.current == config.max_health


def test_update_moves_player(player, monkeypatch):
    monkeypatch.setattr(player, "_read_input", lambda: pygame.Vector2(1, 0))
    start_x = player.pos.x
    player.update(dt=1.0)
    assert player.pos.x == pytest.approx(start_x + 200.0)


def test_update_no_move_on_zero_direction(player, monkeypatch):
    monkeypatch.setattr(player, "_read_input", lambda: pygame.Vector2(0, 0))
    start_pos = pygame.Vector2(player.pos)
    player.update(dt=1.0)
    assert player.pos.x == pytest.approx(start_pos.x)
    assert player.pos.y == pytest.approx(start_pos.y)


@pytest.fixture
def starving_player():
    cfg = PlayerData(
        max_health=100, speed=200.0, width=32, height=32,
        max_hunger=10.0, hunger_decay_rate=1000.0, hunger_damage_rate=5.0,
    )
    p = Player(640.0, 360.0, cfg)
    p.hunger.update(1.0)  # 1000 * 1.0 > 10 → current = 0, is_starving = True
    return p


def test_player_takes_damage_when_starving(starving_player, monkeypatch):
    monkeypatch.setattr(starving_player, "_read_input", lambda: pygame.Vector2(0, 0))
    events: list[dict] = []
    EventBus.on("entity_damaged", events.append)
    starving_player.update(dt=1.0)
    assert len(events) == 1
    assert events[0]["amount"] == pytest.approx(5.0)


def test_player_no_damage_when_not_starving(player, monkeypatch):
    monkeypatch.setattr(player, "_read_input", lambda: pygame.Vector2(0, 0))
    events: list[dict] = []
    EventBus.on("entity_damaged", events.append)
    player.update(dt=1.0)
    assert len(events) == 0
