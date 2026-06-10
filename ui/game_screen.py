import json

import pygame

from data.player_data import PlayerData
from entities.player import Player
from settings import DATA_DIR, DARK_GRAY
from systems.camera import Camera
from ui.base_screen import BaseScreen


class GameScreen(BaseScreen):
    """Главный игровой экран. Владеет игроком и камерой."""

    def __init__(self) -> None:
        config = self._load_player_config()
        self._player = Player(640, 360, config)
        self._camera = Camera()

    def update(self, dt: float) -> None:
        self._player.update(dt)
        self._camera.follow(self._player.pos)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_GRAY)
        self._player.draw(surface, self._camera.offset)

    def _load_player_config(self) -> PlayerData:
        with open(DATA_DIR / "player.json") as f:
            return PlayerData(**json.load(f))
