import pygame

from core.entity import Entity
from data.player_data import PlayerData
from systems.event_bus import EventBus
from systems.hunger import HungerComponent


class Player(Entity):
    """Игрок. Управляется клавишами WASD, скорость берётся из конфига."""

    COLOR = (80, 200, 120)

    def __init__(self, x: float, y: float, config: PlayerData) -> None:
        super().__init__(x, y, config.max_health)
        self._speed: float = config.speed
        self._rect: pygame.Rect = pygame.Rect(0, 0, config.width, config.height)
        self._rect.center = (int(x), int(y))
        self._hunger_damage_rate: float = config.hunger_damage_rate
        self.hunger: HungerComponent = HungerComponent(
            config.max_hunger, config.hunger_decay_rate
        )

    @property
    def rect(self) -> pygame.Rect:
        """Прямоугольник для коллизий и рендера."""
        return self._rect

    def update(self, dt: float, walls: list[pygame.Rect] | None = None) -> None:
        """Обработка голода, ввода WASD, перемещения и коллизий."""
        self.hunger.update(dt)
        if self.hunger.is_starving:
            self.take_damage(self._hunger_damage_rate * dt)
        EventBus.emit("player_hunger_changed", {"percentage": self.hunger.percentage})

        direction = self._read_input()
        if direction.length_squared() == 0:
            return
        direction.normalize_ip()
        speed = self._speed * dt

        self.pos.x += direction.x * speed
        self._rect.centerx = int(self.pos.x)
        if walls:
            self._resolve_x(walls)

        self.pos.y += direction.y * speed
        self._rect.centery = int(self.pos.y)
        if walls:
            self._resolve_y(walls)

        self.pos.x = float(self._rect.centerx)
        self.pos.y = float(self._rect.centery)
        EventBus.emit("player_moved", {"pos": pygame.Vector2(self.pos)})

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        draw_rect = self._rect.move(-int(offset.x), -int(offset.y))
        pygame.draw.rect(surface, self.COLOR, draw_rect)
        pygame.draw.rect(surface, (255, 255, 255), draw_rect, 2)

    def _resolve_x(self, walls: list[pygame.Rect]) -> None:
        for wall in walls:
            if self._rect.colliderect(wall):
                if self._rect.centerx > wall.centerx:
                    self._rect.left = wall.right
                else:
                    self._rect.right = wall.left
                self.pos.x = float(self._rect.centerx)

    def _resolve_y(self, walls: list[pygame.Rect]) -> None:
        for wall in walls:
            if self._rect.colliderect(wall):
                if self._rect.centery > wall.centery:
                    self._rect.top = wall.bottom
                else:
                    self._rect.bottom = wall.top
                self.pos.y = float(self._rect.centery)

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
