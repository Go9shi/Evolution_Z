from __future__ import annotations

import pygame

from core.entity import Entity
from settings import TILE_SIZE
from systems.event_bus import EventBus


class Boss(Entity):
    """Базовый класс боссов. Враждебная сущность с прямоугольником коллизий.

    Совместим с CombatSystem (Targetable): имеет active, pos, faction, rect, take_damage.
    Получает урон существующим способом (через Entity → HealthComponent). При гибели —
    помимо унаследованного `entity_died` — эмитит `boss_defeated` ровно один раз.
    """

    COLOR: tuple[int, int, int] = (120, 30, 120)
    # Босс — faction='enemy', значит проходит через путь начисления XP за врагов
    # (GameScreen._on_entity_died читает entity.xp_reward). Поле нужно для совместимости
    # с этим путём, как у Zombie.xp_reward; 0 = без награды (балансировка — будущий спринт).
    xp_reward: int = 0

    def __init__(self, x: float, y: float, max_health: int, width: int, height: int) -> None:
        super().__init__(x, y, max_health)
        self.faction = "enemy"
        self._rect: pygame.Rect = pygame.Rect(0, 0, width, height)
        self._rect.center = (int(x), int(y))

    @property
    def rect(self) -> pygame.Rect:
        """Прямоугольник для коллизий и рендера."""
        return self._rect

    def take_damage(self, amount: float) -> None:
        """Получить урон существующим способом; при гибели эмитит `boss_defeated`.

        Делегирует `Entity.take_damage` (тот клампит HP, снимает active и эмитит
        `entity_died`), затем добавляет boss-специфичное событие строго на переходе
        жив→мёртв — поэтому ровно один раз, даже при повторных или избыточных попаданиях.
        """
        was_alive = self.is_alive
        super().take_damage(amount)
        if was_alive and not self.is_alive:
            EventBus.emit("boss_defeated", {"boss": self})

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка прямоугольника босса с полоской HP (паттерн Zombie.draw)."""
        draw_rect = self._rect.move(-int(offset.x), -int(offset.y))
        pygame.draw.rect(surface, self.COLOR, draw_rect)

        bar_w = self._rect.width
        hp_w = max(0, int(bar_w * self.health.percentage))
        bar_y = draw_rect.y - 8
        pygame.draw.rect(surface, (60, 0, 0), (draw_rect.x, bar_y, bar_w, 5))
        pygame.draw.rect(surface, (200, 40, 200), (draw_rect.x, bar_y, hp_w, 5))


class PatientZeroBoss(Boss):
    """Носитель Ноль — финальный босс (ядро).

    Реализует только базовую сущность: own max health, faction='enemy', rect, получение
    урона и смерть с событием `boss_defeated`. Расширенные механики (фазы, призыв врагов,
    спец-атаки, кислота) — отдельные будущие спринты.
    """

    COLOR = (150, 20, 90)
    _SIZE: int = TILE_SIZE * 2  # босс крупнее обычных врагов; размер из settings, не магия

    def __init__(self, x: float, y: float, max_health: int) -> None:
        super().__init__(x, y, max_health, self._SIZE, self._SIZE)
