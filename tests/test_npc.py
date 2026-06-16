"""Tests for Sprint 13A: NPC system via TMX object layer + proximity dialogue."""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

from entities.npc import NPC
from main import GameStateManager
from systems.game_world import GameWorld, load_npcs_from_tmx
from systems.level_manager import LevelManager
from ui.dialogue_ui import DialogueUI
from ui.game_screen import GameScreen

_RED = (255, 0, 0)


# ── helpers ───────────────────────────────────────────────────────────────────


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def write_map(path: Path, npcs: list[tuple[str, str, float, float]]) -> Path:
    """Карта 10x10 (открытая) + player_start + object-слой npcs."""
    w = h = 10
    csv = ",\n".join(",".join("0" for _ in range(w)) for _ in range(h))
    npc_xml = "\n".join(
        f'  <object id="{100 + i}" name="npc" x="{x:g}" y="{y:g}"><properties>'
        f'<property name="npc_id" value="{nid}"/>'
        f'<property name="dialogue_id" value="{did}"/></properties><point/></object>'
        for i, (nid, did, x, y) in enumerate(npcs, start=1)
    )
    groups = ' <objectgroup id="2" name="spawns">\n' \
             '  <object id="1" name="player_start" x="50" y="50"><point/></object>\n </objectgroup>\n'
    if npcs:
        groups += f' <objectgroup id="3" name="npcs">\n{npc_xml}\n </objectgroup>\n'
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


def make_game() -> tuple[GameStateManager, GameScreen]:
    manager = GameStateManager()
    screen = GameScreen(manager)
    manager.push(screen)
    return manager, screen


# ── Phase 1/2: данные и TMX ──────────────────────────────────────────────────────


class TestNpcData:
    def test_loads_npc_from_tmx(self, tmp_path: Path) -> None:
        path = write_map(tmp_path / "m.tmx", [("ranger", "ranger_intro", 64.0, 96.0)])
        npcs = load_npcs_from_tmx(path)
        assert len(npcs) == 1
        assert (npcs[0].npc_id, npcs[0].dialogue_id) == ("ranger", "ranger_intro")
        assert (npcs[0].x, npcs[0].y) == (64.0, 96.0)

    def test_world_exposes_npcs(self, tmp_path: Path) -> None:
        path = write_map(tmp_path / "m.tmx", [("a", "d1", 64.0, 96.0)])
        assert len(GameWorld(path).npcs) == 1

    def test_map_without_npcs_layer_is_empty(self, tmp_path: Path) -> None:
        path = write_map(tmp_path / "m.tmx", [])
        assert GameWorld(path).npcs == []

    def test_level1_has_ranger_npc(self) -> None:
        npcs = GameWorld().npcs
        assert any(n.npc_id == "ranger" and n.dialogue_id == "ranger_intro" for n in npcs)


# ── Phase 5: NPC entity / рендер ─────────────────────────────────────────────────


class TestNpcEntity:
    def test_properties(self) -> None:
        npc = NPC(10.0, 20.0, "ranger", "ranger_intro")
        assert npc.npc_id == "ranger"
        assert npc.dialogue_id == "ranger_intro"

    def test_fallback_draw(self) -> None:
        npc = NPC(50.0, 50.0, "ranger", "d")
        surf = pygame.Surface((120, 120))
        surf.fill((0, 0, 0))
        npc.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at((50, 50))[:3] == NPC.COLOR  # fallback-прямоугольник

    def test_sprite_draw(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from systems.asset_loader import AssetLoader
        img = pygame.Surface((16, 16))
        img.fill(_RED)
        pygame.image.save(img, str(tmp_path / "npc_ranger.png"))
        monkeypatch.setattr("systems.asset_loader.SPRITES_DIR", tmp_path)
        AssetLoader.clear()
        npc = NPC(50.0, 50.0, "ranger", "d")
        surf = pygame.Surface((120, 120))
        npc.draw(surf, pygame.Vector2(0, 0))
        assert surf.get_at((50, 50))[:3] == _RED  # спрайт npc_ranger.png


# ── Phase 3: runtime — NPC на текущей карте ──────────────────────────────────────


class TestRuntime:
    def test_gamescreen_spawns_npcs_from_map(self) -> None:
        _, screen = make_game()
        assert any(isinstance(n, NPC) and n.npc_id == "ranger" for n in screen._npcs)

    def test_map_change_rebuilds_npcs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_map(tmp_path / "withnpc.tmx", [("guard", "g_dlg", 50.0, 50.0)])
        write_map(tmp_path / "nonpc.tmx", [])
        monkeypatch.setattr("systems.level_manager.MAPS_DIR", tmp_path)
        monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager("withnpc"))
        _, screen = make_game()
        assert len(screen._npcs) == 1 and screen._npcs[0].npc_id == "guard"
        screen._enter_map("nonpc", "player_start")
        assert screen._npcs == []  # NPC старой карты исчезли, новая без NPC


# ── Phase 4: взаимодействие по близости ──────────────────────────────────────────


class TestInteraction:
    def test_t_near_npc_opens_dialogue(self) -> None:
        manager, screen = make_game()  # игрок на старте, ranger рядом
        screen.handle_event(key_event(pygame.K_t))
        assert isinstance(manager.current, DialogueUI)
        assert screen.dialogue_system.is_active is True

    def test_t_far_from_npc_does_nothing(self) -> None:
        manager, screen = make_game()
        screen._player.pos.update(2000.0, 2000.0)  # далеко от ranger
        screen.handle_event(key_event(pygame.K_t))
        assert screen.dialogue_system.is_active is False
        assert manager.depth == 1  # диалог не открыт

    def test_nearest_npc_selected(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_map(tmp_path / "two.tmx",
                  [("near", "d_near", 60.0, 50.0), ("far", "d_far", 90.0, 50.0)])
        monkeypatch.setattr("systems.level_manager.MAPS_DIR", tmp_path)
        monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager("two"))
        _, screen = make_game()
        screen._player.pos.update(55.0, 50.0)  # ближе к "near"
        assert screen._nearest_npc().npc_id == "near"  # type: ignore[union-attr]
