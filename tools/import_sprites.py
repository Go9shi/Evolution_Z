"""Импорт спрайтов из набора `sprites/` под контракт имён игры.

Набор `d:/game/sprites/`:
- анимированные сущности — папка с подпапками состояний `{idle,walk,attack,death}/*.png`
  (player/zombie_walker/zombie_runner/zombie_spitter/zombie_boss); имена внутри
  сохраняют исходный индекс кадра;
- статика — `npc/`, `food/`, `vaccine/`, `quest/`, `tiles/`, `bunker/`, `weapons/`.

Контракт назначения (assets/sprites/, плоско):
- кадры анимации: `<prefix>_<state>_<i>.png` (i реиндексируется 0..N-1 по числу в имени);
- directional-кадры (Sprint 14C.3): `<prefix>_<state>_<token>_<i>.png`, token ∈ {down,up,side}
  (RIGHT=side, LEFT=side+flip в рендере); базовые кадры сохраняются для fallback;
- статическая база сущности: `<prefix>.png` (первый кадр idle, для зомби — walk),
  чтобы рендер работал и в статическом режиме (AssetLoader.draw_sprite(self.SPRITE));
- NPC `npc_<id>.png`, предметы `item_food`/`item_quest`, тайлы `tile_floor`/`tile_wall`.

Без PNG игра рисует примитивы (fallback сохраняется). Игровой код не трогается.

Запуск (из каталога Evolution_Z):
    python -m tools.import_sprites --dry-run
    python -m tools.import_sprites
    python -m tools.import_sprites --clean
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from settings import BASE_DIR, SPRITES_DIR  # noqa: E402

_DEFAULT_SOURCE: Path = BASE_DIR.parent / "sprites"

_STATES: tuple[str, ...] = ("idle", "walk", "attack", "death")

# Игровой prefix → папка-источник в наборе (подпапки состояний внутри).
ANIMATED: dict[str, str] = {
    "player": "player",
    "zombie_walker": "zombie_walker",
    "zombie_runner": "zombie_runner",
    "zombie_spitter": "zombie_spitter",
    "boss": "zombie_boss",
}

# Directional-раскладка (Sprint 14C.3): game_prefix → state → art-токен → исходные индексы.
# Нарисованы только down/up/side (калибровка 14C.1/14C.3 по контакт-листам); LEFT строится
# отражением side в рендере (см. systems/animation.py). Зомби-типы делят один риг.
_ZOMBIE_DIR: dict[str, dict[str, list[int]]] = {
    "walk": {"down": [52, 53, 54, 55], "side": [58, 59, 60, 61], "up": [64, 65, 66, 67]},
    "attack": {"down": [1, 2], "side": [3, 4], "up": [12, 13]},
}
_DIRECTIONAL: dict[str, dict[str, dict[str, list[int]]]] = {
    "player": {
        "idle": {"down": [52, 53], "up": [64, 65]},
        "walk": {
            "down": [18, 19, 20, 21], "side": [112, 113, 114, 115], "up": [30, 31, 32, 33],
        },
        "attack": {"down": [0, 1], "side": [7, 8], "up": [12, 13]},
    },
    "zombie_walker": _ZOMBIE_DIR,
    "zombie_runner": _ZOMBIE_DIR,
    "zombie_spitter": _ZOMBIE_DIR,
    "boss": _ZOMBIE_DIR,
}

# Имя назначения (без .png) → относительный путь источника в наборе.
STATIC: dict[str, str] = {
    "npc_ranger": "npc/ranger.png",
    "npc_scientist": "npc/scientist_0.png",
    "npc_survivor": "npc/survivor_0.png",
    "item_food": "food/food_Beans_Can.png",
    "item_quest": "vaccine/vaccine_1.png",
    "tile_floor": "tiles/floor_0.png",
    "tile_wall": "tiles/wall_0.png",
}


def _frame_index(path: Path) -> int:
    """Числовой индекс из имени кадра (`player_100.png` → 100); без числа → 0."""
    match = re.search(r"(\d+)\.png$", path.name)
    return int(match.group(1)) if match else 0


def _sorted_frames(state_dir: Path) -> list[Path]:
    """Кадры состояния, отсортированные по исходному индексу."""
    return sorted(state_dir.glob("*.png"), key=_frame_index)


def _index_map(state_dir: Path) -> dict[int, Path]:
    """Отображение исходный_индекс → путь к кадру для каталога состояния."""
    return {_frame_index(p): p for p in state_dir.glob("*.png")}


def _plan(source: Path) -> list[tuple[Path, str]]:
    """Список (источник, имя назначения) для всего импорта (анимации + статика)."""
    plan: list[tuple[Path, str]] = []
    for prefix, folder in ANIMATED.items():
        base = source / folder
        base_static: Path | None = None
        for state in _STATES:
            frames = _sorted_frames(base / state)
            for i, frame in enumerate(frames):
                plan.append((frame, f"{prefix}_{state}_{i}.png"))
            if frames and base_static is None and state in ("idle", "walk"):
                base_static = frames[0]  # статическая база: первый idle, иначе первый walk
        if base_static is not None:
            plan.append((base_static, f"{prefix}.png"))
    # Directional-кадры поверх базовых: `<prefix>_<state>_<token>_<i>` (i реиндексируется).
    for prefix, states in _DIRECTIONAL.items():
        folder = ANIMATED[prefix]
        for state, tokens in states.items():
            idx_map = _index_map(source / folder / state)
            for token, indices in tokens.items():
                for i, src_index in enumerate(indices):
                    src = idx_map.get(src_index, source / folder / state / f"missing_{src_index}.png")
                    plan.append((src, f"{prefix}_{state}_{token}_{i}.png"))
    for dst_name, rel in STATIC.items():
        plan.append((source / rel, f"{dst_name}.png"))
    return plan


def import_all(source: Path, dest: Path, *, dry_run: bool) -> tuple[int, list[str]]:
    """Скопировать спрайты по плану. Возвращает (скопировано, отсутствующие источники)."""
    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing: list[str] = []
    for src, dst_name in _plan(source):
        if not src.exists():
            missing.append(str(src.relative_to(source)) if src.is_relative_to(source) else str(src))
            continue
        if not dry_run:
            shutil.copyfile(src, dest / dst_name)
        copied += 1
    return copied, missing


def clean(dest: Path) -> int:
    """Удалить ранее импортированные спрайты (по префиксам/именам). Возвращает число удалённых."""
    removed = 0
    patterns = [f"{p}.png" for p in ANIMATED] + [f"{p}_*.png" for p in ANIMATED]
    patterns += [f"{name}.png" for name in STATIC]
    for pattern in patterns:
        for target in dest.glob(pattern):
            target.unlink()
            removed += 1
    return removed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Импорт спрайтов под контракт имён игры.")
    parser.add_argument("--source", type=Path, default=_DEFAULT_SOURCE, help="каталог набора")
    parser.add_argument("--dest", type=Path, default=SPRITES_DIR, help="каталог assets/sprites")
    parser.add_argument("--dry-run", action="store_true", help="показать сводку, не писать файлы")
    parser.add_argument("--clean", action="store_true", help="удалить импортированные и выйти")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.clean:
        print(f"Removed {clean(args.dest)} imported sprites from {args.dest}")
        return 0
    if not args.source.exists():
        print(f"ERROR: source not found: {args.source}", file=sys.stderr)
        return 1
    copied, missing = import_all(args.source, args.dest, dry_run=args.dry_run)
    verb = "Would copy" if args.dry_run else "Copied"
    print(f"{verb} {copied} sprites into {args.dest}")
    if missing:
        print(f"WARNING: {len(missing)} source files missing:")
        for name in missing[:15]:
            print(f"  - {name}")
        if len(missing) > 15:
            print(f"  ... and {len(missing) - 15} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
