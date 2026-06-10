import pytest

from systems.health import HealthComponent


@pytest.fixture
def hp():
    return HealthComponent(maximum=100)


def test_initial_current_equals_maximum(hp):
    assert hp.current == 100
    assert hp.maximum == 100


def test_take_damage_reduces_current(hp):
    hp.take_damage(30)
    assert hp.current == 70


def test_take_damage_clamps_to_zero(hp):
    hp.take_damage(9999)
    assert hp.current == 0


def test_is_alive_above_zero(hp):
    assert hp.is_alive is True


def test_is_alive_false_at_zero(hp):
    hp.take_damage(100)
    assert hp.is_alive is False


def test_heal_restores_current(hp):
    hp.take_damage(40)
    hp.heal(20)
    assert hp.current == 80


def test_heal_clamps_to_maximum(hp):
    hp.heal(9999)
    assert hp.current == hp.maximum


def test_percentage_at_full_health(hp):
    assert hp.percentage == pytest.approx(1.0)


def test_percentage_at_half_health(hp):
    hp.take_damage(50)
    assert hp.percentage == pytest.approx(0.5)


def test_percentage_at_zero_health(hp):
    hp.take_damage(100)
    assert hp.percentage == pytest.approx(0.0)


def test_reset_restores_to_maximum(hp):
    hp.take_damage(75)
    hp.reset()
    assert hp.current == hp.maximum
