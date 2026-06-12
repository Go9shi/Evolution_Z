"""Tests for Sprint 8H: Lore System — слой Lore Data → Lore System.

Система хранит каталог лор-записей и набор открытых, эмитит EventBus-событие
'lore_unlocked' ровно один раз на запись. Повторное открытие и неизвестные id безопасны.
"""
from __future__ import annotations

from data.lore_data import LoreEntry
from systems.event_bus import EventBus
from systems.lore import LoreSystem


# ── helpers ───────────────────────────────────────────────────────────────────


def make_entry(
    entry_id: str = "lore1",
    title: str = "Origin of the Virus",
    text: str = "The pathogen was synthetic.",
    category: str = "",
) -> LoreEntry:
    return LoreEntry(id=entry_id, title=title, text=text, category=category)


class Recorder:
    """Записывает данные событий EventBus для проверок."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, data: dict) -> None:
        self.calls.append(data)


# ── LoreEntry (доменная модель) ───────────────────────────────────────────────


class TestLoreEntry:
    def test_has_fields(self) -> None:
        entry = LoreEntry(id="e1", title="T", text="Body", category="note")
        assert entry.id == "e1"
        assert entry.title == "T"
        assert entry.text == "Body"
        assert entry.category == "note"

    def test_category_defaults_empty(self) -> None:
        entry = LoreEntry(id="e1", title="T", text="Body")
        assert entry.category == ""


# ── register / has_entry ──────────────────────────────────────────────────────


class TestRegister:
    def test_register_makes_entry_known(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        assert system.has_entry("a") is True

    def test_unregistered_entry_not_known(self) -> None:
        system = LoreSystem()
        assert system.has_entry("ghost") is False

    def test_registered_entry_in_entries(self) -> None:
        system = LoreSystem()
        entry = make_entry("a")
        system.register(entry)
        assert entry in system.entries

    def test_register_does_not_unlock(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        assert system.is_unlocked("a") is False
        assert system.unlocked_entries == []

    def test_reregister_overwrites(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a", title="Old"))
        system.register(make_entry("a", title="New"))
        assert len(system.entries) == 1
        assert system.entries[0].title == "New"


# ── unlock (базовые сценарии) ─────────────────────────────────────────────────


class TestUnlock:
    def test_unlock_registered_returns_true(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        assert system.unlock("a") is True

    def test_unlock_marks_unlocked(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        system.unlock("a")
        assert system.is_unlocked("a") is True

    def test_unlock_appears_in_unlocked_entries(self) -> None:
        system = LoreSystem()
        entry = make_entry("a")
        system.register(entry)
        system.unlock("a")
        assert system.unlocked_entries == [entry]

    def test_double_unlock_returns_false(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        assert system.unlock("a") is True
        assert system.unlock("a") is False

    def test_double_unlock_does_not_duplicate(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        system.unlock("a")
        system.unlock("a")
        assert len(system.unlocked_entries) == 1


# ── unlocked_entries (список открытых) ────────────────────────────────────────


class TestUnlockedEntries:
    def test_empty_when_nothing_unlocked(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        assert system.unlocked_entries == []

    def test_preserves_unlock_order(self) -> None:
        system = LoreSystem()
        for eid in ("a", "b", "c"):
            system.register(make_entry(eid))
        system.unlock("b")
        system.unlock("a")
        system.unlock("c")
        assert [e.id for e in system.unlocked_entries] == ["b", "a", "c"]

    def test_returns_copy_external_mutation_safe(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        system.unlock("a")
        system.unlocked_entries.clear()
        assert len(system.unlocked_entries) == 1

    def test_only_unlocked_entries_listed(self) -> None:
        system = LoreSystem()
        system.register(make_entry("a"))
        system.register(make_entry("b"))
        system.unlock("a")
        ids = [e.id for e in system.unlocked_entries]
        assert ids == ["a"]


# ── Безопасность ──────────────────────────────────────────────────────────────


class TestSafety:
    def test_unlock_unknown_returns_false(self) -> None:
        system = LoreSystem()
        assert system.unlock("ghost") is False

    def test_unlock_unknown_does_not_unlock(self) -> None:
        system = LoreSystem()
        system.unlock("ghost")
        assert system.is_unlocked("ghost") is False
        assert system.unlocked_entries == []

    def test_empty_system_queries_safe(self) -> None:
        system = LoreSystem()
        assert system.has_entry("x") is False
        assert system.is_unlocked("x") is False
        assert system.unlocked_entries == []
        assert system.entries == []

    def test_multiple_entries_independent(self) -> None:
        system = LoreSystem()
        for eid in ("a", "b", "c"):
            system.register(make_entry(eid))
        system.unlock("a")
        system.unlock("c")
        assert system.is_unlocked("a") is True
        assert system.is_unlocked("b") is False
        assert system.is_unlocked("c") is True
        assert len(system.entries) == 3
        assert len(system.unlocked_entries) == 2


# ── Интеграция: события EventBus ──────────────────────────────────────────────


class TestEvents:
    def test_unlock_emits_event(self) -> None:
        recorder = Recorder()
        EventBus.on("lore_unlocked", recorder)
        system = LoreSystem()
        system.register(make_entry("a"))
        system.unlock("a")
        assert len(recorder.calls) == 1

    def test_event_carries_entry(self) -> None:
        recorder = Recorder()
        EventBus.on("lore_unlocked", recorder)
        system = LoreSystem()
        entry = make_entry("a")
        system.register(entry)
        system.unlock("a")
        assert recorder.calls[0]["entry"] is entry

    def test_double_unlock_emits_once(self) -> None:
        recorder = Recorder()
        EventBus.on("lore_unlocked", recorder)
        system = LoreSystem()
        system.register(make_entry("a"))
        system.unlock("a")
        system.unlock("a")
        assert len(recorder.calls) == 1

    def test_unknown_unlock_emits_nothing(self) -> None:
        recorder = Recorder()
        EventBus.on("lore_unlocked", recorder)
        system = LoreSystem()
        system.unlock("ghost")
        assert recorder.calls == []

    def test_each_entry_emits_its_own_event(self) -> None:
        recorder = Recorder()
        EventBus.on("lore_unlocked", recorder)
        system = LoreSystem()
        system.register(make_entry("a"))
        system.register(make_entry("b"))
        system.unlock("a")
        system.unlock("b")
        ids = [data["entry"].id for data in recorder.calls]
        assert ids == ["a", "b"]
