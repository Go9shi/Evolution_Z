class HealthComponent:
    """Компонент здоровья. Хранит HP и предоставляет логику изменений без побочных эффектов."""

    def __init__(self, maximum: int) -> None:
        self._maximum: int = maximum
        self._current: int = maximum

    @property
    def current(self) -> int:
        """Текущее здоровье."""
        return self._current

    @property
    def maximum(self) -> int:
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

    def take_damage(self, amount: int) -> None:
        """Уменьшить HP на amount, не опускаясь ниже нуля."""
        self._current = max(0, self._current - amount)

    def heal(self, amount: int) -> None:
        """Восстановить HP на amount, не превышая максимум."""
        self._current = min(self._maximum, self._current + amount)

    def reset(self) -> None:
        """Полностью восстановить HP до максимума."""
        self._current = self._maximum
