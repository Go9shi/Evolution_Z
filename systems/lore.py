from data.lore_data import LoreEntry
from systems.event_bus import EventBus


class LoreSystem:
    """Каталог лор-записей и набор открытых игроком.

    register наполняет каталог; unlock переводит запись в открытые и эмитит
    EventBus-событие 'lore_unlocked'. Прямая параллель QuestSystem/DialogueSystem:
    система — единственный владелец состояния открытия, о UI ничего не знает.
    Повторное открытие и неизвестные id безопасны (нет-оп без события).
    """

    def __init__(self) -> None:
        self._entries: dict[str, LoreEntry] = {}
        self._unlocked: list[str] = []

    def register(self, entry: LoreEntry) -> None:
        """Добавить запись в каталог. Повторная регистрация перезаписывает запись."""
        self._entries[entry.id] = entry

    def has_entry(self, entry_id: str) -> bool:
        """Зарегистрирована ли запись с данным id."""
        return entry_id in self._entries

    def is_unlocked(self, entry_id: str) -> bool:
        """Открыта ли запись."""
        return entry_id in self._unlocked

    def unlock(self, entry_id: str) -> bool:
        """Открыть запись. Возвращает True, если открытие новое.

        Нет-оп (возвращает False, событие не эмитится) для неизвестного id и для
        уже открытой записи — гарантирует ровно одно событие 'lore_unlocked' на запись.
        """
        if entry_id not in self._entries:
            return False
        if entry_id in self._unlocked:
            return False
        self._unlocked.append(entry_id)
        EventBus.emit("lore_unlocked", {"entry": self._entries[entry_id]})
        return True

    @property
    def unlocked_entries(self) -> list[LoreEntry]:
        """Открытые записи в порядке открытия (копия — внешняя мутация не трогает систему)."""
        return [self._entries[entry_id] for entry_id in self._unlocked]

    @property
    def entries(self) -> list[LoreEntry]:
        """Все зарегистрированные записи (копия)."""
        return list(self._entries.values())
