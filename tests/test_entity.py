import pytest

from core.entity import Entity
from systems.event_bus import EventBus


@pytest.fixture
def entity():
    return Entity(0, 0, max_health=100)


def test_initial_health_equals_max(entity):
    assert entity.health == 100
    assert entity.max_health == 100


def test_is_alive_when_has_health(entity):
    assert entity.is_alive is True


def test_not_alive_at_zero_health():
    e = Entity(0, 0, max_health=1)
    e.take_damage(1)
    assert e.is_alive is False


def test_take_damage_reduces_health(entity):
    entity.take_damage(30)
    assert entity.health == 70


def test_take_damage_clamps_to_zero(entity):
    entity.take_damage(9999)
    assert entity.health == 0


def test_death_sets_active_false(entity):
    entity.take_damage(100)
    assert entity.active is False


def test_take_damage_emits_damaged_event(entity):
    events = []
    EventBus.on("entity_damaged", lambda d: events.append(d))

    entity.take_damage(10)

    assert len(events) == 1
    assert events[0]["entity"] is entity
    assert events[0]["amount"] == 10


def test_death_emits_died_not_damaged(entity):
    died = []
    damaged = []
    EventBus.on("entity_died", lambda d: died.append(d))
    EventBus.on("entity_damaged", lambda d: damaged.append(d))

    entity.take_damage(100)

    assert len(died) == 1
    assert died[0]["entity"] is entity
    assert damaged == []


def test_heal_restores_health(entity):
    entity.take_damage(40)
    entity.heal(20)
    assert entity.health == 80


def test_heal_clamps_to_max_health(entity):
    entity.heal(9999)
    assert entity.health == entity.max_health
