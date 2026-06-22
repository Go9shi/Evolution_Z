from dataclasses import dataclass


@dataclass
class EnemyData:
    """Конфигурация врага, загружаемая из assets/data/enemies.json."""

    max_health: int
    speed: float
    damage: float
    attack_range: float
    detection_range: float
    attack_cooldown: float
    width: int
    height: int
    xp_reward: int
