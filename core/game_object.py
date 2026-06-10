import pygame


class GameObject:
    """Базовый класс всех игровых объектов. Хранит позицию и идентификатор."""

    _id_counter: int = 0

    def __init__(self, x: float, y: float) -> None:
        GameObject._id_counter += 1
        self.id: int = GameObject._id_counter
        self.pos: pygame.Vector2 = pygame.Vector2(x, y)
        self.active: bool = True

    def update(self, dt: float) -> None:
        """Обновление логики объекта. dt — время кадра в секундах."""

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка объекта с учётом смещения камеры."""
