from dataclasses import dataclass

from data.enemy_data import EnemyData


@dataclass
class SpitterData(EnemyData):
    """Конфигурация SpitterZombie. Расширяет EnemyData полями дальней кислотной атаки."""

    spit_damage: float = 0.0
    spit_speed: float = 0.0
    spit_range: float = 0.0
    safe_distance: float = 0.0
