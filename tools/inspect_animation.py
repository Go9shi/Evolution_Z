"""Числовой анализатор кадров спрайт-листа (Sprint 14C.1).

Выводит по каждому кадру размер и соотношение сторон. Сегменты анимации в этих паках
обрезаны по контенту, поэтому метрики помогают находить границы состояний:
- death/падение → кадры «лежат» (ширина растёт, высота падает, aspect = w/h > 1);
- walk → ровные ряды близких размеров.

Headless, без GUI. Дополняет визуальный contact_sheet, ничего не меняя в игре.

Запуск:
    python -m tools.inspect_animation human_Maxim
    python -m tools.inspect_animation zed_Basic --wide-threshold 1.1
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from settings import BASE_DIR  # noqa: E402

_DEFAULT_SOURCE: Path = BASE_DIR.parent / "new_assets" / "Sprite"
_MAX_FRAMES: int = 2000


def frame_sizes(source: Path, sheet: str) -> list[tuple[int, int]]:
    """Список (width, height) всех кадров листа по порядку индексов."""
    sizes: list[tuple[int, int]] = []
    i = 0
    while i < _MAX_FRAMES and (source / f"{sheet}_{i}.png").exists():
        sizes.append(pygame.image.load(str(source / f"{sheet}_{i}.png")).get_size())
        i += 1
    return sizes


def report(source: Path, sheet: str, wide_threshold: float) -> int:
    """Напечатать таблицу метрик кадров и сводку «лежачих» (кандидаты death)."""
    sizes = frame_sizes(source, sheet)
    if not sizes:
        print(f"No frames found for '{sheet}' in {source}", file=sys.stderr)
        return 1
    heights = sorted(h for _w, h in sizes)
    median_h = heights[len(heights) // 2]
    print(f"=== {sheet}: {len(sizes)} frames, median height {median_h} ===")
    print(" idx   w   h  aspect  flags")
    wide: list[int] = []
    for i, (w, h) in enumerate(sizes):
        aspect = w / h if h else 0.0
        flags = []
        if aspect >= wide_threshold:
            flags.append("WIDE(lying?)")
            wide.append(i)
        if h <= median_h * 0.6:
            flags.append("SHORT")
        print(f" {i:>3} {w:>3} {h:>3}  {aspect:>5.2f}  {' '.join(flags)}")
    print(f"WIDE/lying frame indices (death candidates): {wide}")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Числовой анализ кадров спрайт-листа.")
    parser.add_argument("sheets", nargs="+", help="имена листов без _<i>.png")
    parser.add_argument("--source", type=Path, default=_DEFAULT_SOURCE, help="каталог пака")
    parser.add_argument(
        "--wide-threshold", type=float, default=1.0, help="aspect w/h, выше которого кадр 'лежит'"
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not pygame.get_init():
        pygame.init()
    rc = 0
    for sheet in args.sheets:
        rc |= report(args.source, sheet, args.wide_threshold)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
