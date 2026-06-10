from dataclasses import dataclass


@dataclass
class PlayerData:
    """Конфигурация игрока, загружаемая из assets/data/player.json."""

    max_health: int
    speed: float
    width: int
    height: int
    max_hunger: float = 100.0
    hunger_decay_rate: float = 2.0
    hunger_damage_rate: float = 5.0
