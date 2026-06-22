from dataclasses import dataclass


@dataclass
class WeaponConfig:
    """Конфигурация оружия, загружаемая из assets/data/weapons.json."""

    damage: float
    fire_rate: float
    bullet_speed: float
    bullet_range: float
    bullet_size: int
    # Дробовик (Sprint 10B): число дробинок за выстрел и угол разброса в градусах.
    # Дефолты сохраняют обратную совместимость для одиночного оружия (pistol/rifle).
    pellet_count: int = 1
    spread_degrees: float = 0.0
