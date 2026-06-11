from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from core.entity import Entity
from core.item import Item
from data.player_data import PlayerData
from systems.event_bus import EventBus
from systems.experience import ExperienceComponent
from systems.hunger import HungerComponent
from systems.inventory import Inventory
from systems.skill_tree import SkillTree

if TYPE_CHECKING:
    from core.weapon import Weapon
    from entities.bullet import Bullet


class Player(Entity):
    """Игрок. Управляется клавишами WASD, скорость берётся из конфига."""

    COLOR = (80, 200, 120)

    def __init__(self, x: float, y: float, config: PlayerData) -> None:
        super().__init__(x, y, config.max_health)
        self.faction = "player"
        self._speed: float = config.speed
        self._rect: pygame.Rect = pygame.Rect(0, 0, config.width, config.height)
        self._rect.center = (int(x), int(y))
        self._hunger_damage_rate: float = config.hunger_damage_rate
        self.hunger: HungerComponent = HungerComponent(
            config.max_hunger, config.hunger_decay_rate
        )
        self._weapon: Weapon | None = None
        self._inventory: Inventory = Inventory()
        self._experience: ExperienceComponent = ExperienceComponent()
        self._skill_tree: SkillTree = SkillTree()
        EventBus.on("player_level_up", self._on_level_up)

    @property
    def rect(self) -> pygame.Rect:
        """Прямоугольник для коллизий и рендера."""
        return self._rect

    @property
    def inventory(self) -> Inventory:
        """Инвентарь игрока."""
        return self._inventory

    @property
    def skill_tree(self) -> SkillTree:
        """Дерево навыков игрока."""
        return self._skill_tree

    @property
    def experience(self) -> ExperienceComponent:
        """Компонент опыта и уровней игрока."""
        return self._experience

    def add_xp(self, amount: int) -> bool:
        """Добавить XP. Делегирует ExperienceComponent; возвращает True при level-up."""
        return self._experience.add_xp(amount)

    def apply_weapon_damage_bonus(self, bonus: float) -> None:
        """Передать бонус к урону текущему оружию (если оно экипировано)."""
        if self._weapon is not None:
            self._weapon.add_damage_bonus(bonus)

    def equip(self, weapon: Weapon) -> None:
        """Экипировать оружие."""
        self._weapon = weapon

    def pickup_item(self, item: Item) -> bool:
        """Подобрать предмет с земли. Деактивирует item при успехе."""
        added = self._inventory.add_item(item)
        if added:
            item.active = False
        return added

    def use_item(self, item: Item) -> bool:
        """Использовать предмет из инвентаря. Делегирует Inventory."""
        return self._inventory.use_item(item, self)

    def fire(self, direction: pygame.Vector2) -> list[Bullet]:
        """Выстрелить в direction. Делегирует оружию; возвращает [] без оружия или при кулдауне."""
        if self._weapon is None:
            return []
        return self._weapon.fire(self.pos, direction)

    def update(self, dt: float, walls: list[pygame.Rect] | None = None) -> None:
        """Обработка кулдауна оружия, голода, ввода WASD, перемещения и коллизий."""
        if self._weapon is not None:
            self._weapon.update(dt)
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

    def _on_level_up(self, _data: dict) -> None:
        """Начислить одно очко навыка при каждом повышении уровня."""
        self._skill_tree.add_point()

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
