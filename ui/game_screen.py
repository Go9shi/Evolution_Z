import json
from typing import Any, cast

import pygame

from core.item import Item
from data.enemy_data import EnemyData
from data.player_data import PlayerData
from data.spitter_data import SpitterData
from data.weapon_config import WeaponConfig
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from entities.player import Player
from entities.weapons.pistol import Pistol
from entities.zombie import RunnerZombie, SpitterZombie, WalkerZombie, Zombie
from settings import DATA_DIR, TILE_SIZE
from systems.camera import Camera
from systems.combat import CombatSystem
from systems.event_bus import EventBus
from systems.game_world import GameWorld
from ui.base_screen import BaseScreen

_ENEMY_CONSTRUCTORS: dict[str, type[EnemyData]] = {
    "spitter": SpitterData,
}


class GameScreen(BaseScreen):
    """Главный игровой экран. Владеет миром, игроком, камерой, врагами и боевой системой."""

    # Стартовая позиция игрока — центр комнаты 1 (tile 12, 6)
    _START_X: float = 12 * TILE_SIZE + TILE_SIZE / 2
    _START_Y: float = 6 * TILE_SIZE + TILE_SIZE / 2

    def __init__(self, state_manager: Any = None) -> None:
        self._state_manager = state_manager
        self._world = GameWorld()
        self._player = Player(self._START_X, self._START_Y, self._load_player_config())
        self._player.equip(Pistol(self._load_weapon_config("pistol")))
        self._camera = Camera()
        self._enemies: list[Zombie] = self._spawn_enemies()
        self._combat = CombatSystem()
        self._world_items: list[Item] = self._spawn_items()
        EventBus.on("entity_died", self._on_entity_died)

    def handle_event(self, event: pygame.event.Event) -> None:
        """ЛКМ — выстрел. F — использовать предмет. Tab — дерево навыков."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_world = pygame.Vector2(event.pos) + self._camera.offset
            direction = mouse_world - self._player.pos
            bullets = self._player.fire(direction)
            self._combat.add_bullets(bullets)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            for item in self._player.inventory.items:
                if self._player.use_item(item):
                    break
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            if self._state_manager is not None:
                from ui.skill_tree_ui import SkillTreeUI
                self._state_manager.push(SkillTreeUI(self._player, self._state_manager.pop))

    def update(self, dt: float) -> None:
        walls = self._world.wall_rects
        self._player.update(dt, walls)
        self._camera.follow(self._player.pos)

        for enemy in self._enemies:
            if enemy.active:
                enemy.update(dt, walls, self._player)
                self._combat.add_bullets(enemy.collect_spawned_bullets())
        self._enemies = [e for e in self._enemies if e.active]

        self._combat.update(dt, walls, [*self._enemies, self._player])

        for item in self._world_items:
            if item.active and self._player.rect.colliderect(item.rect):
                self._player.pickup_item(item)
        self._world_items = [i for i in self._world_items if i.active]

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 25))
        self._world.draw(surface, self._camera.offset)
        for item in self._world_items:
            item.draw(surface, self._camera.offset)
        for enemy in self._enemies:
            enemy.draw(surface, self._camera.offset)
        self._combat.draw(surface, self._camera.offset)
        self._player.draw(surface, self._camera.offset)

    # ── private helpers ────────────────────────────────────────────────────

    def _spawn_enemies(self) -> list[Zombie]:
        configs = self._load_enemy_configs()
        w = configs["walker"]
        r = configs["runner"]
        s = cast(SpitterData, configs["spitter"])
        ts = TILE_SIZE
        return [
            # Комната 2: два уокера
            WalkerZombie(35 * ts + ts / 2, 6 * ts + ts / 2, w),
            WalkerZombie(38 * ts + ts / 2, 8 * ts + ts / 2, w),
            # Комната 3: один раннер
            RunnerZombie(12 * ts + ts / 2, 17 * ts + ts / 2, r),
            # Комната 4: один спиттер
            SpitterZombie(37 * ts + ts / 2, 17 * ts + ts / 2, s),
        ]

    @staticmethod
    def _load_player_config() -> PlayerData:
        with open(DATA_DIR / "player.json", encoding="utf-8") as f:
            return PlayerData(**json.load(f))

    @staticmethod
    def _load_weapon_config(name: str) -> WeaponConfig:
        with open(DATA_DIR / "weapons.json", encoding="utf-8") as f:
            raw: dict[str, dict] = json.load(f)
        return WeaponConfig(**raw[name])

    @staticmethod
    def _load_enemy_configs() -> dict[str, EnemyData]:
        with open(DATA_DIR / "enemies.json", encoding="utf-8") as f:
            raw: dict[str, dict] = json.load(f)
        return {
            name: _ENEMY_CONSTRUCTORS.get(name, EnemyData)(**fields)
            for name, fields in raw.items()
        }

    def _on_entity_died(self, data: dict[str, Any]) -> None:
        """Начислить XP игроку при гибели врага."""
        entity = data["entity"]
        if entity.faction == "enemy":
            self._player.add_xp(entity.xp_reward)

    @staticmethod
    def _load_item_configs() -> dict[str, dict]:
        with open(DATA_DIR / "items.json", encoding="utf-8") as f:
            return json.load(f)

    def _spawn_items(self) -> list[Item]:
        cfg = self._load_item_configs()
        ts = TILE_SIZE
        food = cfg["food"]
        quest = cfg["quest"]
        beans = food["canned_beans"]
        ration = food["ration_pack"]
        alpha = quest["vaccine_component_alpha"]
        beta = quest["vaccine_component_beta"]
        return [
            # Комната 1: консервы рядом со стартом
            FoodItem(15 * ts, 6 * ts, "canned_beans", beans["name"], beans["description"], beans["nutrition"]),
            # Комната 2: паёк
            FoodItem(37 * ts, 8 * ts, "ration_pack", ration["name"], ration["description"], ration["nutrition"]),
            # Комната 3: первый компонент вакцины
            QuestItem(14 * ts, 18 * ts, "vaccine_component_alpha", alpha["name"], alpha["description"]),
            # Комната 4: второй компонент вакцины
            QuestItem(39 * ts, 18 * ts, "vaccine_component_beta", beta["name"], beta["description"]),
        ]
