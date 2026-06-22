from typing import Callable

from data.quest_data import Quest, QuestStatus
from systems.event_bus import EventBus
from systems.experience import ExperienceComponent


class QuestSystem:
    """Управляет квестами: принятие, отслеживание прогресса через EventBus, выдача XP."""

    def __init__(self, exp_component: ExperienceComponent) -> None:
        self._active: list[Quest] = []
        self._completed: list[Quest] = []
        self._exp: ExperienceComponent = exp_component
        # Подписки на world-события (Sprint 13C): имя события → bound-хендлер. Имена берутся
        # из данных целей (objective.event_name), а не хардкодятся. Снимаются при teardown.
        self._event_subs: dict[str, Callable[[dict], None]] = {}
        EventBus.on("entity_died", self._on_entity_died)

    @property
    def active_quests(self) -> list[Quest]:
        """Список активных квестов (копия)."""
        return list(self._active)

    @property
    def completed_quests(self) -> list[Quest]:
        """Список завершённых квестов (копия)."""
        return list(self._completed)

    def accept_quest(self, quest: Quest) -> None:
        """Принять квест. Статус меняется AVAILABLE → ACTIVE. Повторный вызов игнорируется."""
        if quest.status != QuestStatus.AVAILABLE:
            return
        quest.status = QuestStatus.ACTIVE
        self._active.append(quest)
        self._subscribe_world_events(quest)

    def update_progress(self, event_data: dict) -> None:
        """Обработать событие гибели сущности и обновить цели активных квестов."""
        entity = event_data.get("entity")
        if entity is None:
            return
        faction: str = getattr(entity, "faction", "")
        for quest in list(self._active):
            for obj in quest.objectives:
                obj.on_kill(faction)
            self._try_complete(quest)

    def complete_quest(self, quest: Quest) -> None:
        """Принудительно завершить активный квест и выдать XP. Нет-оп если квест не активен."""
        if quest not in self._active:
            return
        self._finalize(quest)

    def restore(self, active: list[Quest], completed: list[Quest]) -> None:
        """Восстановить состояние квестов из сохранения.

        Заменяет текущие списки активных/завершённых. НЕ выдаёт XP и НЕ эмитит события
        (в отличие от accept_quest/complete_quest) — награды уже были получены в сейве.
        Используется SaveSystem; обычный игровой поток её не вызывает.
        """
        self._active = []
        self._completed = []
        for quest in active:
            quest.status = QuestStatus.ACTIVE
            self._active.append(quest)
            self._subscribe_world_events(quest)
        for quest in completed:
            quest.status = QuestStatus.COMPLETED
            self._completed.append(quest)

    def _on_entity_died(self, data: dict) -> None:
        self.update_progress(data)

    # ── world events (Sprint 13C) ───────────────────────────────────────────

    def _subscribe_world_events(self, quest: Quest) -> None:
        """Подписаться на world-события, объявленные целями квеста (имена — из данных).

        Каждая цель может объявить нужное событие через атрибут `event_name`. Имя берётся
        обобщённо (без хардкода и без if под конкретный квест); общий хендлер диспатчит
        событие всем активным целям.
        """
        for obj in quest.objectives:
            name: str = getattr(obj, "event_name", "")
            if name and name not in self._event_subs:
                handler = self._make_world_handler(name)
                self._event_subs[name] = handler
                EventBus.on(name, handler)

    def _make_world_handler(self, event_name: str) -> Callable[[dict], None]:
        """Создать хендлер EventBus, помнящий имя события (closure)."""
        def handler(_data: dict) -> None:
            self._on_world_event(event_name)
        return handler

    def _on_world_event(self, event_name: str) -> None:
        """Прогресс по world-событию: уведомить цели активных квестов и проверить завершение."""
        for quest in list(self._active):
            for obj in quest.objectives:
                obj.on_event(event_name)
            self._try_complete(quest)

    def _try_complete(self, quest: Quest) -> None:
        if not quest.objectives:
            return
        if all(obj.is_complete for obj in quest.objectives):
            self._finalize(quest)

    def _finalize(self, quest: Quest) -> None:
        quest.status = QuestStatus.COMPLETED
        self._active.remove(quest)
        self._completed.append(quest)
        self._exp.add_xp(quest.reward_xp)
        EventBus.emit("quest_completed", {"quest": quest})
