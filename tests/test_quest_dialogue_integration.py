"""Tests for Sprint 8G: Quest ↔ Dialogue Integration.

Диалог выдаёт существующий квест: вариант с непустым quest_id при выборе эмитит
`dialogue_choice_selected`, интеграционный слой (GameScreen) принимает квест в
QuestSystem. Системы не дублируют состояние друг друга.
"""
from __future__ import annotations

import pygame

from data.dialogue_data import Dialogue, DialogueChoice, DialogueNode
from data.quest_data import KillZombieObjective, Quest
from main import GameStateManager
from systems.dialogue import DialogueSystem
from systems.event_bus import EventBus
from ui.dialogue_ui import DialogueUI
from ui.game_screen import GameScreen


# ── helpers ────────────────────────────────────────────────────────────────────


def make_game() -> tuple[GameStateManager, GameScreen]:
    manager = GameStateManager()
    screen = GameScreen(manager)
    manager.push(screen)
    return manager, screen


def key_event(key: int) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


def surface() -> pygame.Surface:
    return pygame.Surface((1280, 720))


def open_dialogue(manager: GameStateManager, screen: GameScreen) -> DialogueUI:
    screen.handle_event(key_event(pygame.K_t))
    ui = manager.current
    assert isinstance(ui, DialogueUI)
    return ui


class FakeEnemy:
    """Минимальная сущность для эмуляции гибели врага без pygame.

    xp_reward нужен подписчику GameScreen._on_entity_died (начисление XP за килл).
    """

    def __init__(self, faction: str = "enemy", xp_reward: int = 0) -> None:
        self.faction = faction
        self.xp_reward = xp_reward


def kill_enemy(times: int = 1) -> None:
    """Сэмулировать гибель N врагов через EventBus — двигатель прогресса квестов."""
    for _ in range(times):
        EventBus.emit("entity_died", {"entity": FakeEnemy("enemy")})


def quest_offer_dialogue(quest_id: str = "clear_bunker_a1") -> Dialogue:
    """Маленький диалог с веткой, выдающей квест по quest_id."""
    return Dialogue(
        id="offer",
        start_id="ask",
        nodes={
            "ask": DialogueNode(
                id="ask",
                speaker="Ranger",
                text="Need help clearing bunker A1?",
                choices=[
                    DialogueChoice("I'll help.", next_id="", quest_id=quest_id),
                    DialogueChoice("Not now.", next_id=""),
                ],
            ),
        },
    )


# ── DialogueSystem: событие выбора ────────────────────────────────────────────


class TestChoiceSelectedEvent:
    def test_choose_emits_choice_selected(self) -> None:
        received: list[DialogueChoice] = []
        EventBus.on("dialogue_choice_selected", lambda d: received.append(d["choice"]))
        system = DialogueSystem()
        system.start(quest_offer_dialogue())
        system.choose(0)
        assert len(received) == 1
        assert received[0].quest_id == "clear_bunker_a1"

    def test_choice_without_quest_carries_empty_quest_id(self) -> None:
        received: list[DialogueChoice] = []
        EventBus.on("dialogue_choice_selected", lambda d: received.append(d["choice"]))
        system = DialogueSystem()
        system.start(quest_offer_dialogue())
        system.choose(1)  # "Not now." — без quest_id
        assert len(received) == 1
        assert received[0].quest_id == ""

    def test_advance_emits_choice_selected(self) -> None:
        # Линейный узел (один вариант) тоже сообщает о выборе.
        received: list[DialogueChoice] = []
        EventBus.on("dialogue_choice_selected", lambda d: received.append(d["choice"]))
        system = DialogueSystem()
        dialogue = Dialogue(
            id="lin",
            start_id="a",
            nodes={
                "a": DialogueNode("a", "NPC", "Take this.", [DialogueChoice("Thanks", quest_id="q")]),
            },
        )
        system.start(dialogue)
        system.advance()
        assert len(received) == 1
        assert received[0].quest_id == "q"

    def test_terminal_advance_emits_no_choice(self) -> None:
        # У терминального узла нет вариантов — событие выбора не эмитится.
        received: list[DialogueChoice] = []
        EventBus.on("dialogue_choice_selected", lambda d: received.append(d["choice"]))
        system = DialogueSystem()
        dialogue = Dialogue(
            id="t",
            start_id="end",
            nodes={"end": DialogueNode("end", "NPC", "Bye.")},
        )
        system.start(dialogue)
        system.advance()  # терминал -> end, без выбора
        assert received == []


# ── Принятие квеста через диалог ─────────────────────────────────────────────


class TestQuestAcceptance:
    def test_choice_grants_quest(self) -> None:
        _, screen = make_game()
        assert screen._quest_system.active_quests == []
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(0)  # "I'll help." -> выдать квест
        active = screen._quest_system.active_quests
        assert len(active) == 1
        assert active[0].id == "clear_bunker_a1"

    def test_granted_quest_appears_among_active(self) -> None:
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_RETURN))  # выбор "I'll help" (индекс 0)
        ids = [q.id for q in screen._quest_system.active_quests]
        assert "clear_bunker_a1" in ids

    def test_declining_choice_grants_nothing(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(1)  # "Not now." — без quest_id
        assert screen._quest_system.active_quests == []


# ── Безопасность ──────────────────────────────────────────────────────────────


class TestSafety:
    def test_unknown_quest_id_is_safe(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(quest_offer_dialogue(quest_id="does_not_exist"))
        screen._dialogue_system.choose(0)  # quest_id есть, но в реестре его нет
        assert screen._quest_system.active_quests == []

    def test_empty_quest_id_is_noop(self) -> None:
        _, screen = make_game()
        screen._on_dialogue_choice({"choice": DialogueChoice("x", quest_id="")})
        assert screen._quest_system.active_quests == []

    def test_missing_choice_in_event_is_safe(self) -> None:
        _, screen = make_game()
        screen._on_dialogue_choice({})  # нет ключа "choice"
        assert screen._quest_system.active_quests == []

    def test_repeated_choice_does_not_duplicate_quest(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(0)
        # повторный выбор того же варианта (напр. при перезапуске диалога)
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(0)
        assert len(screen._quest_system.active_quests) == 1

    def test_regrant_after_completion_does_not_reactivate(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(0)
        kill_enemy(4)  # завершить квест
        assert screen._quest_system.active_quests == []
        assert len(screen._quest_system.completed_quests) == 1
        # повторная выдача уже завершённого квеста — нет-оп
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(0)
        assert screen._quest_system.active_quests == []
        assert len(screen._quest_system.completed_quests) == 1


# ── Полный сценарий ───────────────────────────────────────────────────────────


class TestFullScenario:
    def test_dialogue_to_quest_to_kills_to_completion_to_xp(self) -> None:
        manager, screen = make_game()
        player = screen._player
        assert player.experience.current_xp == 0
        assert player.experience.current_level == 1

        # диалог -> выбор -> получение квеста
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_RETURN))  # "I'll help." -> quest granted
        active = screen._quest_system.active_quests
        assert len(active) == 1
        quest = active[0]
        assert quest.id == "clear_bunker_a1"

        # завершить диалог (survivor -> end), вернуться в игру
        ui.handle_event(key_event(pygame.K_RETURN))
        assert screen.dialogue_system.is_active is False
        assert manager.depth == 1

        # убийства -> прогресс -> завершение квеста
        kill_enemy(4)
        assert quest not in screen._quest_system.active_quests
        assert quest in screen._quest_system.completed_quests

        # XP начислен (100 за квест -> level 2)
        assert player.experience.current_xp == 100
        assert player.experience.current_level == 2

    def test_quest_progress_works_as_before_after_grant(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(0)
        quest = screen._quest_system.active_quests[0]
        objective = quest.objectives[0]
        assert isinstance(objective, KillZombieObjective)
        assert objective.progress == "0/4"
        kill_enemy(2)
        assert objective.progress == "2/4"
        assert objective.is_complete is False


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_normal_dialogue_without_quest_still_works(self) -> None:
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        # пройти диалог по ветке без выдачи квеста: "..." (silent, терминал)
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))  # -> silent
        node = screen.dialogue_system.current_node
        assert node is not None and node.id == "silent"
        ui.handle_event(key_event(pygame.K_RETURN))  # терминал -> завершение
        assert screen.dialogue_system.is_active is False
        assert manager.depth == 1

    def test_normal_quest_lifecycle_still_works(self) -> None:
        # Квест, принятый напрямую (без диалога), работает как раньше.
        _, screen = make_game()
        quest = Quest(
            id="side",
            title="Side",
            description="Kill 2",
            reward_xp=10,
            objectives=[KillZombieObjective(target_count=2)],
        )
        screen._quest_system.accept_quest(quest)
        assert quest in screen._quest_system.active_quests
        kill_enemy(2)
        assert quest in screen._quest_system.completed_quests

    def test_dialogue_choice_event_does_not_break_game_loop(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(quest_offer_dialogue())
        screen._dialogue_system.choose(0)
        screen.update(0.016)
        screen.draw(surface())
        assert len(screen._quest_system.active_quests) == 1
