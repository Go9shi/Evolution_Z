from core.game_object import GameObject
from systems.event_bus import EventBus


class Entity(GameObject):
    """Игровая сущность с инкапсулированным HP. Основа для игрока и врагов."""

    def __init__(self, x: float, y: float, max_health: int) -> None:
        super().__init__(x, y)
        self._health: int = max_health
        self._max_health: int = max_health

    @property
    def health(self) -> int:
        """Текущее здоровье."""
        return self._health

    @property
    def max_health(self) -> int:
        """Максимальное здоровье."""
        return self._max_health

    @property
    def is_alive(self) -> bool:
        """Жива ли сущность."""
        return self._health > 0

    def take_damage(self, amount: int) -> None:
        """Нанести урон. Уведомляет шину событий о результате."""
        self._health = max(0, self._health - amount)
        if not self.is_alive:
            self.active = False
            EventBus.emit("entity_died", {"entity": self})
        else:
            EventBus.emit("entity_damaged", {"entity": self, "amount": amount})

    def heal(self, amount: int) -> None:
        """Восстановить HP, не превышая максимум."""
        self._health = min(self._max_health, self._health + amount)
        EventBus.emit("entity_healed", {"entity": self, "amount": amount})
