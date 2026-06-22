from dataclasses import dataclass


@dataclass
class Transition:
    """Зона перехода между картами из TMX object-слоя `transitions` (Sprint 12B).

    Прямоугольная область (пиксели Tiled) + цель: `target_map` (id карты без .tmx) и
    `target_spawn` (имя точки спавна в целевой карте, куда встаёт игрок).
    """

    x: float
    y: float
    width: float
    height: float
    target_map: str
    target_spawn: str
