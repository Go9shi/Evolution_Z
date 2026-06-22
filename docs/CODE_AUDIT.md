# Технический аудит проекта Evolution Z

**Аудитор:** Software Architect / Technical Lead
**Стек:** Python 3.12 · pygame-ce · pytmx · dataclasses · json · pytest/ruff/mypy
**Объём:** ~5 100 строк production-кода (50 модулей) + 56 тест-файлов (1100 тестов)
**Тип:** учебная (дипломная) игра — top-down survival action

---

## 1. Общее назначение проекта

**Задача.** Evolution Z — одиночная 2D top-down survival-action игра («Проект ЭДЕМ»): игрок-выживший
в заражённом бункере получает квест от NPC, отстреливает заражённых, собирает лут, прокачивается и
убивает финального босса (Patient Zero) → экран Victory.

**Бизнес-смысл (учебный).** Цель — не контент, а демонстрация ООП и архитектуры: проект построен так,
чтобы каждый принцип (наследование, инкапсуляция, полиморфизм, композиция, SOLID, событийная развязка,
data-driven) был виден в коде явно. Зафиксировано в `CLAUDE.md`.

**Основные сценарии.**
- Запуск → меню → New Game / Continue / Quit (`ui/main_menu.py`).
- Игровой цикл: WASD, стрельба (ЛКМ), диалог (T), еда (F), инвентарь (I), квесты (J), навыки (Tab),
  лор (L), пауза (ESC), сейв/лоад (F5/F9).
- Прогресс: квест → убийства → XP → уровень → очки навыков.
- Финал: убийство босса → Victory; смерть игрока → Game Over.

**Взаимодействие частей.** `main.py` крутит цикл и стек экранов; активный экран (`ui/game_screen.py`)
владеет миром, игроком, врагами и системами; все побочные эффекты идут через `EventBus`
(бой → XP → квесты → UI), без прямых вызовов между подсистемами.

---

## 2. Архитектура проекта

### Тип
Modular Monolith со слоистой (Layered) организацией и Event-Driven ядром. Не классический MVC, но есть
чёткое разделение «модель данных / игровая логика / представление». Плюс паттерны State (стек экранов),
Component/Composition (сущности), Template Method (AI), Strategy/полиморфизм (оружие, цели квестов).

### Слои

| Слой | Каталог/файлы | Ответственность | Зависимости |
|---|---|---|---|
| Presentation | `ui/`, `main.py` (render) | Отрисовка, ввод, экраны | → Application, Domain (чтение) |
| Application | `ui/game_screen.py`, `main.py` (`Game`, `GameStateManager`) | Оркестрация, роутинг ввода, жизненный цикл экранов | → Domain, Infrastructure |
| Domain | `core/`, `entities/`, `systems/` | Правила игры: бой, AI, прогрессия, квесты | → Data, EventBus |
| Data | `data/*.py` + загрузчики | Модели и валидация контента | → ничего |
| Infrastructure | `asset_loader.py`, `save_system.py`, `game_world.py` (pytmx), JSON-loaders | Файловый IO | → Data |
| Cross-cutting | `event_bus.py`, `settings.py` | Шина событий, константы | используется всеми |

### Схема
```
            main.py: Game loop + GameStateManager      (точка входа)
                                |
        PRESENTATION  ui/ (GameScreen, HUD, *_ui)
                                |
        DOMAIN  core/ + entities/ + systems/
        Combat · AI · Quest · Dialogue · Progression
              |                               |
        DATA  data/  <---- строит из ---- INFRASTRUCTURE
        dataclasses + loaders   JSON/TMX   AssetLoader, SaveSystem, GameWorld(pytmx)

        CROSS-CUTTING: EventBus (pub/sub), settings
```

Правило (соблюдается): системы не импортируют UI; UI читает домен через публичный API; межсистемная
связь — только через `EventBus`. Доказательство: `systems/combat.py` эмитит `"bullet_hit"`, а не зовёт HUD;
`systems/quest_system.py` подписан на `"entity_died"`, а не вызывается из боя.

---

## 3. Структура каталогов

```
Evolution_Z/
├── main.py                  # точка входа, игровой цикл, стек экранов
├── settings.py              # все константы и пути (нет магических чисел)
├── core/                    # базовые абстракции (вершины иерархий)
│   ├── game_object.py       # GameObject
│   ├── entity.py            # Entity(GameObject)
│   ├── weapon.py            # Weapon(ABC)
│   └── item.py              # Item(GameObject, ABC)
├── entities/                # конкретные игровые объекты
│   ├── player.py · zombie.py · boss.py · bullet.py · npc.py
│   ├── weapons/             # Pistol, Rifle, Shotgun
│   └── items/               # FoodItem, QuestItem
├── systems/                 # игровые системы (логика)
│   ├── event_bus.py · combat.py · quest_system.py
│   ├── dialogue.py · lore.py · experience.py · skill_tree.py · inventory.py
│   ├── health.py · hunger.py · animation.py · camera.py
│   ├── asset_loader.py · game_world.py · level_manager.py · save_system.py
├── data/                    # @dataclass-модели + загрузчики (валидация)
├── ui/                      # экраны (State pattern)
├── assets/ (data/maps/sprites/sounds) · tools/ · tests/ · docs/
```

Почему так: `core/` отделён от `entities/` (базовые контракты независимы от конкретики); `data/` —
чистые модели без логики; `systems/` — логика вынесена из сущностей (композиция); `ui/` — представление
отделено правилом «нет геймплея в UI»; `tools/` — пайплайн ассетов вне рантайма.

---

## 4. Анализ классов (ключевые)

- **Game** (`main.py`): окно, цикл `run()` (dt→events→update→render→flip), `GameStateManager`.
- **GameStateManager** (`main.py`): стек экранов (State); `pop` зовёт `cleanup()`.
- **GameObject** (`core/game_object.py`): база — `id/pos/active`, заглушки `update/draw`.
- **Entity(GameObject)** (`core/entity.py`): композиция `health`, `faction`; `take_damage`→`entity_died`.
- **Player(Entity)** (`entities/player.py`): композиция hunger/weapon/inventory/experience/skill_tree/animation.
- **Zombie(Entity, ABC)** (`entities/zombie.py`): Template Method `update`→`update_ai`; Walker/Runner/Spitter.
- **PatientZeroBoss** (`entities/boss.py`): двухфазный AI (кислота+призыв), эмитит `boss_defeated`.
- **EventBus** (`systems/event_bus.py`): pub/sub (`on/off/emit/clear`).
- **CombatSystem** (`systems/combat.py`): пули, AABB-попадание, `Targetable(Protocol)`.
- **QuestSystem** (`systems/quest_system.py`): приём/прогресс/финализация квестов через события.
- **Objective(ABC)** (`data/quest_data.py`): KillZombie/ReachZone (хуки `on_kill/on_event`).
- **SaveSystem** (`systems/save_system.py`): `capture`/`apply` (XP первым), сохраняет id, не объекты.
- **AnimationComponent** (`systems/animation.py`): directional-анимация, fallback-цепочка.
- **GameWorld** (`systems/game_world.py`): загрузка TMX (pytmx), `wall_rects`, отрисовка тайлов.
- **GameScreen(BaseScreen)** (`ui/game_screen.py`): оркестратор игрового слоя.

---

## 5. Анализ ООП

- **Инкапсуляция (9/10):** приватные поля компонентов (`_current/_maximum`), доступ через свойства/методы.
- **Наследование (9/10):** строгие иерархии ≤3 уровней; нет множественного наследования сущностей.
- **Полиморфизм (10/10):** `update/fire/use/on_*`; нет `isinstance` для выбора поведения.
- **Абстракции (9/10):** `ABC` (Weapon/Item/Objective/Zombie), `Protocol` (Targetable).

---

## 6. SOLID

- **S (9/10):** системы однозадачны; минус — `GameScreen` перегружен (composition root).
- **O (9/10):** новый Objective/Weapon/Zombie/Screen без правок существующего (билдеры/наследование).
- **L (9/10):** подклассы взаимозаменяемы; `Shotgun.fire` сохраняет контракт `list[Bullet]`.
- **I (9/10):** узкие интерфейсы (`Targetable`, `BaseScreen`).
- **D (8/10):** зависимость от событий/протоколов; минус — глобальные `EventBus`/`AssetLoader`.

---

## 7. Другие принципы

DRY 8 (дубли `Pistol/Rifle.fire`, hit-flash ×2) · KISS 9 · YAGNI 7 (level2-stub, лишние кадры,
`_build_grid` legacy) · SoC 9 · High Cohesion 9 · Low Coupling 9 · Law of Demeter 7 ·
Composition over Inheritance 10 (эталон).

---

## 8. Паттерны

State (стек экранов) · Observer (EventBus) · Template Method (Zombie AI) · Strategy/полиморфизм
(Weapon/Objective) · Factory/Builder dispatch (`_OBJECTIVE_BUILDERS`, `SaveSystem._build_item`) ·
Component/Composition · Repository-ish/Data Mapper (loaders, `SaveData.to_dict/from_dict`) ·
Facade (GameScreen) · Singleton (EventBus/AssetLoader) · Object Pool (пули) · Protocol (Targetable).
Отсутствуют (и не нужны): CQRS, Mediator, Unit of Work, DI-контейнер.

---

## 9. Поток выполнения

```
main.py __main__ → Game() → push(MainMenuScreen) → Game.run() (events→update→render→flip)
New Game → pop(menu)→push(GameScreen): LevelManager→GameWorld(level1.tmx), spawn из spawns, системы, подписки
Тик: player→enemies(update_ai)→boss→combat(AABB→take_damage→bullet_hit)→подбор→triggers→transitions
Выстрел: ЛКМ→fire→Bullet→CombatSystem→take_damage→entity_died
  ├ GameScreen._on_entity_died → add_xp → player_level_up → очко навыка
  └ QuestSystem._on_entity_died → Objective.on_kill → _finalize → quest_completed (+XP)
Бизнес-логика: systems/+entities/. «БД»: файловый IO. Внешних сервисов нет. Результат: кадр + Victory/GameOver.
```

---

## 10. Качество кода (1–10)

Читаемость 9 · Поддерживаемость 9 · Расширяемость 9 · Тестируемость 10 · Cohesion 9 · Coupling 9 ·
Сложность методов 7 (GameScreen/Boss.update длиннее) · Дублирование 7.

---

## 11. Потенциальные проблемы

1. `GameScreen` (582 стр) — крупный координатор → дробление хелперов.
2. Глобальные `EventBus`/`AssetLoader` (синглтоны) → скрытые зависимости (митигировано `cleanup`/`clear`).
3. Мёртвый код/ассеты: `game_world._build_grid`, rifle/shotgun (в рантайме не экипируются, но тестируются),
   ~600 неиспользуемых кадров, orphan `level2.tmx`.
4. Дубли: `Pistol/Rifle.fire`, hit-flash-блоки.
5. Геймплейный дисбаланс (кайт, босс-губка) — частично смягчено в 15B.
6. Циклы импортов нет (через `TYPE_CHECKING`).
7. Производительность: flip/alpha-surface каждый кадр — кешировать при масштабе.

---

## 13. Итоговое заключение

Архитектура выше среднего для учебного проекта: осознанная слоистая модульная структура с событийным
ядром, чистым разделением data/logic/presentation и сильными OCP-точками. Разработчик — уверенный middle
с дисциплиной senior по тестированию.

**Сильные стороны:** разделение model/view, слабое зацепление (EventBus/Protocol), полиморфизм и
расширяемость, композиция компонентов, 1100 тестов + ruff/mypy зелёные, data-driven, graceful fallback.

**Слабые стороны:** перегруженный `GameScreen`, глобальные синглтоны, мёртвый код/ассеты, точечные дубли,
нет «тяжёлых» алгоритмов и звука.

**Изучить автору:** Dependency Injection (уход от синглтонов), декомпозиция composition root,
Mediator/Command, профилирование/кеширование рантайма.

**Итоговая оценка: 8.5 / 10.** Зрелая, хорошо протестированная и расширяемая архитектура с явной
демонстрацией принципов проектирования; для дипломной работы — заметно выше типичного уровня.
