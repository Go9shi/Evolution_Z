# CLAUDE-progress.md — Evolution Z

Этот файл обновляется вручную после каждой рабочей сессии.
Помогает Claude Code быстро восстановить контекст при следующем запуске.

---

## Текущий статус

**Фаза:** Активная разработка  
**Спринт:** 11C — Sprite Rendering Pipeline ✅ (AssetLoader: загрузка/кэш PNG; спрайты для player/enemies/boss/тайлов с fallback на pygame.draw)  
**Дата последнего обновления:** 2026-06-14

---

## Что сделано

### Спринт 1 — Структура и документация ✅
- [x] `game_design.md`, `architecture.md`, `CLAUDE.md`, `CLAUDE-progress.md`
- [x] Папочная структура, 56 пустых стабов
- [x] `requirements.txt` — pygame-ce, pytmx, ruff, mypy, pytest

### Спринт 2 — Core + Player ✅
- [x] `settings.py` — FPS=60, SCREEN_W=1280, SCREEN_H=720, пути, цвета
- [x] `core/game_object.py` — `GameObject`: id-счётчик, pos (Vector2), active
- [x] `core/entity.py` — `Entity(GameObject)`: делегирует HP в `HealthComponent`, EventBus
- [x] `systems/event_bus.py` — pub/sub шина: `on`, `off`, `emit`, `clear`
- [x] `systems/health.py` — `HealthComponent`: current, maximum, percentage, take_damage, heal, reset
- [x] `systems/camera.py` — `Camera`: `follow(target_pos)`, даёт offset для рендера
- [x] `entities/player.py` — `Player(Entity)`: WASD движение, `_read_input`, эмитит `player_moved`
- [x] `ui/base_screen.py` — `BaseScreen`: интерфейс handle_event/update/draw
- [x] `ui/game_screen.py` — `GameScreen(BaseScreen)`: владеет Player и Camera
- [x] `main.py` — `Game` + `GameStateManager` (стек экранов), пуш GameScreen на старте
- [x] `assets/data/player.json` — speed=220, max_health=100, size=32×32
- [x] Запускаемый прототип: зелёный квадрат (игрок) на тёмно-сером фоне, WASD работает

### Тесты — 38 тестов, все зелёные ✅
- [x] `tests/conftest.py` — pygame_init (session), clean_event_bus (autouse)
- [x] `tests/test_event_bus.py` — 6 тестов
- [x] `tests/test_game_object.py` — 3 теста
- [x] `tests/test_entity.py` — 10 тестов
- [x] `tests/test_health_component.py` — 11 тестов
- [x] `tests/test_camera.py` — 4 теста
- [x] `tests/test_player.py` — 4 теста

### Спринт 3 — Карта + Коллизии ✅
- [x] `settings.py` — `TILE_SIZE=32`, `TILE_FLOOR_COLOR`, `TILE_WALL_COLOR`
- [x] `systems/game_world.py` — `GameWorld`: 50×24 тайловая сетка бункера A1, 4 комнаты + коридоры, `wall_rects`, `draw()` с viewport culling
- [x] `entities/player.py` — `update(dt, walls)`, AABB-коллизии через `_resolve_x`/`_resolve_y`
- [x] `ui/game_screen.py` — интегрирован `GameWorld`, игрок стартует в комнате 1
- [x] `tests/test_game_world.py` — 8 тестов
- [x] Запускаемый прототип: игрок ходит по карте бункера, стены блокируют движение

### Спринт 3.5 — Hunger System ✅
- [x] `systems/hunger.py` — `HungerComponent`: `current`, `maximum`, `percentage`, `is_starving`, `update(dt)`, `consume(amount)`, `reset()`
- [x] `data/player_data.py` — добавлены `max_hunger`, `hunger_decay_rate`, `hunger_damage_rate`
- [x] `assets/data/player.json` — `max_hunger=100`, `hunger_decay_rate=2.0`, `hunger_damage_rate=5.0`
- [x] `entities/player.py` — оркестрация: `hunger.update(dt)` → `is_starving` → `take_damage()` → EventBus
- [x] `systems/health.py` + `core/entity.py` — `take_damage/heal` переведены на `float` (дробный урон)
- [x] `tests/test_hunger.py` — 10 тестов компонента
- [x] `tests/test_player.py` — +2 интеграционных теста (урон при голоде / нет урона без голода)

### Тесты — 58 тестов, все зелёные ✅
Покрытие: 86% (264 stmts). Ключевые модули:
- `systems/hunger.py` — 100%
- `systems/health.py` — 100%
- `core/entity.py` — 100%
- `systems/event_bus.py` — 100%
- `systems/game_world.py` — 89% (draw() требует display)
- `entities/player.py` — 59% (рендер и _read_input требуют display/keyboard)

### Спринт 4 — Враги (ближний бой) ✅
- [x] `data/enemy_data.py` — `@dataclass EnemyData`: 9 полей (max_health, speed, damage, attack_range, detection_range, attack_cooldown, width, height, xp_reward)
- [x] `assets/data/enemies.json` — конфиги walker и runner (без магических чисел в коде)
- [x] `entities/zombie.py` — `AIState` enum (IDLE/PATROL/CHASE/ATTACK) + `Zombie(Entity, ABC)` с Template Method в `update()` + `WalkerZombie` + `RunnerZombie`
- [x] `ui/game_screen.py` — список `_enemies`, полиморфный update/draw цикл, `_spawn_enemies()`, `_load_enemy_configs()`
- [x] Запускаемый прототип: 2 уокера в комнате 2, 1 раннер в комнате 3; патрулируют, преследуют, атакуют

### Тесты — 81 тест, все зелёные ✅
+23 теста в `tests/test_zombie.py`:
- EnemyData: поля и типы
- Иерархия: WalkerZombie → Zombie → Entity
- Обнаружение: detection_range, attack_range
- AI-переходы Walker: PATROL / CHASE / ATTACK
- AI-переходы Runner: IDLE / CHASE / ATTACK
- Атака: урон, событие, кулдаун, восстановление
- Смерть: active=False, entity_died event
- Полиморфизм: единый интерфейс update(), runner быстрее walker
- Интеграционный: update() → attack() → HP игрока снижается

---

## В работе прямо сейчас

- [ ] Спринт 8E — Нарратив: системы. DialogueSystem ✅ + DialogueLoader ✅ + DialogueUI ✅ + интеграция в GameScreen ✅ (8F) + Quest↔Dialogue ✅ (8G) + LoreSystem ✅ (8H) + Lore↔Dialogue ✅ (8I) + Lore UI ✅ (8J) сделаны. Осталось: триггеры открытия записок/терминалов на карте, сюжетные события глав 1–3.

---

## Что делать дальше (бэклог)

### Спринт 3 — Карта + Коллизии ✅ (завершён)

### Спринт 4 — Враги (ближний бой) ✅ (завершён)

### Спринт 5A — Базовая боевая система ✅ (завершён)
- [x] `data/weapon_config.py` — `WeaponConfig @dataclass`: damage, fire_rate, bullet_speed, bullet_range, bullet_size
- [x] `assets/data/weapons.json` — конфиг pistol
- [x] `core/weapon.py` — `Weapon(ABC)`: can_fire, update(dt), fire(pos, dir) → list[Bullet]
- [x] `entities/bullet.py` — `Bullet(GameObject)`: velocity, damage, range_left, size, origin_tag, rect (AABB)
- [x] `entities/weapons/pistol.py` — `Pistol(Weapon)`: fire() создаёт одну пулю, возвращает list[Bullet]
- [x] `systems/combat.py` — `Targetable` Protocol + `CombatSystem`: пул пуль, AABB-попадания, EventBus
- [x] `entities/player.py` — `equip(weapon)`, `fire(direction)`, тик оружия в `update()`
- [x] `ui/game_screen.py` — MOUSEBUTTONDOWN → выстрел, CombatSystem в update/draw
- [x] `tests/test_combat.py` — 26 тестов (WeaponConfig, Bullet, Pistol, CombatSystem, интеграционные)
- [x] Запускаемый прототип: ЛКМ → пистолет стреляет → пуля летит → WalkerZombie / RunnerZombie получают урон → умирают

### Тесты — 107 тестов, все зелёные ✅
+26 тестов в `tests/test_combat.py`:
- WeaponConfig: поля, dataclass
- Bullet: initial_state, движение, деактивация (стена / дальность), rect, damage/size/origin_tag
- Pistol: fire() list[Bullet], кулдаун, нулевое направление, урон из конфига, тик
- CombatSystem: add_bullets, движение, AABB-урон, деактивация, bullet_hit event, очистка пула, промах
- Integration: полный цикл Player→Combat→Walker умирает; мёртвый враг не получает двойной урон

### Спринт 5B — SpitterZombie ✅ (завершён)
- [x] `core/entity.py` — `faction: str = ""` для faction-фильтра в CombatSystem
- [x] `entities/player.py` — `faction = "player"`
- [x] `data/spitter_data.py` — `SpitterData(EnemyData)`: spit_damage, spit_speed, spit_range, safe_distance
- [x] `entities/bullet.py` — `AcidBullet(Bullet)`: зелёный цвет, вся физика из Bullet
- [x] `entities/zombie.py` — `AIState.REPOSITION` + `SpitterZombie` + `collect_spawned_bullets()`
- [x] `systems/combat.py` — `faction` в `Targetable`, faction-фильтр в `_check_hits`, `rect` как `@property`
- [x] `assets/data/enemies.json` — конфиг spitter (13 полей)
- [x] `ui/game_screen.py` — SpitterZombie в комнате 4, сбор пуль, один CombatSystem для всех
- [x] `tests/test_spitter.py` — 25 тестов
- [x] Запускаемый прототип: Spitter отступает при сближении, плюётся кислотой, пули попадают в игрока

### Тесты — 132 теста, все зелёные ✅ (до Спринта 6)
+25 тестов в `tests/test_spitter.py`:
- SpitterData: наследование, базовые и дополнительные поля
- AcidBullet: наследование, цвет, origin_tag, урон, движение
- SpitterZombie: иерархия, faction, spawn
- AI-переходы: PATROL / CHASE / ATTACK / REPOSITION
- attack() + collect_spawned_bullets(): создание снаряда, дренаж очереди, кулдаун, нулевое направление
- Полиморфизм: walker.collect_spawned_bullets() → []
- Faction-фильтр: AcidBullet бьёт игрока, пропускает зомби
- Интеграционный: update() → attack() → collect → AcidBullet создан

### Тесты — 162 теста, все зелёные ✅
+30 тестов в `tests/test_inventory.py`:
- Inventory: add (success/full), remove (found/not found), contains, count, is_full
- use_item: food consumed+removed, quest kept, not-in-inventory guard
- FoodItem: use→True, restores hunger, clamps to maximum
- QuestItem: use→False, иерархия, stackable=False
- Player integration: pickup_item добавляет в инвентарь, деактивирует предмет, full guard, use_item восстанавливает голод
- EventBus: inventory_item_added, inventory_item_removed, item_used, item_used not fired for quest

### Спринт 6 — Инвентарь + Предметы ✅ (завершён)
- [x] `assets/data/items.json` — конфиги canned_beans, ration_pack, vaccine_component_alpha/beta
- [x] `core/item.py` — `Item(GameObject, ABC)`: item_id, name, description, stackable, rect, use(player) → bool, draw()
- [x] `entities/items/food_item.py` — `FoodItem(Item)`: nutrition, use() → player.hunger.consume() → True
- [x] `entities/items/quest_item.py` — `QuestItem(Item)`: use() → False (не расходуется)
- [x] `systems/inventory.py` — `Inventory`: capacity=20, add/remove/contains/use_item, EventBus-события
- [x] `entities/player.py` — `_inventory`, `inventory` property, `pickup_item(item)`, `use_item(item)`
- [x] `ui/game_screen.py` — `_world_items`, подбор на коллизии, клавиша F — использовать первый предмет
- [x] `tests/test_inventory.py` — 30 тестов
- [x] Запускаемый прототип: игрок ходит над предметом → автоподбор; F → еда восстанавливает голод; квест-предметы сохраняются

### Спринт 7A — XP + Уровни ✅ (завершён)
- [x] `systems/experience.py` — `ExperienceComponent`: `current_xp`, `current_level`, `xp_to_next_level`, `add_xp()` → level-up loop + EventBus
- [x] `entities/player.py` — `_experience`, `experience` property, `add_xp()` делегирование
- [x] `ui/game_screen.py` — `_on_entity_died` → `player.add_xp(xp_reward)` при гибели врага
- [x] `tests/test_experience.py` — 26 тестов

### Тесты — 188 тестов, все зелёные ✅ (до Спринта 7B)

### Спринт 7B — Skill Tree Core ✅ (завершён)
- [x] `systems/health.py` — +`increase_maximum(amount)`: увеличивает maximum и current (bounded)
- [x] `systems/hunger.py` — +`reduce_decay_rate(amount)`: уменьшает скорость голода, не ниже 0
- [x] `core/weapon.py` — +`_damage_bonus`, `damage_bonus` property, `add_damage_bonus(amount)`
- [x] `entities/weapons/pistol.py` — bullet damage = `config.damage + _damage_bonus`
- [x] `systems/skill_tree.py` — `SkillType(Enum)`: MAX_HEALTH / HUNGER_EFFICIENCY / PISTOL_DAMAGE; `SkillTree`: `available_points`, `get_level`, `add_point`, `can_upgrade`, `upgrade(skill, player)`
- [x] `entities/player.py` — `_skill_tree`, `skill_tree` property, `apply_weapon_damage_bonus()`, подписка `player_level_up` → `_on_level_up` → `add_point()`
- [x] `tests/test_skill_tree.py` — 36 тестов

### Тесты — 224 теста, все зелёные ✅ (до Спринта 7C)

### Спринт 7C — Skill Tree UI ✅ (завершён)
- [x] `ui/skill_tree_ui.py` — `SkillTreeUI(BaseScreen)`: UP/DOWN навигация, ENTER прокачка, ESC закрытие, текстовый оверлей с уровнями-барами
- [x] `ui/game_screen.py` — +Tab → открывает `SkillTreeUI`; +опциональный `state_manager` в `__init__`
- [x] `main.py` — передаёт `state_manager` в `GameScreen`
- [x] `tests/test_skill_tree_ui.py` — 27 тестов
- [x] `systems/hunger.py` — ✅ сделано досрочно (Спринт 3.5)

### Тесты — 251 тест, все зелёные ✅ (до багфикса)

### Спринт 7C — багфикс: двойная обработка ESC ✅
**Баг:** ESC при открытом SkillTreeUI одновременно закрывал UI и завершал игру.
**Причина:** `main.py._handle_events` безусловно выставлял `_running=False` на K_ESCAPE, затем передавал событие в `SkillTreeUI`.
**Фикс:** `GameStateManager.depth` property + проверка `depth <= 1` перед выходом.
- [x] `main.py` — `GameStateManager.depth: int` property + `if depth <= 1: _running = False`
- [x] `tests/test_skill_tree_ui.py` — +11 регрессионных тестов (TestGameStateManagerDepth × 5, TestEscRoutingRegression × 6)

### Тесты — 309 тестов, все зелёные ✅ (после Спринта 8A)

### Тесты — 262 теста, все зелёные ✅
+11 регрессионных тестов:
- TestGameStateManagerDepth: depth=0/1/2, уменьшение при pop, pop на пустом стеке
- TestEscRoutingRegression: ESC закрывает оверлей и оставляет базовый экран; depth>1 = оверлей открыт; depth=1 = разрешён выход; TAB→ESC→возврат к базовому; повторное открытие после закрытия; on_close ровно 1 раз

### Спринт 8A — Quest System Core ✅ (завершён)
- [x] `data/quest_data.py` — `QuestStatus(Enum)`, `Objective(ABC)`, `KillZombieObjective`, `Quest @dataclass`
- [x] `systems/quest_system.py` — `QuestSystem`: `accept_quest`, `update_progress`, `complete_quest`, EventBus-подписка на `entity_died`, эмит `quest_completed`
- [x] `tests/test_quest_system.py` — 47 тестов: все требования Sprint 8A покрыты
- [x] Вертикальный цикл: принять квест → убить зомби → завершить → XP → level up

### Спринт 8B — Quest Log UI ✅ (завершён)
- [x] `data/quest_data.py` — +полиморфное `Objective.progress` (abstract) → `KillZombieObjective.progress` возвращает `"current/target"`
- [x] `ui/quest_log_ui.py` — `QuestLogUI(BaseScreen)`: только чтение через публичный API QuestSystem; UP/DOWN навигация, ESC закрытие; рендер title/description/status/прогресс целей; пустое состояние
- [x] `ui/game_screen.py` — +`QuestSystem` (с `player.experience`); +стартовый квест `Clear Bunker A1` (4 зомби); +клавиша J → открывает `QuestLogUI` (lazy import, как Tab→SkillTreeUI)
- [x] `tests/test_quest_log_ui.py` — 28 тестов
- [x] `tests/test_quest_system.py` — +3 теста на `Objective.progress`
- [x] Smoke-тест вертикального среза (headless): J → журнал → 4 убийства → квест завершён → XP → level up → ESC → возврат в игру

### Тесты — 340 тестов, все зелёные ✅ (после Спринта 8B)

### Спринт 8C — Quest Data & Narrative Foundation ✅ (завершён)
- [x] `assets/data/quests.json` — данные квестов в JSON (формат `{"quests": [...]}` с `objectives[].type`)
- [x] `data/quest_loader.py` — `load_quests(path)` + `QuestLoadError`; диспетчер `_OBJECTIVE_BUILDERS` (type → builder); валидация структуры, обязательных полей, неизвестных типов
- [x] `ui/game_screen.py` — инлайн-квест `_make_starter_quest()` УДАЛЁН; `_load_quests()` читает `DATA_DIR/quests.json` и `accept_quest` для каждого
- [x] `tests/test_quest_loader.py` — 29 тестов
- [x] Smoke-тест (headless): квест из JSON → J → журнал → 4 убийства → завершён → XP 220 → level 2 → ESC

### Тесты — 369 тестов, все зелёные ✅ (после Спринта 8C)

### Спринт 8D — Narrative Foundation (данные и модель) ✅ (завершён)
Цель: инфраструктура сюжетных данных БЕЗ NPC, диалогов, цепочек, сейвов, боссов — только данные и модели.
- [x] `data/quest_data.py` — `Quest` получил опциональные narrative-поля `lore_text`, `location`, `category` (default `""`); QuestSystem их не использует
- [x] `data/quest_loader.py` — `_build_quest` читает новые поля через `.get(..., "")`; они НЕ входят в `_REQUIRED_QUEST_FIELDS` (опциональны, обратная совместимость)
- [x] `assets/data/quests.json` — `clear_bunker_a1` расширен `lore_text` / `location` / `category`
- [x] `ui/quest_log_ui.py` — `_format_meta(quest)` → строка `[category] @ location`; рисуется под описанием только если непуста (старые квесты без полей строку не получают)
- [x] `tests/test_quest_loader.py` — +14 тестов (загрузка полей, опциональность, частичные метаданные, обратная совместимость, реальный JSON)
- [x] `tests/test_quest_log_ui.py` — +6 тестов (форматирование метаданных, отрисовка с/без полей)

### Тесты — 387 тестов, все зелёные ✅ (после Спринта 8D)

### Спринт 8E — Нарратив: системы (в работе)
- [x] `data/dialogue_data.py` — `@dataclass DialogueChoice` (text, next_id), `DialogueNode` (id, speaker, text, choices, `is_terminal`), `Dialogue` (id, nodes, start_id)
- [x] `systems/dialogue.py` — `DialogueError` + `DialogueSystem`: `start`, `is_active`, `current_node`, `advance` (линейный), `choose(index)` (ветвление), `end`; EventBus-события `dialogue_started` / `dialogue_node_changed` / `dialogue_ended`; без isinstance (ветвление по `len(choices)`)
- [x] `tests/test_dialogue.py` — 32 теста (данные, старт+валидация, advance, choose, end, EventBus, интеграция)
- [x] `assets/data/dialogues.json` — данные диалогов (`{"dialogues": [{id, start_id, nodes: [{id, speaker, text, choices: [{text, next_id}]}]}]}`); пример `ranger_intro`
- [x] `data/dialogue_loader.py` — `load_dialogues(path) → list[Dialogue]` + `DialogueLoadError`; валидация структуры, обязательных полей узлов/диалога, дубликатов id, целостности ссылок (start_id + непустые next_id)
- [x] `tests/test_dialogue_loader.py` — 25 тестов
- [x] `ui/dialogue_ui.py` — `DialogueUI(BaseScreen)`: ref на DialogueSystem + `on_close: Callable`; UP/DOWN — навигация по choices (циклическая), ENTER — `choose(index)` (не-терминал) / `advance()` (терминал → завершает диалог), ESC — `on_close()`; состояние не дублирует, читает `current_node`
- [x] `tests/test_dialogue_ui.py` — 25 тестов
- [ ] `systems/lore.py` — записки и терминалы
- [ ] Сюжетные события глав 1–3

### Спринт 8F — Dialogue Integration ✅ (завершён)
- [x] `ui/game_screen.py` — `_load_dialogues()` (читает `DATA_DIR/dialogues.json`); `self._dialogues: dict[str, Dialogue]`; `self._dialogue_system = DialogueSystem()` (владелец состояния); read-only property `dialogue_system`
- [x] `ui/game_screen.py` — клавиша `T` → `_start_dialogue("ranger_intro")`: lazy import `DialogueUI`, `dialogue_system.start(dialogue)`, `state_manager.push(DialogueUI(..., state_manager.pop))`; нет-оп при `state_manager is None` и неизвестном id
- [x] `ui/game_screen.py` — подписка на EventBus `dialogue_ended` → `_on_dialogue_ended`: снимает оверлей (`pop`), только если сверху `DialogueUI` — авто-возврат в игру по завершении диалога
- [x] `tests/test_dialogue_integration.py` — 14 тестов
- [x] Smoke (headless): GameScreen → T → DialogueUI → выбор → терминал → ENTER → авто-возврат в GameScreen → игра продолжается

### Спринт 8G — Quest ↔ Dialogue Integration ✅ (завершён)
Цель: связать существующие системы диалогов и квестов — диалог выдаёт существующий квест. БЕЗ NPC, lore, глав, сейвов, боссов, новых типов квестов/узлов.
- [x] `data/dialogue_data.py` — `DialogueChoice` получил опциональное поле `quest_id` (default `""`); диалог трактует его как opaque-ссылку, о квестах не знает
- [x] `systems/dialogue.py` — `choose()` и `advance()` маршрутизированы через `_select(choice)`, который эмитит EventBus `dialogue_choice_selected` ({choice}); DialogueSystem не зависит от QuestSystem
- [x] `data/dialogue_loader.py` — `_build_choice` читает `quest_id` через `.get(..., "")` (опционально, обратная совместимость)
- [x] `assets/data/dialogues.json` — у выбора «I'll help clear the bunker» в `ranger_intro` добавлен `"quest_id": "clear_bunker_a1"`; структура узлов сохранена (старые тесты целы)
- [x] `ui/game_screen.py` — квесты грузятся в реестр `self._quests: dict[str, Quest]` БЕЗ авто-принятия; подписка на `dialogue_choice_selected` → `_on_dialogue_choice` → `accept_quest` по quest_id из реестра
- [x] `tests/test_quest_dialogue_integration.py` — 17 тестов
- [x] Smoke (headless): T → диалог → выбор → квест выдан → J → журнал → 4 убийства → завершён → XP 100 → level 2

### Тесты — 500 тестов, все зелёные ✅ (после Спринта 8G)
+17 тестов в `tests/test_quest_dialogue_integration.py`:
- Событие выбора: `choose`/`advance` эмитят `dialogue_choice_selected` с quest_id; терминальный узел не эмитит; вариант без квеста несёт пустой quest_id
- Принятие: выбор с quest_id выдаёт квест; квест среди активных; «Not now» (без quest_id) не выдаёт
- Безопасность: неизвестный quest_id; пустой quest_id; событие без ключа `choice`; повторный выбор не дублирует; повторная выдача завершённого квеста — нет-оп
- Полный сценарий: диалог → выбор → квест → 4 убийства → завершение → XP 100 → level 2; прогресс цели работает как раньше после выдачи
- Регрессии: обычный диалог (ветка без квеста) работает; обычный жизненный цикл квеста (принят напрямую) работает; событие выбора не ломает update/draw

### Спринт 8H — Lore System ✅ (завершён)
Цель: базовая система лора — слой `Lore Data → Lore System`, аналогично quest/dialogue. БЕЗ UI, глав, NPC, боссов, сейвов, JSON-загрузчика (нет данных-потребителей — отложен).
- [x] `data/lore_data.py` — `@dataclass LoreEntry` (id, title, text, `category=""`); чистая модель данных
- [x] `systems/lore.py` — `LoreSystem`: `register`, `has_entry`, `is_unlocked`, `unlock` (→ bool), `unlocked_entries` (копия, порядок открытия), `entries` (копия); EventBus-событие `lore_unlocked` ({entry}) ровно один раз на запись; неизвестный id и повторное открытие — нет-оп
- [x] `tests/test_lore.py` — 25 тестов
- [x] UI/LoreScreen НЕ создавался; `ui/lore_ui.py` остаётся пустым стабом (следующие спринты)

### Тесты — 525 тестов, все зелёные ✅ (после Спринта 8H)
+25 тестов в `tests/test_lore.py`:
- LoreEntry: поля, дефолт `category=""`
- register/has_entry: регистрация делает запись известной; незарегистрированная не известна; запись попадает в `entries`; register не открывает; повторная регистрация перезаписывает
- unlock: возвращает True; помечает открытой; попадает в `unlocked_entries`; повторное открытие → False и без дублей
- unlocked_entries: пуст пока ничего не открыто; сохраняет порядок открытия; возвращает копию (внешняя мутация безопасна); перечисляет только открытые
- Безопасность: неизвестный id → False/нет открытия; пустая система; множественные записи независимы
- События: unlock эмитит `lore_unlocked`; событие несёт entry; повторное открытие эмитит один раз; неизвестный id ничего не эмитит; каждая запись даёт своё событие

### Спринт 8I — Lore Integration ✅ (завершён)
Цель: связать существующие системы диалогов и лора — диалог открывает существующую запись лора. БЕЗ Lore UI, NPC, глав, сейвов, боссов, новых механик. Прямая аналогия 8G (Quest↔Dialogue).
- [x] `data/dialogue_data.py` — `DialogueChoice` получил опциональное поле `lore_id` (default `""`); диалог трактует его как opaque-ссылку, о лоре не знает
- [x] `data/dialogue_loader.py` — `_build_choice` читает `lore_id` через `.get(..., "")` (опционально, обратная совместимость)
- [x] `assets/data/lore.json` — НОВЫЙ файл с записью `bunker_a1_origin` (формат `{"lore": [{id, title, text, category}]}`)
- [x] `assets/data/dialogues.json` — у выбора «Thank you» в `ranger_intro` добавлен `"lore_id": "bunker_a1_origin"`; структура узлов сохранена (тесты 8F/8G целы)
- [x] `ui/game_screen.py` — `self._lore_system = LoreSystem()`, записи грузятся inline `_load_lore_entries()` (как player/weapon/enemy/item) и регистрируются; `_on_dialogue_choice` дополнен открытием лора по `lore_id` (рядом с выдачей квеста, обе ветки независимы)
- [x] `tests/test_lore_dialogue_integration.py` — 16 тестов
- [x] Smoke (headless): T → диалог → «I'll help» → «Thank you» → запись `bunker_a1_origin` открыта в LoreSystem
- [x] Lore UI НЕ создавался; `ui/lore_ui.py` остаётся пустым стабом

### Тесты — 541 тест, все зелёные ✅ (после Спринта 8I)
+16 тестов в `tests/test_lore_dialogue_integration.py`:
- Разблокировка: выбор с lore_id открывает запись; запись среди открытых; выбор без lore_id ничего не открывает
- Безопасность: неизвестный lore_id; пустой lore_id; событие без `choice`; повторное открытие не дублирует
- События: unlock эмитит `lore_unlocked` один раз с entry; повтор не эмитит второй раз; неизвестный id ничего не эмитит
- Полный сценарий: T → выбор → открытие записи → LoreSystem содержит запись; не ломает update/draw
- Регрессии: обычный диалог без лора работает; Quest↔Dialogue (8G) не сломан; обычный жизненный цикл квеста; вариант с quest_id+lore_id выполняет обе интеграции

### Спринт 8J — Lore UI ✅ (завершён)
Цель: дать игроку просматривать открытые записи лора. По образцу SkillTreeUI / QuestLogUI / DialogueUI. БЕЗ NPC, глав, боссов, сейвов, меню, аудио.
- [x] `ui/lore_ui.py` — `LoreUI(BaseScreen)`: `__init__(lore_system, on_close)`; UP/DOWN циклическая навигация, ESC → `on_close`; читает `lore_system.unlocked_entries` напрямую (копия на каждый вызов — не кэширует, не дублирует состояние); рендер title / `[category]` (если есть) / перенос текста по словам; пустое состояние «No lore entries discovered.»
- [x] `ui/game_screen.py` — клавиша `L` → `LoreUI` (lazy import, `state_manager.push`, `on_close=state_manager.pop`); нет-оп при `state_manager is None`; повторяет паттерн Tab/J/T
- [x] `tests/test_lore_ui.py` — 27 тестов
- [x] Smoke (headless): T → открыть запись лора → L → LoreUI → ESC → возврат в GameScreen
- [x] `LoreSystem` не менялся; UI использует только публичный `unlocked_entries`

### Тесты — 568 тестов, все зелёные ✅ (после Спринта 8J)
+27 тестов в `tests/test_lore_ui.py`:
- Инициализация: наследование BaseScreen; начальный индекс 0; пустая система безопасна; UI не кэширует (видит запись, открытую после создания)
- Навигация: UP/DOWN; циклическая в обе стороны; одна запись; пустой список безопасен; игнор не-KEYDOWN
- Закрытие: ESC → on_close ровно один раз; навигация не закрывает
- Отрисовка: пусто / одна / несколько записей; без category; длинный текст (перенос); update — нет-оп
- Живые данные: новая запись появляется без пересоздания UI; зарегистрированная-но-не-открытая не показывается; UI не хранит собственного списка (`_entries`/`_unlocked` отсутствуют)
- Интеграция: L открывает LoreUI (depth 2); UI использует тот же `_lore_system`, что GameScreen; ESC возвращает в GameScreen; L нет-оп без state_manager

### Спринт 9A — Inventory UI ✅ (завершён)
Цель: дать игроку просматривать содержимое инвентаря. По образцу SkillTreeUI / QuestLogUI / LoreUI. БЕЗ stackable-стекинга, drop, drag-and-drop, новых механик.
- [x] `ui/inventory_ui.py` — `InventoryUI(BaseScreen)`: `__init__(inventory, on_close)`; UP/DOWN циклическая навигация, ESC → `on_close`; читает `inventory.items` напрямую (копия на вызов — не кэширует, не дублирует состояние); рендер заголовка «INVENTORY», строки `count/capacity`, списка имён с выделением, description выбранного предмета (перенос по словам); пустое состояние «Inventory is empty.»
- [x] `ui/game_screen.py` — клавиша `I` → `InventoryUI(self._player.inventory, ...)` (lazy import, `state_manager.push`, `on_close=state_manager.pop`); нет-оп при `state_manager is None`; повторяет паттерн Tab/J/L/T
- [x] `tests/test_inventory_ui.py` — 27 тестов
- [x] Smoke (headless): подбор предмета → I → InventoryUI → навигация → draw → ESC → возврат в GameScreen
- [x] `Inventory`/`Item` не менялись; UI использует только публичный `items`/`count`/`capacity`/`name`/`description`

### Тесты — 595 тестов, все зелёные ✅ (после Спринта 9A)
+27 тестов в `tests/test_inventory_ui.py`:
- Инициализация: наследование BaseScreen; начальный индекс 0; пустой инвентарь безопасен; UI не кэширует (видит предмет, добавленный после создания)
- Навигация: UP/DOWN; циклическая в обе стороны; один предмет; пустой список безопасен; игнор не-KEYDOWN
- Закрытие: ESC → on_close ровно один раз; навигация не закрывает
- Отрисовка: пусто / один / несколько; после навигации; длинное описание (перенос); update — нет-оп
- Живые данные: новый предмет появляется без пересоздания UI; удалённый исчезает; UI не хранит собственного списка (`_items` отсутствует)
- Интеграция: I открывает InventoryUI (depth 2); UI использует тот же `player.inventory`, что GameScreen; ESC возвращает в GameScreen; I нет-оп без state_manager

### Спринт 9B — Patient Zero Boss Core ✅ (завершён)
Цель: ядро сущности финального босса. ТОЛЬКО ядро — БЕЗ фаз, спец-атак, кислоты, призыва, AI, анимаций, звука, UI/HP-бара экрана, сейвов, сюжета. Без новых систем и BossManager.
- [x] `entities/boss.py` — иерархия `Entity → Boss → PatientZeroBoss` (как в CLAUDE.md/README). `Boss(Entity)`: faction='enemy', `_rect` + property `rect`, `draw` (прямоугольник + HP-бар, паттерн `Zombie.draw`), override `take_damage` → эмит `boss_defeated` строго на переходе жив→мёртв. `PatientZeroBoss(Boss)`: own max_health (инжектится в конструктор), размер `TILE_SIZE*2` из settings (не магия)
- [x] Death-паттерн врага сохранён: `Entity.take_damage` по-прежнему клампит HP (через HealthComponent), снимает `active` и эмитит `entity_died`; `boss_defeated` — boss-специфичная надстройка, не новая событийная архитектура
- [x] Совместимость с `CombatSystem` (Targetable: active/pos/faction/rect/take_damage) — пуля игрока бьёт босса существующим способом; faction-фильтр не даёт врагам бить босса
- [x] `tests/test_boss.py` — 29 тестов
- [x] Существующие системы (Quest/Dialogue/Lore/Inventory/UI/combat/entity) НЕ менялись

### Тесты — 624 теста, все зелёные ✅ (после Спринта 9B)
+29 тестов в `tests/test_boss.py`:
- Создание: тип; наследование Boss/Entity; faction='enemy'; own max_health; полное HP на старте; жив; активен; rect (центр + размер TILE_SIZE*2)
- Получение урона: снижение HP; накопление нескольких попаданий; HP не ниже 0 (избыточный урон); не-летальный урон оставляет жив+активным
- Смерть: деактивация; смерть от точного урона; смерть от избыточного; жив при уроне на 1 ниже летального
- EventBus: `boss_defeated` эмитится при смерти; данные содержат `{boss}`; не эмитится при не-летальном; ровно один раз при повторных/избыточных ударах; `entity_died` тоже эмитится (совместимость)
- Интеграция: пуля игрока ранит босса через CombatSystem; вражеская пуля не бьёт (faction-фильтр); combat убивает босса и эмитит событие; мёртвый босс игнорируется combat; `heal` следует Entity-паттерну

### Спринт 9C — Boss Integration ✅ (завершён)
Цель: `PatientZeroBoss` становится частью игрового цикла — встретить, атаковать, убить, получить победу. БЕЗ AI/фаз/спец-атак/призыва/звука/катсцен/нового UI-экрана/сейвов.
- [x] `settings.py` — `BOSS_MAX_HEALTH = 600` (конфиг HP босса; константы — в settings по CLAUDE.md)
- [x] `entities/boss.py` — `Boss.xp_reward: int = 0` (НЕОБХОДИМО: босс faction='enemy' проходит через `_on_entity_died`, который читает `entity.xp_reward`; поле завершает enemy-контракт как у `Zombie.xp_reward`; 0 = без награды)
- [x] `ui/game_screen.py` — `self._boss = self._spawn_boss()` (одно поле, не список — босс один); инлайн-координаты Комнаты 4 (43,18), HP из `BOSS_MAX_HEALTH`; босс обновляется (`update(dt)`), участвует в combat (`targets=[*enemies, player, boss]`), рисуется при `active`
- [x] `ui/game_screen.py` — подписка `boss_defeated` → `_on_boss_defeated` → `self._victory = True`; read-only property `victory`; победный результат — центрированный текст «VICTORY — PATIENT ZERO DEFEATED» (минимальный срез, без нового экрана)
- [x] `tests/test_boss_integration.py` — 21 тест
- [x] Smoke (headless): босс 600 HP → атака через combat → смерть → `victory=True` → draw победного текста; босс даёт 0 XP без падения
- [x] Заблокированные системы (Quest/Dialogue/Lore/Inventory/SkillTree + их UI) НЕ менялись

### Тесты — 645 тестов, все зелёные ✅ (после Спринта 9C)
+21 тест в `tests/test_boss_integration.py`:
- Спавн: босс создан; тип `PatientZeroBoss`; активен; HP = `BOSS_MAX_HEALTH`; faction='enemy'
- Игровой цикл: переживает обычный update; получает урон через combat; несколько кадров урона; draw без падения
- Победа: смерть эмитит `boss_defeated` ({boss}); GameScreen ставит `victory`; победа через combat-путь; не ломает update/draw; мёртвый босс не рисуется/обновляется
- Регрессии: зомби по-прежнему спавнятся; убийство зомби даёт XP; босс даёт 0 XP (без падения `_on_entity_died`); мёртвые зомби пруна­тся; системы на месте; диалог по `T` открывается

### Спринт 9D — Boss AI ✅ (завершён)
Цель: минимальный AI босса — преследование, ближняя атака, 2 фазы. БЕЗ спец-атак/кислоты/призыва/новых пуль/событий/экранов/JSON/сейвов.
- [x] `settings.py` — константы AI босса: `BOSS_SPEED/DETECTION_RANGE/ATTACK_RANGE/ATTACK_COOLDOWN/DAMAGE` + фаза 2: `BOSS_PHASE2_HEALTH_FRACTION/SPEED_MULTIPLIER/COOLDOWN_MULTIPLIER` (функциональные значения, не балансировка; новых JSON нет)
- [x] `entities/boss.py` — `PatientZeroBoss` получил AI, зеркалящий зомби: `update(dt, walls, player)` (сигнатура как `Zombie.update`) → преследование `_move_toward` в радиусе обнаружения / ближняя атака `attack` по кулдауну. Хелперы `_detect_player/_in_attack_range/_move_toward/_resolve_x/_resolve_y` — копия подхода Zombie (Zombie не рефакторился: Boss — отдельная ветвь `Entity→Boss`)
- [x] `entities/boss.py` — 2 фазы: property `phase` (1 при HP>50%, 2 при <=50%), `speed`/`attack_cooldown` зависят от фазы (фаза 2 быстрее и чаще), `can_attack`/`_attack_timer`
- [x] `ui/game_screen.py` — единственная правка: `self._boss.update(dt, walls, self._player)` (раньше `update(dt)`) — босс теперь нуждается в walls+player для преследования
- [x] Melee БЕЗ нового события (`zombie_attacked` — событие зомби, у босса не эмитится); урон — через `target.take_damage` (HealthComponent игрока)
- [x] `tests/test_boss_ai.py` — 26 тестов
- [x] Smoke (headless): фаза 1 (speed 90, cd 1.2) → преследование → атака (hp 100→60) → урон до <=50% → фаза 2 (speed 135, cd 0.72)

### Тесты — 671 тест, все зелёные ✅ (после Спринта 9D)
+26 тестов в `tests/test_boss_ai.py`:
- Создание: старт в фазе 1; speed=`BOSS_SPEED`; cooldown=`BOSS_ATTACK_COOLDOWN`; can_attack=True
- Преследование: движение к игроку; верное направление; несколько кадров сокращают дистанцию; не движется вне радиуса обнаружения; player=None безопасен
- Ближняя атака: урон игроку в радиусе (`BOSS_DAMAGE`); `attack` напрямую; кулдаун блокирует повтор; can_attack=False после атаки; атака снова после кулдауна; нет атаки вне радиуса
- Фазы: HP>50% → фаза 1; ровно 50% → фаза 2; <50% → фаза 2; фаза 2 быстрее; фаза 2 ниже кулдаун; фаза 2 проходит больше за кадр
- Регрессии: смерть босса; `boss_defeated`; CombatSystem наносит урон; xp_reward=0; стена блокирует движение

### Спринт 10A — Save System ✅ (завершён)
Цель: минимальное ядро сохранения/загрузки в JSON. БЕЗ меню/слотов/автосейва/версий/миграций/шифрования. Только система + тесты (без интеграции в GameScreen/UI).
- [x] `data/save_file.py` — `@dataclass SaveData` (player_xp/level, skill_levels, inventory_item_ids, active/completed_quest_ids, unlocked_lore_ids) + `to_dict`/`from_dict` (устойчив к битым/пустым ключам)
- [x] `systems/save_system.py` — `SaveSystem` + `SaveError`: `capture` (снимок через публичный API), `save` (JSON), `load` (разбор + SaveError при отсутствии файла/битом JSON/не-объекте), `apply` (восстановление), `load_into`
- [x] `systems/quest_system.py` — НЕОБХОДИМОЕ дополнение: публичный `restore(active, completed)` (нет публичного пути для завершённых квестов; `accept+complete` дважды начислили бы XP/события). Существующее поведение не изменено
- [x] Восстановление через публичный API: XP — `player.add_xp(total)` (детерминированно воспроизводит уровень + выдаёт очки навыков); навыки — `skill_tree.upgrade` по сохранённым уровням (тратит выданные очки, повторно применяет эффекты); инвентарь — пересборка по `item_id` из `items.json` (food→FoodItem, quest→QuestItem); квесты — `load_quests`+`restore`; лор — `lore_system.unlock(id)`
- [x] `tests/test_save_system.py` — 25 тестов
- [x] JSON через `json`, без pickle и сторонних библиотек

### Тесты — 696 тестов, все зелёные ✅ (после Спринта 10A)
+25 тестов в `tests/test_save_system.py`:
- Save: файл создаётся; JSON валиден; секции player/skills/inventory/quests/lore
- SaveData: round-trip to_dict/from_dict; пустой dict → дефолты
- Load/Безопасность: round-trip; отсутствующий файл → SaveError; битый JSON → SaveError; не-объект → SaveError; пустое сохранение `{}` → дефолты; apply пустого безопасен
- Experience: XP восстановлен; уровень восстановлен (level 3)
- Skill Tree: уровни навыков восстановлены; эффект (max_health) повторно применён; свободные очки сохранены
- Inventory: предметы восстановлены по id; тип (FoodItem); неизвестный id пропущен без падения
- Quest: активные восстановлены; завершённые восстановлены; восстановление НЕ начисляет повторно reward_xp
- Lore: открытые восстановлены; незарегистрированные/закрытые не восстанавливаются
- Full round-trip: capture → save → load_into → capture идентичны

### Спринт 10B — Save Integration ✅ (завершён)
Цель: подключить SaveSystem к игре. Минимальный срез: F5 — сохранить, F9 — загрузить, один файл. БЕЗ меню/слотов/UI сохранений/подтверждений/автосейва.
- [x] `ui/game_screen.py` — клавиша `F5` → `_save_game` (SaveSystem().save в `SAVES_DIR/savegame.json`, mkdir); `F9` → `_load_game`. F5/F9 были свободны (заняты ЛКМ/F/Tab/J/L/I/T)
- [x] `_load_game` — `SaveSystem().load` (SaveError → нет-оп: отсутствующий/битый/не-объект файл игру не ломает); восстановление в свежие системы (`_fresh_systems`: player+pistol, QuestSystem, LoreSystem+каталог) через `SaveSystem.apply`; затем подмена `self._player/_quest_system/_lore_system` (поля читаются каждый кадр — swap безопасен)
- [x] `_SAVE_PATH` — класс-атрибут (один файл, тестируется через monkeypatch)
- [x] Логика восстановления не дублируется — переиспользован `SaveSystem.apply` (10A)
- [x] `tests/test_save_integration.py` — 14 тестов
- [x] Smoke (headless): F5 (xp+навык+предмет+квест+лор) → F9 → всё восстановлено

### Тесты — 710 тестов, все зелёные ✅ (после Спринта 10B)
+14 тестов в `tests/test_save_integration.py`:
- F5 Save: создаёт файл; валидный JSON; сохраняет текущее состояние (xp)
- F9 Load: восстанавливает состояние (изменил после save → F9 откатил); пересоздаёт игрока (новый объект)
- Интеграция: восстановлены XP/уровень, навыки, инвентарь, квесты, лор; игра продолжает работать после загрузки
- Безопасность: отсутствующий / битый / не-объект файл → нет-оп, состояние не тронуто (тот же объект игрока)

### Спринт 10C — HUD ✅ (завершён)
Цель: постоянный игровой оверлей поверх GameScreen для уже существующих систем. Чистый UI-слой, без игрового состояния. БЕЗ миникарты/HP-бара босса/меню/экрана победы.
- [x] `ui/hud.py` — `HUD`: `__init__()` (только шрифты), `draw(surface, player, quest_system)`; НЕ BaseScreen, не в GameStateManager, не хранит игровых данных — читает аргументы каждый кадр
- [x] Отображение: HP-бар + `current/maximum` (`player.health.percentage`), бар голода (`player.hunger.percentage`), уровень + XP-бар (`experience.current_level/current_xp/xp_to_next_level`), трекер активных квестов (`quest_system.active_quests` → `title` + `objective.progress`); пусто квестов → ничего
- [x] `ui/game_screen.py` — `self._hud = HUD()` в `__init__`; `self._hud.draw(surface, self._player, self._quest_system)` в конце `draw` (перед victory-текстом). Поля передаются аргументами → подмена при F9 безопасна
- [x] UI-константы (размеры/цвета баров) — module-level приватные в `hud.py` (паттерн `lore_ui`/`inventory_ui`), не settings
- [x] `tests/test_hud.py` — 12 тестов
- [x] Smoke (headless): урон+XP+квест → `GameScreen.draw` рисует HUD; после F5/F9 HUD тот же экземпляр, рисует новые объекты

### Тесты — 722 теста, все зелёные ✅ (после Спринта 10C)
+12 тестов в `tests/test_hud.py`:
- HUD: создание; draw на пустом состоянии (нет квестов); полный HP; низкий HP; голод 0; несколько активных квестов; после изменения состояния игрока; HUD не хранит игровых полей (`_player`/`_quest_system` отсутствуют)
- Интеграция: `GameScreen` владеет HUD; `GameScreen.draw` с HUD не падает; один HUD рисует двух разных игроков (читает аргументы); после F9 HUD — тот же экземпляр, рисует новые player/quest_system без падения

### Спринт 10D — Game Over / Lose Condition ✅ (завершён)
Цель: добавить состояние поражения (симметрично существующей победе) и заморозить игровой цикл в терминальных состояниях. Через существующее событие `entity_died`, без новых систем/событий/JSON.
- [x] `ui/game_screen.py` — `self._game_over: bool` + read-only property `game_over` (по аналогии с `victory`)
- [x] Детект смерти игрока в существующем `_on_entity_died`: `if entity is self._player → game_over=True` (идентичность; swap-safe после F9), иначе прежняя ветка XP за врага. Новых подписок/событий нет
- [x] Заморозка в `update`: ранний `return` при `victory or game_over` — враги/босс/combat/подбор/таймеры не тикают (исправлена и прежняя недоработка: победа теперь тоже замораживает цикл)
- [x] `_draw_game_over` (зеркало `_draw_victory`): центрированный «GAME OVER»; в `draw` — `if victory … elif game_over …` (взаимоисключение); HUD рисуется под оверлеем
- [x] `tests/test_game_over.py` — 13 тестов
- [x] Smoke (headless): летальный урон игроку → game_over=True → update заморожен (HP не меняется) → draw рисует оверлей

### Тесты — 735 тестов, все зелёные ✅ (после Спринта 10D)
+13 тестов в `tests/test_game_over.py`:
- Базовое состояние: game_over=False и victory=False после создания
- Смерть игрока: летальный урон → game_over=True; не-летальный → False
- Регрессии: смерть зомби не вызывает game_over; смерть босса не вызывает game_over (вместо этого victory)
- Заморозка: контроль (без терминала combat двигает пулю); после game_over пуля не двигается; после victory пуля не двигается
- Отрисовка: draw при game_over и при victory не падает
- Совместимость: победа по-прежнему работает; game_over и victory независимы

### Спринт 10E — Main Menu ✅ (завершён)
Цель: игра стартует с главного меню (New Game / Continue / Quit), один файл сейва, без слотов. БЕЗ Pause Menu/Audio/Minimap/Endings.
- [x] `ui/main_menu.py` — `MainMenuScreen(BaseScreen)`: `__init__(state_manager, on_quit)`; UP/DOWN циклическая навигация, ENTER — активировать; пункты New Game / Continue / Quit
- [x] New Game / Continue **заменяют** меню на GameScreen (pop меню + push GameScreen → игра на глубине 1, ESC-выход сохранён); Continue активен только при наличии файла сейва
- [x] Continue использует существующий SaveSystem через `GameScreen.load_game()` (без дублирования save-логики); Continue без сейва — нет-оп (остаёмся в меню)
- [x] Quit — переданный колбэк `on_quit` (паттерн `on_close`); в `main.py` → `Game.stop()` (новый метод, `_running=False`)
- [x] `ui/game_screen.py` — `_load_game` → публичный `load_game` (используется F9 и Continue); поведение не изменено
- [x] `main.py` — `__main__` пушит `MainMenuScreen(state_manager, game.stop)` вместо прямого `GameScreen`
- [x] `tests/test_main_menu.py` — 20 тестов
- [x] Smoke (headless): меню → New Game → GameScreen (depth 1); сейв → Continue → xp восстановлен; Quit → колбэк

### Тесты — 755 тестов, все зелёные ✅ (после Спринта 10E)
+20 тестов в `tests/test_main_menu.py`:
- Меню: BaseScreen; первый пункт выбран; циклические UP/DOWN; игнор не-KEYDOWN
- New Game: ENTER запускает GameScreen; меню заменено (depth 1)
- Continue: без сейва — нет-оп (остаёмся в меню); с сейвом — запускает GameScreen; состояние загружено (xp)
- Quit: ENTER вызывает on_quit-колбэк; не запускает игру
- Отрисовка: draw без/с сейвом (Continue приглушён); update нет-оп
- Интеграция: меню — вершина стека; `state_manager is None` безопасен
- Регрессии: GameScreen строится и рисуется; F9-загрузка работает (после переименования `load_game`)

### Спринт 10F — EventBus Cleanup / GameScreen Teardown ✅ (завершён)
Цель: устранить накопление подписчиков EventBus при F9 / New Game / Continue. Без изменения геймплея и без глобального рефактора EventBus (его `off` уже есть).
- [x] Фактическая картина: на один GameScreen — 6 подписок (GameScreen ×4: entity_died/dialogue_ended/dialogue_choice_selected/boss_defeated; Player ×1: player_level_up; QuestSystem ×1: entity_died). DialogueSystem/LoreSystem не подписываются (только эмитят)
- [x] `ui/base_screen.py` — `cleanup()` (нет-оп по умолчанию) как lifecycle-хук
- [x] `main.py` — `GameStateManager.pop` вызывает `screen.cleanup()` при снятии экрана
- [x] `ui/game_screen.py` — `cleanup()` (идемпотентно, флаг `_cleaned`): снимает свои 4 подписки + подписки текущих player/quest_system; helper `_detach_systems(player, quest_system)`
- [x] `ui/game_screen.py` — `load_game` (F9): перед swap снимает подписки СТАРЫХ player/quest_system → повторные загрузки не копят обработчики
- [x] QuestSystem/Player НЕ модифицированы: их bound-методы снимаются через `EventBus.off` из GameScreen (равенство bound-методов позволяет `list.remove`)
- [x] `tests/test_eventbus_cleanup.py` — 17 тестов

### Спринт 11C — Sprite Rendering Pipeline ✅ (завершён)
Цель: первый графический пайплайн — подключаемые PNG-спрайты для сущностей и тайлов, с сохранением fallback на pygame.draw. Только статические изображения (без анимаций/sprite sheets/направлений/состояний).
- [x] `systems/asset_loader.py` — `AssetLoader`: `get(name)` грузит `SPRITES_DIR/<name>.png` через `pygame.image.load().convert_alpha()`, кэширует (повторный запрос — тот же объект); отсутствующий файл → None (negative cache, без повторных загрузок и падений); `convert_alpha` защищён (без видеорежима отдаёт raw); `draw_sprite(surface,name,rect)→bool`; `clear()`
- [x] Сущности: `SPRITE`-атрибут + «спрайт или fallback» в `draw` — Player (`player`), WalkerZombie (`zombie_walker`), RunnerZombie (`zombie_runner`), SpitterZombie (`zombie_spitter`), PatientZeroBoss (`boss`). HP-бары рисуются поверх как раньше
- [x] `GameWorld.draw` — тайлы `tile_wall`/`tile_floor` спрайтом, иначе прежний цветной rect
- [x] `tests/conftest.py` — autouse-очистка кэша спрайтов (как у EventBus)
- [x] Fallback сохранён: спрайтов в проекте нет → `get()` даёт None → рендер идентичен прежнему → существующие тесты зелёные
- [x] `tests/test_asset_loader.py` — 18 тестов
- [x] Smoke: без ассетов New Game рисуется (fallback) и геймплей идёт; с реальным PNG спрайт грузится/кэшируется и виден (player.rect.center = красный); выстрел работает

### Тесты — 934 теста, все зелёные ✅ (после Спринта 11C)
+18 тестов в `tests/test_asset_loader.py`:
- AssetLoader: загрузка PNG; кэш (тот же объект); отсутствующий файл → None; negative-cache; имя None → None; clear(); draw_sprite True+blit / False при отсутствии
- Сущности: Player/WalkerZombie/Boss рисуются спрайтом при наличии файла и fallback-примитивом (по COLOR) при отсутствии — проверка по пикселю центра
- Тайлы: GameWorld.draw использует тайловые спрайты при наличии и не падает без них
- Регрессия: в проекте спрайтов нет → все get() = None; полный world.draw без ассетов без исключений

### Спринт 11B — TMX Spawn Objects (Phase 2) ✅ (завершён)
Цель: перенести размещение игровых объектов (игрок/враги/босс/предметы) из захардкоженных координат `GameScreen` в TMX object-слой `spawns`. Завершает переход к data-driven level design. Только источник данных; игровые системы не менялись.
- [x] Эмпирически проверено: pytmx читает object-слой (`.name`/`.x`/`.y` float); отсутствие слоя → `ValueError` (ловим → пустой список)
- [x] `data/spawn_point.py` — `@dataclass SpawnPoint(name, x, y)` (слой data)
- [x] `assets/maps/level1.tmx` — добавлен object-слой `spawns` с 10 точками (player_start / 2×enemy_walker / enemy_runner / enemy_spitter / boss / 4 item_id), координаты = прежним захардкоженным → паритет. Слой `collision` не тронут (паритет 11A сохранён)
- [x] `systems/game_world.py` — `load_spawns_from_tmx(path)` + `GameWorld.spawns`. Контракт `wall_rects`/`draw`/`pixel_*` неизменен
- [x] `ui/game_screen.py` — удалены `_START_X/_START_Y` и все координаты уровня (`_spawn_enemies`/`_spawn_boss`/`_spawn_items` строят из `self._world.spawns`); `_fresh_systems` (F9/load) берёт player_start из карты; маппинг `_ENEMY_SPAWNS` (токен→класс+конфиг). Реальные item_id (без выдуманного medkit — по инструкции спринта); категория (food/quest) — из items.json
- [x] Не тронуты: CombatSystem/EventBus/SaveSystem/Entity/Weapon/Boss AI/Skill/Quest/Inventory/UI-flow. Удалены неиспользуемые импорты `cast`/`TILE_SIZE`
- [x] `tests/test_game_world_spawns.py` — 14 тестов
- [x] Smoke (New Game → spawns из TMX): player (400,208), 4 врага [Walker,Walker,Runner,Spitter], boss (1392,592), 4 предмета (2 food/2 quest), выстрел даёт пулю

### Тесты — 916 тестов, все зелёные ✅ (после Спринта 11B)
+14 тестов в `tests/test_game_world_spawns.py`:
- Загрузка спавнов: level1 даёт 10 точек; player_start/enemy_*/boss/item_id присутствуют; float-координаты; отсутствие слоя → пустой список
- Интеграция GameScreen: игрок/враги(4)/босс/предметы(4: 2 food+2 quest) создаются из TMX в нужных координатах
- Паритет: счётчики совпадают со старым уровнем
- Кастомные карты: позиция игрока и число врагов задаются ТОЛЬКО TMX-файлом (Python не меняется)

### Спринт 11A — TMX Geometry Pipeline (Phase 1) ✅ (завершён)
Цель: перевести источник геометрии уровня `_build_grid()` → `level1.tmx` → `wall_rects`, сохранив публичный API `GameWorld`. Только геометрия; спавны/NPC/триггеры/переходы/спрайты/аудио — вне скоупа (Phase 2+).
- [x] Эмпирически проверено: `pytmx.TiledMap(path)` парсит image-less TMX (только данные слоя, без загрузки картинок) — рендер остаётся примитивами
- [x] `assets/maps/level1.tmx` сгенерирован из `_build_grid()` (50×24, gid 1=стена) → **байт-точный паритет** старой сетке → существующие тесты `test_game_world.py` не трогались
- [x] `systems/game_world.py`: `load_grid_from_tmx(path)` (gid≠0→WALL); `GameWorld(map_path=level1.tmx)` грузит сетку из TMX; `_rows/_cols` — поля экземпляра (из карты), `draw`/`pixel_*`/`_compute_wall_rects` используют их. Публичный контракт (`wall_rects`/`draw`/`pixel_width`/`pixel_height`) неизменен
- [x] `_build_grid`/`_COLS`/`_ROWS` сохранены как эталон паритета (используются тестами)
- [x] Контракт `wall_rects: list[pygame.Rect]` неизменен → CombatSystem/EventBus/SaveSystem/Entity/Weapon/UI/GameScreen-flow НЕ затронуты
- [x] `tests/test_game_world_tmx.py` — 9 тестов
- [x] Headless smoke: GameScreen грузит мир из TMX (368 стен), паритет с `_build_grid` True, коллизии на месте, update+draw без падений

### Тесты — 902 теста, все зелёные ✅ (после Спринта 11A)
+9 тестов в `tests/test_game_world_tmx.py`:
- Загрузка: дефолтный мир грузится из TMX (wall_rects непусты); хелпер `load_grid_from_tmx` возвращает сетку FLOOR/WALL; явный путь карты
- Размеры: pixel_width/height = 50×24 тайлов из карты
- wall_rects: все прямоугольники размером TILE_SIZE
- Паритет: сетка из TMX == `_build_grid()`; множество стен из `wall_rects` == из `_build_grid()`
- Новый уровень из файла: кастомный 3×3 TMX (рамка+пол) и 6×4 сплошных стен задают геометрию/размер **только файлом**, без правки Python

### Спринт 10C — Release Coherence Cleanup ✅ (завершён)
Документационный спринт: синхронизировать README/CLAUDE.md/requirements с фактической реализацией, убрать мёртвые плейсхолдеры и битые ссылки. Код/тесты не менялись (893 зелёные до и после).
- [x] **Удалены мёртвые плейсхолдеры** (нигде не импортируются, подтверждено grep): `entities/npc.py`, `systems/audio.py`, 4× `assets/maps/*.tmx` (0 байт)
- [x] **README.md** переписан под реальность: статус-чеклист отмечен выполненным; управление = реальные клавиши (LMB/WASD/F/I/Tab/J/L/T/Esc/Enter/F5/F9, убраны несуществующие R/E); босс = **две фазы** (+кислота/призыв/патруль); оружие Pistol/Rifle/Shotgun; раздел «Вне скоупа v1» (4 главы/TMX/концовки/аудио/спрайты/переключение оружия); ссылки на `docs/…` и `CLAUDE-progress.md` починены; запуск через `requirements.txt`
- [x] **CLAUDE.md** синхронизирован: `pytmx` помечен «зарезервирован, в v1 не используется»; структура (maps/sprites/sounds — зарезервированы, v1 рендерит примитивами, карта в коде); таблица локаций помечена «проектный замысел — НЕ реализовано в v1»; `pip install -r requirements.txt`
- [x] **requirements.txt**: `pytmx` помечен как зарезервированный (не используется в v1)
- [x] Повторный аудит: пустых исходных `.py` (кроме `__init__`) нет; `.tmx` нет; все doc-ссылки резолвятся; упоминания pytmx/перезарядки — только в честном контексте «зарезервировано/вне скоупа»
- [x] QA после удалений: ruff/mypy/pytest зелёные (893), `mypy` теперь 99 файлов (было 101 — минус 2 удалённых)

### Спринт 10B — Weapons Polymorphism & Release Coherence ✅ (завершён)
(Не путать с ранним «10B — Save Integration». Имя задано постановкой; weapons-трек.)
Цель: реализовать Rifle и Shotgun через существующую оружейную иерархию — закрыть пустые стабы и усилить демонстрацию наследования/полиморфизма. Без изменений архитектуры.
- [x] Анализ: `Weapon(ABC)` с абстрактным `fire`; `Pistol(Weapon)` — одиночный выстрел; `WeaponConfig` из `weapons.json`; путь ЛКМ→`Player.fire`→`Weapon.fire`→`CombatSystem`. Бонус урона навыка работает для любого `Weapon` через `add_damage_bonus`
- [x] `data/weapon_config.py`: +`pellet_count: int = 1`, `spread_degrees: float = 0.0` (дефолты → обратная совместимость; pistol/rifle грузятся без новых ключей)
- [x] `assets/data/weapons.json`: +`rifle` (fire_rate 6.0 > pistol 2.0; damage 12 < 25), +`shotgun` (pellet_count 6, spread 30°, низкая скорострельность)
- [x] `entities/weapons/rifle.py` (был пуст): `Rifle(Weapon)` — одиночная пуля, отличие в параметрах конфига
- [x] `entities/weapons/shotgun.py` (был пуст): `Shotgun(Weapon)` — переопределяет `fire()`, веер `pellet_count` дробинок через существующий `Bullet`, без изменений CombatSystem
- [x] Доступны в конфигурации (`weapons.json`) и конструируемы; GameScreen-архитектура и стартовый Pistol не тронуты
- [x] `tests/test_weapons.py` — 20 тестов; обновлён 1 существующий (`test_combat.test_weapon_config_is_dataclass`: 5→7 полей)
- [x] Headless smoke: pistol 1 / rifle 1 / shotgun 6 пуль; Player+Shotgun → 6 пуль в CombatSystem; кулдаун блокирует второй залп

### Тесты — 893 теста, все зелёные ✅ (после Спринта 10B оружия)
+20 тестов в `tests/test_weapons.py`:
- Совместимость конфига: 5-полевой конфиг валиден (дефолты); все три оружия грузятся из json
- Rifle: is-a Weapon; одиночная пуля; origin=player; нулевое направление — нет-оп; кулдаун после выстрела и восстановление; бонус урона; fire_rate > pistol; damage < pistol
- Shotgun: is-a Weapon; несколько дробинок (==pellet_count); разброс (разные направления); все origin=player; урон дробинки из конфига; нулевое направление — нет-оп; кулдаун блокирует залп и восстанавливается
- Полиморфизм: единый вызов `Weapon.fire` для Pistol/Rifle/Shotgun

### Спринт 10A — Boss Patrol Outside Combat ✅ (завершён)
(Boss-трек; не путать с ранним «10A — Save System». Имя спринта задано постановкой.)
Цель: пока игрок не обнаружен, босс патрулирует точки вокруг спавна; обнаружение немедленно прекращает патруль, потеря игрока — возобновляет. Только `settings.py` + `entities/boss.py`, без новых систем/singleton.
- [x] Фактическая проверка: движение босса было лишь в ветке `_detect_player` (`update`), вне обнаружения босс стоял; `player is None` — ранний выход
- [x] `settings.py`: `BOSS_PATROL_RADIUS=96`, `BOSS_PATROL_SPEED_FACTOR=0.5`, `BOSS_PATROL_ARRIVE_DIST=8`
- [x] `entities/boss.py` (`PatientZeroBoss`): `_patrol_anchor` (копия spawn-позиции, фиксируется до движения), `_patrol_points` (4 точки вокруг якоря — «несколько точек»), `_patrol_index`; property `patrol_target`; метод `_patrol` (движение к точке через существующий `_move_toward` со сниженной скоростью, циклический переход по достижении). В `update` — ветка `else: self._patrol(...)` (срабатывает при игроке≠None, но не обнаруженном)
- [x] Паттерн взят у `Zombie._patrol` (сниженная скорость, общий `_move_toward` с коллизиями стен); `player is None` остаётся ранним выходом — патруль только при наличии игрока
- [x] Обновлён существующий тест `test_boss_ai`: `test_does_not_move_when_player_out_of_range` → `test_patrols_when_player_out_of_range` (босс теперь двигается); `test_no_player_is_safe` сохранён (None → не патрулирует)
- [x] `tests/test_boss_patrol.py` — 17 тестов
- [x] Headless smoke: патруль вне боя → обнаружение прекращает патруль (погоня) → потеря игрока возобновляет патруль; acid при обнаружении и `boss_defeated` не сломаны

### Тесты — 873 теста, все зелёные ✅ (после Спринта 10A boss-патруля)
+17 тестов в `tests/test_boss_patrol.py`:
- Создание: якорь = спавн; ≥3 точек; первая цель = якорь + точка[0]
- Движение: двигается вне обнаружения; к первой точке; держится у якоря (200 кадров ≤ radius+допуск); обходит несколько точек циклически; без игрока не патрулирует
- Переходы: обнаружение прекращает патруль и переходит в погоню; потеря игрока возобновляет патруль
- Регрессии: melee; acid/summon при обнаружении; патруль не спавнит спецатак; переключение фаз; `boss_defeated`; патруль уважает стены
(Обновлён 1 ранее существовавший тест под новое поведение — не удалён, перенацелен.)

### Спринт 9G — Boss Encounter Tuning ✅ (завершён)
Цель: закрыть локальные шероховатости поведения босса с минимальным риском, без новой архитектуры. Только `settings.py` + `entities/boss.py` (+ синхронизация тестов).
- [x] XP за босса: `BOSS_XP_REWARD=200` в settings; `Boss.xp_reward` берёт его (было 0). Идёт существующим путём `_on_entity_died` (entity.xp_reward), без новой системы наград
- [x] Гейт кислоты и призыва: блок Phase 2 в `update` обёрнут существующим `self._detect_player(player_pos)` — спецатаки только при обнаруженном игроке (тот же радиус, что у melee/преследования; без отдельной системы агро)
- [x] Прунинг миньонов: `summon_minion` перед добавлением фильтрует `_summoned` по `active` — список не копит трупы, лимит (`can_summon`/`BOSS_SUMMON_MAX`) не изменён
- [x] Docstring `PatientZeroBoss` обновлён: кислота (9E) и призыв (9F) описаны как реализованные, а не «будущие»
- [x] Синхронизация существующих тестов под новое поведение: `test_boss_ai.test_xp_reward_from_settings` (==BOSS_XP_REWARD), `test_boss_integration.test_boss_death_grants_xp` (==BOSS_XP_REWARD), GameScreen-интеграция в `test_boss_ranged_attack`/`test_boss_summon` — игрок ставится в радиус обнаружения; лимит-тесты `test_boss_summon` используют co-located игрока (босс стоит на месте, всегда обнаружен при больших dt)
- [x] `tests/test_boss_tuning.py` — 14 тестов
- [x] Headless smoke: вне detection — 0 кислоты/0 призыва; внутри — 1/1; убийство босса в GameScreen даёт 200 XP

### Тесты — 856 тестов, все зелёные ✅ (после Спринта 9G)
+14 тестов в `tests/test_boss_tuning.py`:
- XP: `xp_reward == BOSS_XP_REWARD`; положителен
- Гейт кислоты: вне detection не стреляет; внутри — 1 снаряд
- Гейт призыва: вне detection не призывает; внутри — 1 WalkerZombie
- Прунинг: мёртвый миньон не учитывается (`_active_minions`); слот освобождается и `_summoned` ограничен (1 живая после прунинга); контракт `BOSS_SUMMON_MAX` сохранён (MAX+5 попыток → MAX)
- Регрессии: melee при обнаружении; фаза 1 не использует спецатаки; переключение фазы на 50% HP
(Также обновлены 4 ранее существовавших теста под новое поведение XP/гейта — не ослаблены, перенацелены на новый контракт.)

### Спринт 9F — Patient Zero Minion Summon (Phase 2) ✅ (завершён)
Цель: во второй фазе (HP≤50%) босс периодически призывает заражённых рядом с собой. Только существующие типы зомби, без новой системы спавна/типов миньонов.
- [x] Фактическая проверка: `WalkerZombie(x, y, EnemyData)` требует конфиг; у босса его нет, JSON в entity-слое нарушил бы слои. Расхождение задача↔код решено инъекцией `EnemyData` в `PatientZeroBoss(minion_config=None)` — босс строит реальные WalkerZombie из готового dataclass
- [x] `settings.py` — `BOSS_SUMMON_COOLDOWN`, `BOSS_SUMMON_MAX` (рядом с прочими `BOSS_*`; без BossData/JSON)
- [x] `entities/boss.py` (`PatientZeroBoss`): опц. `minion_config`; `_summon_timer`, `_pending_minions`, `_summoned`; `can_summon` (конфиг + кулдаун + лимит живых `_active_minions()`); `summon_minion` (WalkerZombie у `pos.x+TILE_SIZE`, в очередь + учёт ссылки); `collect_spawned_minions` (слив очереди, паттерн `collect_spawned_bullets`). Ветка Phase 2 в `update` — кислота и призыв, каждый по своему кулдауну, под общим гейтом `is_alive and phase==2`
- [x] `ui/game_screen.py` — `_spawn_boss` передаёт walker-конфиг боссу; в `update` после `boss.update` — `self._enemies.extend(self._boss.collect_spawned_minions())`. CombatSystem/EventBus/Zombie не менялись
- [x] XP за миньонов работает «бесплатно»: WalkerZombie `faction='enemy'`, `_on_entity_died` уже начисляет `xp_reward`
- [x] `tests/test_boss_summon.py` — 24 теста
- [x] Headless smoke: phase 2 → миньон появился в `_enemies` (4→5) → его AI обновляется (state=ATTACK) → получает урон от пули игрока через CombatSystem (80→70)

### Тесты — 844 теста, все зелёные ✅ (после Спринта 9F)
+24 теста в `tests/test_boss_summon.py`:
- Создание: пустая очередь; `collect_spawned_minions` есть; очередь сливается; `can_summon` True с конфигом / False без
- Фазы: Phase 1 не призывает; Phase 2 призывает WalkerZombie; без конфига/без игрока/мёртвый босс — не призывает
- Кулдаун: повторный призыв в пределах кулдауна блокируется; после истечения — снова
- Лимиты: соблюдён `BOSS_SUMMON_MAX` одновременно; не растёт бесконечно (20 попыток → MAX); слот освобождается при гибели миньона
- Интеграция: GameScreen получает врага (+1); миньон участвует в update (state→ATTACK), в draw (не падает), в CombatSystem (пуля игрока ранит)
- Регрессии: melee фазы 1; кислота фазы 2; `boss_defeated` один раз; victory/game_over

### Спринт 9E — Patient Zero Acid Attack (Phase 2) ✅ (завершён)
Цель: дальнобойная кислотная спец-атака `PatientZeroBoss` во второй фазе (HP≤50%), периодический плевок по игроку. Через существующие паттерны, без новой архитектуры снарядов.
- [x] Фактическая проверка: `AcidBullet` уже есть (`entities/bullet.py`), переиспользован напрямую — новый класс снаряда НЕ создан. Контракт Bullet не менялся
- [x] `settings.py` — `BOSS_ACID_COOLDOWN/DAMAGE/SPEED/RANGE/SIZE` (рядом с прочими `BOSS_*`). Обоснование: CLAUDE.md требует константы в settings и запрещает магию; задача запрещает BossData/JSON → settings единственный совместимый дом
- [x] `entities/boss.py` (`PatientZeroBoss`): `_acid_timer`, `_pending_bullets`, `can_spit`, `spit_acid` (зеркало `SpitterZombie.attack`: нормализация направления, `AcidBullet(origin_tag='enemy')`, очередь), `collect_spawned_bullets` (слив очереди). В `update` — декремент `_acid_timer` + ветка Phase 2: `is_alive and phase==2 and can_spit` → плевок по отдельному кулдауну. Melee/преследование/фазы 9D не тронуты
- [x] `ui/game_screen.py` — после `boss.update` собираем `self._boss.collect_spawned_bullets()` в combat (как для зомби, одна строка). CombatSystem/EventBus не менялись
- [x] `tests/test_boss_ranged_attack.py` — 23 теста
- [x] Headless smoke: GameScreen → босс в Phase 2 → spit → CombatSystem → игрок получает 15 урона (100→85); полный `GameScreen.update` тоже собирает пули босса

### Тесты — 820 тестов, все зелёные ✅ (после Спринта 9E)
+23 теста в `tests/test_boss_ranged_attack.py`:
- Создание: пустая очередь снарядов; `collect_spawned_bullets` есть; `can_spit` изначально True; возвращается list
- Спавн: Phase 1 не плюётся; Phase 2 спавнит AcidBullet; без игрока — нет; мёртвый босс (0%HP→phase2) — нет (гейт `is_alive`); collect сливает очередь; нулевое направление — нет-оп
- Направление: летит вниз/вправо к игроку; диагональ нормализована (dx≈dy)
- Кулдаун: повторный выстрел в пределах кулдауна блокируется; после истечения — снова стреляет
- Интеграция: GameScreen собирает пули босса в CombatSystem; реальный Player получает урон от кислоты; melee фазы 1 продолжает работать; `origin_tag='enemy'` и `damage=BOSS_ACID_DAMAGE`
- Регрессии: `boss_defeated` эмитится один раз; victory/game_over работают; Phase 1 поведение прежнее (погоня, без снарядов)

### Спринт 10G — Pause Menu / завершение жизненного цикла сессии ✅ (завершён)
Цель: устранить игровые тупики (ESC убивал приложение; из Game Over/Victory нет выхода) и дать штатный Save через UI. Минимальный вертикальный срез на существующем стеке экранов, без новых менеджеров/систем/данных.
- [x] `ui/pause_menu.py` (был пустой стаб) — `PauseMenuScreen`: оверлей Resume/Save Game/Main Menu/Quit; UP/DOWN (циклически), ENTER, ESC→Resume. Стиль MainMenu + полупрозрачный overlay (как SkillTreeUI/QuestLogUI). Не владеет логикой — 4 колбэка (паттерн `on_close`)
- [x] `ui/game_screen.py` — опц. параметр `on_quit` (default нет-оп → тесты не ломаются); ESC→`_open_pause_menu` (push PauseMenuScreen); `_return_to_main_menu` (снимает оверлей+GameScreen через pop→cleanup, push свежий MainMenuScreen); терминальный guard в `handle_event`: при victory/game_over активен только ENTER→`_return_to_main_menu`, прочий ввод игнорируется
- [x] `ui/game_screen.py` — Save из паузы идёт через существующий `_save_game` (тот же путь, что F5) — без дублирования save-логики
- [x] `main.py` — ESC делегируется активному экрану; приложение завершается лишь если ESC нажат на корневом экране И тот не открыл оверлей (`at_root до` и `depth<=1 после`). Main Menu (ESC→quit) не менялся; GameScreen открывает паузу, оверлеи закрываются — без выхода
- [x] `ui/main_menu.py` — проброс `self._on_quit` в `GameScreen(...)` (New Game/Continue), чтобы Quit/Main Menu из паузы работали
- [x] `tests/test_pause_menu.py` — 25 тестов
- [x] Headless smoke: New Game→ESC→пауза→Resume; пауза→Main Menu; Game Over→ENTER→Main Menu; Quit→колбэк. Все переходы и глубины стека верны

### Тесты — 797 тестов, все зелёные ✅ (после Спринта 10G)
+25 тестов в `tests/test_pause_menu.py`:
- PauseMenu (unit): BaseScreen; стартовый индекс; UP/DOWN циклически (4 пункта); игнор не-KEYDOWN; ENTER на каждом пункте зовёт свой колбэк; ESC→Resume; draw/update без падения
- Интеграция GameScreen↔пауза: ESC открывает PauseMenu (depth 2); Resume возвращает в игру (depth 1); Save Game пишет файл (фикстура `save_path`); Main Menu → MainMenuScreen (depth 1); Quit зовёт `on_quit`; `state_manager is None` безопасен
- Терминальные состояния: Game Over+ENTER→Main Menu; Victory+ENTER→Main Menu; терминал игнорирует прочий ввод (I, ЛКМ)
- Регрессии/утечки: возврат в меню снимает все подписки EventBus (→0); терминальный выход тоже (→0); повторные сессии не копят подписчиков

### Тесты — 772 теста, все зелёные ✅ (после Спринта 10F)
+17 тестов в `tests/test_eventbus_cleanup.py`:
- Подписки: GameScreen регистрирует 6; entity_died имеет 2 слушателя
- Cleanup: снимает все подписки (→0); идемпотентен
- Повторное создание: create→cleanup→create не растит счётчик; 5 циклов чисты
- pop(): pop GameScreen вызывает cleanup (→0); pop обычного BaseScreen безопасен
- F9: 5 загрузок держат счётчик стабильным; player_level_up=1, entity_died=2 после нескольких load
- Continue/New Game: 3 цикла не накапливают (макс 6, после pop →0)
- Регрессии: quest-прогресс; диалог (T); victory; game over; XP за килл после F9 начисляется один раз

### Тесты — 483 теста, все зелёные ✅ (после Спринта 8F)
+14 тестов в `tests/test_dialogue_integration.py`:
- Загрузка: диалоги доступны GameScreen, корректный стартовый узел
- Открытие: T → DialogueUI, push ровно одного экрана, диалог активен, UI использует тот же экземпляр DialogueSystem
- Закрытие: завершение диалога → возврат в GameScreen; ESC закрывает оверлей и возвращает в игру; ESC не завершает состояние диалога
- Поведение: повторное открытие перезапускает диалог; неизвестный id безопасен; `state_manager is None` безопасен; неактивный диалог не ломает update/draw
- Интеграция: полный сценарий T → выбор → терминал → завершение → возврат

### Тесты — 469 тестов, все зелёные ✅ (после DialogueUI в 8E.2)
+25 тестов в `tests/test_dialogue_ui.py`:
- Инициализация: наследование BaseScreen, начальный индекс, неактивная система (пустой диалог)
- Навигация: UP/DOWN, циклическая, один вариант, терминальный узел (индекс 0), неактивная система, игнор не-KEYDOWN
- Выбор: ENTER → choose первого/второго варианта, сброс индекса после перехода, ENTER на терминале → завершение, безопасность на неактивной системе
- Закрытие: ESC → on_close ровно один раз; ESC не завершает диалог (владелец — DialogueSystem)
- Отрисовка: draw без падения, терминальный узел, неактивная система, пустые тексты вариантов, update
- Интеграция: полный проход start → выбор → терминал → завершение; линейный диалог с одним вариантом

### Тесты — 444 теста, все зелёные ✅ (после DialogueLoader в 8E.1)
+25 тестов в `tests/test_dialogue_loader.py`:
- Успешная загрузка: поля Dialogue, nodes как map, choices, терминальный узел, дефолт next_id, прогон загруженного диалога в DialogueSystem
- Несколько диалогов; пустой список `dialogues` → []
- Ошибки: нет файла, битый JSON, не-объект, нет ключа `dialogues`, `dialogues` не список, нет поля диалога/узла, `nodes`/`choices` не список, choice без `text`, висячий start_id, висячая ссылка в choice, дубли id узлов, пустой диалог (нет узлов)
- Реальный `assets/data/dialogues.json`: грузится, start_id валиден, проходится до конца

### Тесты — 419 тестов, все зелёные ✅ (после DialogueSystem в 8E)
+32 теста в `tests/test_dialogue.py`:
- DialogueChoice / DialogueNode / Dialogue: поля, дефолты, `is_terminal`
- start: активация, стартовый узел, ошибка при отсутствии start_id, события started + node_changed
- advance: переход по линии, завершение на терминальном узле, событие node_changed, ошибка без активного диалога, ошибка при нескольких выборах, пустой next_id → end
- choose: первая/вторая ветка, индекс вне диапазона, отрицательный индекс, без активного диалога, висячая ссылка, пустой next_id → end
- end: очистка состояния, событие ended, нет-оп без активного диалога
- Integration: полный проход с ветвлением и порядком событий; перезапуск после end

### Спринт 9 — Финальный босс
- [x] `entities/boss.py` — базовый `Boss(Entity)` + `PatientZeroBoss` — **ядро** (9B): HP, faction, урон, смерть, `boss_defeated`
- [x] Интеграция босса в GameScreen (9C): спавн в Комнате 4, combat/урон/смерть, победное состояние по `boss_defeated`
- [x] AI босса (9D): преследование игрока, ближняя атака по кулдауну, 2 фазы (HP<=50% → быстрее + ниже кулдаун)
- [x] Кислотная спец-атака фазы 2 (9E): дальнобойный AcidBullet по отдельному кулдауну, по образцу SpitterZombie
- [x] Призыв миньонов фазы 2 (9F): WalkerZombie рядом с боссом, отдельный кулдаун + лимит одновременно живых
- [x] Тюнинг боя (9G): XP за босса (`BOSS_XP_REWARD`), спецатаки только при обнаруженном игроке, прунинг мёртвых миньонов
- [x] Патруль вне боя (10A): обход точек вокруг спавна, пока игрок не обнаружен; прерывается обнаружением, возобновляется при потере
- [ ] Экран/катсцена победы, концовки (хорошая/плохая) — будущий спринт
- [ ] `assets/maps/eden7.tmx` — арена финального боя
- [ ] Логика концовок: хорошая / плохая

### Спринт 10 — Полировка
- [x] `systems/save_system.py` — сохранение / загрузка JSON (10A: ядро; без меню/слотов/интеграции)
- [x] Интеграция SaveSystem в GameScreen (10B): F5 — сохранить, F9 — загрузить, один файл
- [ ] Слоты сохранений, меню сохранений — будущий спринт
- [x] `ui/main_menu.py` — главное меню (10E): New Game / Continue / Quit, один файл сейва (слоты — будущее)
- [x] `ui/pause_menu.py` — меню паузы (10G): ESC→Resume/Save Game/Main Menu/Quit; выход из Game Over/Victory в меню по ENTER
- [ ] `systems/audio.py` — SFX и музыка
- [x] Game Over (10D): поражение при смерти игрока + заморозка victory/game_over в `update`; «GAME OVER» оверлей
- [x] HUD (10C): HP-бар, бар голода, уровень/XP, трекер квестов (`ui/hud.py`); миникарта — отложена
- [ ] Миникарта (отдельный спринт)
- [ ] Финальное тестирование прохождения 25–35 мин

---

## Архитектурные решения (лог)

| Дата | Решение | Причина |
|---|---|---|
| 2026-06-10 | EventBus вместо прямых зависимостей | развязать системы между собой |
| 2026-06-10 | Стек экранов вместо булевых флагов | чистое управление состоянием |
| 2026-06-10 | JSON-конфиги для всех данных | нет магических чисел, легко балансировать |
| 2026-06-10 | pygame-ce вместо pygame | активно поддерживается, лучше производительность |
| 2026-06-10 | `HealthComponent` как отдельный класс | демонстрация композиции; Entity делегирует, не хранит int |
| 2026-06-10 | `entity.health` возвращает `HealthComponent` | `player.health.percentage` готово для HP-бара в HUD |
| 2026-06-10 | EventBus-события остались в Entity, не в HealthComponent | компонент чистый; Entity оркестрирует побочные эффекты |
| 2026-06-10 | `GameStateManager` в `main.py`, `GameScreen` пушится снаружи | `Game` остаётся generic, не знает о конкретных экранах |
| 2026-06-10 | `take_damage/heal` принимают `float` вместо `int` | дробный урон от голода (hunger_damage_rate * dt); `int` — частный случай `float` |
| 2026-06-10 | `HungerComponent` не знает о `HealthComponent` | связь только через `Player.update()`: голод → `is_starving` → `take_damage()` → EventBus |
| 2026-06-11 | `Zombie(Entity, ABC)` — ABC добавлен к Zombie, не к Entity | Entity остаётся чистым; Python корректно разрешает metaclass ABCMeta |
| 2026-06-11 | Template Method в `Zombie.update()` | декремент таймера + вызов `update_ai()` — общая логика один раз; подклассы реализуют только хук |
| 2026-06-11 | `AIState` enum в `entities/zombie.py`, не в `core/` | состояния AI релевантны только врагам; Boss в Sprint 9 может полностью игнорировать enum |
| 2026-06-11 | SpitterZombie перенесён в Sprint 5 (с Combat) | SpitterZombie нужен Bullet; реализация вместе с Combat-системой исключает временный код |
| 2026-06-11 | Патруль через таймер (3 сек → разворот), не через детекцию стены | детекция стены при малом dt ненадёжна из-за целочисленного rounding; таймер детерминирован |
| 2026-06-11 | `Weapon(ABC)` в `core/`, не GameObject | оружие — не позиционированный объект; ABC достаточно; TYPE_CHECKING для Bullet избегает core→entities |
| 2026-06-11 | `Targetable` Protocol в `systems/combat.py` | CombatSystem не зависит от Zombie/Player; любой объект с active+pos+rect+take_damage подходит |
| 2026-06-11 | AABB через `Bullet.rect.colliderect(target.rect)` | точнее distance-based; rect вычисляется on-the-fly из pos+size |
| 2026-06-11 | `Player.fire(direction) → list[Bullet]` | Player владеет оружием (композиция); GameScreen только даёт направление и передаёт пули в CombatSystem |
| 2026-06-11 | `faction: str` на Entity; "player" / "enemy" на подклассах | один CombatSystem для всех пуль; фильтр `origin_tag == faction` предотвращает friendly fire |
| 2026-06-11 | `collect_spawned_bullets() → list[Bullet]` на Zombie (default []) | SpitterZombie накапливает пули в `_pending_bullets`; GameScreen дренирует после каждого update — без EventBus и без каскада сигнатур |
| 2026-06-11 | `SpitterData(EnemyData)` с 4 доп. полями | иерархия данных отражает иерархию сущностей; Walker/Runner не получают spitter-поля |
| 2026-06-11 | `Targetable.rect` как `@property` в Protocol | `rect` read-only в Zombie/Player; property в Protocol устраняет mypy incompatibility |
| 2026-06-11 | `Item(GameObject, ABC)` в `core/` | предмет — позиционированный объект с draw(); ABC для абстрактного use(); паттерн повторяет Zombie(Entity, ABC) |
| 2026-06-11 | `Inventory.use_item(item, player)` с player как параметр | Inventory не хранит ref на Player; Player передаёт self → нет хранимой зависимости; TYPE_CHECKING устраняет circular import |
| 2026-06-11 | Подбор предметов через `colliderect` в GameScreen, автоматически | нет отдельной клавиши подбора; ходить над предметом = подобрать; F — использовать первый доступный предмет (полиморфизм: quest пропускается, food применяется) |
| 2026-06-11 | `entities/items/` субпакет для FoodItem и QuestItem | следует паттерну `entities/weapons/`; отдельная папка для подтипов одной категории |
| 2026-06-11 | `player_level_up` EventBus → `_on_level_up` → `add_point()` | ExperienceComponent эмитит событие для каждого level-up в while-цикле; подписка корректно начисляет N очков при N level-up за один вызов add_xp |
| 2026-06-11 | `_damage_bonus: float` в Weapon + `Pistol.fire()` суммирует `config.damage + _damage_bonus` | SkillTree не зависит от Pistol; Player.apply_weapon_damage_bonus() делегирует weapon; weapon хранит накопленный бонус |
| 2026-06-11 | Публичные константы `HP_PER_LEVEL`, `DAMAGE_PER_LEVEL` и др. в `skill_tree.py` | доступны из тестов без дублирования магических чисел; аналогично `settings.py` паттерну |
| 2026-06-11 | `_apply_effect` if/elif на `SkillType` enum (не isinstance) | SkillType конечен и контролируем; dispatch dict создал бы circular import на уровне модуля |
| 2026-06-11 | `SkillTreeUI(player, on_close: Callable)` вместо зависимости на GameStateManager | GameStateManager в main.py; callable избегает circular import; тесты передают lambda |
| 2026-06-11 | Lazy import `from ui.skill_tree_ui import SkillTreeUI` внутри метода в GameScreen | GameScreen не импортирует SkillTreeUI на уровне модуля; Tab-нажатие — редкое событие; исключает circular import |
| 2026-06-11 | `state_manager: Any = None` в GameScreen.__init__ | default None сохраняет обратную совместимость; Any исключает зависимость GameScreen→main |
| 2026-06-11 | `GameStateManager.depth <= 1` как условие выхода по ESC | depth>1 означает открытый оверлей (SkillTreeUI и любой будущий); при depth=1 ESC завершает игру как раньше |
| 2026-06-11 | `Objective.on_kill(faction: str)` с default no-op в базовом классе | QuestSystem вызывает `obj.on_kill(faction)` полиморфно для всех целей без isinstance; будущие цели (не про убийства) наследуют no-op |
| 2026-06-11 | `QuestSystem` подписывается на `entity_died`, не на гипотетический `zombie_killed` | `entity_died` — существующее событие; faction=="enemy" отфильтровывает не-зомби; нет необходимости в новом событии |
| 2026-06-11 | `QuestSystem._try_complete` пропускает квест без целей | квест с пустым `objectives` не завершается автоматически; требует `complete_quest()` — предотвращает мгновенное завершение незаполненных квестов |
| 2026-06-11 | `update_progress(event_data: dict)` публичный — `_on_entity_died` делегирует ему | публичный метод позволяет тестировать прогресс без EventBus; EventBus-подписка остаётся внутренней деталью |
| 2026-06-11 | `Objective.progress` (abstract property) → str вместо isinstance в UI | UI отображает "3/5" полиморфно; `current_count`/`target_count` есть только у KillZombieObjective; isinstance запрещён CLAUDE.md; абстракция отдаёт готовую строку |
| 2026-06-11 | `QuestLogUI(quest_system, on_close)` — держит ref на QuestSystem, читает `active_quests` в draw | не дублирует состояние квестов; `active_quests` возвращает копию → UI физически не может мутировать внутренний список; повторяет паттерн `SkillTreeUI(player, on_close)` |
| 2026-06-11 | Клавиша J → QuestLogUI через lazy import в GameScreen | повторяет Tab→SkillTreeUI (Sprint 7C): GameScreen не импортирует UI на уровне модуля; depth>1 корректно обрабатывает ESC |
| 2026-06-11 | Стартовый квест инлайн в `GameScreen._make_starter_quest()` | параллель `_spawn_enemies()` (позиции спавна тоже инлайн в GameScreen); JSON-загрузчик квестов отложен до Спринта 8C; Sprint 8B = только UI отображения |
| 2026-06-11 | `quests.json` в `assets/data/`, не в `data/` | CLAUDE.md и все JSON-конфиги (enemies/items/weapons/player) лежат в `assets/data/`; там уже был пустой стаб `quests.json`; `data/` — пакет Python-структур. Репозиторий — источник истины, конвенция важнее буквального текста задачи |
| 2026-06-11 | `data/quest_loader.py` — отдельный модуль `load_quests(path) → list[Quest]` | загрузчик зависит только от `quest_data` (+ json/pathlib); НЕ зависит от UI и QuestSystem; чистое преобразование JSON→объекты; GameScreen передаёт `DATA_DIR/quests.json` |
| 2026-06-11 | `QuestLoadError` — единый тип ошибки загрузки | отсутствие файла, повреждённый JSON, неизвестный тип цели, нехватка полей — всё оборачивается в один тип; тестам и вызывающему коду достаточно ловить `QuestLoadError` |
| 2026-06-11 | `_OBJECTIVE_BUILDERS: dict[str, Callable]` (type → builder) | data-driven диспетчер без isinstance; новый тип Objective = одна строка в dict; builder-функции локальны в модуле → нет circular import (в отличие от skill_tree, где dict на уровне модуля создавал бы цикл) |
| 2026-06-11 | narrative-поля `lore_text/location/category` опциональны (default `""`), НЕ в `_REQUIRED_QUEST_FIELDS` | обратная совместимость: старые квесты без полей грузятся; loader читает через `.get(..., "")`; данные остаются data-driven, без хардкода в коде |
| 2026-06-11 | QuestSystem не читает narrative-поля; только QuestLogUI отображает их (`_format_meta`) | разделение: метаданные — для отображения, не для логики прохождения; UI рисует строку только если поля непусты — нет мусора у старых квестов |
| 2026-06-12 | Диалоги: `data/dialogue_data.py` (dataclasses) + `systems/dialogue.py` (рантайм) | прямая аналогия quest: `quest_data.py` + `quest_system.py`. Слой данных — обязательный нижний слой по CLAUDE.md (data → systems), не расширение скоупа |
| 2026-06-12 | Диалог как граф `dict[str, DialogueNode]` + `start_id`, переходы по `next_id` | ветвление и линейный диалог одной моделью; `next_id == ""` = конец; узел без choices = терминальный (`is_terminal`) |
| 2026-06-12 | `advance()` (0–1 выбор) vs `choose(index)` (ветвление); ветвление по `len(choices)`, не isinstance | isinstance запрещён CLAUDE.md; `advance()` при >1 выборе поднимает DialogueError — caller обязан вызвать `choose()` |
| 2026-06-12 | `DialogueSystem` сообщает о состоянии только через EventBus (`dialogue_started/node_changed/ended`) | UI и прочие системы подписываются; нет прямых импортов UI в системе — как QuestSystem эмитит `quest_completed` |
| 2026-06-12 | JSON-загрузчик диалогов и UI вынесены из задачи | повторяет инкремент quest: 8B (UI) и 8C (loader) делались отдельно; данная задача — только рантайм-система + слой данных |
| 2026-06-12 | `data/dialogue_loader.py` — `load_dialogues(path) → list[Dialogue]` + `DialogueLoadError` | прямая копия паттерна `quest_loader`: чистое преобразование JSON→объекты, зависит только от `dialogue_data` (+json/pathlib), не зависит от DialogueSystem/UI |
| 2026-06-12 | `nodes` в JSON — список объектов с `id`; loader строит `dict[str, DialogueNode]` | формат удобен для редактирования; loader превращает в map (как ожидает `Dialogue`); дубли id отлавливаются сравнением длины |
| 2026-06-12 | Loader проверяет целостность ссылок (start_id + непустые next_id → существующий узел) | висячие ссылки ловятся на загрузке, а не в рантайме DialogueSystem; пустой next_id (`""`) пропускается — это легитимный конец диалога |
| 2026-06-12 | `choices`/`next_id` опциональны в JSON (`.get` с дефолтом) | терминальный узел = без `choices`; реплика-конец = `next_id` опущен → `""`; data-driven без хардкода |
| 2026-06-12 | `DialogueUI(dialogue_system, on_close)` держит ref на DialogueSystem, читает `current_node` | повторяет `QuestLogUI(quest_system, on_close)` / `SkillTreeUI(player, on_close)`: UI не дублирует состояние, владелец — система; lazy TYPE_CHECKING-импорт DialogueSystem без circular import |
| 2026-06-12 | ENTER на терминальном узле → `dialogue_system.advance()` (не `end()`) | `advance()` при 0 choices сам вызывает `end()` — используется существующий публичный API, новые методы в DialogueSystem не добавлялись |
| 2026-06-12 | ESC → только `on_close()`, диалог НЕ завершается | строго как QuestLogUI/SkillTreeUI: ESC закрывает оверлей; завершение диалога — решение владельца (DialogueSystem), не UI; не добавляем поведение сверх требований |
| 2026-06-12 | `_selected_index` сбрасывается в 0 после `choose`; навигация и выбор клампятся по `len(current_node.choices)` | число вариантов меняется между узлами; индекс всегда валиден для `choose()`; терминальный/неактивный узел → индекс 0, без падений |
| 2026-06-12 | GameScreen владеет одним `DialogueSystem` + `dict[str, Dialogue]`; клавиша `T` → `_start_dialogue("ranger_intro")` | повторяет Tab→SkillTreeUI / J→QuestLogUI: lazy import UI, push с `on_close=state_manager.pop`; данные грузятся статиком `_load_dialogues` как `_load_quests` |
| 2026-06-12 | Завершение диалога закрывает оверлей через EventBus `dialogue_ended` → `GameScreen._on_dialogue_ended` → `pop` | DialogueUI остаётся чистым экраном (8E.2: end() не дёргает on_close); закрытие — задача интеграции; реакция на событие повторяет `entity_died`→`_on_entity_died`; isinstance здесь — guard стека, не полиморфный dispatch |
| 2026-06-12 | `_start_dialogue` — нет-оп при `state_manager is None` и неизвестном id (`dict.get` → None) | отсутствующий диалог и отсутствие менеджера не ломают игру; safe-by-default, без исключений в игровом цикле |
| 2026-06-12 | read-only property `GameScreen.dialogue_system` | минимальный доступ для интеграционных тестов и будущих триггеров; владелец состояния один, дублирования нет |
| 2026-06-12 | Связь quest↔dialogue через EventBus `dialogue_choice_selected`, а не прямой вызов | предпочтительный подход из задачи 8G; DialogueSystem остаётся владельцем диалогов, QuestSystem — квестов; GameScreen — интеграционный слой; нет прямого импорта QuestSystem в DialogueSystem |
| 2026-06-12 | `quest_id: str = ""` на `DialogueChoice` (data-driven, не `if dialogue_id ==`) | выдаваемый квест задаётся в JSON, не хардкодом; диалог трактует id как opaque-данные; минимальное расширение JSON по требованию задачи |
| 2026-06-12 | `choose`/`advance` маршрутизированы через `_select(choice)` → эмит `dialogue_choice_selected` | единая точка эмита для ветвления и линейного шага; терминальный узел (0 choices) не проходит через `_select` → не эмитит; новое событие не ломает существующие проверки порядка (они слушают только started/node_changed/ended) |
| 2026-06-12 | GameScreen грузит квесты в реестр `_quests` БЕЗ авто-принятия; диалог выдаёт через `accept_quest` | без этого выдача из диалога была бы нет-оп (квест уже ACTIVE); квест появляется в журнале только после диалога — как требует сценарий 8G; ни один тест не завязан на авто-принятие старта |
| 2026-06-12 | `_on_dialogue_choice` читает quest_id через `getattr(choice, "quest_id", "")`, выдаёт из реестра | безопасно при пустом/неизвестном quest_id (`_quests.get`→None) и повторной выдаче (`accept_quest` нет-оп для не-AVAILABLE); isinstance не нужен — opaque-доступ к данным |
| 2026-06-12 | Lore: `data/lore_data.py` (`LoreEntry`) + `systems/lore.py` (`LoreSystem`) | прямая аналогия quest/dialogue: слой данных + рантайм-система; обязательный нижний слой по CLAUDE.md (data → systems), не расширение скоупа |
| 2026-06-12 | `LoreSystem.register` (каталог) отделён от `unlock` (открытие) | «существование записи» и «открытие записи» — разные операции из задачи; unlock неизвестного id → нет-оп; каталог наполняется заранее, открытие — рантайм-событие |
| 2026-06-12 | `unlock() → bool`, эмит `lore_unlocked` ровно один раз на запись | защита от повторного открытия: второй вызов возвращает False без события; параллель `quest_completed`/`dialogue_*` — система сообщает о состоянии только через EventBus |
| 2026-06-12 | JSON-загрузчик лора НЕ реализован в 8H | нет потребителей данных (нет Lore UI/триггеров); повторяет инкремент quest/dialogue, где loader делался отдельным спринтом при появлении нужды; задача 8H — только доменная модель + система |
| 2026-06-12 | `unlocked_entries`/`entries` возвращают копии | внешний код (будущий Lore UI) физически не может мутировать внутреннее состояние; повторяет `QuestSystem.active_quests` |
| 2026-06-12 | Lore↔Dialogue связан через тот же EventBus `dialogue_choice_selected`, что и Quest↔Dialogue (8G) | новый паттерн не вводится; `_on_dialogue_choice` обрабатывает и `quest_id`, и `lore_id` независимо; LoreSystem владеет лором, DialogueSystem — диалогами, GameScreen — интеграционный слой |
| 2026-06-12 | `lore_id: str = ""` на `DialogueChoice` (data-driven, не `if node_id ==`) | открываемая запись задаётся в JSON, не хардкодом; диалог трактует id как opaque-данные; минимальное расширение модели по образцу `quest_id` |
| 2026-06-12 | Лор-записи грузятся inline `GameScreen._load_lore_entries()` из `lore.json`, БЕЗ отдельного `lore_loader.py` | повторяет inline-паттерн player/weapon/enemy/item в GameScreen; интеграция 8I не требует валидирующего загрузчика; отдельный `lore_loader` (как quest/dialogue) — будущий инкремент при появлении Lore UI/триггеров |
| 2026-06-12 | `_on_dialogue_choice` открывает лор через `getattr(choice, "lore_id", "")` → `lore_system.unlock` | безопасно при пустом/неизвестном lore_id (`unlock` нет-оп → False, без события) и при повторе; ранний `return` убран, чтобы quest_id и lore_id обрабатывались независимо в одном выборе |
| 2026-06-12 | `LoreUI(lore_system, on_close)` читает `unlocked_entries` напрямую в draw/navigation | точная копия `QuestLogUI(quest_system, on_close)`: UI не кэширует и не дублирует состояние; `unlocked_entries` отдаёт копию → UI физически не может мутировать систему; живые данные без пересоздания UI |
| 2026-06-12 | Клавиша `L` → LoreUI через lazy import в GameScreen | завершает ряд Tab→SkillTreeUI / J→QuestLogUI / T→Dialogue; lazy import исключает циклический импорт; `on_close=state_manager.pop`; нет-оп при `state_manager is None` |
| 2026-06-12 | Перенос текста записи по словам (`LoreUI._wrap`) — презентационная логика в UI | лор-текст длиннее реплик/описаний; перенос — форматирование отображения, не игровая логика и не модель данных; держит draw читаемым и не роняет на длинном тексте |
| 2026-06-12 | `InventoryUI(inventory, on_close)` читает `inventory.items` напрямую в draw/navigation | точная копия паттерна LoreUI/QuestLogUI: UI не кэширует и не дублирует список; `items` отдаёт копию → UI физически не может мутировать инвентарь; живые данные без пересоздания UI |
| 2026-06-12 | Клавиша `I` → InventoryUI через lazy import в GameScreen; передаётся `player.inventory` | завершает ряд Tab/J/L/T; выполняет давнее обещание README (`I` — Инвентарь), которое не было подключено; `state_manager.pop` как on_close; нет-оп при `state_manager is None` |
| 2026-06-12 | InventoryUI показывает description только для выбранного предмета | список даёт обзор (имена), деталь (description) — для текущего выбора; минимальный осмысленный объём по требованию; stackable/drop/use-from-UI вынесены в будущие спринты |
| 2026-06-12 | Иерархия `Entity → Boss → PatientZeroBoss` (Boss — отдельная ветвь, не под Zombie) | строго по CLAUDE.md/README; демонстрация наследования (цель ООП-проекта); `Boss` базовый держит общую boss-логику (rect, boss_defeated), `PatientZeroBoss` — конкретный финальный |
| 2026-06-12 | `boss_defeated` эмитится в override `Boss.take_damage` на переходе жив→мёртв | переиспользует единственную точку детекции смерти (Entity.take_damage), не вводит новую событийную архитектуру; `was_alive and not is_alive` гарантирует ровно одно событие при повторных/избыточных ударах; `entity_died` остаётся (death-паттерн врагов) |
| 2026-06-12 | `PatientZeroBoss(x, y, max_health)` — max_health инжектится, размер `TILE_SIZE*2` | без магических чисел: HP задаёт вызывающий (позже из JSON), размер — из settings; ядро не создаёт BossData/JSON-загрузчик (вне скоупа 9B, как loader откладывался у quest/lore) |
| 2026-06-12 | Босс — отдельное поле `GameScreen._boss`, не в `_enemies` | босс один (не список); `_enemies: list[Zombie]` типизирован Zombie, а `Boss(Entity)` не Zombie и имеет другую сигнатуру update; combat-участие — через включение в `targets`, без новой структуры |
| 2026-06-12 | `Boss.xp_reward = 0` добавлен в 9C (необходимое изменение) | босс faction='enemy' проходит через существующий `_on_entity_died`, который читает `entity.xp_reward`; без поля — AttributeError при интеграции; решение завершает enemy-контракт (как `Zombie.xp_reward`), оставляя generic XP-обработчик GameScreen неизменным → «XP за зомби не ломается» гарантировано |
| 2026-06-12 | `BOSS_MAX_HEALTH` в settings.py, координаты спавна инлайн в `_spawn_boss` | CLAUDE.md: константы — в settings; позиции врагов уже инлайн в `_spawn_enemies` — босс следует тому же паттерну; босс-JSON/загрузчик не вводятся (минимальный срез, без новой архитектуры) |
| 2026-06-12 | Победа = флаг `_victory` + текст в `GameScreen.draw`, без нового экрана | требование «минимальный вертикальный срез, без VictoryScreen»; реакция на существующее `boss_defeated` через EventBus (паттерн `entity_died`→`_on_entity_died`); read-only `victory` property для тестов/будущих концовок |
| 2026-06-12 | AI босса (9D) — копия подхода Zombie в `PatientZeroBoss`, а не наследование/рефактор Zombie | иерархия `Entity→Boss→PatientZeroBoss` фиксирована (CLAUDE.md); наследование от Zombie нарушило бы её и требовало EnemyData; вынос хелперов в общий базовый класс = рефактор несвязанного Zombie (запрещён). Минимум — зеркало `_move_toward/_resolve_x/_resolve_y/_detect_player/_in_attack_range` |
| 2026-06-12 | `PatientZeroBoss.update(dt, walls=None, player=None)` — сигнатура как `Zombie.update` | LSP-совместимо с `GameObject.update(dt)` (доп. параметры с дефолтами), mypy чист (как у Zombie); GameScreen зовёт `boss.update(dt, walls, player)` единообразно с врагами |
| 2026-06-12 | Константы AI босса — в settings.py, без новых JSON | прецедент `BOSS_MAX_HEALTH` (9C); сприн запрещает новые JSON-конфиги; CLAUDE.md: константы — в settings; значения функциональные, не балансировка |
| 2026-06-12 | 2 фазы как property `phase` + производные `speed`/`attack_cooldown` (множители фазы 2) | минимально и без состояния перехода: фаза вычисляется из `health.percentage` на лету; фаза 2 (HP<=50%) даёт ×1.5 скорость и ×0.6 кулдаун — «агрессивнее» одной формулой |
| 2026-06-12 | Melee босса НЕ эмитит `zombie_attacked` | новых событий вводить нельзя, а зомби-событие от босса семантически некорректно и без продакшн-подписчиков; требование — лишь урон, выполняется `target.take_damage(BOSS_DAMAGE)` |
| 2026-06-12 | `SaveData` (data/) + `SaveSystem` (systems/): capture/save/load/apply | разделение модель↔оркестрация как у quest/dialogue (data + loader/system); сохраняем только состояние (id/числа), не игровые объекты |
| 2026-06-12 | Восстановление навыков через `add_xp`→очки→`upgrade`, без сеттеров | у SkillTree нет публичного сеттера уровней; `player.add_xp` через `player_level_up` сам выдаёт (level−1) очков, которые `upgrade` тратит по сохранённым уровням (и повторно применяет эффекты). Чисто публичный API, инвариант level−1 ≥ Σуровней держится для валидных сейвов |
| 2026-06-12 | Восстановление XP через `add_xp(total_xp)` | `ExperienceComponent` хранит суммарный XP и выводит уровень формулой; повтор `add_xp(total)` на свежем компоненте детерминированно воспроизводит и XP, и уровень — сеттеры не нужны |
| 2026-06-12 | Добавлен публичный `QuestSystem.restore(active, completed)` (необходимо) | нет публичного пути восстановить ЗАВЕРШЁННЫЕ квесты; `accept_quest`+`complete_quest` повторно начислили бы reward_xp и эмитили `quest_completed`. `restore` ставит статусы и списки без наград/событий; обычный поток её не вызывает |
| 2026-06-12 | Предметы восстанавливаются по `item_id` из `items.json` (food→FoodItem, quest→QuestItem) | сохраняем минимум (item_id); пересборка повторяет категории `GameScreen._spawn_items`; неизвестный id пропускается. `systems→entities` уже легитимен (combat импортирует bullet) |
| 2026-06-12 | Лор восстанавливается `lore_system.unlock(id)` (каталог уже зарегистрирован) | LoreSystem-дизайн: каталог регистрируется отдельно, открытие — по id; SaveSystem лишь открывает сохранённые id; незарегистрированные — нет-оп |
| 2026-06-12 | Save Integration: F5/F9 в GameScreen, один файл `SAVES_DIR/savegame.json` | клавиши были свободны; единый файл по ТЗ (без слотов/меню); `_SAVE_PATH` — класс-атрибут для тестируемости (monkeypatch) |
| 2026-06-12 | F9 строит свежие player/quest/lore (`_fresh_systems`) и подменяет ссылки | `SaveSystem.apply` (10A) рассчитан на чистые объекты (add_xp/add_item/upgrade аккумулируют); загрузка в живые объекты двоила бы состояние. Поля систем читаются каждый кадр → swap корректен; restore-логика не дублируется (переиспользован apply) |
| 2026-06-12 | F9 на отсутствующем/битом файле — нет-оп (ловим SaveError до подмены) | игра не должна ломаться; свежие системы строятся только после успешного `load`; при ошибке текущее состояние сохраняется нетронутым |
| 2026-06-14 | HUD — обычный класс (не BaseScreen), не в GameStateManager | HUD не экран стека, а постоянный оверлей поверх GameScreen; рисуется напрямую в `GameScreen.draw` (как `_draw_victory`); чистый UI без игрового состояния |
| 2026-06-14 | HUD читает `player`/`quest_system` аргументами `draw` каждый кадр, не хранит ссылок | F9 подменяет `GameScreen._player/_quest_system`; передача полей аргументами гарантирует, что HUD всегда показывает актуальные объекты без устаревших ссылок |
| 2026-06-14 | XP-бар = `current_xp / (current_xp + xp_to_next_level)` | используется только разрешённый публичный API (3 поля); знаменатель = порог следующего уровня, всегда > 0; монотонная доля 0..1 без доступа к нижнему порогу уровня |
| 2026-06-14 | HUD-константы (размеры/цвета баров) — module-level приватные в `hud.py` | повторяет паттерн `lore_ui`/`inventory_ui`/`dialogue_ui` (presentation-константы локальны в UI-файле); settings.py — для геймплейных констант |
| 2026-06-14 | Game Over через существующий `entity_died` в `_on_entity_died` (`entity is self._player`) | зеркало `boss_defeated`→`victory`; новых событий/подписок нет; идентичность игрока корректна и после F9-подмены `_player` (не ловит «утёкший» старый player) |
| 2026-06-14 | Заморозка терминальных состояний — ранний `return` в `update` при `victory or game_over` | минимально и безопасно; попутно устранена прежняя недоработка (победа не останавливала цикл); `draw` продолжает работать, HUD виден под оверлеем |
| 2026-06-14 | `draw`: `if victory … elif game_over …` (взаимоисключение) | оба флага одновременно невозможны (заморозка не даёт второму событию случиться), elif исключает наложение текстов; victory приоритетна |
| 2026-06-14 | Main Menu стартует первым; New Game/Continue **заменяют** меню (pop+push), а не стекаются | игра остаётся на глубине 1 → ESC-выход (`depth<=1`) работает как раньше; стек GameScreen-overlays (Tab/J/L/I) ведёт себя прежне; меню не нужно после старта (Pause Menu вне скоупа) |
| 2026-06-14 | MainMenuScreen(state_manager, on_quit): транзишены через стек, выход — колбэк | переходы экранов тестируемы на самом меню (как GameScreen строит свои sub-UI); `on_quit` — паттерн `on_close`, в main.py → `Game.stop()`; обе зависимости легко мокаются в тестах |
| 2026-06-14 | `GameScreen._load_game` → публичный `load_game` | Continue вызывает существующую загрузку (SaveSystem внутри), не дублируя логику; F9 теперь зовёт тот же публичный метод; поведение не изменено |
| 2026-06-14 | Continue читает наличие сейва через `GameScreen._SAVE_PATH.exists()` | единый файл-сейв (без слотов); проверка пути — не дублирование SaveSystem; нет сейва → нет-оп, остаёмся в меню |
| 2026-06-14 | `cleanup()` как lifecycle-хук в `BaseScreen` (нет-оп), переопределён в GameScreen; вызывается из `GameStateManager.pop` | минимальный механизм teardown без рефактора EventBus (его `off` уже есть); все экраны имеют cleanup → `pop` безопасен; будущий return-to-menu автоматически чистит GameScreen |
| 2026-06-14 | GameScreen снимает подписки Player/QuestSystem через `EventBus.off(bound_method)`, не модифицируя их | QuestSystem (Quest) — в списке «не трогать»; равенство bound-методов (`==` по instance+func) позволяет `list.remove` найти и снять; GameScreen — владелец этих объектов, он же управляет их жизненным циклом подписок |
| 2026-06-14 | F9 `load_game` снимает подписки СТАРЫХ player/quest перед swap | повторная загрузка: `_fresh_systems` добавляет +2 подписки, detach старых −2 → счётчик стабилен; GameScreen-подписки (4) не трогаются (экран жив) |
| 2026-06-14 | `cleanup` идемпотентен (флаг `_cleaned`) | защита от двойного `off` (ValueError из `list.remove`) при cleanup + последующем pop того же экрана; EventBus не трогаем |
| 2026-06-14 | PauseMenu (10G) — push поверх GameScreen (стек), 4 колбэка вместо ссылки на GameScreen | паттерн `on_close` проекта (overlays получают систему + колбэк); без импорта GameScreen → нет цикла, тривиально мокается; Save = `_save_game` (путь F5), не дублирует SaveSystem |
| 2026-06-14 | Единый `_return_to_main_menu` для пункта паузы и терминального ENTER | один путь возврата (требование «не делать отдельную реализацию»); снимает оверлей паузы (если есть) и GameScreen через `pop`→`cleanup` → подписки не текут; устойчив к обеим высотам стека (цикл `while current is not self`) |
| 2026-06-14 | ESC-выход вынесен из `main.py` в делегирование экрану; quit лишь если корневой экран не открыл оверлей (`at_root до` + `depth<=1 после`) | GameScreen перехватывает ESC (пауза, depth↑→нет quit); оверлеи закрываются (pop); Main Menu не изменён (ESC игнорирует → depth не растёт → quit). Альтернатива (ESC-обработчик в MainMenu) запрещена правилом «не рефакторить Main Menu» |
| 2026-06-14 | `GameScreen.on_quit` опционален (default нет-оп); проброшен из MainMenu (New Game/Continue) | существующие тесты создают GameScreen без on_quit — не ломаются; реальная игра прокидывает `Game.stop` → Quit/Main Menu из паузы завершают/перезапускают сессию |
| 2026-06-14 | Терминальный guard в `handle_event`: при victory/game_over только ENTER→меню | завершает жизненный цикл и попутно чинит латентный недочёт (на мёртвом экране принимались стрельба/инвентарь — `update` был заморожен, а `handle_event` нет) |
| 2026-06-14 | Кислота босса (9E) — переиспользование `AcidBullet`, без нового класса снаряда | `AcidBullet` уже существует и подходит (контракт Bullet, `origin_tag='enemy'` не бьёт врагов/босса, бьёт игрока); ввод нового снаряда нарушил бы «не вводить новую систему снарядов» |
| 2026-06-14 | `BOSS_ACID_*` в `settings.py`, а не BossData/JSON | CLAUDE.md: константы в settings + запрет магии; все `BOSS_*` уже там; задача запрещает BossData/JSON-конфиг босса → settings единственный совместимый дом (4-е изменение обосновано) |
| 2026-06-14 | Спец-атака — зеркало `SpitterZombie` на `PatientZeroBoss` (`_pending_bullets`/`collect_spawned_bullets`), не вынос в общий базовый класс | запрет рефакторинга Zombie и выноса логики; босс уже дублирует AI-хелперы зомби осознанно (9D) — кислота следует тому же решению; `Boss`-база не трогается |
| 2026-06-14 | Отдельный `_acid_timer` параллельно `_attack_timer`; гейт `is_alive and phase==2 and can_spit` | отдельный кулдаун кислоты не связан с melee; `is_alive` не даёт «трупу» (0%HP→phase2 по `percentage`) выстрелить при прямом вызове update; melee 9D остаётся без изменений |
| 2026-06-14 | Сбор пуль босса — одна строка в `GameScreen.update` после `boss.update` (как для зомби) | босс обновлялся отдельно от `_enemies` и его `collect_spawned_bullets` не вызывался; минимальная интеграция в существующий поток, CombatSystem не меняется |
| 2026-06-14 | Призыв миньонов (9F) — инъекция `EnemyData` (walker) в `PatientZeroBoss(minion_config=None)`, босс строит реальные `WalkerZombie` | `WalkerZombie` требует `EnemyData`; загрузка JSON в `entities/` нарушила бы слои. Инъекция готового dataclass — без BossData/JSON в entity-слое и без нового типа миньона. Дефолт None → юнит-тесты `PatientZeroBoss(x,y,hp)` целы. Цикла импорта нет (zombie не зависит от boss) |
| 2026-06-14 | Лимит призыва — счёт живых ссылок `_summoned` (`_active_minions`), не счётчик/событие | лимит «одновременно живых» требует видеть гибель; общие ссылки с `_enemies` дают `m.active` без EventBus; слот сам освобождается при смерти миньона |
| 2026-06-14 | Сбор миньонов — `self._enemies.extend(boss.collect_spawned_minions())` после `boss.update` | паттерн `collect_spawned_bullets`; новые враги попадают в существующий поток (update/draw/combat-targets/очистка/XP) без новой системы спавна |
| 2026-06-14 | Кислота и призыв — общий гейт `is_alive and phase==2`, каждый со своим кулдауном | оба — способности фазы 2; единый гейт читаем и не даёт «трупу» (0%HP→phase2) действовать; melee 9D ниже не тронут |
| 2026-06-14 | XP за босса (9G) — `BOSS_XP_REWARD` в settings, `Boss.xp_reward` = константа | путь начисления уже есть (`_on_entity_died`→`entity.xp_reward`); новой системы наград не вводится; значение конфигурируемо, не магия |
| 2026-06-14 | Спецатаки гейтятся существующим `_detect_player` (9G) | переиспользование уже реализованного радиуса обнаружения; без отдельной системы агро; босс больше не плюётся/призывает «сквозь карту» вне аггро |
| 2026-06-14 | Прунинг `_summoned` в `summon_minion` (фильтр по `active` перед append) | устраняет рост списка мёртвых ссылок; список ограничен ≤`BOSS_SUMMON_MAX`; контракт лимита (`can_summon`) не меняется |
| 2026-06-14 | Тесты, завязанные на старое поведение, перенацелены, не ослаблены (9G) | `xp_reward==0`→`==BOSS_XP_REWARD`; GameScreen-интеграция/лимиты ставят игрока в радиус обнаружения (иначе гейт корректно блокирует спецатаки при больших dt и overshoot движения) |
| 2026-06-14 | Патруль (10A) — точки вокруг якоря (spawn), ветка `else` в `update`, по образцу `Zombie._patrol` | существующий паттерн; обнаружение в `if/elif` выше немедленно прерывает патруль, потеря игрока → `else` снова; спецатаки/melee/фазы не тронуты |
| 2026-06-14 | Патруль активен только при игроке≠None (не обнаружен); `player is None` — ранний выход | сохраняет семантику `test_no_player_is_safe`; в реальной игре игрок всегда есть, патруль работает; мёртвый босс не патрулирует (GameScreen зовёт update лишь при `_boss.active`) |
| 2026-06-14 | Патруль переиспользует `_move_toward` со сниженной скоростью (`dt*BOSS_PATROL_SPEED_FACTOR`) | без дублирования логики коллизий стен; зеркало `Zombie._patrol` (`dt*0.5`); патруль уважает стены |
| 2026-06-14 | Rifle/Shotgun (10B) — прямые подклассы `Weapon`, не `Pistol` | задача: «наследуется от Weapon»; плоская иерархия `Weapon→{Pistol,Rifle,Shotgun}` чище демонстрирует полиморфизм; одиночный выстрел Rifle совпадает по форме с Pistol (осознанное мелкое дублирование, как у Boss/Zombie-хелперов) |
| 2026-06-14 | Параметры дробовика — поля `WeaponConfig` с дефолтами (`pellet_count=1`, `spread_degrees=0`), а не settings | данные оружия живут в JSON (CLAUDE.md); дефолты сохраняют обратную совместимость pistol/rifle и существующих фикстур `WeaponConfig(...)`; без новой dataclass |
| 2026-06-14 | Оружие доступно «в конфигурации» (weapons.json), не привязано к вводу GameScreen | ограничение «не менять GameScreen-архитектуру»; полиморфизм демонстрируется классами+тестами; переключение оружия по клавишам — вне скоупа (см. остаточные риски) |
| 2026-06-14 | `test_weapon_config_is_dataclass` 5→7 полей — перенацелен, не ослаблен | dataclass легитимно получил 2 поля; тест отражает новый контракт, остальные `WeaponConfig(...)` целы благодаря дефолтам |

---

## Известные проблемы и риски

| # | Описание | Приоритет | Статус |
|---|---|---|---|
| 1 | ~~Нет карты — игрок ходит по пустому фону~~ | ~~высокий~~ | ✅ Решено в Спринте 3 |
| 2 | ~~Игрок умирает от голода без возможности поесть~~ | ~~средний~~ | ✅ Решено в Спринте 6: FoodItem + Inventory + автоподбор |
| 3 | Camera не ограничена границами мира (может выйти за пределы карты) | низкий | Решится при добавлении TMX или в Спринте 10 |
| 4 | ~~Игрок не может убивать врагов (нет оружия)~~ | ~~средний~~ | ✅ Решено в Спринте 5A |

---

## Заметки

> `player.health` — это `HealthComponent`, не int. Для получения числа: `player.health.current`.  
> Для HP-бара: `player.health.percentage` (float 0.0–1.0).  
> `player.hunger` — это `HungerComponent`. Для hunger-бара: `player.hunger.percentage`.  
> `take_damage` / `heal` принимают `float` (не `int`) — дробный урон корректен.  
> При смене сцены вызывать `EventBus.clear()`.  
> `Zombie.update(dt, walls, player)` — player передаётся каждый кадр, не хранится в зомби.  
> `enemy.active == False` → зомби убирается из списка в `GameScreen.update()` после итерации.  
> `AIState` импортируется из `entities.zombie`, не из `core`.  
> `player.fire(direction)` возвращает `list[Bullet]`; передать в `combat.add_bullets(bullets)`.  
> `CombatSystem.update(dt, walls, targets)` — `targets` это `list[Targetable]`; Zombie удовлетворяет протоколу.  
> `Weapon.update(dt)` тикается внутри `Player.update()` — GameScreen не трогает weapon напрямую.  
> `SpitterZombie.collect_spawned_bullets()` — вызывать после `enemy.update()` в GameScreen, до `_enemies` prune.
> `AcidBullet.origin_tag == "enemy"` — faction-фильтр в CombatSystem не даёт кислоте бить зомби.
> `_ENEMY_CONSTRUCTORS` dict в `game_screen.py` — диспетчер конструкторов; для нового врага добавить одну строку.
> `player.inventory` — `Inventory` с capacity=20. `player.pickup_item(item)` — подбор; `player.use_item(item)` — делегирует `inventory.use_item(item, self)`.
> `FoodItem.use(player)` — вызывает `player.hunger.consume(nutrition)`, всегда возвращает True.
> `QuestItem.use(player)` — возвращает False, из инвентаря не удаляется.
> EventBus-события инвентаря: `inventory_item_added`, `inventory_item_removed`, `item_used`.
> В GameScreen: предметы в `_world_items`; автоподбор при `colliderect`; клавиша F — использовать первый предмет (полиморфизм: quest пропускается, food применяется).
> `PatientZeroBoss(x, y, max_health)` — финальный босс (ядро, 9B). Иерархия `Entity → Boss → PatientZeroBoss`. faction='enemy', `xp_reward=0` (9C), `rect` (TILE_SIZE*2), совместим с CombatSystem. При смерти эмитит `boss_defeated` ({boss}) ровно один раз ПЛЮС унаследованный `entity_died` ({entity}).
> Босс интегрирован в GameScreen (9C): `_boss` спавнится в Комнате 4 (HP=`settings.BOSS_MAX_HEALTH`), обновляется/рисуется при `active`, входит в combat-`targets`. Подписка `boss_defeated` → `_on_boss_defeated` → `_victory=True`; `GameScreen.victory` (read-only) + победный текст в draw. Босс даёт 0 XP. ВНИМАНИЕ: босс — faction='enemy', поэтому его смерть инкрементит активные KillZombieObjective (generic-фильтр QuestSystem) — будущая балансировка/раздельные цели.
> EventBus Cleanup (10F): один GameScreen = 6 подписок EventBus. `BaseScreen.cleanup()` (нет-оп) → переопределён в `GameScreen.cleanup()` (идемпотентен): снимает свои 4 + подписки текущих player/quest_system. `GameStateManager.pop()` зовёт `cleanup()` снятого экрана. `GameScreen.load_game` (F9) перед swap снимает подписки старых player/quest (`_detach_systems`). QuestSystem/Player не менялись — их bound-методы снимаются через `EventBus.off`. Подписчики НЕ копятся при F9/New Game/Continue.
> Main Menu (10E): игра стартует с `MainMenuScreen(state_manager, on_quit)` (main.py пушит его, `on_quit=game.stop`). New Game: pop меню + push `GameScreen` (depth 1). Continue: при `GameScreen._SAVE_PATH.exists()` → push GameScreen + `screen.load_game()` (публичный, тот же что F9); иначе нет-оп. Quit → `on_quit()` → `Game.stop()` (`_running=False`). ESC в меню (depth 1) тоже выходит (main.py). Слоты/Pause Menu/возврат-в-меню — будущее.
> Game Over (10D): `GameScreen.game_over` (read-only) выставляется в `_on_entity_died` при `entity is self._player` (событие `entity_died`, новых событий нет). `update` замораживается ранним `return` при `victory or game_over` (враги/босс/combat/подбор/таймеры стоят). `_draw_game_over` рисует «GAME OVER» (взаимоисключение с victory через elif), HUD остаётся под оверлеем. Рестарт/возврат в меню после смерти — будущий спринт.
> HUD (10C): `HUD()` (ui/hud.py) — не BaseScreen, не в стеке. `GameScreen._hud` создаётся в `__init__`, рисуется в `draw` как `self._hud.draw(surface, self._player, self._quest_system)`. Читает только публичный API (`health.percentage`, `hunger.percentage`, `experience.{current_level,current_xp,xp_to_next_level}`, `quest_system.active_quests`→`title`/`objective.progress`). Состояния не хранит → корректен после F9-подмены. Миникарта/HP-бар босса — вне 10C.
> Save Integration (10B): в GameScreen `F5` → `_save_game` (SaveSystem().save в `GameScreen._SAVE_PATH = SAVES_DIR/savegame.json`), `F9` → `_load_game`. F9 строит свежие системы (`_fresh_systems`), `apply`, подменяет `_player/_quest_system/_lore_system`. Отсутствующий/битый файл — нет-оп (SaveError). Игрок/квесты/лор пересоздаются → старые объекты остаются подписанными на EventBus (известный leak, см. риски). Позиция/HP/голод/прогресс целей квестов не сохраняются (вне 10A). `_SAVE_PATH` патчится в тестах через monkeypatch.
> SaveSystem (10A): `SaveSystem().save(path, player, quest_system, lore_system)` / `.load(path)→SaveData` / `.apply(data, ...)` / `.load_into(path, ...)`. `SaveError` при отсутствии файла/битом JSON. `SaveData` (data/save_file.py) — снимок: xp/level, skill_levels, inventory_item_ids, active/completed_quest_ids, unlocked_lore_ids; `to_dict`/`from_dict`. ВАЖНО: `apply` рассчитан на СВЕЖИЕ системы; XP восстанавливается первым (выдаёт очки навыков). Завершённые квесты — через новый `QuestSystem.restore` (без повторного XP). Лор-каталог должен быть зарегистрирован до apply. НЕ интегрирован в GameScreen/клавиши — будущий спринт. Активные квесты восстанавливаются на уровне id (прогресс целей не сохраняется — минимальный срез).
> Boss AI (9D): `boss.update(dt, walls, player)` — преследует игрока в радиусе `BOSS_DETECTION_RANGE` (`_move_toward`, как зомби) и бьёт в радиусе `BOSS_ATTACK_RANGE` по кулдауну `attack_cooldown`. GameScreen зовёт `self._boss.update(dt, walls, self._player)` (НЕ `update(dt)`). Фазы: `boss.phase` (1/2 от `health.percentage`, порог `BOSS_PHASE2_HEALTH_FRACTION`); `boss.speed`/`boss.attack_cooldown` зависят от фазы (фаза 2 = ×`SPEED_MULTIPLIER` / ×`COOLDOWN_MULTIPLIER`). `can_attack` по `_attack_timer`. Все константы — в settings.py. Melee не эмитит событий.
> `InventoryUI(inventory, on_close)` — оверлей инвентаря (BaseScreen). Открывается клавишей `I` в GameScreen (lazy import, `on_close=state_manager.pop`). UP/DOWN циклическая навигация, ESC закрывает. Только чтение через `inventory.items` (+ `count`/`capacity`); состояние не дублирует. Пустой → «Inventory is empty.». Показывает имена списком + description выбранного. `ui/inventory_ui.py` больше не стаб.
> `player.skill_tree` — `SkillTree`. `skill_tree.add_point()` вызывается через EventBus `player_level_up` (по одному разу на каждый level-up). `skill_tree.upgrade(SkillType.X, player)` — тратит 1 очко, применяет эффект. Константы: `HP_PER_LEVEL=20`, `HUNGER_REDUCTION_PER_LEVEL=0.5`, `DAMAGE_PER_LEVEL=5.0`, `MAX_SKILL_LEVEL=5`.
> `player.apply_weapon_damage_bonus(bonus)` — передаёт бонус в `_weapon.add_damage_bonus()`; no-op если оружие не экипировано.
> `weapon.damage_bonus` — накопленный бонус к урону от навыков. `Pistol.fire()` создаёт пулю с `config.damage + _damage_bonus`.
> `SkillTreeUI(player, on_close)` — `on_close: Callable[[], None]`; в GameScreen передаётся `state_manager.pop`. Tab открывает, ESC закрывает.
> `ui/skill_tree_ui.py` — `_SKILLS = list(SkillType)` — порядок навигации совпадает с порядком enum. `selected_skill` — публичный property для тестов.
> `QuestSystem(exp_component)` — принимает `ExperienceComponent`; автоматически подписывается на `entity_died`. XP выдаётся через `exp_component.add_xp(quest.reward_xp)`.
> `quest_system.accept_quest(quest)` — переводит `AVAILABLE → ACTIVE`. Повторный вызов / вызов для завершённого квеста — нет-оп.
> `quest_system.update_progress(event_data)` — принимает dict с ключом `"entity"`; вызывает `obj.on_kill(faction)` на всех целях; полиморфно, без isinstance.
> `quest_system.complete_quest(quest)` — принудительное завершение активного квеста; нет-оп если квест не в active.
> EventBus-события квестов: входящее `entity_died`, исходящее `quest_completed` (data: `{"quest": quest}`).
> Квест с пустым `objectives` не завершается через `update_progress` — только через `complete_quest()`.
> `KillZombieObjective.on_kill("enemy")` не превышает `target_count` — guard `not self.is_complete` внутри метода.
> `Objective.progress` — абстрактное property → str; `KillZombieObjective.progress` отдаёт `"current/target"`. Используется QuestLogUI для отображения без isinstance.
> `QuestLogUI(quest_system, on_close)` — только чтение; навигация UP/DOWN, ESC закрывает. В GameScreen открывается по клавише J (lazy import), `on_close = state_manager.pop`.
> `GameScreen._quest_system` — `QuestSystem(player.experience)`. Квесты из `quests.json` грузятся в реестр `GameScreen._quests: dict[str, Quest]` и НЕ принимаются автоматически (Sprint 8G): их выдаёт диалог. Прогресс идёт автоматически через подписку QuestSystem на `entity_died`.
> `LoreSystem` (8H) — каталог лор-записей и набор открытых. `register(entry)` наполняет каталог; `unlock(entry_id) → bool` открывает (True если новое; нет-оп/False для неизвестного id и повторного открытия); `has_entry`/`is_unlocked` — проверки; `unlocked_entries` (порядок открытия, копия) / `entries` (копия). EventBus-событие `lore_unlocked` ({entry}) эмитится ровно один раз на запись. Без UI/загрузчика/глав — только модель данных (`data/lore_data.py: LoreEntry`) + система.
> Открытие записок на карте/терминалах → вызвать `lore_system.unlock(id)` из триггера (как `_start_dialogue`). Lore UI и триггеры на карте — следующие спринты; `ui/lore_ui.py` пока пустой стаб.
> Lore↔Dialogue (8I): выбор варианта с непустым `DialogueChoice.lore_id` → DialogueSystem эмитит `dialogue_choice_selected` ({choice}) → `GameScreen._on_dialogue_choice` → `lore_system.unlock(lore_id)`. Безопасно при пустом/неизвестном id и повторе. Новая запись лора, открываемая диалогом → добавить запись в `lore.json` + `lore_id` в нужный choice в `dialogues.json`.
> `GameScreen._lore_system` — `LoreSystem`; записи регистрируются из `lore.json` через `_load_lore_entries()` (inline json.load, как player/weapon/enemy/item). Один выбор диалога может нести и `quest_id`, и `lore_id` — обе интеграции независимы.
> `LoreUI(lore_system, on_close)` — оверлей журнала лора (BaseScreen). Открывается клавишей `L` в GameScreen (lazy import, `on_close=state_manager.pop`). UP/DOWN циклическая навигация, ESC закрывает. Только чтение через `lore_system.unlocked_entries`; состояние не дублирует. Пустой журнал → «No lore entries discovered.». `ui/lore_ui.py` больше не стаб.
> Quest↔Dialogue (8G): выбор варианта с непустым `DialogueChoice.quest_id` → DialogueSystem эмитит `dialogue_choice_selected` ({choice}) → `GameScreen._on_dialogue_choice` → `accept_quest(_quests[quest_id])`. Безопасно при пустом/неизвестном id и повторной выдаче. Новый квест, выдаваемый диалогом → добавить запись в `quests.json` + `quest_id` в нужный choice в `dialogues.json`.
> EventBus: при гибели врага срабатывают ДВА независимых подписчика — `GameScreen._on_entity_died` (XP за килл) и `QuestSystem._on_entity_died` (прогресс квеста). Не конфликтуют.
> `data/quest_loader.py` — `load_quests(path: Path) → list[Quest]`. Поднимает `QuestLoadError` при любой ошибке (нет файла / битый JSON / неизвестный тип цели / нет обязательных полей).
> Формат `quests.json`: `{"quests": [{id, title, description, reward_xp, objectives: [{type, ...}]}]}`. Тип цели `"kill_zombie"` требует `target_count`.
> Новый тип Objective в JSON → добавить builder и строку в `_OBJECTIVE_BUILDERS` в `quest_loader.py` (плюс класс в `quest_data.py`). isinstance не используется.
> `GameScreen._load_quests()` читает `DATA_DIR/quests.json`; инлайн-квестов в коде больше НЕТ. Стартовый квест уровня — `clear_bunker_a1` (4 зомби, 100 XP).
> `DialogueSystem` — рантайм диалогов. `start(dialogue)` активирует; `current_node` / `is_active` — состояние; `advance()` — линейный шаг (0 выборов→конец, 1→переход, >1→DialogueError); `choose(index)` — ветвление; `end()` — завершить (нет-оп если не активен).
> Модель диалога: `Dialogue(id, nodes: dict[str, DialogueNode], start_id)`. `DialogueNode(id, speaker, text, choices)`, `is_terminal` = нет choices. `DialogueChoice(text, next_id)`, `next_id == ""` → конец диалога.
> EventBus-события диалога: `dialogue_started` ({dialogue}), `dialogue_node_changed` ({node}), `dialogue_ended` ({dialogue}). UI подписывается на них — прямых вызовов из системы в UI нет.
> Диалоги НЕ интегрированы в GameScreen/UI — это отдельная под-задача Спринта 8E (как UI 8B у квестов).
> `data/dialogue_loader.py` — `load_dialogues(path: Path) → list[Dialogue]`. Поднимает `DialogueLoadError` при любой ошибке (нет файла / битый JSON / нет обязательных полей / дубли id узлов / висячие ссылки / пустой диалог без узлов).
> Формат `dialogues.json`: `{"dialogues": [{id, start_id, nodes: [{id, speaker, text, choices: [{text, next_id}]}]}]}`. `choices` и `next_id` опциональны; `next_id == ""` (или опущен) = конец диалога; узел без `choices` = терминальный.
> Loader строит `nodes` (список в JSON) в `dict[str, DialogueNode]` и валидирует целостность ссылок: start_id и все непустые next_id должны указывать на существующий узел.
> `DialogueUI(dialogue_system, on_close)` — оверлей диалога (BaseScreen). UP/DOWN навигация по вариантам (циклическая), ENTER — `choose(index)` на не-терминальном узле / `advance()` на терминальном (завершает диалог), ESC — `on_close()` (НЕ завершает диалог). Только отображение+ввод; состояние читается из DialogueSystem.
> Диалоги интегрированы в игру (8F): клавиша `T` в GameScreen запускает `ranger_intro` и открывает DialogueUI. `GameScreen._dialogues` — `dict[str, Dialogue]` из `dialogues.json`; `GameScreen._dialogue_system` — единственный владелец состояния (read-only property `dialogue_system`).
> Закрытие оверлея диалога: НЕ в DialogueUI. GameScreen подписан на EventBus `dialogue_ended` → `_on_dialogue_ended` → снимает DialogueUI через `state_manager.pop` (только если сверху именно DialogueUI). ESC закрывает оверлей сразу через `on_close` (диалог при этом не завершается).
> Новый диалог в игре → добавить запись в `dialogues.json` и вызвать `_start_dialogue(id)` из нужного триггера (пока только клавиша T для MVP). NPC/триггеры на карте — следующие спринты.

---

*Обновляй этот файл в конце каждой рабочей сессии.*
