"""Кадровая анимация поверх существующего AssetLoader (Sprint 14B).

Архитектурный слой: система готова принять реальные spritesheets позже, но PNG пока
нет, поэтому имена кадров (`<prefix>_<state>_<i>`) резолвятся в None и рендер уходит в
статический SPRITE-fallback — геймплей не меняется. Никакой логики боя/движения здесь нет:
компонент лишь выбирает текущий кадр по состоянию и времени.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pygame

from settings import ANIMATION_FPS
from systems.asset_loader import AssetLoader


class AnimState(Enum):
    """Состояния анимации сущности. Значение — токен в имени кадра (`player_idle_0`)."""

    IDLE = "idle"
    WALK = "walk"
    ATTACK = "attack"
    DEATH = "death"


class Facing(Enum):
    """Логическое направление взгляда сущности (Sprint 14C.2, Variant B)."""

    DOWN = "down"
    UP = "up"
    LEFT = "left"
    RIGHT = "right"


# Маппинг логического направления на токен арта (Variant B): нарисованы только
# down/up/side; RIGHT использует side напрямую, LEFT — тот же side, отражённый в рендере.
_ART_TOKEN: dict[Facing, str] = {
    Facing.DOWN: "down",
    Facing.UP: "up",
    Facing.RIGHT: "side",
    Facing.LEFT: "side",
}


def facing_from_vector(dx: float, dy: float, current: Facing) -> Facing:
    """Выбрать направление по вектору движения/взгляда (экранные оси: y растёт вниз).

    Доминирующая ось решает: |dx|>|dy| → LEFT/RIGHT, иначе UP/DOWN. Нулевой вектор
    (сущность стоит) → сохранить текущее направление.
    """
    if dx == 0.0 and dy == 0.0:
        return current
    if abs(dx) > abs(dy):
        return Facing.RIGHT if dx > 0 else Facing.LEFT
    return Facing.DOWN if dy > 0 else Facing.UP


@dataclass(frozen=True)
class AnimationClip:
    """Один анимационный клип: имена кадров, частота и цикличность.

    frames — имена спрайтов для AssetLoader (могут отсутствовать как PNG → fallback).
    loop=True — циклическая анимация (idle/walk); loop=False — одноразовая (death).
    """

    frames: tuple[str, ...]
    fps: float
    loop: bool


# Раскладка по умолчанию: (число кадров, цикличность) на каждое состояние. Числа — это
# логические слоты под будущие spritesheets, а не балансировка. death — одноразовая.
_DEFAULT_LAYOUT: dict[AnimState, tuple[int, bool]] = {
    AnimState.IDLE: (2, True),
    AnimState.WALK: (4, True),
    AnimState.ATTACK: (2, True),
    AnimState.DEATH: (4, False),
}


class AnimationComponent:
    """Компонент анимации: хранит клипы состояний и выдаёт текущий кадр по dt.

    Композиция, а не наследование: подключается к сущности полем `animation`. Имена кадров
    строятся по соглашению `<prefix>_<state>_<index>` (например `player_walk_0`). Пустой
    prefix или отсутствие кадров → current_sprite=None (сущность рисует статический SPRITE).
    """

    def __init__(
        self,
        prefix: str | None,
        *,
        fps: float = ANIMATION_FPS,
        layout: dict[AnimState, tuple[int, bool]] | None = None,
        initial: AnimState = AnimState.IDLE,
    ) -> None:
        self._prefix: str = prefix or ""
        chosen = layout if layout is not None else _DEFAULT_LAYOUT
        safe_fps = fps if fps > 0.0 else ANIMATION_FPS
        self._clips: dict[AnimState, AnimationClip] = {}
        for state, (count, loop) in chosen.items():
            if self._prefix and count > 0:
                frames = tuple(f"{self._prefix}_{state.value}_{i}" for i in range(count))
            else:
                frames = ()
            self._clips[state] = AnimationClip(frames, safe_fps, loop)
        self._state: AnimState = initial
        self._frame: int = 0
        self._elapsed: float = 0.0
        self._finished: bool = False
        self._facing: Facing = Facing.DOWN

    # ── состояние ────────────────────────────────────────────────────────────

    @property
    def state(self) -> AnimState:
        """Текущее состояние анимации."""
        return self._state

    @property
    def facing(self) -> Facing:
        """Текущее логическое направление взгляда."""
        return self._facing

    def set_facing(self, facing: Facing) -> None:
        """Задать направление взгляда (для directional-рендера). Кадр/время не сбрасывает."""
        self._facing = facing

    @property
    def flip_horizontal(self) -> bool:
        """Нужно ли отражать кадр по горизонтали (LEFT = отражённый side)."""
        return self._facing is Facing.LEFT

    @property
    def directional_sprite(self) -> str | None:
        """Имя directional-кадра `<prefix>_<state>_<art>_<i>` (art: down/up/side) или None.

        Опционально: если directional-PNG нет, AssetLoader вернёт None и рендер уйдёт
        в обычный current_sprite → static SPRITE → примитив (обратная совместимость).
        """
        if not self._prefix:
            return None
        clip = self._clips.get(self._state)
        if clip is None or not clip.frames:
            return None
        token = _ART_TOKEN[self._facing]
        return f"{self._prefix}_{self._state.value}_{token}_{self._frame}"

    @property
    def frame_index(self) -> int:
        """Индекс текущего кадра внутри активного клипа."""
        return self._frame

    @property
    def is_finished(self) -> bool:
        """True, если одноразовый клип (loop=False) доиграл до последнего кадра."""
        return self._finished

    def frame_count(self, state: AnimState) -> int:
        """Число кадров в клипе состояния (0, если клип/кадры отсутствуют)."""
        clip = self._clips.get(state)
        return len(clip.frames) if clip is not None else 0

    @property
    def current_sprite(self) -> str | None:
        """Имя спрайта текущего кадра или None (нет клипа/кадров → статический fallback)."""
        clip = self._clips.get(self._state)
        if clip is None or not clip.frames:
            return None
        return clip.frames[self._frame]

    # ── управление ───────────────────────────────────────────────────────────

    def play(self, state: AnimState, *, restart: bool = False) -> None:
        """Переключить состояние. Без restart повторный вызов того же состояния — нет-оп.

        Сброс к первому кадру нужен, чтобы новая анимация (или перезапуск death) начиналась
        с начала. restart=True перезапускает даже текущее состояние.
        """
        if state == self._state and not restart:
            return
        self._state = state
        self._frame = 0
        self._elapsed = 0.0
        self._finished = False

    def update(self, dt: float) -> None:
        """Продвинуть кадр по времени. Циклические зацикливаются, одноразовые — стопорятся."""
        clip = self._clips.get(self._state)
        if clip is None or len(clip.frames) <= 1:
            # 0–1 кадр: продвигать нечего; одноразовый клип считается доигранным.
            if clip is not None and not clip.loop:
                self._finished = True
            return
        if self._finished or dt <= 0.0:
            return
        self._elapsed += dt
        frame_time = 1.0 / clip.fps
        last = len(clip.frames) - 1
        while self._elapsed >= frame_time:
            self._elapsed -= frame_time
            if self._frame < last:
                self._frame += 1
            elif clip.loop:
                self._frame = 0
            else:
                self._finished = True
                break


def draw_animated(
    surface: pygame.Surface,
    rect: pygame.Rect,
    component: AnimationComponent,
    fallback_sprite: str | None,
) -> bool:
    """Нарисовать кадр с цепочкой fallback и горизонтальным flip для LEFT.

    Цепочка: directional-кадр `<prefix>_<state>_<art>_<i>` (LEFT — тот же side, отражённый) →
    обычный кадр `<prefix>_<state>_<i>` → статический SPRITE → (False = рисуй примитив).
    Без directional-PNG поведение совпадает с прежним (обратная совместимость). AssetLoader
    не меняется: используются существующие get()/draw_sprite(); flip — только в рендере.
    """
    directional = component.directional_sprite
    if directional is not None:
        sprite = AssetLoader.get(directional)
        if sprite is not None:
            scaled = pygame.transform.scale(sprite, (rect.width, rect.height))
            if component.flip_horizontal:
                scaled = pygame.transform.flip(scaled, True, False)
            surface.blit(scaled, (rect.x, rect.y))
            return True
    if AssetLoader.draw_sprite(surface, component.current_sprite, rect):
        return True
    return AssetLoader.draw_sprite(surface, fallback_sprite, rect)
