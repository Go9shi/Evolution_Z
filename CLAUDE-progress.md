# CLAUDE-progress.md — Evolution Z

Этот файл обновляется вручную после каждой рабочей сессии.
Помогает Claude Code быстро восстановить контекст при следующем запуске.

---

## Текущий статус

**Фаза:** Активная разработка  
**Спринт:** 7B — Skill Tree Core ✅  
**Дата последнего обновления:** 2026-06-11

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

- [ ] Ничего — Спринт 7B завершён, ждём старта Спринта 8

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

### Тесты — 224 теста, все зелёные ✅

### Спринт 7 (остаток) — UI дерева навыков
- [ ] `ui/skill_tree_ui.py` — визуальное дерево
- [x] `systems/hunger.py` — ✅ сделано досрочно (Спринт 3.5)

### Спринт 8 — Квесты + Нарратив
- [ ] `systems/quest_system.py` — триггеры, цели, прогресс
- [ ] `assets/data/quests.json` — данные квестов
- [ ] `systems/lore.py` — записки и терминалы
- [ ] `systems/dialogue.py` — диалоги
- [ ] Сюжетные события глав 1–3

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

---

*Обновляй этот файл в конце каждой рабочей сессии.*
