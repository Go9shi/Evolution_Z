import json
from pathlib import Path
from typing import Any, Callable, cast

import pygame

from core.item import Item
from data.dialogue_data import Dialogue
from data.dialogue_loader import load_dialogues
from data.enemy_data import EnemyData
from data.lore_data import LoreEntry
from data.player_data import PlayerData
from data.quest_data import Quest
from data.quest_loader import load_quests
from data.spitter_data import SpitterData
from data.weapon_config import WeaponConfig
from entities.boss import PatientZeroBoss
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from entities.player import Player
from entities.weapons.pistol import Pistol
from entities.zombie import RunnerZombie, SpitterZombie, WalkerZombie, Zombie
from settings import BOSS_MAX_HEALTH, DATA_DIR, SAVES_DIR, SCREEN_H, SCREEN_W, TILE_SIZE
from systems.camera import Camera
from systems.combat import CombatSystem
from systems.dialogue import DialogueSystem
from systems.event_bus import EventBus
from systems.game_world import GameWorld
from systems.lore import LoreSystem
from systems.quest_system import QuestSystem
from systems.save_system import SaveError, SaveSystem
from ui.base_screen import BaseScreen
from ui.hud import HUD

_ENEMY_CONSTRUCTORS: dict[str, type[EnemyData]] = {
    "spitter": SpitterData,
}


class GameScreen(BaseScreen):
    """Главный игровой экран. Владеет миром, игроком, камерой, врагами и боевой системой."""

    # Стартовая позиция игрока — центр комнаты 1 (tile 12, 6)
    _START_X: float = 12 * TILE_SIZE + TILE_SIZE / 2
    _START_Y: float = 6 * TILE_SIZE + TILE_SIZE / 2

    # Единый файл быстрого сохранения (без слотов).
    _SAVE_PATH: Path = SAVES_DIR / "savegame.json"

    def __init__(
        self, state_manager: Any = None, on_quit: Callable[[], None] | None = None
    ) -> None:
        self._state_manager = state_manager
        # Колбэк завершения приложения (из Main Menu). По умолчанию нет-оп — тесты,
        # создающие GameScreen напрямую, не обязаны его передавать.
        self._on_quit: Callable[[], None] = on_quit if on_quit is not None else (lambda: None)
        self._world = GameWorld()
        self._player = Player(self._START_X, self._START_Y, self._load_player_config())
        self._player.equip(Pistol(self._load_weapon_config("pistol")))
        self._camera = Camera()
        self._enemies: list[Zombie] = self._spawn_enemies()
        self._boss: PatientZeroBoss = self._spawn_boss()
        self._victory: bool = False
        self._game_over: bool = False
        self._cleaned: bool = False
        self._font_victory = pygame.font.SysFont("monospace", 44, bold=True)
        self._hud = HUD()
        self._combat = CombatSystem()
        self._world_items: list[Item] = self._spawn_items()
        self._quest_system = QuestSystem(self._player.experience)
        # Квесты загружены в реестр, но не приняты: их выдаёт диалог (Sprint 8G).
        self._quests: dict[str, Quest] = {q.id: q for q in self._load_quests()}
        self._dialogue_system = DialogueSystem()
        self._dialogues: dict[str, Dialogue] = {d.id: d for d in self._load_dialogues()}
        # Лор-записи регистрируются в каталоге; открывает их диалог (Sprint 8I).
        self._lore_system = LoreSystem()
        for entry in self._load_lore_entries():
            self._lore_system.register(entry)
        EventBus.on("entity_died", self._on_entity_died)
        EventBus.on("dialogue_ended", self._on_dialogue_ended)
        EventBus.on("dialogue_choice_selected", self._on_dialogue_choice)
        EventBus.on("boss_defeated", self._on_boss_defeated)

    @property
    def dialogue_system(self) -> DialogueSystem:
        """Система диалогов — владелец состояния активного диалога (только чтение)."""
        return self._dialogue_system

    @property
    def victory(self) -> bool:
        """Достигнуто ли победное состояние (босс повержен)."""
        return self._victory

    @property
    def game_over(self) -> bool:
        """Наступило ли поражение (игрок погиб)."""
        return self._game_over

    def handle_event(self, event: pygame.event.Event) -> None:
        """ESC — пауза. ЛКМ — выстрел. F — предмет. I — инвентарь. Tab — навыки. J — квесты. L — лор. T — диалог. F5 — сохранить. F9 — загрузить. На терминальном экране ENTER — в меню."""
        if self._victory or self._game_over:
            # Терминальный экран: активен только возврат в меню (ENTER); прочий ввод игнорируется.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self._return_to_main_menu()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._open_pause_menu()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_j:
            if self._state_manager is not None:
                from ui.quest_log_ui import QuestLogUI
                self._state_manager.push(QuestLogUI(self._quest_system, self._state_manager.pop))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            if self._state_manager is not None:
                from ui.lore_ui import LoreUI
                self._state_manager.push(LoreUI(self._lore_system, self._state_manager.pop))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_i:
            if self._state_manager is not None:
                from ui.inventory_ui import InventoryUI
                self._state_manager.push(
                    InventoryUI(self._player.inventory, self._state_manager.pop)
                )
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
            self._start_dialogue("ranger_intro")
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
            self._save_game()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
            self.load_game()

    def update(self, dt: float) -> None:
        # Терминальные состояния (победа / поражение) замораживают игровой цикл.
        if self._victory or self._game_over:
            return
        walls = self._world.wall_rects
        self._player.update(dt, walls)
        self._camera.follow(self._player.pos)

        for enemy in self._enemies:
            if enemy.active:
                enemy.update(dt, walls, self._player)
                self._combat.add_bullets(enemy.collect_spawned_bullets())
        self._enemies = [e for e in self._enemies if e.active]

        if self._boss.active:
            self._boss.update(dt, walls, self._player)
            self._combat.add_bullets(self._boss.collect_spawned_bullets())
            self._enemies.extend(self._boss.collect_spawned_minions())

        self._combat.update(dt, walls, [*self._enemies, self._player, self._boss])

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
        if self._boss.active:
            self._boss.draw(surface, self._camera.offset)
        self._combat.draw(surface, self._camera.offset)
        self._player.draw(surface, self._camera.offset)
        self._hud.draw(surface, self._player, self._quest_system)
        if self._victory:
            self._draw_victory(surface)
        elif self._game_over:
            self._draw_game_over(surface)

    def _draw_victory(self, surface: pygame.Surface) -> None:
        """Минимальный победный результат: центрированное текстовое сообщение."""
        text = self._font_victory.render("VICTORY — PATIENT ZERO DEFEATED", True, (240, 230, 120))
        surface.blit(text, text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))

    def _draw_game_over(self, surface: pygame.Surface) -> None:
        """Минимальный экран поражения: центрированный текст GAME OVER."""
        text = self._font_victory.render("GAME OVER", True, (210, 60, 60))
        surface.blit(text, text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))

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

    def _spawn_boss(self) -> PatientZeroBoss:
        """Создать финального босса.

        Минимальное решение: координаты спавна заданы инлайн (как у `_spawn_enemies`) —
        интерьер Комнаты 4 (rows 15–20, cols 29–45), отдельно от спиттера. max_health —
        из `settings.BOSS_MAX_HEALTH` (конфигурируемая константа, не магическое число).
        """
        ts = TILE_SIZE
        # Конфиг призываемых миньонов (Sprint 9F): существующий walker из enemies.json,
        # инъецируется боссу — без BossData/JSON в entity-слое.
        minion_config = self._load_enemy_configs()["walker"]
        return PatientZeroBoss(
            43 * ts + ts / 2, 18 * ts + ts / 2, BOSS_MAX_HEALTH, minion_config
        )

    def _on_boss_defeated(self, data: dict[str, Any]) -> None:
        """Установить победное состояние при гибели босса (EventBus `boss_defeated`)."""
        self._victory = True

    # ── session lifecycle (Sprint 10G) ──────────────────────────────────────

    def _open_pause_menu(self) -> None:
        """ESC во время игры: открыть оверлей паузы поверх GameScreen (стек экранов)."""
        if self._state_manager is None:
            return
        from ui.pause_menu import PauseMenuScreen
        self._state_manager.push(
            PauseMenuScreen(
                on_resume=self._state_manager.pop,
                on_save=self._save_game,
                on_main_menu=self._return_to_main_menu,
                on_quit=self._on_quit,
            )
        )

    def _return_to_main_menu(self) -> None:
        """Завершить сессию и вернуться в Main Menu (пункт паузы и ENTER на терминале).

        Снимает со стека оверлей паузы (если открыт) и сам GameScreen — каждый pop зовёт
        cleanup(), поэтому подписки EventBus не утекают, — затем кладёт свежий
        MainMenuScreen. Единственный путь возврата; терминальные экраны используют его же.
        """
        if self._state_manager is None:
            return
        from ui.main_menu import MainMenuScreen
        while not self._state_manager.is_empty and self._state_manager.current is not self:
            self._state_manager.pop()
        if self._state_manager.current is self:
            self._state_manager.pop()
        self._state_manager.push(MainMenuScreen(self._state_manager, self._on_quit))

    # ── save / load (Sprint 10B) ────────────────────────────────────────────

    def _save_game(self) -> None:
        """F5: сохранить текущее состояние через SaveSystem в единый файл."""
        self._SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SaveSystem().save(self._SAVE_PATH, self._player, self._quest_system, self._lore_system)

    def load_game(self) -> None:
        """Загрузить сохранение и восстановить состояние (F9 и Continue из меню).

        Отсутствующий или повреждённый файл не ломает игру (SaveError → нет-оп).
        Восстановление идёт в свежие системы (SaveSystem.apply рассчитан на чистые
        объекты), затем ссылки подменяются — последующие кадры читают новые системы.
        """
        save_system = SaveSystem()
        try:
            data = save_system.load(self._SAVE_PATH)
        except SaveError:
            return
        player, quest_system, lore_system = self._fresh_systems()
        save_system.apply(data, player, quest_system, lore_system)
        # Снять подписки заменяемых систем, чтобы повторные загрузки не копили обработчики.
        self._detach_systems(self._player, self._quest_system)
        self._player = player
        self._quest_system = quest_system
        self._lore_system = lore_system

    def cleanup(self) -> None:
        """Снять все подписки EventBus этого экрана при его уничтожении (teardown).

        Снимает собственные подписки GameScreen и подписки текущих игрока и системы
        квестов. Идемпотентно: повторный вызов безопасен. Вызывается GameStateManager.pop.
        """
        if self._cleaned:
            return
        self._cleaned = True
        EventBus.off("entity_died", self._on_entity_died)
        EventBus.off("dialogue_ended", self._on_dialogue_ended)
        EventBus.off("dialogue_choice_selected", self._on_dialogue_choice)
        EventBus.off("boss_defeated", self._on_boss_defeated)
        self._detach_systems(self._player, self._quest_system)

    @staticmethod
    def _detach_systems(player: Player, quest_system: QuestSystem) -> None:
        """Снять подписки EventBus у игрока и системы квестов (при swap на F9 / teardown)."""
        EventBus.off("player_level_up", player._on_level_up)
        EventBus.off("entity_died", quest_system._on_entity_died)

    def _fresh_systems(self) -> tuple[Player, QuestSystem, LoreSystem]:
        """Построить чистые player/quest/lore для восстановления сохранения."""
        player = Player(self._START_X, self._START_Y, self._load_player_config())
        player.equip(Pistol(self._load_weapon_config("pistol")))
        quest_system = QuestSystem(player.experience)
        lore_system = LoreSystem()
        for entry in self._load_lore_entries():
            lore_system.register(entry)
        return player, quest_system, lore_system

    @staticmethod
    def _load_quests() -> list[Quest]:
        """Загрузить квесты уровня из assets/data/quests.json."""
        return load_quests(DATA_DIR / "quests.json")

    @staticmethod
    def _load_dialogues() -> list[Dialogue]:
        """Загрузить диалоги уровня из assets/data/dialogues.json."""
        return load_dialogues(DATA_DIR / "dialogues.json")

    @staticmethod
    def _load_lore_entries() -> list[LoreEntry]:
        """Загрузить лор-записи уровня из assets/data/lore.json."""
        with open(DATA_DIR / "lore.json", encoding="utf-8") as f:
            raw: dict[str, list[dict]] = json.load(f)
        return [LoreEntry(**entry) for entry in raw["lore"]]

    def _start_dialogue(self, dialogue_id: str) -> None:
        """Запустить диалог по id и открыть DialogueUI поверх игры.

        Нет-оп, если нет state_manager или id не найден среди загруженных диалогов.
        """
        if self._state_manager is None:
            return
        dialogue = self._dialogues.get(dialogue_id)
        if dialogue is None:
            return
        from ui.dialogue_ui import DialogueUI
        self._dialogue_system.start(dialogue)
        self._state_manager.push(DialogueUI(self._dialogue_system, self._state_manager.pop))

    def _on_dialogue_choice(self, data: dict[str, Any]) -> None:
        """Выдать квест и/или открыть лор по ссылкам выбранного варианта диалога.

        Реакция на EventBus-событие `dialogue_choice_selected`: связывает диалог с
        квестами (Sprint 8G) и лором (Sprint 8I), не дублируя их состояние. QuestSystem
        остаётся владельцем квестов, LoreSystem — лора, DialogueSystem — диалогов.
        Безопасно при пустых / неизвестных id и при повторе (accept_quest и unlock —
        нет-оп для уже принятого квеста / уже открытой записи).
        """
        choice = data.get("choice")
        quest_id: str = getattr(choice, "quest_id", "")
        if quest_id:
            quest = self._quests.get(quest_id)
            if quest is not None:
                self._quest_system.accept_quest(quest)
        lore_id: str = getattr(choice, "lore_id", "")
        if lore_id:
            self._lore_system.unlock(lore_id)

    def _on_dialogue_ended(self, data: dict[str, Any]) -> None:
        """Снять оверлей диалога и вернуться в игру при завершении диалога.

        Реакция на EventBus-событие: DialogueSystem завершает диалог (end), а закрытие
        экрана — задача интеграции. Снимаем только если сверху действительно DialogueUI.
        """
        if self._state_manager is None:
            return
        from ui.dialogue_ui import DialogueUI
        if isinstance(self._state_manager.current, DialogueUI):
            self._state_manager.pop()

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
        """Начислить XP при гибели врага; объявить поражение при гибели игрока."""
        entity = data["entity"]
        if entity is self._player:
            self._game_over = True
        elif entity.faction == "enemy":
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
