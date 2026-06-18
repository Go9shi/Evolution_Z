"""Tests for Sprint 13B: Quest triggers & world events via TMX object layer + EventBus."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from data.trigger_zone import TriggerZone
from main import GameStateManager
from systems.event_bus import EventBus
from systems.game_world import GameWorld, load_triggers_from_tmx
from systems.level_manager import LevelManager
from ui.game_screen import GameScreen


# ── helpers ───────────────────────────────────────────────────────────────────


def write_map(path: Path, triggers: list[tuple[str, str, float, float, float, float]]) -> Path:
    """Карта 12x12 (открытая) + player_start + object-слой triggers (если задан)."""
    w = h = 12
    csv = ",\n".join(",".join("0" for _ in range(w)) for _ in range(h))
    tr = "\n".join(
        f'  <object id="{100 + i}" x="{x:g}" y="{y:g}" width="{tw:g}" height="{th:g}">'
        f'<properties><property name="trigger_id" value="{tid}"/>'
        f'<property name="event_name" value="{ev}"/></properties></object>'
        for i, (tid, ev, x, y, tw, th) in enumerate(triggers, start=1)
    )
    groups = ' <objectgroup id="2" name="spawns">\n' \
             '  <object id="1" name="player_start" x="40" y="40"><point/></object>\n </objectgroup>\n'
    if triggers:
        groups += f' <objectgroup id="3" name="triggers">\n{tr}\n </objectgroup>\n'
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


def make_game_on(monkeypatch: pytest.MonkeyPatch, map_id: str) -> tuple[GameStateManager, GameScreen]:
    monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager(map_id))
    manager = GameStateManager()
    screen = GameScreen(manager)
    manager.push(screen)
    return manager, screen


@pytest.fixture
def trigger_map(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Карта с одной зоной-триггером (квестовое событие) в подменённом MAPS_DIR."""
    write_map(tmp_path / "tmap.tmx", [("zone_a", "quest_zone_entered", 200.0, 200.0, 64.0, 64.0)])
    write_map(tmp_path / "notrig.tmx", [])
    monkeypatch.setattr("systems.level_manager.MAPS_DIR", tmp_path)
    return tmp_path


# ── Phase 1: TriggerZone ─────────────────────────────────────────────────────────


class TestTriggerZone:
    def test_fields_and_rect(self) -> None:
        tz = TriggerZone("z", "ev", 10.0, 20.0, 30.0, 40.0)
        assert (tz.trigger_id, tz.event_name) == ("z", "ev")
        assert tz.rect == pygame.Rect(10, 20, 30, 40)
        assert tz.active is True


# ── Phase 2: TMX integration ─────────────────────────────────────────────────────


class TestTmx:
    def test_loads_triggers(self, trigger_map: Path) -> None:
        tr = load_triggers_from_tmx(trigger_map / "tmap.tmx")
        assert len(tr) == 1
        assert (tr[0].trigger_id, tr[0].event_name) == ("zone_a", "quest_zone_entered")
        assert tr[0].rect == pygame.Rect(200, 200, 64, 64)

    def test_world_exposes_triggers(self, trigger_map: Path) -> None:
        assert len(GameWorld(trigger_map / "tmap.tmx").triggers) == 1

    def test_no_trigger_layer_is_empty(self, trigger_map: Path) -> None:
        assert GameWorld(trigger_map / "notrig.tmx").triggers == []

    def test_default_maps_have_no_triggers(self) -> None:
        assert GameWorld().triggers == []  # level1 без слоя triggers


# ── Phase 3/4/5: runtime — вход, emit, однократность ─────────────────────────────


class TestRuntime:
    def test_gamescreen_builds_triggers(self, trigger_map: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _, screen = make_game_on(monkeypatch, "tmap")
        assert len(screen._triggers) == 1

    def test_entering_zone_emits_event(self, trigger_map: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _, screen = make_game_on(monkeypatch, "tmap")
        events: list[dict] = []
        EventBus.on("quest_zone_entered", events.append)
        screen._player.pos.update(232.0, 232.0)  # центр зоны (200..264)
        screen._player.rect.center = (232, 232)
        screen.update(0.016)
        assert len(events) == 1
        assert events[0]["trigger_id"] == "zone_a"

    def test_single_activation(self, trigger_map: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _, screen = make_game_on(monkeypatch, "tmap")
        events: list[dict] = []
        EventBus.on("quest_zone_entered", events.append)
        screen._player.pos.update(232.0, 232.0)
        screen._player.rect.center = (232, 232)
        screen.update(0.016)  # активация
        screen.update(0.016)  # повторный вход — без повторного emit
        assert len(events) == 1
        assert screen._triggers[0].active is False

    def test_outside_zone_no_event(self, trigger_map: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _, screen = make_game_on(monkeypatch, "tmap")
        events: list[dict] = []
        EventBus.on("quest_zone_entered", events.append)
        screen.update(0.016)  # игрок на старте (40,40), вне зоны
        assert events == []

    def test_map_change_rebuilds_triggers(self, trigger_map: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _, screen = make_game_on(monkeypatch, "tmap")
        assert len(screen._triggers) == 1
        screen._enter_map("notrig", "player_start")
        assert screen._triggers == []  # карта без триггеров

    def test_revisiting_map_rearms_trigger(self, trigger_map: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _, screen = make_game_on(monkeypatch, "tmap")
        events: list[dict] = []
        EventBus.on("quest_zone_entered", events.append)
        screen._player.pos.update(232.0, 232.0)
        screen._player.rect.center = (232, 232)
        screen.update(0.016)  # активировали
        screen._enter_map("notrig", "player_start")  # ушли
        screen._enter_map("tmap", "player_start")  # вернулись → свежие триггеры
        assert screen._triggers[0].active is True
