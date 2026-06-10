import pygame


class BaseScreen:
    """Базовый класс для всех игровых экранов (состояний)."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Обработка одного события pygame."""

    def update(self, dt: float) -> None:
        """Обновление логики экрана. dt — время кадра в секундах."""

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовка экрана на переданной поверхности."""
