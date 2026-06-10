from dataclasses import dataclass


@dataclass
class WeaponConfig:
    """Конфигурация оружия, загружаемая из assets/data/weapons.json."""

    damage: float
    fire_rate: float
    bullet_speed: float
    bullet_range: float
    bullet_size: int
