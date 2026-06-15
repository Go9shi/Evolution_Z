from dataclasses import dataclass


@dataclass
class SpawnPoint:
    """Точка спавна из TMX object-слоя `spawns`: имя-токен и пиксельные координаты.

    `name` — игровой идентификатор объекта (player_start / enemy_walker / boss /
    реальный item_id). Координаты — абсолютные пиксели, как их сохраняет Tiled.
    """

    name: str
    x: float
    y: float
