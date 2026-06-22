class HealthComponent:
    """Компонент здоровья. Хранит HP и предоставляет логику изменений без побочных эффектов."""

    def __init__(self, maximum: float) -> None:
        self._maximum: float = maximum
        self._current: float = maximum

    @property
    def current(self) -> float:
        """Текущее здоровье."""
        return self._current

    @property
    def maximum(self) -> float:
        """Максимальное здоровье."""
        return self._maximum

    @property
    def is_alive(self) -> bool:
        """Жива ли сущность."""
        return self._current > 0

    @property
    def percentage(self) -> float:
        """Доля HP от максимума в диапазоне 0.0–1.0. Используется для HP-бара."""
        return self._current / self._maximum if self._maximum > 0 else 0.0

    def take_damage(self, amount: float) -> None:
        """Уменьшить HP на amount, не опускаясь ниже нуля."""
        self._current = max(0.0, self._current - amount)

    def heal(self, amount: float) -> None:
        """Восстановить HP на amount, не превышая максимум."""
        self._current = min(self._maximum, self._current + amount)

    def increase_maximum(self, amount: float) -> None:
        """Увеличить максимум и текущее HP на одинаковую величину (ограничено новым максимумом)."""
        self._maximum += amount
        self._current = min(self._current + amount, self._maximum)

    def reset(self) -> None:
        """Полностью восстановить HP до максимума."""
        self._current = self._maximum
