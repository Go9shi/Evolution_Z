import pygame

from core.weapon import Weapon
from entities.bullet import Bullet


class Pistol(Weapon):
    """Пистолет. Стреляет одной пулей за выстрел с заданным кулдауном из конфига."""

    def fire(self, pos: pygame.Vector2, direction: pygame.Vector2) -> list[Bullet]:
        """Выстрел в direction. Возвращает [] при кулдауне или нулевом направлении."""
        if not self.can_fire or direction.length_squared() == 0:
            return []
        velocity = direction.normalize() * self._config.bullet_speed
        bullet = Bullet(
            pos.x,
            pos.y,
            velocity,
            self._config.damage,
            self._config.bullet_range,
            self._config.bullet_size,
            origin_tag="player",
        )
        self._cooldown = 1.0 / self._config.fire_rate
        return [bullet]
