from systems.event_bus import EventBus


def required_xp(level: int) -> int:
    """Суммарный XP, необходимый для повышения с данного уровня. Формула: 50 * level * (level + 1)."""
    return 50 * level * (level + 1)


class ExperienceComponent:
    """Компонент опыта и уровней игрока. Накапливает XP, повышает уровень по формуле."""

    def __init__(self) -> None:
        self._current_xp: int = 0
        self._current_level: int = 1

    @property
    def current_xp(self) -> int:
        """Суммарный накопленный XP."""
        return self._current_xp

    @property
    def current_level(self) -> int:
        """Текущий уровень игрока."""
        return self._current_level

    @property
    def xp_to_next_level(self) -> int:
        """XP, которого не хватает до следующего уровня."""
        return required_xp(self._current_level) - self._current_xp

    def add_xp(self, amount: int) -> bool:
        """Добавить XP. Возвращает True если произошёл хотя бы один level-up."""
        self._current_xp += amount
        EventBus.emit("player_xp_gained", {"amount": amount, "total_xp": self._current_xp})
        leveled_up = False
        while self._current_xp >= required_xp(self._current_level):
            self._current_level += 1
            leveled_up = True
            EventBus.emit("player_level_up", {"level": self._current_level})
        return leveled_up
