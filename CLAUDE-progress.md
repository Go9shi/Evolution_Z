# CLAUDE-progress.md — Evolution Z

Этот файл обновляется вручную после каждой рабочей сессии.
Помогает Claude Code быстро восстановить контекст при следующем запуске.

---

## Текущий статус

**Фаза:** Активная разработка  
**Спринт:** 3.5 — Hunger System  
**Дата последнего обновления:** 2026-06-10

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

---

## В работе прямо сейчас

- [ ] Ничего — Спринт 3.5 завершён, ждём старта Спринта 4

---

## Что делать дальше (бэклог)

### Спринт 3 — Карта + Коллизии ✅ (завершён)

### Спринт 4 — Боёвка
- [ ] `core/weapon.py` — базовый класс оружия
- [ ] `entities/weapons/pistol.py` — первое оружие
- [ ] `entities/bullet.py` — пуля как GameObject
- [ ] `systems/combat.py` — хитбоксы, урон, группы спрайтов
- [x] `systems/health.py` — ✅ сделано досрочно
- [ ] Запускаемый прототип: игрок стреляет, пули летят

### Спринт 5 — Враги
- [ ] AI-стейты в Entity: IDLE, PATROL, CHASE, ATTACK
- [ ] `entities/zombie.py` — `Zombie(Entity)` + `WalkerZombie`, `RunnerZombie`, `SpitterZombie`
- [ ] Спавн врагов через TMX object layer
- [ ] Запускаемый прототип: враги патрулируют, реагируют, умирают

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

---

## Известные проблемы и риски

| # | Описание | Приоритет | Статус |
|---|---|---|---|
| 1 | ~~Нет карты — игрок ходит по пустому фону~~ | ~~высокий~~ | ✅ Решено в Спринте 3 |
| 2 | Игрок умирает от голода без возможности поесть (еда появится в Спринте 6) | средний | Временно: `hunger_decay_rate=2.0` → опустошение за 50 сек; при необходимости снизить до 0.1 |
| 3 | Camera не ограничена границами мира (может выйти за пределы карты) | низкий | Решится при добавлении TMX или в Спринте 10 |

---

## Заметки

> `player.health` — это `HealthComponent`, не int. Для получения числа: `player.health.current`.  
> Для HP-бара: `player.health.percentage` (float 0.0–1.0).  
> `player.hunger` — это `HungerComponent`. Для hunger-бара: `player.hunger.percentage`.  
> `take_damage` / `heal` принимают `float` (не `int`) — дробный урон корректен.  
> При смене сцены вызывать `EventBus.clear()`.

---

*Обновляй этот файл в конце каждой рабочей сессии.*
