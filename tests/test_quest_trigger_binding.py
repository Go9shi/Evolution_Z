"""Tests for Sprint 13C: Quest trigger binding — world events advance quests via EventBus."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from data.quest_data import (
    KillZombieObjective,
    Quest,
    QuestStatus,
    ReachZoneObjective,
)
from data.quest_loader import load_quests
from main import GameStateManager
from systems.event_bus import EventBus
from systems.experience import ExperienceComponent
from systems.level_manager import LevelManager
from systems.quest_system import QuestSystem
from ui.game_screen import GameScreen


# ── helpers ───────────────────────────────────────────────────────────────────


def quest_system() -> QuestSystem:
    return QuestSystem(ExperienceComponent())


def zone_quest(event_name: str = "quest_zone_entered", qid: str = "zq") -> Quest:
    return Quest(
        id=qid, title="Reach zone", description="d", reward_xp=70,
        objectives=[ReachZoneObjective(event_name=event_name)],
    )


def write_trigger_map(path: Path, event_name: str) -> Path:
    w = h = 12
    csv = ",\n".join(",".join("0" for _ in range(w)) for _ in range(h))
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<map version="1.10" orientation="orthogonal" width="{w}" height="{h}" '
        f'tilewidth="32" tileheight="32" infinite="0" nextlayerid="4" nextobjectid="200">\n'
        f' <tileset firstgid="1" name="c" tilewidth="32" tileheight="32" tilecount="1" '
        f'columns="1"><grid orientation="orthogonal" width="32" height="32"/><tile id="0"/>'
        f'</tileset>\n'
        f' <layer id="1" name="collision" width="{w}" height="{h}"><data encoding="csv">\n'
        f'{csv}\n</data></layer>\n'
        f' <objectgroup id="2" name="spawns"><object id="1" name="player_start" x="40" y="40">'
        f'<point/></object></objectgroup>\n'
        f' <objectgroup id="3" name="triggers"><object id="9" x="200" y="200" width="64" '
        f'height="64"><properties><property name="trigger_id" value="z"/>'
        f'<property name="event_name" value="{event_name}"/></properties></object>'
        f'</objectgroup>\n</map>\n',
        encoding="utf-8",
    )
    return path


# ── Phase 1/3: data-driven objective ─────────────────────────────────────────────


class TestReachZoneObjective:
    def test_starts_incomplete(self) -> None:
        obj = ReachZoneObjective("ev")
        assert obj.is_complete is False
        assert obj.progress == "0/1"

    def test_completes_on_matching_event(self) -> None:
        obj = ReachZoneObjective("ev")
        obj.on_event("ev")
        assert obj.is_complete is True
        assert obj.progress == "1/1"

    def test_ignores_other_event(self) -> None:
        obj = ReachZoneObjective("ev")
        obj.on_event("other")
        assert obj.is_complete is False

    def test_kill_does_not_affect_zone(self) -> None:
        obj = ReachZoneObjective("ev")
        obj.on_kill("enemy")  # no-op
        assert obj.is_complete is False

    def test_event_does_not_affect_kill(self) -> None:
        obj = KillZombieObjective(2)
        obj.on_event("ev")  # no-op (default)
        assert obj.is_complete is False


# ── data-driven loading (reach_zone из JSON) ─────────────────────────────────────


class TestLoader:
    def test_loads_reach_zone_objective(self, tmp_path: Path) -> None:
        raw = {"quests": [{"id": "q", "title": "t", "description": "d", "reward_xp": 10,
                           "objectives": [{"type": "reach_zone", "event_name": "lab_entered"}]}]}
        path = tmp_path / "q.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        quests = load_quests(path)
        obj = quests[0].objectives[0]
        assert isinstance(obj, ReachZoneObjective)
        assert obj.event_name == "lab_entered"


# ── Phase 2/4: QuestSystem subscribes & progresses via EventBus ──────────────────


class TestQuestSystemBinding:
    def test_accept_subscribes_and_event_completes(self) -> None:
        qs = quest_system()
        q = zone_quest("quest_zone_entered")
        qs.accept_quest(q)
        EventBus.emit("quest_zone_entered", {"trigger_id": "z"})
        assert q.status == QuestStatus.COMPLETED
        assert q in qs.completed_quests

    def test_event_grants_reward_xp(self) -> None:
        exp = ExperienceComponent()
        from systems.quest_system import QuestSystem
        qs = QuestSystem(exp)
        qs.accept_quest(zone_quest())
        EventBus.emit("quest_zone_entered", {})
        assert exp.current_xp == 70

    def test_unrelated_event_does_nothing(self) -> None:
        qs = quest_system()
        q = zone_quest("lab_entered")
        qs.accept_quest(q)
        EventBus.emit("some_other_event", {})
        assert q.status == QuestStatus.ACTIVE

    def test_kill_quest_still_works(self) -> None:
        qs = quest_system()
        q = Quest(id="k", title="t", description="d", reward_xp=10,
                  objectives=[KillZombieObjective(1)])
        qs.accept_quest(q)

        class _E:
            faction = "enemy"
        EventBus.emit("entity_died", {"entity": _E()})
        assert q.status == QuestStatus.COMPLETED  # старый механизм не сломан

    def test_no_subscription_without_event_objective(self) -> None:
        qs = quest_system()
        qs.accept_quest(Quest(id="k", title="t", description="d", reward_xp=10,
                              objectives=[KillZombieObjective(1)]))
        assert qs._event_subs == {}  # kill-квест не плодит world-подписок


# ── Phase 5: полная цепочка TMX → EventBus → QuestSystem ─────────────────────────


class TestFullChain:
    def test_trigger_advances_quest(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_trigger_map(tmp_path / "m.tmx", "quest_zone_entered")
        monkeypatch.setattr("systems.level_manager.MAPS_DIR", tmp_path)
        monkeypatch.setattr("ui.game_screen.LevelManager", lambda: LevelManager("m"))
        manager = GameStateManager()
        screen = GameScreen(manager)
        manager.push(screen)
        # квест с зоной принят (как сделал бы диалог)
        screen._quest_system.accept_quest(zone_quest("quest_zone_entered"))
        # игрок входит в зону → trigger → EventBus → quest progress
        screen._player.pos.update(232.0, 232.0)
        screen._player.rect.center = (232, 232)
        screen.update(0.016)
        assert screen._quest_system.completed_quests[0].id == "zq"


# ── Регрессия: teardown снимает world-подписки ───────────────────────────────────


class TestTeardown:
    def test_cleanup_removes_world_subscriptions(self) -> None:
        manager = GameStateManager()
        screen = GameScreen(manager)
        manager.push(screen)
        screen._quest_system.accept_quest(zone_quest("quest_zone_entered"))
        assert "quest_zone_entered" in EventBus._listeners
        assert len(EventBus._listeners["quest_zone_entered"]) == 1
        screen.cleanup()
        assert EventBus._listeners.get("quest_zone_entered", []) == []
