"""Tests for Sprint 8B: QuestLogUI — read-only display of active quests."""
from __future__ import annotations

import pygame

from data.quest_data import KillZombieObjective, Quest, QuestStatus
from systems.experience import ExperienceComponent
from systems.quest_system import QuestSystem
from ui.base_screen import BaseScreen
from ui.quest_log_ui import QuestLogUI


# ── helpers ────────────────────────────────────────────────────────────────────


class FakeEntity:
    """Минимальная сущность-зомби для прогона update_progress без pygame."""

    def __init__(self, faction: str = "enemy") -> None:
        self.faction = faction


def make_system() -> QuestSystem:
    return QuestSystem(ExperienceComponent())


def make_quest(quest_id: str = "q", target: int = 5, reward: int = 50) -> Quest:
    return Quest(
        id=quest_id,
        title=f"Kill {target} Zombies",
        description="Thin the horde.",
        reward_xp=reward,
        objectives=[KillZombieObjective(target_count=target)],
    )


def make_ui(system: QuestSystem | None = None, on_close: object = None) -> QuestLogUI:
    if system is None:
        system = make_system()
    if on_close is None:
        on_close = lambda: None  # noqa: E731
    return QuestLogUI(system, on_close)  # type: ignore[arg-type]


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def mouse_event() -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (0, 0)})


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


# ── TestOpen ───────────────────────────────────────────────────────────────────


class TestOpen:
    def test_is_base_screen(self) -> None:
        assert isinstance(make_ui(), BaseScreen)

    def test_initial_selected_index_zero(self) -> None:
        assert make_ui().selected_index == 0

    def test_reads_from_quest_system_not_copy(self) -> None:
        system = make_system()
        ui = make_ui(system)
        system.accept_quest(make_quest())
        # UI не кэширует — видит квест, принятый после создания UI
        assert len(ui._quest_system.active_quests) == 1


# ── TestClose ──────────────────────────────────────────────────────────────────


class TestClose:
    def test_esc_calls_on_close(self) -> None:
        called: list[int] = []
        ui = make_ui(on_close=lambda: called.append(1))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert len(called) == 1

    def test_esc_calls_once_per_press(self) -> None:
        called: list[int] = []
        ui = make_ui(on_close=lambda: called.append(1))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        ui.handle_event(key_event(pygame.K_ESCAPE))
        assert len(called) == 2

    def test_other_keys_do_not_close(self) -> None:
        called: list[int] = []
        ui = make_ui(on_close=lambda: called.append(1))
        for k in (pygame.K_UP, pygame.K_DOWN, pygame.K_RETURN, pygame.K_SPACE):
            ui.handle_event(key_event(k))
        assert len(called) == 0


# ── TestNavigation ─────────────────────────────────────────────────────────────


class TestNavigation:
    def _system_with(self, n: int) -> QuestSystem:
        system = make_system()
        for i in range(n):
            system.accept_quest(make_quest(quest_id=f"q{i}", target=i + 1))
        return system

    def test_down_advances_selection(self) -> None:
        ui = make_ui(self._system_with(3))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 1

    def test_down_twice_reaches_third(self) -> None:
        ui = make_ui(self._system_with(3))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 2

    def test_down_wraps_to_first(self) -> None:
        ui = make_ui(self._system_with(3))
        for _ in range(3):
            ui.handle_event(key_event(pygame.K_DOWN))
        assert ui.selected_index == 0

    def test_up_from_start_wraps_to_last(self) -> None:
        ui = make_ui(self._system_with(3))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 2

    def test_up_after_down_returns_to_start(self) -> None:
        ui = make_ui(self._system_with(3))
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 0

    def test_navigation_on_empty_stays_zero(self) -> None:
        ui = make_ui(make_system())
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert ui.selected_index == 0

    def test_unrelated_event_type_ignored(self) -> None:
        ui = make_ui(self._system_with(3))
        ui.handle_event(mouse_event())
        assert ui.selected_index == 0

    def test_unrelated_key_ignored(self) -> None:
        ui = make_ui(self._system_with(3))
        ui.handle_event(key_event(pygame.K_SPACE))
        assert ui.selected_index == 0


# ── TestDrawEmpty ──────────────────────────────────────────────────────────────


class TestDrawEmpty:
    def test_draw_empty_does_not_raise(self) -> None:
        make_ui(make_system()).draw(surface())

    def test_empty_list_selected_index_zero(self) -> None:
        assert make_ui(make_system()).selected_index == 0


# ── TestDrawSingle ─────────────────────────────────────────────────────────────


class TestDrawSingle:
    def test_draw_single_quest_does_not_raise(self) -> None:
        system = make_system()
        system.accept_quest(make_quest())
        make_ui(system).draw(surface())

    def test_draw_quest_without_objectives_does_not_raise(self) -> None:
        system = make_system()
        system.accept_quest(
            Quest(id="q", title="Talk", description="No objectives", reward_xp=10)
        )
        make_ui(system).draw(surface())


# ── TestDrawMultiple ───────────────────────────────────────────────────────────


class TestDrawMultiple:
    def test_draw_multiple_quests_does_not_raise(self) -> None:
        system = make_system()
        system.accept_quest(make_quest(quest_id="q1", target=5))
        system.accept_quest(make_quest(quest_id="q2", target=10))
        make_ui(system).draw(surface())

    def test_draw_after_navigation_does_not_raise(self) -> None:
        system = make_system()
        system.accept_quest(make_quest(quest_id="q1", target=5))
        system.accept_quest(make_quest(quest_id="q2", target=10))
        ui = make_ui(system)
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.draw(surface())


# ── TestProgressReflectsLiveData ───────────────────────────────────────────────


class TestProgressReflectsLiveData:
    def test_objective_progress_string_format(self) -> None:
        quest = make_quest(target=5)
        obj = quest.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.progress == "0/5"

    def test_progress_updates_after_kill(self) -> None:
        system = make_system()
        quest = make_quest(target=5)
        system.accept_quest(quest)
        ui = make_ui(system)
        system.update_progress({"entity": FakeEntity("enemy")})
        # UI читает живые данные из системы — прогресс обновился
        live = ui._quest_system.active_quests[0]
        obj = live.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.progress == "1/5"

    def test_draw_after_progress_does_not_raise(self) -> None:
        system = make_system()
        system.accept_quest(make_quest(target=5))
        ui = make_ui(system)
        system.update_progress({"entity": FakeEntity("enemy")})
        ui.draw(surface())

    def test_completed_quest_disappears_from_log(self) -> None:
        system = make_system()
        quest = make_quest(target=1, reward=50)
        system.accept_quest(quest)
        ui = make_ui(system)
        system.update_progress({"entity": FakeEntity("enemy")})
        assert quest not in ui._quest_system.active_quests
        ui.draw(surface())  # должен корректно показать пустой список


# ── Sprint 8D: narrative metadata display ───────────────────────────────────────


def make_narrative_quest(
    quest_id: str = "q",
    location: str = "Bunker A1",
    category: str = "main_story",
    lore_text: str = "Emergency transmission...",
) -> Quest:
    return Quest(
        id=quest_id,
        title="Clear Bunker A1",
        description="Eliminate infected units.",
        reward_xp=100,
        objectives=[KillZombieObjective(target_count=4)],
        lore_text=lore_text,
        location=location,
        category=category,
    )


class TestNarrativeMetadataDisplay:
    def test_format_meta_combines_category_and_location(self) -> None:
        quest = make_narrative_quest()
        assert QuestLogUI._format_meta(quest) == "[main_story] @ Bunker A1"

    def test_format_meta_only_location(self) -> None:
        quest = make_narrative_quest(category="")
        assert QuestLogUI._format_meta(quest) == "@ Bunker A1"

    def test_format_meta_only_category(self) -> None:
        quest = make_narrative_quest(location="")
        assert QuestLogUI._format_meta(quest) == "[main_story]"

    def test_format_meta_empty_when_no_metadata(self) -> None:
        # старый квест без narrative-полей → пустая строка → строка не рисуется
        quest = make_quest()
        assert QuestLogUI._format_meta(quest) == ""

    def test_draw_quest_with_metadata_does_not_raise(self) -> None:
        system = make_system()
        system.accept_quest(make_narrative_quest())
        make_ui(system).draw(surface())

    def test_draw_quest_without_metadata_does_not_raise(self) -> None:
        system = make_system()
        system.accept_quest(make_quest())
        make_ui(system).draw(surface())


# ── TestReadOnly ───────────────────────────────────────────────────────────────


class TestReadOnly:
    def test_draw_does_not_change_quest_count(self) -> None:
        system = make_system()
        system.accept_quest(make_quest(quest_id="q1"))
        system.accept_quest(make_quest(quest_id="q2"))
        ui = make_ui(system)
        before = len(system.active_quests)
        ui.draw(surface())
        assert len(system.active_quests) == before

    def test_navigation_does_not_change_quest_status(self) -> None:
        system = make_system()
        quest = make_quest()
        system.accept_quest(quest)
        ui = make_ui(system)
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_UP))
        assert quest.status == QuestStatus.ACTIVE

    def test_navigation_does_not_advance_progress(self) -> None:
        system = make_system()
        quest = make_quest(target=5)
        system.accept_quest(quest)
        ui = make_ui(system)
        ui.handle_event(key_event(pygame.K_DOWN))
        obj = quest.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.current_count == 0

    def test_active_quests_is_a_copy_ui_cannot_mutate_internal(self) -> None:
        system = make_system()
        system.accept_quest(make_quest())
        # active_quests возвращает копию — внешняя мутация не трогает систему
        system.active_quests.clear()
        assert len(system.active_quests) == 1
