import pygame

from core.game_object import GameObject
from systems.asset_loader import AssetLoader


class Bullet(GameObject):
    """Снаряд. Движется в заданном направлении, деактивируется при касании стены или цели."""

    COLOR: tuple[int, int, int] = (255, 230, 50)
    SPRITE: str | None = "bullet"  # assets/sprites/bullet.png; нет файла → fallback-круг

    def __init__(
        self,
        x: float,
        y: float,
        velocity: pygame.Vector2,
        damage: float,
        max_range: float,
        size: int,
        origin_tag: str,
    ) -> None:
        super().__init__(x, y)
        self._velocity: pygame.Vector2 = pygame.Vector2(velocity)
        self._damage: float = damage
        self._range_left: float = max_range
        self._size: int = size
        self._origin_tag: str = origin_tag

    @property
    def damage(self) -> float:
        """Урон при попадании."""
        return self._damage

    @property
    def size(self) -> int:
        """Радиус пули в пикселях."""
        return self._size

    @property
    def origin_tag(self) -> str:
        """Источник пули: 'player' или 'enemy'."""
        return self._origin_tag

    @property
    def rect(self) -> pygame.Rect:
        """AABB пули для коллизий (квадрат со стороной size*2, центрированный на pos)."""
        return pygame.Rect(
            int(self.pos.x) - self._size,
            int(self.pos.y) - self._size,
            self._size * 2,
            self._size * 2,
        )

    def update(self, dt: float, walls: list[pygame.Rect] | None = None) -> None:
        """Движение + коллизии со стенами. Деактивирует при касании стены или исчерпании дальности."""
        dist = self._velocity.length() * dt
        self.pos += self._velocity * dt
        self._range_left -= dist

        if self._range_left <= 0.0:
            self.active = False
            return

        if walls:
            bullet_rect = self.rect
            for wall in walls:
                if bullet_rect.colliderect(wall):
                    self.active = False
                    return

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка пули спрайтом (или fallback-кругом при отсутствии PNG)."""
        screen_rect = self.rect.move(-int(offset.x), -int(offset.y))
        if AssetLoader.draw_sprite(surface, self.SPRITE, screen_rect):
            return
        screen_x = int(self.pos.x - offset.x)
        screen_y = int(self.pos.y - offset.y)
        pygame.draw.circle(surface, self.COLOR, (screen_x, screen_y), self._size)


class AcidBullet(Bullet):
    """Кислотный снаряд SpitterZombie. Физика из Bullet, отличается цветом."""

    COLOR: tuple[int, int, int] = (100, 220, 50)
    SPRITE = "acid_bullet"
