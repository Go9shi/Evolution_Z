from dataclasses import dataclass


@dataclass
class NpcData:
    """Запись NPC из TMX object-слоя `npcs` (Sprint 13A): id, диалог и пиксельная позиция.

    Минимальная модель: без деревьев поведения и боя. `dialogue_id` ссылается на диалог
    из существующей DialogueSystem; позиция — абсолютные пиксели Tiled.
    """

    npc_id: str
    dialogue_id: str
    x: float
    y: float
