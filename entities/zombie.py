from abc import ABC, abstractmethod
from enum import Enum, auto

import pygame

from core.entity import Entity
from data.enemy_data import EnemyData
from systems.event_bus import EventBus


class AIState(Enum):
    """Состояния AI врагов. REPOSITION будет добавлен в Sprint 5 для SpitterZombie."""

    IDLE = auto()
    PATROL = auto()
    CHASE = auto()
    ATTACK = auto()


class Zombie(Entity, ABC):
    """Базовый класс врага. Реализует Template Method: update() → update_ai().

    Подклассы обязаны реализовать update_ai() и attack().
    Общая логика (обнаружение, движение, патруль, коллизии) находится здесь.
    """

    COLOR: tuple[int, int, int] = (160, 40, 40)
    _PATROL_REVERSE_INTERVAL: float = 3.0

    def __init__(self, x: float, y: float, data: EnemyData) -> None:
        super().__init__(x, y, data.max_health)
        self._data: EnemyData = data
        self._state: AIState = AIState.IDLE
        self._attack_timer: float = 0.0
        self._patrol_timer: float = self._PATROL_REVERSE_INTERVAL
        self._patrol_dir: pygame.Vector2 = pygame.Vector2(1, 0)
        self._rect: pygame.Rect = pygame.Rect(0, 0, data.width, data.height)
        self._rect.center = (int(x), int(y))

    # ── public properties ──────────────────────────────────────────────────

    @property
    def state(self) -> AIState:
        """Текущее AI-состояние."""
        return self._state

    @property
    def can_attack(self) -> bool:
        """Готов ли враг к атаке (кулдаун истёк)."""
        return self._attack_timer <= 0.0

    @property
    def rect(self) -> pygame.Rect:
        """Прямоугольник для коллизий и рендера."""
        return self._rect

    # ── Template Method ────────────────────────────────────────────────────

    def update(
        self,
        dt: float,
        walls: list[pygame.Rect] | None = None,
        player: Entity | None = None,
    ) -> None:
        """Template Method: декремент таймеров → хук update_ai."""
        self._attack_timer = max(0.0, self._attack_timer - dt)
        if player is not None:
            self.update_ai(dt, walls or [], player)

    # ── abstract hooks ─────────────────────────────────────────────────────

    @abstractmethod
    def update_ai(
        self, dt: float, walls: list[pygame.Rect], player: Entity
    ) -> None:
        """AI-логика: переходы состояний, движение, атака. Реализуется в подклассах."""

    @abstractmethod
    def attack(self, target: Entity) -> None:
        """Атака цели. Каждый подкласс атакует по-своему (melee / ranged)."""

    # ── render ─────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка спрайта и HP-бара."""
        draw_rect = self._rect.move(-int(offset.x), -int(offset.y))
        pygame.draw.rect(surface, self.COLOR, draw_rect)

        bar_w = self._rect.width
        hp_w = max(0, int(bar_w * self.health.percentage))
        bar_y = draw_rect.y - 6
        pygame.draw.rect(surface, (80, 0, 0), (draw_rect.x, bar_y, bar_w, 4))
        pygame.draw.rect(surface, (220, 50, 50), (draw_rect.x, bar_y, hp_w, 4))

    # ── shared AI helpers ──────────────────────────────────────────────────

    def _detect_player(self, player_pos: pygame.Vector2) -> bool:
        """Возвращает True, если игрок в радиусе detection_range."""
        return self.pos.distance_to(player_pos) <= self._data.detection_range

    def _in_attack_range(self, player_pos: pygame.Vector2) -> bool:
        """Возвращает True, если игрок достижим для атаки."""
        return self.pos.distance_to(player_pos) <= self._data.attack_range

    def _move_toward(
        self,
        target_pos: pygame.Vector2,
        walls: list[pygame.Rect],
        dt: float,
    ) -> None:
        """Движение к target_pos с AABB-коллизиями стен."""
        direction = target_pos - self.pos
        if direction.length_squared() == 0:
            return
        direction.normalize_ip()
        speed = self._data.speed * dt

        self.pos.x += direction.x * speed
        self._rect.centerx = int(self.pos.x)
        self._resolve_x(walls)

        self.pos.y += direction.y * speed
        self._rect.centery = int(self.pos.y)
        self._resolve_y(walls)

        self.pos.x = float(self._rect.centerx)
        self.pos.y = float(self._rect.centery)

    def _patrol(self, walls: list[pygame.Rect], dt: float) -> None:
        """Патрульное движение: идёт по patrol_dir, разворачивается по таймеру."""
        self._patrol_timer -= dt
        if self._patrol_timer <= 0.0:
            self._patrol_dir *= -1
            self._patrol_timer = self._PATROL_REVERSE_INTERVAL

        target = self.pos + self._patrol_dir * self._data.detection_range
        self._move_toward(target, walls, dt * 0.5)

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


# ── concrete enemies ───────────────────────────────────────────────────────


class WalkerZombie(Zombie):
    """Медленный зомби с высоким HP. Патрулирует, преследует при обнаружении, бьёт в ближнем бою."""

    COLOR = (180, 50, 50)

    def update_ai(
        self, dt: float, walls: list[pygame.Rect], player: Entity
    ) -> None:
        player_pos = player.pos
        if self._in_attack_range(player_pos) and self._detect_player(player_pos):
            self._state = AIState.ATTACK
            if self.can_attack:
                self.attack(player)
                self._attack_timer = self._data.attack_cooldown
        elif self._detect_player(player_pos):
            self._state = AIState.CHASE
            self._move_toward(player_pos, walls, dt)
        else:
            self._state = AIState.PATROL
            self._patrol(walls, dt)

    def attack(self, target: Entity) -> None:
        """Медленный удар с высоким уроном."""
        target.take_damage(self._data.damage)
        EventBus.emit("zombie_attacked", {"attacker": self, "target": target})


class RunnerZombie(Zombie):
    """Быстрый зомби с низким HP. Агрессивно преследует, атакует быстро и часто."""

    COLOR = (220, 80, 30)

    def update_ai(
        self, dt: float, walls: list[pygame.Rect], player: Entity
    ) -> None:
        player_pos = player.pos
        if self._in_attack_range(player_pos):
            self._state = AIState.ATTACK
            if self.can_attack:
                self.attack(player)
                self._attack_timer = self._data.attack_cooldown
        elif self._detect_player(player_pos):
            self._state = AIState.CHASE
            self._move_toward(player_pos, walls, dt)
        else:
            self._state = AIState.IDLE
            self._patrol(walls, dt)

    def attack(self, target: Entity) -> None:
        """Быстрый удар с низким уроном."""
        target.take_damage(self._data.damage)
        EventBus.emit("zombie_attacked", {"attacker": self, "target": target})
