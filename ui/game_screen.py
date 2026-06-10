import json

import pygame

from data.player_data import PlayerData
from entities.player import Player
from settings import DATA_DIR, TILE_SIZE
from systems.camera import Camera
from systems.game_world import GameWorld
from ui.base_screen import BaseScreen


class GameScreen(BaseScreen):
    """Главный игровой экран. Владеет миром, игроком и камерой."""

    # Стартовая позиция внутри комнаты 1 (tile 12, 6)
    _START_X: float = 12 * TILE_SIZE + TILE_SIZE / 2
    _START_Y: float = 6 * TILE_SIZE + TILE_SIZE / 2

    def __init__(self) -> None:
        self._world = GameWorld()
        config = self._load_player_config()
        self._player = Player(self._START_X, self._START_Y, config)
        self._camera = Camera()

    def update(self, dt: float) -> None:
        self._player.update(dt, self._world.wall_rects)
        self._camera.follow(self._player.pos)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 25))
        self._world.draw(surface, self._camera.offset)
        self._player.draw(surface, self._camera.offset)

    def _load_player_config(self) -> PlayerData:
        with open(DATA_DIR / "player.json", encoding="utf-8") as f:
            return PlayerData(**json.load(f))
