import pytest

from core.game_object import GameObject


def test_ids_are_sequential():
    a = GameObject(0, 0)
    b = GameObject(0, 0)
    assert b.id == a.id + 1


def test_active_true_by_default():
    obj = GameObject(0, 0)
    assert obj.active is True


def test_position_stored_correctly():
    obj = GameObject(15.5, 42.0)
    assert obj.pos.x == pytest.approx(15.5)
    assert obj.pos.y == pytest.approx(42.0)
