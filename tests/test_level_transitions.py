"""Tests for Sprint 12B: Level/Scene Manager, TMX transitions, map-aware Save."""
from __future__ import annotations

from pathlib import Path

import pytest

from data.save_file import SaveData
from systems.game_world import GameWorld, load_transitions_from_tmx
from systems.level_manager import LevelManager
from ui.game_screen import GameScreen


# ── helpers: генерация TMX с collision/spawns/transitions ─────────────────────────


def write_map(
    path: Path,
    grid: list[list[int]],
    spawns: list[tuple[str, float, float]],
    transitions: list[tuple[float, float, float, float, str, str]] = (),  # type: ignore[assignment]
) -> Path:
    h, w = len(grid), len(grid[0])
    csv = ",\n".join(",".join(str(v) for v in row) for row in grid)
    sp = "\n".join(
        f'  <object id="{i}" name="{n}" x="{x:g}" y="{y:g}"><point/></object>'
        for i, (n, x, y) in enumerate(spawns, start=1)
    )
    tr = "\n".join(
        f'  <object id="{100 + i}" x="{x:g}" y="{y:g}" width="{tw:g}" height="{th:g}">'
        f'<properties><property name="target_map" value="{tm}"/>'
        f'<property name="target_spawn" value="{ts}"/></properties></object>'
        for i, (x, y, tw, th, tm, ts) in enumerate(transitions, start=1)
    )
    groups = f' <objectgroup id="2" name="spawns">\n{sp}\n </objectgroup>\n'
    if transitions:
        groups += f' <objectgroup id="3" name="transitions">\n{tr}\n </objectgroup>\n'
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" orientation="orthogonal" width="{w}" height="{h}" '
        f'tilewidth="32" tileheight="32" infinite="0" nextlayerid="4" nextobjectid="200">\n'
        f' <tileset firstgid="1" name="c" tilewidth="32" tileheight="32" tilecount="1" '
        f'columns="1"><grid orientation="orthogonal" width="32" height="32"/><tile id="0"/>'
        f'</tileset>\n'
        f' <layer id="1" name="collision" width="{w}" height="{h}"><data encoding="csv">\n'
        f'{csv}\n</data></layer>\n{groups}</map>\n',
        encoding="utf-8",
    )
    return path


def open_grid(w: int = 10, h: int = 10) -> list[list[int]]:
    return [[0] * w for _ in range(h)]


@pytest.fixture
def two_maps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Две карты в подменённом MAPS_DIR: mapA (с переходом→mapB) и mapB (entry-спавн)."""
    write_map(
        tmp_path / "mapA.tmx", open_grid(),
        [("player_start", 50.0, 50.0)],
        [(200.0, 200.0, 32.0, 32.0, "mapB", "entry")],
    )
    write_map(
        tmp_path / "mapB.tmx", open_grid(),
        [("player_start", 16.0, 16.0), ("entry", 120.0, 130.0)],
    )
    monkeypatch.setattr("systems.level_manager.MAPS_DIR", tmp_path)
    return tmp_path


# ── Phase 1: TMX transitions ─────────────────────────────────────────────────────


class TestTransitionLayer:
    def test_reads_transition_objects(self, two_maps: Path) -> None:
        tr = load_transitions_from_tmx(two_maps / "mapA.tmx")
        assert len(tr) == 1
        assert tr[0].target_map == "mapB"
        assert tr[0].target_spawn == "entry"
        assert (tr[0].x, tr[0].y, tr[0].width, tr[0].height) == (200.0, 200.0, 32.0, 32.0)

    def test_world_exposes_transitions(self, two_maps: Path) -> None:
        assert len(GameWorld(two_maps / "mapA.tmx").transitions) == 1

    def test_no_transition_layer_is_empty(self, two_maps: Path) -> None:
        assert GameWorld(two_maps / "mapB.tmx").transitions == []


# ── Phase 2: LevelManager ────────────────────────────────────────────────────────


class TestLevelManager:
    def test_loads_initial_map(self, two_maps: Path) -> None:
        lm = LevelManager("mapA")
        assert lm.current_map_id == "mapA"
        assert isinstance(lm.world, GameWorld)

    def test_change_map(self, two_maps: Path) -> None:
        lm = LevelManager("mapA")
        old_world = lm.world
        lm.change_map("mapB")
        assert lm.current_map_id == "mapB"
        assert lm.world is not old_world  # пересоздан

    def test_wall_rects_contract_preserved(self, two_maps: Path) -> None:
        assert isinstance(LevelManager("mapA").world.wall_rects, list)


# ── Phase 4: GameScreen переключает карту при входе в зону ────────────────────────


class TestGameScreenTransition:
    def _screen_on(self, monkeypatch: pytest.MonkeyPatch, map_id: str) -> GameScreen:
        monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager(map_id))
        return GameScreen()

    def test_entering_zone_switches_map(self, two_maps: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        screen = self._screen_on(monkeypatch, "mapA")
        assert screen._level.current_map_id == "mapA"
        # Поставить игрока в зону перехода (200..232).
        screen._player.pos.update(210.0, 210.0)
        screen._player.rect.center = (210, 210)
        screen.update(0.016)
        assert screen._level.current_map_id == "mapB"

    def test_player_teleported_to_target_spawn(self, two_maps: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        screen = self._screen_on(monkeypatch, "mapA")
        screen._player.pos.update(210.0, 210.0)
        screen._player.rect.center = (210, 210)
        screen.update(0.016)
        assert (screen._player.pos.x, screen._player.pos.y) == (120.0, 130.0)  # entry mapB

    def test_no_transition_no_switch(self, two_maps: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        screen = self._screen_on(monkeypatch, "mapA")
        screen.update(0.016)  # игрок на старте, вне зоны
        assert screen._level.current_map_id == "mapA"


# ── Phase 3: map-aware Save ──────────────────────────────────────────────────────


class TestMapAwareSave:
    def test_savedata_has_map_fields(self) -> None:
        d = SaveData(map_id="mapB", player_x=120.0, player_y=130.0)
        raw = d.to_dict()
        assert raw["map"] == {"id": "mapB", "x": 120.0, "y": 130.0}

    def test_roundtrip_preserves_map(self) -> None:
        d = SaveData(map_id="mapB", player_x=120.0, player_y=130.0)
        assert SaveData.from_dict(d.to_dict()) == d

    def test_old_save_without_map_defaults(self) -> None:
        # Сейв без секции "map" (старый формат) → level1, позиция (0,0).
        old = {"player": {"xp": 10, "level": 1}, "skills": {}, "inventory": [],
               "quests": {"active": [], "completed": []}, "lore": []}
        d = SaveData.from_dict(old)
        assert d.map_id == "level1" and d.player_x == 0.0 and d.player_y == 0.0

    def test_save_records_current_map_and_position(
        self, two_maps: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager("mapA"))
        monkeypatch.setattr(GameScreen, "_SAVE_PATH", tmp_path / "sg.json")
        screen = GameScreen()
        screen._player.pos.update(77.0, 88.0)
        screen._save_game()
        data = SaveData.from_dict(__import__("json").loads(
            (tmp_path / "sg.json").read_text(encoding="utf-8")))
        assert data.map_id == "mapA"
        assert (data.player_x, data.player_y) == (77.0, 88.0)

    def test_load_restores_map_and_position(
        self, two_maps: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        save = tmp_path / "sg.json"
        monkeypatch.setattr(GameScreen, "_SAVE_PATH", save)
        # Сохранить на mapB в позиции (120,130), затем загрузить в экран, стартовавший на mapA.
        monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager("mapB"))
        s_b = GameScreen()
        s_b._player.pos.update(120.0, 130.0)
        s_b._save_game()
        s_b.cleanup()

        monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager("mapA"))
        s_a = GameScreen()
        s_a.load_game()
        assert s_a._level.current_map_id == "mapB"
        assert (s_a._player.pos.x, s_a._player.pos.y) == (120.0, 130.0)
