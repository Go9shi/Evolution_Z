# CLAUDE-progress.md — Evolution Z

Этот файл обновляется вручную после каждой рабочей сессии.
Помогает Claude Code быстро восстановить контекст при следующем запуске.

---

## Текущий статус

**Фаза:** Активная разработка  
**Спринт:** 3 — Карта + Коллизии  
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

---

## В работе прямо сейчас

- [ ] Ничего — ждём старта Спринта 3

---

## Что делать дальше (бэклог)

### Спринт 3 — Карта + Коллизии (следующий)
- [ ] `systems/game_world.py` — загрузка `.tmx` через pytmx, рендер тайлов
- [ ] Коллизии игрока со стенами (слой объектов из TMX)
- [ ] `assets/maps/bunker_a1.tmx` — создать первую карту в Tiled
- [ ] Обновить `GameScreen`: передавать `GameWorld` в `update` и `draw`
- [ ] Запускаемый прототип: игрок ходит по карте бункера, стены блокируют

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
- [ ] `systems/hunger.py` — компонент голода

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

---

## Известные проблемы и риски

| # | Описание | Приоритет | Статус |
|---|---|---|---|
| 1 | Нет карты — игрок ходит по пустому фону | высокий | Спринт 3 |
| 2 | Нет визуального подтверждения движения (камера следит, фон однородный) | средний | Решится в Спринте 3 с тайлами |

---

## Заметки

> `player.health` — это `HealthComponent`, не int. Для получения числа: `player.health.current`.  
> Для HP-бара: `player.health.percentage` (float 0.0–1.0).  
> При смене сцены вызывать `EventBus.clear()`.

---

*Обновляй этот файл в конце каждой рабочей сессии.*
