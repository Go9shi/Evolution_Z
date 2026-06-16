from pathlib import Path

import pygame
import pytmx

from data.npc_data import NpcData
from data.spawn_point import SpawnPoint
from data.transition import Transition
from data.trigger_zone import TriggerZone
from settings import (
    MAPS_DIR,
    SCREEN_H,
    SCREEN_W,
    TILE_FLOOR_COLOR,
    TILE_SIZE,
    TILE_WALL_COLOR,
)
from systems.asset_loader import AssetLoader

FLOOR = 0
WALL = 1

_COLS = 50
_ROWS = 24

# Слои TMX и карта уровня по умолчанию (Sprint 11A/11B/12B).
_COLLISION_LAYER = "collision"
_SPAWNS_LAYER = "spawns"
_TRANSITIONS_LAYER = "transitions"
_NPCS_LAYER = "npcs"
_TRIGGERS_LAYER = "triggers"
_DEFAULT_MAP: Path = MAPS_DIR / "level1.tmx"

# Имена тайловых спрайтов (Sprint 11C); нет файла → fallback на pygame.draw.
_TILE_WALL_SPRITE = "tile_wall"
_TILE_FLOOR_SPRITE = "tile_floor"


def load_grid_from_tmx(map_path: Path) -> list[list[int]]:
    """Загрузить сетку коллизий из TMX-слоя `collision`: gid != 0 → WALL, иначе FLOOR.

    Парсит только данные слоя (pytmx.TiledMap, без загрузки изображений тайлсета) —
    рендер остаётся на примитивах. Возвращает 2D-сетку в том же формате, что _build_grid.
    """
    tmx = pytmx.TiledMap(str(map_path))
    layer = tmx.get_layer_by_name(_COLLISION_LAYER)
    return [[WALL if gid != 0 else FLOOR for gid in row] for row in layer.data]


def load_spawns_from_tmx(map_path: Path) -> list[SpawnPoint]:
    """Загрузить точки спавна из TMX object-слоя `spawns` (Sprint 11B).

    Каждый объект → SpawnPoint(name, x, y) в абсолютных пикселях. Отсутствие слоя —
    не ошибка (карта без объектов): возвращается пустой список.
    """
    tmx = pytmx.TiledMap(str(map_path))
    try:
        layer = tmx.get_layer_by_name(_SPAWNS_LAYER)
    except ValueError:
        return []
    return [SpawnPoint(obj.name, float(obj.x), float(obj.y)) for obj in layer]


def load_transitions_from_tmx(map_path: Path) -> list[Transition]:
    """Загрузить зоны перехода из TMX object-слоя `transitions` (Sprint 12B).

    Каждый прямоугольный объект → Transition(x,y,width,height, target_map, target_spawn),
    где target_* берутся из custom-свойств объекта. Отсутствие слоя → пустой список.
    """
    tmx = pytmx.TiledMap(str(map_path))
    try:
        layer = tmx.get_layer_by_name(_TRANSITIONS_LAYER)
    except ValueError:
        return []
    out: list[Transition] = []
    for obj in layer:
        props = obj.properties
        out.append(
            Transition(
                float(obj.x),
                float(obj.y),
                float(obj.width),
                float(obj.height),
                str(props.get("target_map", "")),
                str(props.get("target_spawn", "")),
            )
        )
    return out


def load_npcs_from_tmx(map_path: Path) -> list[NpcData]:
    """Загрузить NPC из TMX object-слоя `npcs` (Sprint 13A).

    Каждый объект → NpcData(npc_id, dialogue_id, x, y) из custom-свойств и позиции.
    Отсутствие слоя (карта без NPC) → пустой список.
    """
    tmx = pytmx.TiledMap(str(map_path))
    try:
        layer = tmx.get_layer_by_name(_NPCS_LAYER)
    except ValueError:
        return []
    out: list[NpcData] = []
    for obj in layer:
        props = obj.properties
        out.append(
            NpcData(
                str(props.get("npc_id", "")),
                str(props.get("dialogue_id", "")),
                float(obj.x),
                float(obj.y),
            )
        )
    return out


def load_triggers_from_tmx(map_path: Path) -> list[TriggerZone]:
    """Загрузить зоны-триггеры из TMX object-слоя `triggers` (Sprint 13B).

    Каждый прямоугольный объект → TriggerZone(trigger_id, event_name, x,y,width,height)
    из custom-свойств и геометрии. Отсутствие слоя (карта без триггеров) → пустой список.
    """
    tmx = pytmx.TiledMap(str(map_path))
    try:
        layer = tmx.get_layer_by_name(_TRIGGERS_LAYER)
    except ValueError:
        return []
    out: list[TriggerZone] = []
    for obj in layer:
        props = obj.properties
        out.append(
            TriggerZone(
                str(props.get("trigger_id", "")),
                str(props.get("event_name", "")),
                float(obj.x),
                float(obj.y),
                float(obj.width),
                float(obj.height),
            )
        )
    return out


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
        self._spawns: list[SpawnPoint] = load_spawns_from_tmx(map_path)
        self._transitions: list[Transition] = load_transitions_from_tmx(map_path)
        self._npcs: list[NpcData] = load_npcs_from_tmx(map_path)
        self._triggers: list[TriggerZone] = load_triggers_from_tmx(map_path)

    @property
    def wall_rects(self) -> list[pygame.Rect]:
        """Список прямоугольников стен для проверки коллизий."""
        return self._wall_rects

    @property
    def spawns(self) -> list[SpawnPoint]:
        """Точки спавна из object-слоя карты (player/enemies/boss/items)."""
        return self._spawns

    @property
    def transitions(self) -> list[Transition]:
        """Зоны перехода на другие карты из object-слоя `transitions`."""
        return self._transitions

    @property
    def npcs(self) -> list[NpcData]:
        """NPC текущей карты из object-слоя `npcs`."""
        return self._npcs

    @property
    def triggers(self) -> list[TriggerZone]:
        """Зоны-триггеры текущей карты из object-слоя `triggers`."""
        return self._triggers

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
                is_wall = self._grid[row][col] == WALL
                rect = pygame.Rect(col * ts - ox, row * ts - oy, ts, ts)
                name = _TILE_WALL_SPRITE if is_wall else _TILE_FLOOR_SPRITE
                if not AssetLoader.draw_sprite(surface, name, rect):
                    pygame.draw.rect(
                        surface, TILE_WALL_COLOR if is_wall else TILE_FLOOR_COLOR, rect
                    )

    def _compute_wall_rects(self) -> list[pygame.Rect]:
        rects: list[pygame.Rect] = []
        ts = TILE_SIZE
        for row in range(self._rows):
            for col in range(self._cols):
                if self._grid[row][col] == WALL:
                    rects.append(pygame.Rect(col * ts, row * ts, ts, ts))
        return rects
