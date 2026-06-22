"""Tests for Sprint 6: Inventory + Items."""
from __future__ import annotations

import pytest

from core.item import Item
from data.player_data import PlayerData
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from entities.player import Player
from systems.event_bus import EventBus
from systems.inventory import Inventory


# ── helpers ───────────────────────────────────────────────────────────────────

def make_food(nutrition: float = 25.0) -> FoodItem:
    return FoodItem(0.0, 0.0, "test_food", "Test Food", "Desc", nutrition)


def make_quest() -> QuestItem:
    return QuestItem(0.0, 0.0, "quest_alpha", "Component Alpha", "Desc")


def make_player(decay_rate: float = 0.0) -> Player:
    config = PlayerData(
        max_health=100,
        speed=200.0,
        width=32,
        height=32,
        max_hunger=100.0,
        hunger_decay_rate=decay_rate,
        hunger_damage_rate=5.0,
    )
    return Player(0.0, 0.0, config)


# ── Inventory ─────────────────────────────────────────────────────────────────

class TestInventoryAddItem:
    def test_add_item_success(self) -> None:
        inv = Inventory()
        food = make_food()
        assert inv.add_item(food) is True

    def test_add_item_stored(self) -> None:
        inv = Inventory()
        food = make_food()
        inv.add_item(food)
        assert inv.contains(food)

    def test_add_item_when_full_returns_false(self) -> None:
        inv = Inventory(capacity=1)
        inv.add_item(make_food())
        assert inv.add_item(make_food()) is False

    def test_add_item_when_full_does_not_store(self) -> None:
        inv = Inventory(capacity=1)
        inv.add_item(make_food())
        extra = make_food()
        inv.add_item(extra)
        assert not inv.contains(extra)


class TestInventoryRemoveItem:
    def test_remove_item_success(self) -> None:
        inv = Inventory()
        food = make_food()
        inv.add_item(food)
        assert inv.remove_item(food) is True
        assert not inv.contains(food)

    def test_remove_item_not_present_returns_false(self) -> None:
        inv = Inventory()
        assert inv.remove_item(make_food()) is False


class TestInventoryContains:
    def test_contains_present(self) -> None:
        inv = Inventory()
        food = make_food()
        inv.add_item(food)
        assert inv.contains(food) is True

    def test_contains_not_present(self) -> None:
        inv = Inventory()
        assert inv.contains(make_food()) is False


class TestInventoryCount:
    def test_count_empty(self) -> None:
        assert Inventory().count == 0

    def test_count_after_add(self) -> None:
        inv = Inventory()
        inv.add_item(make_food())
        inv.add_item(make_quest())
        assert inv.count == 2


class TestInventoryIsFull:
    def test_is_full_when_at_capacity(self) -> None:
        inv = Inventory(capacity=2)
        inv.add_item(make_food())
        inv.add_item(make_food())
        assert inv.is_full() is True

    def test_is_not_full_below_capacity(self) -> None:
        inv = Inventory(capacity=2)
        inv.add_item(make_food())
        assert inv.is_full() is False


class TestInventoryUseItem:
    def test_use_item_consumes_food(self) -> None:
        player = make_player()
        inv = Inventory()
        food = make_food(25.0)
        inv.add_item(food)
        player.hunger.update(5.0)  # deplete some hunger with decay_rate default
        # use food — should return True
        assert inv.use_item(food, player) is True

    def test_use_item_removes_food_from_inventory(self) -> None:
        player = make_player()
        inv = Inventory()
        food = make_food()
        inv.add_item(food)
        inv.use_item(food, player)
        assert not inv.contains(food)

    def test_use_item_keeps_quest_item(self) -> None:
        player = make_player()
        inv = Inventory()
        quest = make_quest()
        inv.add_item(quest)
        inv.use_item(quest, player)
        assert inv.contains(quest)

    def test_use_item_not_in_inventory_returns_false(self) -> None:
        player = make_player()
        inv = Inventory()
        assert inv.use_item(make_food(), player) is False


# ── FoodItem ──────────────────────────────────────────────────────────────────

class TestFoodItem:
    def test_use_returns_true(self) -> None:
        food = make_food()
        player = make_player()
        assert food.use(player) is True

    def test_restores_hunger(self) -> None:
        player = make_player(decay_rate=10.0)
        player.hunger.update(5.0)  # hunger = max(0, 100 - 50) = 50
        food = make_food(nutrition=25.0)
        food.use(player)
        assert player.hunger.current == pytest.approx(75.0)

    def test_clamps_to_maximum(self) -> None:
        player = make_player(decay_rate=10.0)
        player.hunger.update(5.0)  # hunger = 50
        food = make_food(nutrition=200.0)
        food.use(player)
        assert player.hunger.current == pytest.approx(player.hunger.maximum)


# ── QuestItem ─────────────────────────────────────────────────────────────────

class TestQuestItem:
    def test_use_returns_false(self) -> None:
        quest = make_quest()
        player = make_player()
        assert quest.use(player) is False

    def test_hierarchy(self) -> None:
        quest = make_quest()
        assert isinstance(quest, Item)

    def test_is_not_stackable_by_default(self) -> None:
        quest = make_quest()
        assert quest.stackable is False


# ── Player integration ────────────────────────────────────────────────────────

class TestPlayerInventoryIntegration:
    def test_pickup_item_adds_to_inventory(self) -> None:
        player = make_player()
        food = make_food()
        player.pickup_item(food)
        assert player.inventory.contains(food)

    def test_pickup_item_deactivates_world_item(self) -> None:
        player = make_player()
        food = make_food()
        player.pickup_item(food)
        assert food.active is False

    def test_pickup_item_returns_false_when_full(self) -> None:
        config = PlayerData(
            max_health=100, speed=200.0, width=32, height=32,
            max_hunger=100.0, hunger_decay_rate=0.0, hunger_damage_rate=5.0,
        )
        player = Player(0.0, 0.0, config)
        # fill inventory to capacity
        for _ in range(20):
            player.pickup_item(make_food())
        extra = make_food()
        assert player.pickup_item(extra) is False
        assert extra.active is True

    def test_use_item_restores_hunger(self) -> None:
        player = make_player(decay_rate=10.0)
        player.hunger.update(5.0)  # hunger = 50
        food = make_food(nutrition=30.0)
        player.pickup_item(food)
        player.use_item(food)
        assert player.hunger.current == pytest.approx(80.0)


# ── EventBus ──────────────────────────────────────────────────────────────────

class TestInventoryEvents:
    def test_inventory_item_added_event(self) -> None:
        received: list[dict] = []
        EventBus.on("inventory_item_added", received.append)
        inv = Inventory()
        food = make_food()
        inv.add_item(food)
        assert len(received) == 1
        assert received[0]["item"] is food

    def test_inventory_item_removed_event(self) -> None:
        received: list[dict] = []
        EventBus.on("inventory_item_removed", received.append)
        inv = Inventory()
        food = make_food()
        inv.add_item(food)
        inv.remove_item(food)
        assert len(received) == 1
        assert received[0]["item"] is food

    def test_item_used_event(self) -> None:
        received: list[dict] = []
        EventBus.on("item_used", received.append)
        player = make_player()
        inv = Inventory()
        food = make_food()
        inv.add_item(food)
        inv.use_item(food, player)
        assert len(received) == 1
        assert received[0]["item"] is food

    def test_item_used_event_not_fired_for_quest_item(self) -> None:
        received: list[dict] = []
        EventBus.on("item_used", received.append)
        player = make_player()
        inv = Inventory()
        quest = make_quest()
        inv.add_item(quest)
        inv.use_item(quest, player)
        assert len(received) == 0
