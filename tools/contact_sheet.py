"""Генератор контактных листов спрайт-паков (Sprint 14C.1).

Раскладывает ВСЕ кадры листа (`<sheet>_0.png`, `<sheet>_1.png`, ...) в одну PNG-сетку с
подписанными индексами — для визуальной проверки, какие кадры соответствуют состояниям
анимации (idle/walk/attack/death). Headless: не открывает окно, не требует GUI.

Запуск (из каталога Evolution_Z):
    python -m tools.contact_sheet human_Maxim
    python -m tools.contact_sheet zed_Basic zed_runner_military --cols 12 --cell 72

Результат: assets/debug/<sheet>_contact.png. Игровую архитектуру не трогает — это
автономный dev-инструмент (не часть рантайма).
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

# Headless-режим: драйвер-пустышка до импорта pygame, чтобы работать без дисплея.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from settings import ASSETS_DIR, BASE_DIR  # noqa: E402

_DEFAULT_SOURCE: Path = BASE_DIR.parent / "new_assets" / "Sprite"
_DEFAULT_OUT: Path = ASSETS_DIR / "debug"
_MAX_FRAMES: int = 2000  # предохранитель от бесконечного перебора

_CELL_BG: tuple[int, int, int] = (54, 54, 64)
_CELL_BG_ALT: tuple[int, int, int] = (44, 44, 52)
_LABEL_COLOR: tuple[int, int, int] = (245, 220, 90)
_GRID_COLOR: tuple[int, int, int] = (90, 90, 100)
_HIGHLIGHT_COLOR: tuple[int, int, int] = (90, 230, 120)
_LABEL_H: int = 14  # высота полоски с индексом сверху ячейки


def count_frames(source: Path, sheet: str) -> int:
    """Число кадров листа: подряд идущие `<sheet>_<i>.png` от 0. Одиночный `<sheet>.png` → 1."""
    if not (source / f"{sheet}_0.png").exists():
        return 1 if (source / f"{sheet}.png").exists() else 0
    count = 0
    while count < _MAX_FRAMES and (source / f"{sheet}_{count}.png").exists():
        count += 1
    return count


def _frame_path(source: Path, sheet: str, index: int, total: int) -> Path:
    """Путь к кадру: для одиночного листа — `<sheet>.png`, иначе `<sheet>_<i>.png`."""
    if total == 1 and not (source / f"{sheet}_0.png").exists():
        return source / f"{sheet}.png"
    return source / f"{sheet}_{index}.png"


def _fit_scale(frame_w: int, frame_h: int, max_w: int, max_h: int) -> int:
    """Целочисленный масштаб, чтобы кадр влез в область (минимум 1 — сохраняем пиксель-арт)."""
    if frame_w <= 0 or frame_h <= 0:
        return 1
    return max(1, min(max_w // frame_w, max_h // frame_h))


def _parse_range(spec: str | None) -> set[int]:
    """Разобрать строку диапазонов '0-3,42-45' в множество индексов. Пусто → пустое множество."""
    out: set[int] = set()
    if not spec:
        return out
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        else:
            out.add(int(chunk))
    return out


def _render_grid(
    frames: list[tuple[int, Path]],
    out_path: Path,
    *,
    cols: int,
    cell: int,
    highlight: set[int] | None = None,
) -> Path:
    """Отрисовать сетку кадров (метка = индекс) и сохранить PNG. Возвращает путь.

    frames — пары (метка-индекс, путь к PNG); порядок ячеек = порядок списка. Каждый кадр
    вписан целочисленным масштабом в ячейку cell×cell с полоской индекса сверху.
    """
    if not pygame.get_init():
        pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()

    highlight = highlight or set()
    rows = max(1, math.ceil(len(frames) / cols))
    font = pygame.font.SysFont("monospace", 11, bold=True)
    surface = pygame.Surface((cols * cell, rows * cell))
    surface.fill((20, 20, 24))

    inner_w = cell - 4
    inner_h = cell - _LABEL_H - 2

    for slot, (index, path) in enumerate(frames):
        col = slot % cols
        row = slot // cols
        cx, cy = col * cell, row * cell
        bg = _CELL_BG if (col + row) % 2 == 0 else _CELL_BG_ALT
        pygame.draw.rect(surface, bg, (cx, cy, cell, cell))
        pygame.draw.rect(surface, _GRID_COLOR, (cx, cy, cell, cell), 1)
        surface.blit(font.render(str(index), True, _LABEL_COLOR), (cx + 3, cy + 2))

        if path.exists():
            try:
                frame = pygame.image.load(str(path))
                fw, fh = frame.get_size()
                if fw > 0 and fh > 0:
                    scale = _fit_scale(fw, fh, inner_w, inner_h)
                    scaled = pygame.transform.scale(frame, (fw * scale, fh * scale))
                    dx = cx + (cell - scaled.get_width()) // 2
                    dy = cy + _LABEL_H + (inner_h - scaled.get_height()) // 2
                    surface.blit(scaled, (dx, dy))
            except pygame.error:
                pass

        if index in highlight:
            pygame.draw.rect(surface, _HIGHLIGHT_COLOR, (cx, cy, cell, cell), 3)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(out_path))
    return out_path


def build_contact_sheet(
    source: Path,
    sheet: str,
    out_dir: Path,
    *,
    cols: int = 10,
    cell: int = 80,
    start: int = 0,
    end: int | None = None,
    highlight: set[int] | None = None,
) -> Path:
    """Собрать контактный лист плоского листа `<sheet>_<i>.png` и сохранить PNG.

    start/end задают подмножество кадров (zoom). highlight — индексы для подсветки рамкой.
    Имя файла: `<sheet>_contact.png` или `<sheet>_<start>-<end>_contact.png` для подмножества.
    """
    total = count_frames(source, sheet)
    if total == 0:
        raise FileNotFoundError(f"No frames found for sheet '{sheet}' in {source}")

    last = total - 1 if end is None else min(end, total - 1)
    start = max(0, start)
    is_subset = start != 0 or last != total - 1
    frames = [(i, _frame_path(source, sheet, i, total)) for i in range(start, last + 1)]
    name = f"{sheet}_{start}-{last}_contact.png" if is_subset else f"{sheet}_contact.png"
    return _render_grid(frames, out_dir / name, cols=cols, cell=cell, highlight=highlight)


def build_from_dir(
    frame_dir: Path,
    out_dir: Path,
    *,
    name: str | None = None,
    cols: int = 8,
    cell: int = 110,
    highlight: set[int] | None = None,
) -> Path:
    """Контактный лист из каталога кадров с произвольными индексами (папки-состояния).

    Берёт все `*.png` каталога, сортирует по числу в имени, метка = исходный индекс кадра.
    Имя файла по умолчанию: `<родитель>_<папка>_contact.png` (напр. `player_walk_contact.png`).
    """
    paths = sorted(frame_dir.glob("*.png"), key=_dir_frame_index)
    if not paths:
        raise FileNotFoundError(f"No PNG frames in {frame_dir}")
    frames = [(_dir_frame_index(p), p) for p in paths]
    label = name or f"{frame_dir.parent.name}_{frame_dir.name}"
    return _render_grid(frames, out_dir / f"{label}_contact.png", cols=cols, cell=cell,
                        highlight=highlight)


def _dir_frame_index(path: Path) -> int:
    """Числовой индекс из имени кадра (`player_115.png` → 115); без числа → 0."""
    digits = "".join(c for c in path.stem if c.isdigit())
    return int(digits) if digits else 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Генератор контактных листов спрайт-паков.")
    parser.add_argument("sheets", nargs="*", help="имена листов без _<i>.png (напр. human_Maxim)")
    parser.add_argument("--source", type=Path, default=_DEFAULT_SOURCE, help="каталог пака")
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT, help="каталог для PNG")
    parser.add_argument("--cols", type=int, default=10, help="число колонок в сетке")
    parser.add_argument("--cell", type=int, default=80, help="размер ячейки в пикселях")
    parser.add_argument("--range", dest="frange", help="подмножество кадров 'A-B' (zoom)")
    parser.add_argument("--highlight", help="подсветить кадры, напр. '0-3,42'")
    parser.add_argument(
        "--dir", dest="dirs", action="append", default=[], type=Path,
        help="каталог кадров с произвольными индексами (папка-состояние); можно несколько",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    highlight_dirs = _parse_range(args.highlight)
    if args.dirs:
        rc = 0
        for frame_dir in args.dirs:
            try:
                out = build_from_dir(
                    frame_dir, args.out, cols=args.cols, cell=args.cell, highlight=highlight_dirs
                )
            except FileNotFoundError as exc:
                print(f"SKIP {frame_dir}: {exc}", file=sys.stderr)
                rc = 1
                continue
            print(f"{frame_dir} -> {out}")
        return rc
    if not args.source.exists():
        print(f"ERROR: source not found: {args.source}", file=sys.stderr)
        return 1
    frange = _parse_range(args.frange)
    start = min(frange) if frange else 0
    end = max(frange) if frange else None
    highlight = _parse_range(args.highlight)
    rc = 0
    for sheet in args.sheets:
        try:
            out = build_contact_sheet(
                args.source, sheet, args.out, cols=args.cols, cell=args.cell,
                start=start, end=end, highlight=highlight,
            )
        except FileNotFoundError as exc:
            print(f"SKIP {sheet}: {exc}", file=sys.stderr)
            rc = 1
            continue
        print(f"{sheet}: {count_frames(args.source, sheet)} frames -> {out}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
