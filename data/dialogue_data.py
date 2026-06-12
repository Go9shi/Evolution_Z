from dataclasses import dataclass, field


@dataclass
class DialogueChoice:
    """Вариант ответа игрока в узле диалога.

    next_id указывает на узел, к которому переходит диалог при выборе.
    Пустая строка означает завершение диалога.
    """

    text: str
    next_id: str = ""


@dataclass
class DialogueNode:
    """Узел диалога: реплика говорящего и варианты ответа.

    Узел без вариантов (choices пуст) — терминальный: после него диалог завершается.
    """

    id: str
    speaker: str
    text: str
    choices: list[DialogueChoice] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        """Терминальный ли узел (нет вариантов ответа)."""
        return not self.choices


@dataclass
class Dialogue:
    """Диалог как граф узлов с точкой входа.

    nodes отображает id узла в сам узел; start_id — узел, с которого начинается диалог.
    """

    id: str
    nodes: dict[str, DialogueNode]
    start_id: str
