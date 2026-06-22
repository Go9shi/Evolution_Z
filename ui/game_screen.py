import json
from pathlib import Path
from typing import Any, Callable

import pygame

from core.item import Item
from data.dialogue_data import Dialogue
from data.dialogue_loader import load_dialogues
from data.enemy_data import EnemyData
from data.lore_data import LoreEntry
from data.npc_data import NpcData
from data.player_data import PlayerData
from data.quest_data import Quest
from data.quest_loader import load_quests
from data.spawn_point import SpawnPoint
from data.spitter_data import SpitterData
from data.trigger_zone import TriggerZone
from data.weapon_config import WeaponConfig
from entities.boss import PatientZeroBoss
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from entities.npc import NPC
from entities.player import Player
from entities.weapons.pistol import Pistol
from entities.zombie import RunnerZombie, SpitterZombie, WalkerZombie, Zombie
from settings import BOSS_MAX_HEALTH, DATA_DIR, NPC_INTERACTION_RANGE, SAVES_DIR, SCREEN_H, SCREEN_W
from systems.camera import Camera
from systems.combat import CombatSystem
from systems.dialogue import DialogueSystem
from systems.event_bus import EventBus
from systems.level_manager import LevelManager
from systems.lore import LoreSystem
from systems.quest_system import QuestSystem
from systems.save_system import SaveError, SaveSystem
from ui.base_screen import BaseScreen
from ui.hud import HUD

_ENEMY_CONSTRUCTORS: dict[str, type[EnemyData]] = {
    "spitter": SpitterData,
}

# Токен спавна enemy_* → (класс врага, ключ конфига в enemies.json). Sprint 11B.
_ENEMY_SPAWNS: dict[str, tuple[type[Zombie], str]] = {
    "enemy_walker": (WalkerZombie, "walker"),
    "enemy_runner": (RunnerZombie, "runner"),
    "enemy_spitter": (SpitterZombie, "spitter"),
}


class GameScreen(BaseScreen):
    """Главный игровой экран. Владеет миром, игроком, камерой, врагами и боевой системой."""

    # Единый файл быстрого сохранения (без слотов).
    _SAVE_PATH: Path = SAVES_DIR / "savegame.json"

    def __init__(
        self, state_manager: Any = None, on_quit: Callable[[], None] | None = None
    ) -> None:
        self._state_manager = state_manager
        # Колбэк завершения приложения (из Main Menu). По умолчанию нет-оп — тесты,
        # создающие GameScreen напрямую, не обязаны его передавать.
        self._on_quit: Callable[[], None] = on_quit if on_quit is not None else (lambda: None)
        # Карта — через LevelManager (Sprint 12B): GameScreen не владеет GameWorld напрямую.
        self._level = LevelManager()
        # Размещение всех игровых объектов — из object-слоя карты (Sprint 11B):
        # GameScreen больше не хранит координат уровня.
        spawns = self._level.world.spawns
        self._player_start: tuple[float, float] = self._find_player_start(spawns)
        self._player = Player(*self._player_start, self._load_player_config())
        self._player.equip(Pistol(self._load_weapon_config("pistol")))
        self._camera = Camera()
        self._enemies: list[Zombie] = self._spawn_enemies(spawns)
        self._boss: PatientZeroBoss = self._spawn_boss(spawns)
        self._npcs: list[NPC] = self._spawn_npcs(self._level.world.npcs)
        self._triggers: list[TriggerZone] = self._level.world.triggers
        self._victory: bool = False
        self._game_over: bool = False
        self._cleaned: bool = False
        self._font_victory = pygame.font.SysFont("monospace", 44, bold=True)
        # Подсказки (Sprint 15B): «Press ENTER» на терминале и «Press T» у NPC.
        self._font_hint = pygame.font.SysFont("monospace", 18, bold=True)
        self._hud = HUD()
        self._combat = CombatSystem()
        self._world_items: list[Item] = self._spawn_items(spawns)
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
            self._interact_with_npc()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
            self._save_game()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
            self.load_game()

    def update(self, dt: float) -> None:
        # Терминальные состояния (победа / поражение) замораживают игровой цикл.
        if self._victory or self._game_over:
            return
        walls = self._level.world.wall_rects
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

        self._check_triggers()
        self._check_transitions()

    def _check_triggers(self) -> None:
        """Вход игрока в зону-триггер → emit event_name через EventBus (однократно).

        Single activation: после эмита `active=False`; повторный вход не эмитит снова.
        Подписчики (квест-контент/тесты) слушают именованное событие — без if под квесты.
        """
        pr = self._player.rect
        for tz in self._triggers:
            if tz.active and tz.event_name and pr.colliderect(tz.rect):
                tz.active = False
                EventBus.emit(tz.event_name, {"trigger_id": tz.trigger_id})

    def _check_transitions(self) -> None:
        """Вход игрока в зону перехода → загрузка целевой карты и телепорт в target_spawn."""
        pr = self._player.rect
        for t in self._level.world.transitions:
            if not t.target_map:
                continue
            zone = pygame.Rect(int(t.x), int(t.y), int(t.width), int(t.height))
            if pr.colliderect(zone):
                self._enter_map(t.target_map, t.target_spawn)
                return

    def _enter_map(self, map_id: str, spawn_name: str) -> None:
        """Сменить карту и переместить существующего игрока в названную точку спавна.

        Игрок персистит (несёт прогресс), мир/враги/босс/предметы пересоздаются под новую
        карту, combat сбрасывается. EventBus-подписки не меняются (player/screen те же).
        """
        self._level.change_map(map_id)
        spawns = self._level.world.spawns
        self._player_start = self._find_player_start(spawns)
        pos = self._find_spawn(spawns, spawn_name) or self._player_start
        self._player.pos.update(pos[0], pos[1])
        self._player.rect.center = (int(pos[0]), int(pos[1]))
        self._enemies = self._spawn_enemies(spawns)
        self._boss = self._spawn_boss(spawns)
        self._world_items = self._spawn_items(spawns)
        self._npcs = self._spawn_npcs(self._level.world.npcs)
        self._triggers = self._level.world.triggers
        self._combat = CombatSystem()
        self._camera.follow(self._player.pos)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 20, 25))
        self._level.world.draw(surface, self._camera.offset)
        for item in self._world_items:
            item.draw(surface, self._camera.offset)
        for npc in self._npcs:
            npc.draw(surface, self._camera.offset)
        for enemy in self._enemies:
            enemy.draw(surface, self._camera.offset)
        if self._boss.active:
            self._boss.draw(surface, self._camera.offset)
        self._combat.draw(surface, self._camera.offset)
        self._player.draw(surface, self._camera.offset)
        if not (self._victory or self._game_over):
            self._draw_npc_hint(surface)
        self._hud.draw(surface, self._player, self._quest_system)
        if self._victory:
            self._draw_victory(surface)
        elif self._game_over:
            self._draw_game_over(surface)

    def _draw_npc_hint(self, surface: pygame.Surface) -> None:
        """Подсказка «Press T to Talk» над ближайшим NPC в радиусе (Sprint 15B)."""
        npc = self._nearest_npc()
        if npc is None:
            return
        rect = npc.rect.move(-int(self._camera.offset.x), -int(self._camera.offset.y))
        text = self._font_hint.render("Press T to Talk", True, (240, 240, 160))
        surface.blit(text, text.get_rect(center=(rect.centerx, rect.top - 10)))

    def _draw_victory(self, surface: pygame.Surface) -> None:
        """Победный результат: сообщение + подсказка возврата в меню."""
        text = self._font_victory.render("VICTORY — PATIENT ZERO DEFEATED", True, (240, 230, 120))
        surface.blit(text, text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
        self._draw_return_hint(surface)

    def _draw_game_over(self, surface: pygame.Surface) -> None:
        """Экран поражения: GAME OVER + подсказка возврата в меню."""
        text = self._font_victory.render("GAME OVER", True, (210, 60, 60))
        surface.blit(text, text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
        self._draw_return_hint(surface)

    def _draw_return_hint(self, surface: pygame.Surface) -> None:
        """Подсказка «Press ENTER to return to menu» под терминальным сообщением (Sprint 15B)."""
        hint = self._font_hint.render("Press ENTER to return to menu", True, (230, 230, 235))
        surface.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 44)))

    # ── private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _find_spawn(spawns: list[SpawnPoint], name: str) -> tuple[float, float] | None:
        """Координаты точки спавна по имени; None, если объект отсутствует."""
        for sp in spawns:
            if sp.name == name:
                return sp.x, sp.y
        return None

    @staticmethod
    def _find_player_start(spawns: list[SpawnPoint]) -> tuple[float, float]:
        """Координаты старта игрока из карты (`player_start`); (0,0), если объект отсутствует."""
        return GameScreen._find_spawn(spawns, "player_start") or (0.0, 0.0)

    @staticmethod
    def _spawn_npcs(npc_data: list[NpcData]) -> list[NPC]:
        """Создать NPC текущей карты из данных TMX-слоя `npcs` (Sprint 13A)."""
        return [NPC(d.x, d.y, d.npc_id, d.dialogue_id) for d in npc_data]

    def _nearest_npc(self) -> NPC | None:
        """Ближайший NPC в радиусе `NPC_INTERACTION_RANGE`; None, если рядом никого нет."""
        nearest: NPC | None = None
        best = NPC_INTERACTION_RANGE
        for npc in self._npcs:
            distance = self._player.pos.distance_to(npc.pos)
            if distance <= best:
                best = distance
                nearest = npc
        return nearest

    def _interact_with_npc(self) -> None:
        """T: открыть диалог ближайшего NPC в радиусе. Без NPC рядом — нет-оп."""
        npc = self._nearest_npc()
        if npc is not None:
            self._start_dialogue(npc.dialogue_id)

    def _spawn_enemies(self, spawns: list[SpawnPoint]) -> list[Zombie]:
        """Создать врагов из точек спавна enemy_* (класс и конфиг — по токену имени)."""
        configs = self._load_enemy_configs()
        enemies: list[Zombie] = []
        for sp in spawns:
            entry = _ENEMY_SPAWNS.get(sp.name)
            if entry is not None:
                cls, key = entry
                enemies.append(cls(sp.x, sp.y, configs[key]))
        return enemies

    def _spawn_boss(self, spawns: list[SpawnPoint]) -> PatientZeroBoss:
        """Создать финального босса из точки спавна `boss` (координаты — из карты).

        max_health — из `settings.BOSS_MAX_HEALTH`; minion_config (Sprint 9F) — walker из
        enemies.json (это конфиг, а не координата уровня). Если объекта boss нет — (0,0).
        """
        minion_config = self._load_enemy_configs()["walker"]
        x, y = 0.0, 0.0
        for sp in spawns:
            if sp.name == "boss":
                x, y = sp.x, sp.y
                break
        return PatientZeroBoss(x, y, BOSS_MAX_HEALTH, minion_config)

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
        """F5: сохранить текущее состояние (включая карту и позицию) через SaveSystem."""
        self._SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SaveSystem().save(
            self._SAVE_PATH,
            self._player,
            self._quest_system,
            self._lore_system,
            self._level.current_map_id,
        )

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
        # Map-aware (Sprint 12B): при иной карте — сменить её; позиция (0,0) у старых
        # сейвов трактуется как «не задана» → спавн в player_start.
        map_changed = data.map_id != self._level.current_map_id
        if map_changed:
            self._level.change_map(data.map_id)
            self._player_start = self._find_player_start(self._level.world.spawns)
        has_pos = data.player_x != 0.0 or data.player_y != 0.0
        pos = (data.player_x, data.player_y) if has_pos else self._player_start

        player, quest_system, lore_system = self._fresh_systems(pos)
        save_system.apply(data, player, quest_system, lore_system)
        # Снять подписки заменяемых систем, чтобы повторные загрузки не копили обработчики.
        self._detach_systems(self._player, self._quest_system)
        self._player = player
        self._quest_system = quest_system
        self._lore_system = lore_system
        # Карта/позиция изменились → пересоздать содержимое уровня под восстановленную карту.
        if map_changed or has_pos:
            spawns = self._level.world.spawns
            self._enemies = self._spawn_enemies(spawns)
            self._boss = self._spawn_boss(spawns)
            self._world_items = self._spawn_items(spawns)
            self._npcs = self._spawn_npcs(self._level.world.npcs)
            self._triggers = self._level.world.triggers
            self._combat = CombatSystem()
            self._camera.follow(self._player.pos)

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
        # World-подписки квестов (Sprint 13C): снять каждую, иначе при swap/teardown утекут.
        for name, handler in quest_system._event_subs.items():
            EventBus.off(name, handler)
        quest_system._event_subs.clear()

    def _fresh_systems(
        self, pos: tuple[float, float] | None = None
    ) -> tuple[Player, QuestSystem, LoreSystem]:
        """Построить чистые player/quest/lore для восстановления сохранения.

        pos — позиция игрока (из сейва); по умолчанию — стартовая точка текущей карты.
        """
        start = pos if pos is not None else self._player_start
        player = Player(*start, self._load_player_config())
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

    def _spawn_items(self, spawns: list[SpawnPoint]) -> list[Item]:
        """Создать предметы из точек спавна с реальными item_id; категория — из items.json.

        Токен спавна — реальный item_id (`canned_beans`/`ration_pack`/`vaccine_component_*`):
        если он есть в секции food → FoodItem, в quest → QuestItem. Неизвестные id — пропуск.
        """
        cfg = self._load_item_configs()
        food = cfg["food"]
        quest = cfg["quest"]
        items: list[Item] = []
        for sp in spawns:
            if sp.name in food:
                c = food[sp.name]
                items.append(
                    FoodItem(sp.x, sp.y, sp.name, c["name"], c["description"], c["nutrition"])
                )
            elif sp.name in quest:
                c = quest[sp.name]
                items.append(QuestItem(sp.x, sp.y, sp.name, c["name"], c["description"]))
        return items
