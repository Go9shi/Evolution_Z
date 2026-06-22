# Architecture Document
## Evolution Z

> Версия: 0.2  
> Стек: Python 3.12.1 · pygame-ce · pytmx · dataclasses · json

---

## Общая структура игры

Все основные объекты и системы подчиняются классу `Game`.  
Он владеет игровым миром, игроком, врагами, инвентарём, интерфейсом и сохранениями.

```
Game
│
├── World          # карта, камера, тайлы, спавн объектов
├── Player         # управление, характеристики, прогресс
├── Enemy          # AI, поведение, атаки
├── Inventory      # слоты предметов, экипировка
├── Item           # предметы мира: лут, аптечки, компоненты
├── UI             # HUD, меню, диалоги, экраны
└── SaveManager    # сериализация и загрузка состояния
```

---

## Наследование

Все живые объекты и предметы наследуются от базового класса `Entity`.  
Это позволяет использовать единый интерфейс: `update()`, `draw()`, `take_damage()`.

```
Entity
├── Player
│   └── (единственный экземпляр, управляется игроком)
├── Zombie
│   ├── WalkerZombie    # медленный, высокий HP, ближний бой
│   ├── RunnerZombie    # быстрый, низкий HP, рывок
│   ├── SpitterZombie   # дальний бой, кислотный плевок
│   └── PatientZeroBoss # финальный босс, 3 фазы
├── Item
│   ├── MedKit          # восстанавливает здоровье
│   ├── Ammo            # патроны
│   └── VaccineComponent # компонент вакцины (ключевой предмет)
└── Resource
    ├── PowerCell       # питание для гермодверей
    └── KeyCard         # доступ в закрытые зоны
```

Пример цепочки наследования для финального босса:
```
Entity → Zombie → Boss → PatientZeroBoss
```

---

## Композиция

`Player` не наследует системы — он их **содержит**.  
Каждая система — отдельный объект со своей ответственностью.

```
Player
├── Inventory      # сетка слотов, подбор и использование предметов
├── Health         # HP, максимальный HP, регенерация
└── Hunger         # голод, скорость убывания, эффекты
```

Пример в коде:
```python
class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos)
        self.inventory = Inventory(slots=20)   # has-a
        self.health    = HealthComponent(hp=100)  # has-a
        self.hunger    = HungerComponent(max=100) # has-a
```

Такой подход проще наследования: каждый компонент можно изменить,  
протестировать и переиспользовать независимо от остальных.

---

## Структура файлов

```
project_eden/
├── main.py                     # точка входа, Game loop
├── settings.py                 # константы: FPS, разрешение, цвета
│
├── core/
│   ├── entity.py               # Entity — базовый класс
│   ├── weapon.py               # Weapon — базовое оружие
│   └── item.py                 # Item — базовый предмет
│
├── entities/
│   ├── player.py               # Player(Entity)
│   ├── zombie.py               # Zombie + WalkerZombie / Runner / Spitter
│   └── boss.py                 # Boss + PatientZeroBoss
│
├── systems/
│   ├── game_world.py           # World: карта, камера, спавн
│   ├── inventory.py            # Inventory: слоты, предметы
│   ├── health.py               # HealthComponent
│   ├── hunger.py               # HungerComponent
│   ├── combat.py               # пули, хитбоксы, урон
│   ├── quest_system.py         # квесты и триггеры
│   ├── skill_tree.py           # дерево навыков
│   ├── save_system.py          # SaveManager: JSON сохранение
│   └── event_bus.py            # pub/sub шина событий
│
└── ui/
    ├── base_screen.py          # Screen(ABC)
    ├── main_menu.py
    ├── game_screen.py          # HUD
    ├── inventory_ui.py
    └── pause_menu.py
```

---

## Принципы ООП — итоговая таблица

| Принцип | Где | Пример |
|---|---|---|
| Наследование | `core/` → `entities/` | `WalkerZombie(Zombie(Entity))` |
| Полиморфизм | `systems/game_world.py` | `enemy.update(dt)` у каждого типа — своя логика |
| Инкапсуляция | `systems/health.py` | `_hp` скрыт, доступ через `take_damage()` и `@property` |
| Композиция | `entities/player.py` | `Player` содержит `Inventory`, `Health`, `Hunger` |

---

*Документ обновляется по мере разработки.*