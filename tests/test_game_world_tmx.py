"""Tests for Sprint 11A: TMX geometry pipeline — GameWorld loads collision grid from .tmx."""
from __future__ import annotations

from pathlib import Path

import pygame

from settings import TILE_SIZE
from systems.game_world import (
    FLOOR,
    WALL,
    GameWorld,
    _build_grid,
    load_grid_from_tmx,
)

_DEFAULT_MAP = Path(__file__).resolve().parent.parent / "assets" / "maps" / "level1.tmx"


# ── helpers ───────────────────────────────────────────────────────────────────


def wall_cells_from_grid(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {(c, r) for r, row in enumerate(grid) for c, v in enumerate(row) if v == WALL}


def wall_cells_from_rects(world: GameWorld) -> set[tuple[int, int]]:
    return {(rect.x // TILE_SIZE, rect.y // TILE_SIZE) for rect in world.wall_rects}


def write_tmx(path: Path, grid: list[list[int]]) -> Path:
    """Сгенерировать минимальный TMX (только слой collision) из 2D-сетки."""
    h = len(grid)
    w = len(grid[0])
    csv = ",\n".join(",".join(str(v) for v in row) for row in grid)
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" orientation="orthogonal" renderorder="right-down" '
        f'width="{w}" height="{h}" tilewidth="32" tileheight="32" infinite="0" '
        f'nextlayerid="2" nextobjectid="1">\n'
        f' <tileset firstgid="1" name="collision" tilewidth="32" tileheight="32" '
        f'tilecount="1" columns="1">\n'
        f'  <grid orientation="orthogonal" width="32" height="32"/>\n  <tile id="0"/>\n </tileset>\n'
        f' <layer id="1" name="collision" width="{w}" height="{h}">\n'
        f'  <data encoding="csv">\n{csv}\n</data>\n </layer>\n</map>\n',
        encoding="utf-8",
    )
    return path


# ── Загрузка TMX ────────────────────────────────────────────────────────────────


class TestTmxLoad:
    def test_default_world_loads_from_tmx(self) -> None:
        world = GameWorld()
        assert len(world.wall_rects) > 0

    def test_loader_helper_returns_grid(self) -> None:
        grid = load_grid_from_tmx(_DEFAULT_MAP)
        assert isinstance(grid, list) and isinstance(grid[0], list)
        assert set(grid[0]) <= {FLOOR, WALL}

    def test_explicit_path_argument(self) -> None:
        world = GameWorld(_DEFAULT_MAP)
        assert len(world.wall_rects) > 0


# ── Размеры карты ────────────────────────────────────────────────────────────────


class TestDimensions:
    def test_pixel_dimensions_from_map(self) -> None:
        world = GameWorld()
        assert world.pixel_width == 50 * TILE_SIZE
        assert world.pixel_height == 24 * TILE_SIZE


# ── Построение wall_rects ────────────────────────────────────────────────────────


class TestWallRects:
    def test_rects_are_tile_sized(self) -> None:
        for rect in GameWorld().wall_rects:
            assert isinstance(rect, pygame.Rect)
            assert rect.width == TILE_SIZE
            assert rect.height == TILE_SIZE


# ── Паритет TMX ↔ старый уровень ─────────────────────────────────────────────────


class TestParity:
    def test_loader_grid_equals_build_grid(self) -> None:
        assert load_grid_from_tmx(_DEFAULT_MAP) == _build_grid()

    def test_wall_rects_match_build_grid(self) -> None:
        world = GameWorld()
        assert wall_cells_from_rects(world) == wall_cells_from_grid(_build_grid())


# ── Новый уровень из файла (без правки Python) ────────────────────────────────────


class TestCustomLevel:
    def test_custom_tmx_defines_geometry(self, tmp_path: Path) -> None:
        # 3×3 уровень: рамка из стен, пол в центре — задаётся ТОЛЬКО файлом.
        grid = [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]
        path = write_tmx(tmp_path / "tiny.tmx", grid)
        world = GameWorld(path)
        assert world.pixel_width == 3 * TILE_SIZE
        assert world.pixel_height == 3 * TILE_SIZE
        assert wall_cells_from_rects(world) == wall_cells_from_grid(grid)
        assert (1, 1) not in wall_cells_from_rects(world)  # центр — пол

    def test_custom_map_size_is_data_driven(self, tmp_path: Path) -> None:
        grid = [[1] * 6 for _ in range(4)]  # сплошные стены 6×4
        world = GameWorld(write_tmx(tmp_path / "solid.tmx", grid))
        assert world.pixel_width == 6 * TILE_SIZE
        assert world.pixel_height == 4 * TILE_SIZE
        assert len(world.wall_rects) == 6 * 4
