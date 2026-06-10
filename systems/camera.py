import pygame

from settings import SCREEN_H, SCREEN_W


class Camera:
    """Камера, центрированная на цели. Вычисляет offset для рендера объектов."""

    def __init__(self) -> None:
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)

    def follow(self, target_pos: pygame.Vector2) -> None:
        """Переместить камеру так, чтобы цель оказалась в центре экрана."""
        self.offset.x = target_pos.x - SCREEN_W // 2
        self.offset.y = target_pos.y - SCREEN_H // 2
