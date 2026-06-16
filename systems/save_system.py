from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from data.quest_loader import load_quests
from data.save_file import SaveData
from entities.items.food_item import FoodItem
from entities.items.quest_item import QuestItem
from settings import DATA_DIR
from systems.skill_tree import SkillType

if TYPE_CHECKING:
    from core.item import Item
    from entities.player import Player
    from systems.lore import LoreSystem
    from systems.quest_system import QuestSystem


class SaveError(Exception):
    """Ошибка чтения или разбора файла сохранения."""


class SaveSystem:
    """Сохранение/загрузка минимального состояния игры в JSON.

    Снимает состояние с существующих систем через их публичный API (capture) и
    восстанавливает его в свежие системы (apply). Сохраняет только данные, не объекты:
    прогресс игрока, уровни навыков, id предметов/квестов/лора. Без слотов, меню,
    автосейва и версий формата.
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir

    # ── capture / serialize ─────────────────────────────────────────────────

    def capture(
        self,
        player: Player,
        quest_system: QuestSystem,
        lore_system: LoreSystem,
        map_id: str = "level1",
    ) -> SaveData:
        """Снять снимок состояния через публичный API систем (+ карта и позиция игрока)."""
        exp = player.experience
        return SaveData(
            player_xp=exp.current_xp,
            player_level=exp.current_level,
            skill_levels={skill.name: player.skill_tree.get_level(skill) for skill in SkillType},
            inventory_item_ids=[item.item_id for item in player.inventory.items],
            active_quest_ids=[quest.id for quest in quest_system.active_quests],
            completed_quest_ids=[quest.id for quest in quest_system.completed_quests],
            unlocked_lore_ids=[entry.id for entry in lore_system.unlocked_entries],
            map_id=map_id,
            player_x=player.pos.x,
            player_y=player.pos.y,
        )

    def save(
        self,
        path: Path,
        player: Player,
        quest_system: QuestSystem,
        lore_system: LoreSystem,
        map_id: str = "level1",
    ) -> None:
        """Снять снимок и записать его в JSON-файл path."""
        data = self.capture(player, quest_system, lore_system, map_id)
        path.write_text(json.dumps(data.to_dict(), indent=2), encoding="utf-8")

    # ── deserialize / apply ─────────────────────────────────────────────────

    def load(self, path: Path) -> SaveData:
        """Прочитать и разобрать файл сохранения. Поднимает SaveError при ошибке."""
        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SaveError(f"Cannot read save file: {path}") from exc

        try:
            raw = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise SaveError(f"Invalid JSON in save file {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise SaveError("Save file must contain a JSON object")

        return SaveData.from_dict(raw)

    def apply(
        self,
        data: SaveData,
        player: Player,
        quest_system: QuestSystem,
        lore_system: LoreSystem,
    ) -> None:
        """Восстановить состояние из SaveData в свежие системы (через публичный API).

        Порядок важен: XP восстанавливается первым — `player.add_xp` через подписку
        `player_level_up` выдаёт очки навыков, которые затем тратятся на восстановление
        уровней навыков (`upgrade` заодно повторно применяет их эффекты к игроку).
        """
        if data.player_xp:
            player.add_xp(data.player_xp)
        self._restore_skills(data, player)
        self._restore_inventory(data, player)
        self._restore_quests(data, quest_system)
        self._restore_lore(data, lore_system)

    def load_into(
        self,
        path: Path,
        player: Player,
        quest_system: QuestSystem,
        lore_system: LoreSystem,
    ) -> SaveData:
        """Загрузить файл и применить его к системам. Возвращает разобранный SaveData."""
        data = self.load(path)
        self.apply(data, player, quest_system, lore_system)
        return data

    # ── restore helpers ─────────────────────────────────────────────────────

    def _restore_skills(self, data: SaveData, player: Player) -> None:
        for name, level in data.skill_levels.items():
            skill = SkillType.__members__.get(name)
            if skill is None:
                continue
            for _ in range(level):
                player.skill_tree.upgrade(skill, player)

    def _restore_inventory(self, data: SaveData, player: Player) -> None:
        configs = self._load_item_configs()
        for item_id in data.inventory_item_ids:
            item = self._build_item(item_id, configs)
            if item is not None:
                player.inventory.add_item(item)

    def _restore_quests(self, data: SaveData, quest_system: QuestSystem) -> None:
        quests_by_id = {q.id: q for q in load_quests(self._data_dir / "quests.json")}
        active = [quests_by_id[qid] for qid in data.active_quest_ids if qid in quests_by_id]
        completed = [
            quests_by_id[qid] for qid in data.completed_quest_ids if qid in quests_by_id
        ]
        quest_system.restore(active, completed)

    @staticmethod
    def _restore_lore(data: SaveData, lore_system: LoreSystem) -> None:
        for lore_id in data.unlocked_lore_ids:
            lore_system.unlock(lore_id)

    # ── item reconstruction by item_id ──────────────────────────────────────

    def _load_item_configs(self) -> dict[str, Any]:
        with open(self._data_dir / "items.json", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return data

    @staticmethod
    def _build_item(item_id: str, configs: dict[str, Any]) -> Item | None:
        """Восстановить предмет по item_id из конфигов items.json. None если id неизвестен."""
        food = configs.get("food", {})
        if item_id in food:
            cfg = food[item_id]
            return FoodItem(0.0, 0.0, item_id, cfg["name"], cfg["description"], cfg["nutrition"])
        quest = configs.get("quest", {})
        if item_id in quest:
            cfg = quest[item_id]
            return QuestItem(0.0, 0.0, item_id, cfg["name"], cfg["description"])
        return None
