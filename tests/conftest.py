import pygame
import pytest

from systems.event_bus import EventBus


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    """Инициализация pygame для всех тестов. pygame.Vector2 и Rect требуют init."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def clean_event_bus():
    """Очистка EventBus до и после каждого теста — шина является глобальным состоянием."""
    EventBus.clear()
    yield
    EventBus.clear()
