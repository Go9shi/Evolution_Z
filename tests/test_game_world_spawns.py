"""Tests for Sprint 11B: TMX spawn objects — data-driven placement of player/enemies/boss/items."""
from __future__ import annotations

from pathlib import Path

import pytest

from data.spawn_point import SpawnPoint
from entities.boss import PatientZeroBoss
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from entities.player import Player
from entities.zombie import RunnerZombie, SpitterZombie, WalkerZombie, Zombie
from systems.game_world import GameWorld, load_spawns_from_tmx
from ui.game_screen import GameScreen

_LEVEL1 = Path(__file__).resolve().parent.parent / "assets" / "maps" / "level1.tmx"


# ── helpers ───────────────────────────────────────────────────────────────────


def names(spawns: list[SpawnPoint]) -> list[str]:
    return [s.name for s in spawns]


def write_tmx(path: Path, grid: list[list[int]], objects: list[tuple[str, float, float]]) -> Path:
    """Сгенерировать TMX со слоем collision и object-слоем spawns."""
    h, w = len(grid), len(grid[0])
    csv = ",\n".join(",".join(str(v) for v in row) for row in grid)
    objs = "\n".join(
        f'  <object id="{i}" name="{n}" x="{x:g}" y="{y:g}"><point/></object>'
        for i, (n, x, y) in enumerate(objects, start=1)
    )
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" orientation="orthogonal" renderorder="right-down" '
        f'width="{w}" height="{h}" tilewidth="32" tileheight="32" infinite="0" '
        f'nextlayerid="3" nextobjectid="{len(objects) + 1}">\n'
        f' <tileset firstgid="1" name="collision" tilewidth="32" tileheight="32" '
        f'tilecount="1" columns="1"><grid orientation="orthogonal" width="32" height="32"/>'
        f'<tile id="0"/></tileset>\n'
        f' <layer id="1" name="collision" width="{w}" height="{h}"><data encoding="csv">\n'
        f'{csv}\n</data></layer>\n'
        f' <objectgroup id="2" name="spawns">\n{objs}\n </objectgroup>\n</map>\n',
        encoding="utf-8",
    )
    return path


# ── Загрузка спавнов из TMX ──────────────────────────────────────────────────────


class TestSpawnLoading:
    def test_level1_exposes_spawns(self) -> None:
        assert len(GameWorld().spawns) == 10

    def test_player_start_present(self) -> None:
        assert "player_start" in names(GameWorld().spawns)

    def test_enemy_spawns_present(self) -> None:
        ns = names(GameWorld().spawns)
        assert ns.count("enemy_walker") == 2
        assert "enemy_runner" in ns
        assert "enemy_spitter" in ns

    def test_boss_spawn_present(self) -> None:
        assert "boss" in names(GameWorld().spawns)

    def test_item_spawns_present(self) -> None:
        ns = names(GameWorld().spawns)
        for item_id in ("canned_beans", "ration_pack",
                        "vaccine_component_alpha", "vaccine_component_beta"):
            assert item_id in ns

    def test_spawn_has_float_coords(self) -> None:
        sp = GameWorld().spawns[0]
        assert isinstance(sp.x, float) and isinstance(sp.y, float)

    def test_missing_spawns_layer_is_empty(self, tmp_path: Path) -> None:
        # Карта без object-слоя (только геометрия) → пустой список спавнов, без ошибки.
        path = tmp_path / "geom_only.tmx"
        path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<map version="1.10" orientation="orthogonal" width="3" height="3" '
            'tilewidth="32" tileheight="32" infinite="0" nextlayerid="2" nextobjectid="1">\n'
            ' <tileset firstgid="1" name="c" tilewidth="32" tileheight="32" tilecount="1" '
            'columns="1"><grid orientation="orthogonal" width="32" height="32"/><tile id="0"/>'
            '</tileset>\n'
            ' <layer id="1" name="collision" width="3" height="3"><data encoding="csv">'
            '1,1,1,1,0,1,1,1,1</data></layer>\n</map>\n',
            encoding="utf-8",
        )
        assert load_spawns_from_tmx(path) == []


# ── Интеграция: GameScreen строит объекты из TMX ─────────────────────────────────


class TestGameScreenIntegration:
    def test_player_spawned_from_tmx(self) -> None:
        screen = GameScreen()
        assert isinstance(screen._player, Player)
        # player_start в level1 = (400, 208)
        assert (screen._player.pos.x, screen._player.pos.y) == (400.0, 208.0)

    def test_enemies_spawned_from_tmx(self) -> None:
        screen = GameScreen()
        assert len(screen._enemies) == 4
        assert all(isinstance(e, Zombie) for e in screen._enemies)
        kinds = {type(e) for e in screen._enemies}
        assert {WalkerZombie, RunnerZombie, SpitterZombie} <= kinds

    def test_boss_spawned_from_tmx(self) -> None:
        screen = GameScreen()
        assert isinstance(screen._boss, PatientZeroBoss)
        assert (screen._boss.pos.x, screen._boss.pos.y) == (1392.0, 592.0)

    def test_items_spawned_from_tmx(self) -> None:
        screen = GameScreen()
        assert len(screen._world_items) == 4
        food = [i for i in screen._world_items if isinstance(i, FoodItem)]
        quest = [i for i in screen._world_items if isinstance(i, QuestItem)]
        assert len(food) == 2
        assert len(quest) == 2


# ── Паритет со старым уровнем ────────────────────────────────────────────────────


class TestParity:
    def test_counts_match_old_level(self) -> None:
        screen = GameScreen()
        assert len(screen._enemies) == 4       # 2 walker + runner + spitter
        assert len(screen._world_items) == 4   # 2 food + 2 quest
        assert isinstance(screen._boss, PatientZeroBoss)
        assert isinstance(screen._player, Player)


# ── Кастомные карты: размещение задаётся только TMX ───────────────────────────────


class TestCustomLevel:
    """Размещение объектов задаётся ТОЛЬКО TMX-файлом (Python-код не меняется)."""

    def _grid(self) -> list[list[int]]:
        return [[1] * 6 for _ in range(6)]

    def _use_map(self, monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
        """Заставить GameScreen строить мир из конкретной карты (подмена LevelManager)."""
        from systems.level_manager import LevelManager

        def factory() -> LevelManager:
            lm = LevelManager()  # грузит level1, затем подменяем мир на кастомную карту
            lm._world = GameWorld(path)
            return lm

        monkeypatch.setattr("ui.game_screen.LevelManager", factory)

    def test_custom_player_position(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        path = write_tmx(tmp_path / "lvl.tmx", self._grid(), [("player_start", 96.0, 64.0)])
        self._use_map(monkeypatch, path)
        screen = GameScreen()
        assert (screen._player.pos.x, screen._player.pos.y) == (96.0, 64.0)

    def test_custom_enemy_count(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        objs = [("player_start", 50.0, 50.0),
                ("enemy_walker", 60.0, 60.0), ("enemy_runner", 70.0, 70.0)]
        path = write_tmx(tmp_path / "lvl2.tmx", self._grid(), objs)
        self._use_map(monkeypatch, path)
        screen = GameScreen()
        assert len(screen._enemies) == 2  # размещение задано только файлом
