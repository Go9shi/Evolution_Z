# CLAUDE-progress.md — Evolution Z

Этот файл обновляется вручную после каждой рабочей сессии.
Помогает Claude Code быстро восстановить контекст при следующем запуске.

---

## Текущий статус

**Фаза:** Активная разработка  
**Спринт:** 8G — Quest ↔ Dialogue Integration ✅ (диалог выдаёт существующий квест через EventBus)  
**Дата последнего обновления:** 2026-06-12

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

- [ ] Спринт 8E — Нарратив: системы. DialogueSystem ✅ + DialogueLoader ✅ + DialogueUI ✅ + интеграция в GameScreen ✅ (8F) + Quest↔Dialogue ✅ (8G) сделаны. Осталось: `systems/lore.py` (записки/терминалы), сюжетные события глав 1–3.

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
- [ ] `entities/boss.py` — базовый `Boss(Entity)` + `PatientZeroBoss` (3 фазы)
- [ ] `assets/maps/eden7.tmx` — арена финального боя
- [ ] Логика концовок: хорошая / плохая

### Спринт 10 — Полировка
- [ ] `systems/save_system.py` — сохранение / загрузка JSON
- [ ] `ui/main_menu.py` — главное меню со слотами сохранений
- [ ] `systems/audio.py` — SFX и музыка
- [ ] HUD: HP-бар (через `player.health.percentage`), миникарта, трекер квестов
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
