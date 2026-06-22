from pathlib import Path

import pygame

from settings import SPRITES_DIR


class AssetLoader:
    """Кэширующий загрузчик статических спрайтов PNG (Sprint 11C).

    `get(name)` грузит `SPRITES_DIR/<name>.png` один раз и кэширует Surface. Отсутствующий
    файл кэшируется как None (negative cache) — игра не падает и не пытается грузить повторно.
    Анимации/sprite sheets — вне скоупа: только статические изображения.
    """

    _cache: dict[str, pygame.Surface | None] = {}

    @classmethod
    def get(cls, name: str | None) -> pygame.Surface | None:
        """Вернуть кэшированный Surface спрайта по имени или None, если файла нет."""
        if not name:
            return None
        if name in cls._cache:
            return cls._cache[name]
        surface = cls._load(SPRITES_DIR / f"{name}.png")
        cls._cache[name] = surface
        return surface

    @staticmethod
    def _load(path: Path) -> pygame.Surface | None:
        """Загрузить PNG с convert_alpha; None при отсутствии файла, raw-Surface без видеорежима."""
        try:
            surface = pygame.image.load(str(path))
        except (FileNotFoundError, pygame.error):
            return None
        try:
            return surface.convert_alpha()
        except pygame.error:
            return surface  # нет активного видеорежима (напр. в тестах) — отдаём как есть

    @classmethod
    def draw_sprite(cls, surface: pygame.Surface, name: str | None, rect: pygame.Rect) -> bool:
        """Нарисовать спрайт `name`, вписанный в `rect`. True — нарисован; False — fallback нужен."""
        sprite = cls.get(name)
        if sprite is None:
            return False
        surface.blit(pygame.transform.scale(sprite, (rect.width, rect.height)), (rect.x, rect.y))
        return True

    @classmethod
    def clear(cls) -> None:
        """Очистить кэш спрайтов (изоляция тестов / смена набора ассетов)."""
        cls._cache.clear()
