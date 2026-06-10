# CLAUDE-progress.md — Evolution Z

Этот файл обновляется вручную после каждой рабочей сессии.
Помогает Claude Code быстро восстановить контекст при следующем запуске.

---

## Текущий статус

**Фаза:** Активная разработка  
**Спринт:** 5A — Базовая боевая система ✅  
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

- [ ] Ничего — Спринт 5A завершён, ждём старта Спринта 5B

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

### Спринт 5B — SpitterZombie (следующий)
- [ ] `entities/zombie.py` — добавить `SpitterZombie` + `AIState.REPOSITION`
- [ ] `assets/data/enemies.json` — конфиг spitter
- [ ] Запускаемый прототип: Spitter отступает и плюётся, пули попадают в игрока

### Спринт 6 — Инвентарь + Предметы (бывший 5)

### Спринт 6 — Инвентарь + Предметы
- [ ] `systems/inventory.py` — сетка слотов
- [ ] `core/item.py` — базовый предмет
- [ ] `assets/data/items.json` — конфиги предметов
- [ ] Подбор предметов с пола
- [ ] `ui/inventory_ui.py` — отображение инвентаря
- [ ] Компоненты вакцины как предметы

### Спринт 7 — Прогрессия
- [ ] XP и уровни в `Player`
- [ ] `systems/skill_tree.py` — три ветки навыков
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

---

## Известные проблемы и риски

| # | Описание | Приоритет | Статус |
|---|---|---|---|
| 1 | ~~Нет карты — игрок ходит по пустому фону~~ | ~~высокий~~ | ✅ Решено в Спринте 3 |
| 2 | Игрок умирает от голода без возможности поесть (еда появится в Спринте 6) | средний | Временно: `hunger_decay_rate=2.0` → опустошение за 50 сек; при необходимости снизить до 0.1 |
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
> `Bullet.origin_tag == "player"` — пригодится в Sprint 5B, когда SpitterZombie будет создавать enemy-пули.

---

*Обновляй этот файл в конце каждой рабочей сессии.*
