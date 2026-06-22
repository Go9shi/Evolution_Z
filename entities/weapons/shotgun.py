import pygame

from core.weapon import Weapon
from entities.bullet import Bullet


class Shotgun(Weapon):
    """Дробовик. Переопределяет fire(): выпускает несколько дробинок веером за один выстрел.

    Число дробинок и угол разброса — из конфига (pellet_count/spread_degrees), каждая
    дробинка — существующий Bullet (без изменений CombatSystem). Низкая скорострельность.
    """

    def fire(self, pos: pygame.Vector2, direction: pygame.Vector2) -> list[Bullet]:
        """Веер дробинок в direction. Возвращает [] при кулдауне или нулевом направлении."""
        if not self.can_fire or direction.length_squared() == 0:
            return []
        base = direction.normalize()
        count = self._config.pellet_count
        spread = self._config.spread_degrees
        bullets: list[Bullet] = []
        for i in range(count):
            # Равномерное распределение углов в диапазоне [-spread/2, +spread/2].
            angle = -spread / 2.0 + spread * i / (count - 1) if count > 1 else 0.0
            velocity = base.rotate(angle) * self._config.bullet_speed
            bullets.append(
                Bullet(
                    pos.x,
                    pos.y,
                    velocity,
                    self._config.damage + self._damage_bonus,
                    self._config.bullet_range,
                    self._config.bullet_size,
                    origin_tag="player",
                )
            )
        self._cooldown = 1.0 / self._config.fire_rate
        return bullets
