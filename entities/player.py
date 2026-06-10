import pygame

from core.entity import Entity
from data.player_data import PlayerData
from systems.event_bus import EventBus


class Player(Entity):
    """Игрок. Управляется клавишами WASD, скорость берётся из конфига."""

    COLOR = (80, 200, 120)

    def __init__(self, x: float, y: float, config: PlayerData) -> None:
        super().__init__(x, y, config.max_health)
        self._speed: float = config.speed
        self._rect: pygame.Rect = pygame.Rect(0, 0, config.width, config.height)
        self._rect.center = (int(x), int(y))

    @property
    def rect(self) -> pygame.Rect:
        """Прямоугольник для коллизий и рендера."""
        return self._rect

    def update(self, dt: float) -> None:
        """Обработка ввода WASD и перемещение."""
        direction = self._read_input()
        if direction.length_squared() > 0:
            direction.normalize_ip()
            self.pos += direction * self._speed * dt
            self._rect.center = (int(self.pos.x), int(self.pos.y))
            EventBus.emit("player_moved", {"pos": pygame.Vector2(self.pos)})

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        draw_rect = self._rect.move(-int(offset.x), -int(offset.y))
        pygame.draw.rect(surface, self.COLOR, draw_rect)
        pygame.draw.rect(surface, (255, 255, 255), draw_rect, 2)

    def _read_input(self) -> pygame.Vector2:
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1
        return direction
