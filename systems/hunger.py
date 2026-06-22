class HungerComponent:
    """Компонент сытости. Убывает со временем; при 0 — голодание."""

    def __init__(self, maximum: float, decay_rate: float) -> None:
        self._maximum: float = maximum
        self._current: float = maximum
        self._decay_rate: float = decay_rate

    @property
    def current(self) -> float:
        """Текущий уровень сытости."""
        return self._current

    @property
    def maximum(self) -> float:
        """Максимальный уровень сытости."""
        return self._maximum

    @property
    def percentage(self) -> float:
        """Доля сытости 0.0–1.0, для HUD-бара."""
        return self._current / self._maximum

    @property
    def is_starving(self) -> bool:
        """True, когда сытость достигла нуля."""
        return self._current <= 0.0

    def update(self, dt: float) -> None:
        """Уменьшить сытость на decay_rate * dt. Не ниже 0."""
        self._current = max(0.0, self._current - self._decay_rate * dt)

    def consume(self, amount: float) -> None:
        """Восстановить сытость (еда). Не превышает максимум."""
        self._current = min(self._maximum, self._current + amount)

    def reduce_decay_rate(self, amount: float) -> None:
        """Уменьшить скорость убывания сытости. Не ниже нуля."""
        self._decay_rate = max(0.0, self._decay_rate - amount)

    def reset(self) -> None:
        """Восстановить сытость до максимума."""
        self._current = self._maximum
