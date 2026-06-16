from pathlib import Path

from settings import MAPS_DIR
from systems.game_world import GameWorld


class LevelManager:
    """Владелец текущей карты (Sprint 12B). Загружает GameWorld по id карты и меняет карты.

    GameScreen владеет LevelManager, а не GameWorld напрямую — это даёт фундамент для
    мультикарт/глав/переходов. Контракт GameWorld (wall_rects/draw/pixel_*/spawns) не меняется.
    """

    def __init__(self, map_id: str = "level1") -> None:
        self._map_id: str = map_id
        self._world: GameWorld = GameWorld(self._path(map_id))

    @staticmethod
    def _path(map_id: str) -> Path:
        """Путь к TMX по id карты (`level1` → assets/maps/level1.tmx)."""
        return MAPS_DIR / f"{map_id}.tmx"

    @property
    def world(self) -> GameWorld:
        """Текущий загруженный GameWorld."""
        return self._world

    @property
    def current_map_id(self) -> str:
        """Id текущей карты."""
        return self._map_id

    def change_map(self, map_id: str) -> None:
        """Сменить карту: загрузить новый GameWorld для map_id."""
        self._map_id = map_id
        self._world = GameWorld(self._path(map_id))
