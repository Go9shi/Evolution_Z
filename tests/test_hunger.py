import pytest

from systems.hunger import HungerComponent


@pytest.fixture
def hunger() -> HungerComponent:
    return HungerComponent(maximum=100.0, decay_rate=10.0)


def test_initial_current_equals_maximum(hunger: HungerComponent) -> None:
    assert hunger.current == hunger.maximum


def test_update_decreases_hunger(hunger: HungerComponent) -> None:
    hunger.update(1.0)
    assert hunger.current == pytest.approx(90.0)


def test_hunger_does_not_go_below_zero(hunger: HungerComponent) -> None:
    hunger.update(9999.0)
    assert hunger.current == pytest.approx(0.0)


def test_is_starving_false_above_zero(hunger: HungerComponent) -> None:
    assert hunger.is_starving is False


def test_is_starving_true_at_zero(hunger: HungerComponent) -> None:
    hunger.update(9999.0)
    assert hunger.is_starving is True


def test_percentage_at_full(hunger: HungerComponent) -> None:
    assert hunger.percentage == pytest.approx(1.0)


def test_percentage_at_half(hunger: HungerComponent) -> None:
    hunger.update(5.0)  # 100 - 10*5 = 50
    assert hunger.percentage == pytest.approx(0.5)


def test_consume_increases_hunger(hunger: HungerComponent) -> None:
    hunger.update(5.0)  # current = 50
    hunger.consume(20.0)
    assert hunger.current == pytest.approx(70.0)


def test_consume_clamps_at_maximum(hunger: HungerComponent) -> None:
    hunger.consume(9999.0)
    assert hunger.current == pytest.approx(hunger.maximum)


def test_reset_restores_to_maximum(hunger: HungerComponent) -> None:
    hunger.update(5.0)
    hunger.reset()
    assert hunger.current == pytest.approx(hunger.maximum)
