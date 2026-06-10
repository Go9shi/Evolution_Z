from dataclasses import dataclass


@dataclass
class PlayerData:
    """Конфигурация игрока, загружаемая из assets/data/player.json."""

    max_health: int
    speed: float
    width: int
    height: int
