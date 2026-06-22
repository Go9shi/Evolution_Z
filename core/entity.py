from core.game_object import GameObject
from systems.event_bus import EventBus
from systems.health import HealthComponent


class Entity(GameObject):
    """Игровая сущность с инкапсулированным HP. Основа для игрока и врагов."""

    def __init__(self, x: float, y: float, max_health: int) -> None:
        super().__init__(x, y)
        self.health: HealthComponent = HealthComponent(max_health)
        self.faction: str = ""

    @property
    def is_alive(self) -> bool:
        """Жива ли сущность."""
        return self.health.is_alive

    def take_damage(self, amount: float) -> None:
        """Нанести урон. Делегирует компоненту, затем оркестрирует события."""
        self.health.take_damage(amount)
        if not self.is_alive:
            self.active = False
            EventBus.emit("entity_died", {"entity": self})
        else:
            EventBus.emit("entity_damaged", {"entity": self, "amount": amount})

    def heal(self, amount: float) -> None:
        """Восстановить HP, не превышая максимум."""
        self.health.heal(amount)
        EventBus.emit("entity_healed", {"entity": self, "amount": amount})
