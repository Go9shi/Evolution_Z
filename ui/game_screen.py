import json

import pygame

from data.enemy_data import EnemyData
from data.player_data import PlayerData
from entities.player import Player
from entities.zombie import RunnerZombie, WalkerZombie, Zombie
from settings import DATA_DIR, TILE_SIZE
from systems.camera import Camera
from systems.game_world import GameWorld
from ui.base_screen import BaseScreen


class GameScreen(BaseScreen):
    """Главный игровой экран. Владеет миром, игроком, камерой и врагами."""

    # Стартовая позиция игрока — центр комнаты 1 (tile 12, 6)
    _START_X: float = 12 * TILE_SIZE + TILE_SIZE / 2
    _START_Y: float = 6 * TILE_SIZE + TILE_SIZE / 2

    def __init__(self) -> None:
        self._world = GameWorld()
        self._player = Player(self._START_X, self._START_Y, self._load_player_config())
        self._camera = Camera()
        self._enemies: list[Zombie] = self._spawn_enemies()

    def update(self, dt: float) -> None:
        self._player.update(dt, self._world.wall_rects)
        self._camera.follow(self._player.pos)

        walls = self._world.wall_rects
        for enemy in self._enemies:
            if enemy.active:
                enemy.update(dt, walls, self._player)
        self._enemies = [e for e in self._enemies if e.active]

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 25))
        self._world.draw(surface, self._camera.offset)
        for enemy in self._enemies:
            enemy.draw(surface, self._camera.offset)
        self._player.draw(surface, self._camera.offset)

    # ── private helpers ────────────────────────────────────────────────────

    def _spawn_enemies(self) -> list[Zombie]:
        configs = self._load_enemy_configs()
        w = configs["walker"]
        r = configs["runner"]
        ts = TILE_SIZE
        return [
            # Комната 2: два уокера
            WalkerZombie(35 * ts + ts / 2, 6 * ts + ts / 2, w),
            WalkerZombie(38 * ts + ts / 2, 8 * ts + ts / 2, w),
            # Комната 3: один раннер
            RunnerZombie(12 * ts + ts / 2, 17 * ts + ts / 2, r),
        ]

    @staticmethod
    def _load_player_config() -> PlayerData:
        with open(DATA_DIR / "player.json", encoding="utf-8") as f:
            return PlayerData(**json.load(f))

    @staticmethod
    def _load_enemy_configs() -> dict[str, EnemyData]:
        with open(DATA_DIR / "enemies.json", encoding="utf-8") as f:
            raw: dict[str, dict] = json.load(f)
        return {name: EnemyData(**fields) for name, fields in raw.items()}
