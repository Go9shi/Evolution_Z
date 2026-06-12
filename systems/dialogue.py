from __future__ import annotations

from data.dialogue_data import Dialogue, DialogueNode
from systems.event_bus import EventBus


class DialogueError(Exception):
    """Ошибка работы с диалогом: некорректный переход, отсутствующий узел, неверный выбор."""


class DialogueSystem:
    """Рантайм-движок диалогов.

    Хранит текущий диалог и активный узел, продвигает реплики линейно (advance)
    или по выбору игрока (choose). О смене состояния сообщает только через EventBus —
    UI и прочие системы подписываются на события, прямых вызовов нет.
    """

    def __init__(self) -> None:
        self._dialogue: Dialogue | None = None
        self._current: DialogueNode | None = None

    @property
    def is_active(self) -> bool:
        """Идёт ли диалог сейчас."""
        return self._current is not None

    @property
    def current_node(self) -> DialogueNode | None:
        """Активный узел диалога или None, если диалог не идёт."""
        return self._current

    def start(self, dialogue: Dialogue) -> None:
        """Начать диалог с его стартового узла.

        Поднимает DialogueError, если start_id отсутствует в узлах диалога.
        """
        if dialogue.start_id not in dialogue.nodes:
            raise DialogueError(f"Dialogue '{dialogue.id}' has no start node '{dialogue.start_id}'")
        self._dialogue = dialogue
        self._current = dialogue.nodes[dialogue.start_id]
        EventBus.emit("dialogue_started", {"dialogue": dialogue})
        EventBus.emit("dialogue_node_changed", {"node": self._current})

    def advance(self) -> None:
        """Продвинуть линейный диалог к следующему узлу.

        Применимо к узлам с 0 или 1 вариантом: при 0 — диалог завершается,
        при 1 — переход по единственному варианту. При нескольких вариантах
        требуется choose() — иначе DialogueError.
        """
        node = self._require_active()
        if len(node.choices) > 1:
            raise DialogueError("Node has multiple choices; use choose() to pick one")
        if not node.choices:
            self.end()
            return
        self._follow(node.choices[0].next_id)

    def choose(self, index: int) -> None:
        """Выбрать вариант ответа по индексу и перейти к связанному узлу.

        Поднимает DialogueError, если диалог не идёт или индекс вне диапазона.
        """
        node = self._require_active()
        if index < 0 or index >= len(node.choices):
            raise DialogueError(f"Choice index {index} out of range for node '{node.id}'")
        self._follow(node.choices[index].next_id)

    def end(self) -> None:
        """Завершить текущий диалог. Нет-оп, если диалог не идёт."""
        if self._dialogue is None:
            return
        finished = self._dialogue
        self._dialogue = None
        self._current = None
        EventBus.emit("dialogue_ended", {"dialogue": finished})

    def _follow(self, next_id: str) -> None:
        """Перейти к узлу next_id; пустой id завершает диалог."""
        if not next_id:
            self.end()
            return
        assert self._dialogue is not None  # гарантируется _require_active
        target = self._dialogue.nodes.get(next_id)
        if target is None:
            raise DialogueError(f"Dialogue '{self._dialogue.id}' has no node '{next_id}'")
        self._current = target
        EventBus.emit("dialogue_node_changed", {"node": target})

    def _require_active(self) -> DialogueNode:
        """Вернуть активный узел или поднять DialogueError, если диалог не идёт."""
        if self._current is None:
            raise DialogueError("No active dialogue")
        return self._current
