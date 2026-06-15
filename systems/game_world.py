from pathlib import Path

import pygame
import pytmx

from settings import (
    MAPS_DIR,
    SCREEN_H,
    SCREEN_W,
    TILE_FLOOR_COLOR,
    TILE_SIZE,
    TILE_WALL_COLOR,
)

FLOOR = 0
WALL = 1

_COLS = 50
_ROWS = 24

# Слой коллизий в TMX и карта уровня по умолчанию (Sprint 11A).
_COLLISION_LAYER = "collision"
_DEFAULT_MAP: Path = MAPS_DIR / "level1.tmx"


def load_grid_from_tmx(map_path: Path) -> list[list[int]]:
    """Загрузить сетку коллизий из TMX-слоя `collision`: gid != 0 → WALL, иначе FLOOR.

    Парсит только данные слоя (pytmx.TiledMap, без загрузки изображений тайлсета) —
    рендер остаётся на примитивах. Возвращает 2D-сетку в том же формате, что _build_grid.
    """
    tmx = pytmx.TiledMap(str(map_path))
    layer = tmx.get_layer_by_name(_COLLISION_LAYER)
    return [[WALL if gid != 0 else FLOOR for gid in row] for row in layer.data]


def _build_grid() -> list[list[int]]:
    """Строит 2D-сетку бункера A1. 0 = пол, 1 = стена."""
    grid = [[FLOOR] * _COLS for _ in range(_ROWS)]

    def fill_h(row: int, c1: int, c2: int) -> None:
        for c in range(c1, c2 + 1):
            grid[row][c] = WALL

    def fill_v(col: int, r1: int, r2: int) -> None:
        for r in range(r1, r2 + 1):
            grid[r][col] = WALL

    # Внешняя граница
    fill_h(0, 0, _COLS - 1)
    fill_h(_ROWS - 1, 0, _COLS - 1)
    fill_v(0, 0, _ROWS - 1)
    fill_v(_COLS - 1, 0, _ROWS - 1)

    # Комната 1 (верх-лево): rows 3-10, cols 3-22
    fill_h(3, 3, 22)
    fill_h(10, 3, 22)
    fill_v(3, 3, 10)
    fill_v(22, 3, 10)

    # Комната 2 (верх-право): rows 3-10, cols 28-46
    fill_h(3, 28, 46)
    fill_h(10, 28, 46)
    fill_v(28, 3, 10)
    fill_v(46, 3, 10)

    # Комната 3 (низ-лево): rows 14-21, cols 3-22
    fill_h(14, 3, 22)
    fill_h(21, 3, 22)
    fill_v(3, 14, 21)
    fill_v(22, 14, 21)

    # Комната 4 (низ-право): rows 14-21, cols 28-46
    fill_h(14, 28, 46)
    fill_h(21, 28, 46)
    fill_v(28, 14, 21)
    fill_v(46, 14, 21)

    # Горизонтальный коридор К1↔К2 (row 6, cols 22-28)
    fill_h(5, 23, 27)   # стена-потолок коридора
    fill_h(7, 23, 27)   # стена-пол коридора
    grid[6][22] = FLOOR  # дверь в правой стене К1
    grid[6][28] = FLOOR  # дверь в левой стене К2

    # Вертикальный коридор К1↔К3 (cols 12-13, rows 10-14)
    fill_v(11, 11, 13)   # левая стена коридора
    fill_v(14, 11, 13)   # правая стена коридора
    grid[10][12] = FLOOR  # дверь в нижней стене К1
    grid[10][13] = FLOOR
    grid[14][12] = FLOOR  # дверь в верхней стене К3
    grid[14][13] = FLOOR

    # Вертикальный коридор К2↔К4 (cols 36-37, rows 10-14)
    fill_v(35, 11, 13)
    fill_v(38, 11, 13)
    grid[10][36] = FLOOR  # дверь в нижней стене К2
    grid[10][37] = FLOOR
    grid[14][36] = FLOOR  # дверь в верхней стене К4
    grid[14][37] = FLOOR

    # Горизонтальный коридор К3↔К4 (row 17, cols 22-28)
    fill_h(16, 23, 27)
    fill_h(18, 23, 27)
    grid[17][22] = FLOOR  # дверь в правой стене К3
    grid[17][28] = FLOOR  # дверь в левой стене К4

    return grid


class GameWorld:
    """Игровой мир: тайловая сетка уровня с коллизиями, загружается из TMX (Sprint 11A).

    Геометрия читается из TMX-слоя `collision` (data-driven уровень). Публичный контракт
    неизменен: wall_rects / draw / pixel_width / pixel_height.
    """

    def __init__(self, map_path: Path = _DEFAULT_MAP) -> None:
        self._grid: list[list[int]] = load_grid_from_tmx(map_path)
        self._rows: int = len(self._grid)
        self._cols: int = len(self._grid[0]) if self._grid else 0
        self._wall_rects: list[pygame.Rect] = self._compute_wall_rects()

    @property
    def wall_rects(self) -> list[pygame.Rect]:
        """Список прямоугольников стен для проверки коллизий."""
        return self._wall_rects

    @property
    def pixel_width(self) -> int:
        """Ширина мира в пикселях."""
        return self._cols * TILE_SIZE

    @property
    def pixel_height(self) -> int:
        """Высота мира в пикселях."""
        return self._rows * TILE_SIZE

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка видимых тайлов с учётом смещения камеры."""
        ox, oy = int(offset.x), int(offset.y)
        ts = TILE_SIZE

        col_start = max(0, ox // ts)
        col_end = min(self._cols, (ox + SCREEN_W) // ts + 2)
        row_start = max(0, oy // ts)
        row_end = min(self._rows, (oy + SCREEN_H) // ts + 2)

        for row in range(row_start, row_end):
            for col in range(col_start, col_end):
                color = TILE_WALL_COLOR if self._grid[row][col] == WALL else TILE_FLOOR_COLOR
                pygame.draw.rect(
                    surface,
                    color,
                    (col * ts - ox, row * ts - oy, ts, ts),
                )

    def _compute_wall_rects(self) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        ts = TILE_SIZE
        for row in range(self._rows):
            for col in range(self._cols):
                if self._grid[row][col] == WALL:
                    rects.append(pygame.Rect(col * ts, row * ts, ts, ts))
        return rects
