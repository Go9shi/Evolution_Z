from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto


class QuestStatus(Enum):
    """Статус квеста."""

    AVAILABLE = auto()
    ACTIVE = auto()
    COMPLETED = auto()


class Objective(ABC):
    """Абстрактная цель квеста. Реагирует на игровые события и сигнализирует о завершении."""

    def on_kill(self, faction: str) -> None:
        """Уведомить цель, что убита сущность данной фракции. По умолчанию — нет реакции."""

    def on_event(self, event_name: str) -> None:
        """Уведомить цель о мировом событии (напр. вход в зону). По умолчанию — нет реакции."""

    @property
    @abstractmethod
    def is_complete(self) -> bool:
        """Выполнена ли цель."""

    @property
    @abstractmethod
    def progress(self) -> str:
        """Человекочитаемый прогресс цели для отображения, напр. '3/5'."""


class KillZombieObjective(Objective):
    """Цель: убить N зомби-врагов."""

    def __init__(self, target_count: int) -> None:
        self.target_count: int = target_count
        self.current_count: int = 0

    def on_kill(self, faction: str) -> None:
        """Увеличить счётчик при гибели сущности фракции 'enemy'."""
        if faction == "enemy" and not self.is_complete:
            self.current_count += 1

    @property
    def is_complete(self) -> bool:
        """Выполнена, когда убито target_count врагов."""
        return self.current_count >= self.target_count

    @property
    def progress(self) -> str:
        """Прогресс в формате 'current/target', напр. '3/5'."""
        return f"{self.current_count}/{self.target_count}"


class ReachZoneObjective(Objective):
    """Цель: получить мировое событие `event_name` (напр. вход в зону-триггер).

    Имя события — данные (из квеста), а не хардкод: цель сама сверяет приходящее
    событие со своим `event_name`. Завершается при первом совпадении.
    """

    def __init__(self, event_name: str) -> None:
        self.event_name: str = event_name
        self._reached: bool = False

    def on_event(self, event_name: str) -> None:
        """Отметить выполнение при совпадении события с целевым `event_name`."""
        if event_name == self.event_name:
            self._reached = True

    @property
    def is_complete(self) -> bool:
        """Выполнена, когда нужное событие получено."""
        return self._reached

    @property
    def progress(self) -> str:
        """Прогресс '1/1' после события, иначе '0/1'."""
        return "1/1" if self._reached else "0/1"


@dataclass
class Quest:
    """Квест с набором целей и XP-наградой за выполнение.

    Narrative-метаданные (lore_text, location, category) — опциональны и не влияют
    на игровую логику; QuestSystem их не использует. Служат только для отображения.
    """

    id: str
    title: str
    description: str
    reward_xp: int
    objectives: list[Objective] = field(default_factory=list)
    status: QuestStatus = QuestStatus.AVAILABLE
    lore_text: str = ""
    location: str = ""
    category: str = ""
