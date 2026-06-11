"""Tests for Sprint 8A: QuestSystem Core."""
from __future__ import annotations

from data.quest_data import KillZombieObjective, Objective, Quest, QuestStatus
from systems.event_bus import EventBus
from systems.experience import ExperienceComponent, required_xp
from systems.quest_system import QuestSystem


# ── helpers ───────────────────────────────────────────────────────────────────

def make_exp() -> ExperienceComponent:
    return ExperienceComponent()


def make_quest(quest_id: str = "q1", reward_xp: int = 50) -> Quest:
    return Quest(id=quest_id, title="Test Quest", description="Desc", reward_xp=reward_xp)


def make_kill_quest(target_count: int = 3, reward_xp: int = 50, quest_id: str = "kq") -> Quest:
    return Quest(
        id=quest_id,
        title="Kill Quest",
        description="Kill some zombies",
        reward_xp=reward_xp,
        objectives=[KillZombieObjective(target_count=target_count)],
    )


class FakeEntity:
    """Минимальная сущность для тестов — имитирует Entity без pygame."""

    def __init__(self, faction: str = "enemy") -> None:
        self.faction = faction


# ── QuestStatus ───────────────────────────────────────────────────────────────

class TestQuestStatus:
    def test_has_available(self) -> None:
        assert QuestStatus.AVAILABLE is not None

    def test_has_active(self) -> None:
        assert QuestStatus.ACTIVE is not None

    def test_has_completed(self) -> None:
        assert QuestStatus.COMPLETED is not None

    def test_values_distinct(self) -> None:
        statuses = [QuestStatus.AVAILABLE, QuestStatus.ACTIVE, QuestStatus.COMPLETED]
        assert len(set(statuses)) == 3


# ── Quest dataclass ───────────────────────────────────────────────────────────

class TestQuest:
    def test_fields_set(self) -> None:
        q = Quest(id="q1", title="T", description="D", reward_xp=100)
        assert q.id == "q1"
        assert q.title == "T"
        assert q.description == "D"
        assert q.reward_xp == 100

    def test_default_status_available(self) -> None:
        assert make_quest().status == QuestStatus.AVAILABLE

    def test_default_objectives_empty(self) -> None:
        assert Quest(id="q1", title="T", description="D", reward_xp=0).objectives == []

    def test_objectives_independent_between_instances(self) -> None:
        q1 = make_quest("q1")
        q2 = make_quest("q2")
        q1.objectives.append(KillZombieObjective(1))
        assert len(q2.objectives) == 0


# ── KillZombieObjective ───────────────────────────────────────────────────────

class TestKillZombieObjective:
    def test_initial_target_count(self) -> None:
        assert KillZombieObjective(target_count=5).target_count == 5

    def test_initial_current_count_zero(self) -> None:
        assert KillZombieObjective(target_count=5).current_count == 0

    def test_not_complete_initially(self) -> None:
        assert not KillZombieObjective(target_count=3).is_complete

    def test_enemy_kill_increments(self) -> None:
        obj = KillZombieObjective(target_count=5)
        obj.on_kill("enemy")
        assert obj.current_count == 1

    def test_player_faction_does_not_increment(self) -> None:
        obj = KillZombieObjective(target_count=5)
        obj.on_kill("player")
        assert obj.current_count == 0

    def test_complete_when_target_reached(self) -> None:
        obj = KillZombieObjective(target_count=2)
        obj.on_kill("enemy")
        obj.on_kill("enemy")
        assert obj.is_complete

    def test_count_does_not_exceed_target(self) -> None:
        obj = KillZombieObjective(target_count=1)
        obj.on_kill("enemy")
        obj.on_kill("enemy")
        assert obj.current_count == 1

    def test_target_zero_is_immediately_complete(self) -> None:
        assert KillZombieObjective(target_count=0).is_complete

    def test_is_objective_subclass(self) -> None:
        assert isinstance(KillZombieObjective(target_count=1), Objective)


# ── accept_quest ──────────────────────────────────────────────────────────────

class TestAcceptQuest:
    def test_accept_adds_to_active(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest()
        qs.accept_quest(q)
        assert q in qs.active_quests

    def test_accept_changes_status_to_active(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest()
        qs.accept_quest(q)
        assert q.status == QuestStatus.ACTIVE

    def test_accept_does_not_add_to_completed(self) -> None:
        qs = QuestSystem(make_exp())
        qs.accept_quest(make_kill_quest())
        assert len(qs.completed_quests) == 0

    def test_cannot_accept_already_active_quest(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest()
        qs.accept_quest(q)
        qs.accept_quest(q)
        assert len(qs.active_quests) == 1

    def test_cannot_accept_completed_quest(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest()
        qs.accept_quest(q)
        qs.complete_quest(q)
        qs.accept_quest(q)
        assert len(qs.active_quests) == 0

    def test_active_quests_returns_copy(self) -> None:
        qs = QuestSystem(make_exp())
        external = qs.active_quests
        external.append(make_kill_quest())
        assert len(qs.active_quests) == 0


# ── update_progress ───────────────────────────────────────────────────────────

class TestUpdateProgress:
    def test_enemy_kill_increments_objective(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=3)
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("enemy")})
        obj = q.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.current_count == 1

    def test_player_kill_does_not_progress(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=3)
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("player")})
        obj = q.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.current_count == 0

    def test_missing_entity_key_is_safe(self) -> None:
        qs = QuestSystem(make_exp())
        qs.update_progress({})  # must not raise

    def test_quest_completes_after_enough_kills(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=2)
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("enemy")})
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert q.status == QuestStatus.COMPLETED
        assert q in qs.completed_quests
        assert q not in qs.active_quests

    def test_not_yet_active_quest_not_updated(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=1)
        # quest never accepted
        qs.update_progress({"entity": FakeEntity("enemy")})
        obj = q.objectives[0]
        assert isinstance(obj, KillZombieObjective)
        assert obj.current_count == 0


# ── EventBus integration ──────────────────────────────────────────────────────

class TestEventBusIntegration:
    def test_entity_died_event_triggers_progress(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=1)
        qs.accept_quest(q)
        EventBus.emit("entity_died", {"entity": FakeEntity("enemy")})
        assert q.status == QuestStatus.COMPLETED

    def test_quest_completed_event_emitted_on_finish(self) -> None:
        received: list[dict] = []
        EventBus.on("quest_completed", received.append)
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=1)
        qs.accept_quest(q)
        EventBus.emit("entity_died", {"entity": FakeEntity("enemy")})
        assert len(received) == 1
        assert received[0]["quest"] is q

    def test_no_quest_completed_event_for_incomplete_progress(self) -> None:
        received: list[dict] = []
        EventBus.on("quest_completed", received.append)
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=3)
        qs.accept_quest(q)
        EventBus.emit("entity_died", {"entity": FakeEntity("enemy")})
        assert len(received) == 0


# ── XP reward ─────────────────────────────────────────────────────────────────

class TestXpReward:
    def test_reward_xp_added_on_completion(self) -> None:
        exp = make_exp()
        qs = QuestSystem(exp)
        q = make_kill_quest(target_count=1, reward_xp=75)
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert exp.current_xp == 75

    def test_reward_xp_causes_level_up(self) -> None:
        exp = make_exp()
        qs = QuestSystem(exp)
        # required_xp(1) == 100 → one kill quest completes and levels up
        q = make_kill_quest(target_count=1, reward_xp=required_xp(1))
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert exp.current_level == 2

    def test_no_xp_before_completion(self) -> None:
        exp = make_exp()
        qs = QuestSystem(exp)
        q = make_kill_quest(target_count=3, reward_xp=100)
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert exp.current_xp == 0


# ── cannot complete twice ──────────────────────────────────────────────────────

class TestCannotCompleteTwice:
    def test_force_complete_removes_from_active(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest()
        qs.accept_quest(q)
        qs.complete_quest(q)
        assert q not in qs.active_quests

    def test_force_complete_adds_to_completed(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest()
        qs.accept_quest(q)
        qs.complete_quest(q)
        assert q in qs.completed_quests

    def test_complete_twice_does_not_double_xp(self) -> None:
        exp = make_exp()
        qs = QuestSystem(exp)
        q = make_kill_quest(target_count=1, reward_xp=50)
        qs.accept_quest(q)
        qs.complete_quest(q)
        qs.complete_quest(q)  # second call ignored
        assert exp.current_xp == 50

    def test_kills_after_completion_grant_no_xp(self) -> None:
        exp = make_exp()
        qs = QuestSystem(exp)
        q = make_kill_quest(target_count=1, reward_xp=50)
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("enemy")})
        xp_snapshot = exp.current_xp
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert exp.current_xp == xp_snapshot


# ── multiple active quests ─────────────────────────────────────────────────────

class TestMultipleQuests:
    def test_two_quests_track_independently(self) -> None:
        qs = QuestSystem(make_exp())
        q1 = make_kill_quest(target_count=1, quest_id="q1")
        q2 = make_kill_quest(target_count=2, quest_id="q2")
        qs.accept_quest(q1)
        qs.accept_quest(q2)
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert q1.status == QuestStatus.COMPLETED
        assert q2.status == QuestStatus.ACTIVE
        assert len(qs.active_quests) == 1
        assert len(qs.completed_quests) == 1

    def test_both_quests_complete_in_one_kill(self) -> None:
        qs = QuestSystem(make_exp())
        q1 = make_kill_quest(target_count=1, quest_id="q1")
        q2 = make_kill_quest(target_count=1, quest_id="q2")
        qs.accept_quest(q1)
        qs.accept_quest(q2)
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert len(qs.active_quests) == 0
        assert len(qs.completed_quests) == 2

    def test_xp_from_multiple_quests_accumulates(self) -> None:
        exp = make_exp()
        qs = QuestSystem(exp)
        q1 = make_kill_quest(target_count=1, reward_xp=30, quest_id="q1")
        q2 = make_kill_quest(target_count=1, reward_xp=20, quest_id="q2")
        qs.accept_quest(q1)
        qs.accept_quest(q2)
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert exp.current_xp == 50

    def test_completed_quests_returns_copy(self) -> None:
        qs = QuestSystem(make_exp())
        external = qs.completed_quests
        external.append(make_kill_quest())
        assert len(qs.completed_quests) == 0


# ── edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_quest_without_objectives_never_auto_completes(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_quest()
        qs.accept_quest(q)
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert q.status == QuestStatus.ACTIVE

    def test_quest_without_objectives_can_be_force_completed(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_quest(reward_xp=10)
        qs.accept_quest(q)
        qs.complete_quest(q)
        assert q.status == QuestStatus.COMPLETED

    def test_objectives_called_polymorphically_no_isinstance(self) -> None:
        """QuestSystem не использует isinstance — вызывает obj.on_kill(faction) полиморфно."""
        qs = QuestSystem(make_exp())
        q = make_kill_quest(target_count=1)
        qs.accept_quest(q)
        # objectives обновляются через on_kill, не через isinstance-проверки
        qs.update_progress({"entity": FakeEntity("enemy")})
        assert q.status == QuestStatus.COMPLETED

    def test_complete_quest_noop_if_not_in_active(self) -> None:
        qs = QuestSystem(make_exp())
        q = make_kill_quest()
        qs.complete_quest(q)  # never accepted — must not raise
        assert len(qs.completed_quests) == 0

    def test_vertical_loop_accept_kill_level_up(self) -> None:
        """Вертикальный цикл: принять → убить → завершить → XP → level up."""
        exp = make_exp()
        qs = QuestSystem(exp)
        q = make_kill_quest(target_count=10, reward_xp=required_xp(1))
        qs.accept_quest(q)
        assert q.status == QuestStatus.ACTIVE
        for _ in range(10):
            EventBus.emit("entity_died", {"entity": FakeEntity("enemy")})
        assert q.status == QuestStatus.COMPLETED
        assert exp.current_level == 2
