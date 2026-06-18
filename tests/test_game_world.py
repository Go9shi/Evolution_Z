import pygame
import pytest

from settings import TILE_SIZE
from systems.game_world import FLOOR, WALL, GameWorld, _COLS, _ROWS, _build_grid


@pytest.fixture
def world() -> GameWorld:
    return GameWorld()


def test_wall_rects_not_empty(world: GameWorld) -> None:
    assert len(world.wall_rects) > 0


def test_wall_rects_are_pygame_rects(world: GameWorld) -> None:
    for rect in world.wall_rects:
        assert isinstance(rect, pygame.Rect)


def test_pixel_dimensions(world: GameWorld) -> None:
    assert world.pixel_width == _COLS * TILE_SIZE
    assert world.pixel_height == _ROWS * TILE_SIZE


def test_outer_border_is_walls() -> None:
    grid = _build_grid()
    for c in range(_COLS):
        assert grid[0][c] == WALL, f"top border col {c}"
        assert grid[_ROWS - 1][c] == WALL, f"bottom border col {c}"
    for r in range(_ROWS):
        assert grid[r][0] == WALL, f"left border row {r}"
        assert grid[r][_COLS - 1] == WALL, f"right border row {r}"


def test_room1_interior_is_floor() -> None:
    grid = _build_grid()
    # Комната 1: rows 3-10, cols 3-22 → интерьер rows 4-9, cols 4-21
    for r in range(4, 10):
        for c in range(4, 22):
            assert grid[r][c] == FLOOR, f"room1 interior ({r},{c}) should be floor"


def test_room1_wall_in_wall_rects(world: GameWorld) -> None:
    # Верхняя стена комнаты 1: row=3, col=3
    expected = pygame.Rect(3 * TILE_SIZE, 3 * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    assert expected in world.wall_rects


def test_h_corridor_r1_r2_is_passable() -> None:
    grid = _build_grid()
    # Проход row=6, col=22 (дверь правой стены К1) и col=28 (дверь левой стены К2)
    assert grid[6][22] == FLOOR
    assert grid[6][28] == FLOOR
    # Сам коридор row=6, cols 23-27
    for c in range(23, 28):
        assert grid[6][c] == FLOOR, f"corridor tile (6,{c}) should be floor"


def test_v_corridor_r1_r3_is_passable() -> None:
    grid = _build_grid()
    # Двери
    assert grid[10][12] == FLOOR
    assert grid[10][13] == FLOOR
    assert grid[14][12] == FLOOR
    assert grid[14][13] == FLOOR
    # Тело коридора
    for r in range(11, 14):
        assert grid[r][12] == FLOOR, f"corridor tile ({r},12) should be floor"
        assert grid[r][13] == FLOOR, f"corridor tile ({r},13) should be floor"
