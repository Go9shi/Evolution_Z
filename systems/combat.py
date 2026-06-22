from typing import Protocol

import pygame

from entities.bullet import Bullet
from systems.event_bus import EventBus


class Targetable(Protocol):
    """Интерфейс цели для CombatSystem: любой объект с позицией, AABB и методом получения урона."""

    active: bool
    pos: pygame.Vector2
    faction: str

    @property
    def rect(self) -> pygame.Rect:
        """AABB для коллизий."""

    def take_damage(self, amount: float) -> None:
        """Нанести урон объекту."""
        ...


class CombatSystem:
    """Управляет пулями: движение, коллизии со стенами и AABB-попадания по целям."""

    def __init__(self) -> None:
        self._bullets: list[Bullet] = []

    @property
    def bullets(self) -> list[Bullet]:
        """Текущий пул активных пуль (только для чтения)."""
        return self._bullets

    def add_bullets(self, bullets: list[Bullet]) -> None:
        """Добавить пули в пул."""
        self._bullets.extend(bullets)

    def update(
        self,
        dt: float,
        walls: list[pygame.Rect],
        targets: list[Targetable],
    ) -> None:
        """Обновить все пули: движение, стены, AABB-попадания по целям."""
        for bullet in self._bullets:
            if not bullet.active:
                continue
            bullet.update(dt, walls)
            if not bullet.active:
                continue
            self._check_hits(bullet, targets)

        self._bullets = [b for b in self._bullets if b.active]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовать все активные пули."""
        for bullet in self._bullets:
            if bullet.active:
                bullet.draw(surface, offset)

    def _check_hits(self, bullet: Bullet, targets: list[Targetable]) -> None:
        """Проверить AABB-коллизию пули с каждой целью. При попадании — нанести урон и деактивировать пулю."""
        b_rect = bullet.rect
        for target in targets:
            if not target.active:
                continue
            if bullet.origin_tag == target.faction:
                continue
            if b_rect.colliderect(target.rect):
                target.take_damage(bullet.damage)
                bullet.active = False
                EventBus.emit("bullet_hit", {"bullet": bullet, "target": target})
                return
