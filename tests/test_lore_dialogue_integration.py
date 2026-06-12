"""Tests for Sprint 8I: Lore ↔ Dialogue Integration.

Диалог открывает существующую запись лора: вариант с непустым lore_id при выборе
эмитит `dialogue_choice_selected`, интеграционный слой (GameScreen) открывает запись
в LoreSystem. Системы не дублируют состояние друг друга.
"""
from __future__ import annotations

import pygame

from data.dialogue_data import Dialogue, DialogueChoice, DialogueNode
from data.quest_data import KillZombieObjective, Quest
from main import GameStateManager
from systems.event_bus import EventBus
from ui.dialogue_ui import DialogueUI
from ui.game_screen import GameScreen

# Запись лора, зарегистрированная GameScreen из assets/data/lore.json.
LORE_ID = "bunker_a1_origin"


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


def lore_offer_dialogue(lore_id: str = LORE_ID) -> Dialogue:
    """Маленький диалог с веткой, открывающей запись лора по lore_id."""
    return Dialogue(
        id="lore_offer",
        start_id="ask",
        nodes={
            "ask": DialogueNode(
                id="ask",
                speaker="Ranger",
                text="Before the outbreak, this bunker stored medical samples.",
                choices=[
                    DialogueChoice("Tell me more.", next_id="", lore_id=lore_id),
                    DialogueChoice("I don't care.", next_id=""),
                ],
            ),
        },
    )


class FakeEnemy:
    """Минимальная сущность для эмуляции гибели врага без pygame."""

    def __init__(self, faction: str = "enemy", xp_reward: int = 0) -> None:
        self.faction = faction
        self.xp_reward = xp_reward


def kill_enemy(times: int = 1) -> None:
    for _ in range(times):
        EventBus.emit("entity_died", {"entity": FakeEnemy("enemy")})


# ── Разблокировка ─────────────────────────────────────────────────────────────


class TestLoreUnlock:
    def test_choice_unlocks_lore(self) -> None:
        _, screen = make_game()
        assert screen._lore_system.unlocked_entries == []
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)  # "Tell me more." -> открыть запись
        assert screen._lore_system.is_unlocked(LORE_ID) is True

    def test_unlocked_entry_appears_among_unlocked(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)
        ids = [e.id for e in screen._lore_system.unlocked_entries]
        assert LORE_ID in ids

    def test_choice_without_lore_unlocks_nothing(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(1)  # "I don't care." — без lore_id
        assert screen._lore_system.unlocked_entries == []


# ── Безопасность ──────────────────────────────────────────────────────────────


class TestSafety:
    def test_unknown_lore_id_is_safe(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue(lore_id="does_not_exist"))
        screen._dialogue_system.choose(0)  # lore_id есть, но в каталоге его нет
        assert screen._lore_system.unlocked_entries == []
        assert screen._lore_system.is_unlocked("does_not_exist") is False

    def test_empty_lore_id_is_noop(self) -> None:
        _, screen = make_game()
        screen._on_dialogue_choice({"choice": DialogueChoice("x", lore_id="")})
        assert screen._lore_system.unlocked_entries == []

    def test_missing_choice_in_event_is_safe(self) -> None:
        _, screen = make_game()
        screen._on_dialogue_choice({})  # нет ключа "choice"
        assert screen._lore_system.unlocked_entries == []

    def test_repeated_unlock_does_not_duplicate(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)
        # повторный выбор того же варианта (напр. при перезапуске диалога)
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)
        assert len(screen._lore_system.unlocked_entries) == 1


# ── Интеграция: событие lore_unlocked ─────────────────────────────────────────


class TestEvents:
    def test_unlock_emits_lore_unlocked_once(self) -> None:
        calls: list[dict] = []
        EventBus.on("lore_unlocked", calls.append)
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)
        assert len(calls) == 1
        assert calls[0]["entry"].id == LORE_ID

    def test_repeated_unlock_emits_no_second_event(self) -> None:
        calls: list[dict] = []
        EventBus.on("lore_unlocked", calls.append)
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)
        assert len(calls) == 1

    def test_unknown_lore_emits_nothing(self) -> None:
        calls: list[dict] = []
        EventBus.on("lore_unlocked", calls.append)
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue(lore_id="ghost"))
        screen._dialogue_system.choose(0)
        assert calls == []


# ── Полный сценарий ───────────────────────────────────────────────────────────


class TestFullScenario:
    def test_dialogue_to_choice_to_unlock_via_t(self) -> None:
        manager, screen = make_game()
        assert screen._lore_system.is_unlocked(LORE_ID) is False

        # T -> DialogueUI; "I'll help" (индекс 0) -> survivor
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_RETURN))
        # "Thank you." (несёт lore_id) -> завершение диалога + открытие записи
        ui.handle_event(key_event(pygame.K_RETURN))

        assert screen.dialogue_system.is_active is False
        assert manager.depth == 1
        # запись лора открыта и присутствует в LoreSystem
        assert screen._lore_system.is_unlocked(LORE_ID) is True
        assert LORE_ID in [e.id for e in screen._lore_system.unlocked_entries]

    def test_unlock_does_not_break_game_loop(self) -> None:
        _, screen = make_game()
        screen._dialogue_system.start(lore_offer_dialogue())
        screen._dialogue_system.choose(0)
        screen.update(0.016)
        screen.draw(surface())
        assert len(screen._lore_system.unlocked_entries) == 1


# ── Регрессии ─────────────────────────────────────────────────────────────────


class TestRegressions:
    def test_normal_dialogue_without_lore_still_works(self) -> None:
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        # ветка без лора: "..." (silent, терминал)
        ui.handle_event(key_event(pygame.K_DOWN))
        ui.handle_event(key_event(pygame.K_RETURN))  # -> silent
        node = screen.dialogue_system.current_node
        assert node is not None and node.id == "silent"
        ui.handle_event(key_event(pygame.K_RETURN))  # терминал -> завершение
        assert screen.dialogue_system.is_active is False
        assert screen._lore_system.unlocked_entries == []

    def test_quest_dialogue_integration_still_works(self) -> None:
        # Sprint 8G не сломан: тот же выбор по-прежнему выдаёт квест.
        manager, screen = make_game()
        ui = open_dialogue(manager, screen)
        ui.handle_event(key_event(pygame.K_RETURN))  # "I'll help" -> квест выдан
        ids = [q.id for q in screen._quest_system.active_quests]
        assert "clear_bunker_a1" in ids

    def test_normal_quest_lifecycle_still_works(self) -> None:
        _, screen = make_game()
        quest = Quest(
            id="side",
            title="Side",
            description="Kill 2",
            reward_xp=10,
            objectives=[KillZombieObjective(target_count=2)],
        )
        screen._quest_system.accept_quest(quest)
        kill_enemy(2)
        assert quest in screen._quest_system.completed_quests

    def test_choice_grants_quest_and_lore_together(self) -> None:
        # Вариант может нести и quest_id, и lore_id — обе интеграции независимы.
        _, screen = make_game()
        screen._on_dialogue_choice(
            {"choice": DialogueChoice("x", quest_id="clear_bunker_a1", lore_id=LORE_ID)}
        )
        assert "clear_bunker_a1" in [q.id for q in screen._quest_system.active_quests]
        assert screen._lore_system.is_unlocked(LORE_ID) is True
