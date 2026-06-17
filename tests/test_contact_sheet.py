"""Tests for Sprint 14C.1: генератор контактных листов (tools.contact_sheet).

Самодостаточные тесты на синтетических кадрах (не зависят от внешнего пака new_assets):
авто-подсчёт кадров, генерация PNG нужного размера, одиночный лист, отсутствие кадров.
Headless — модуль сам выставляет SDL_VIDEODRIVER=dummy.
"""
from __future__ import annotations

import math
from pathlib import Path

import pygame
import pytest

from tools import contact_sheet


def _make_frames(source: Path, sheet: str, n: int, size: int = 16) -> None:
    for i in range(n):
        surf = pygame.Surface((size, size))
        surf.fill((10 * i % 256, 20, 30))
        pygame.image.save(surf, str(source / f"{sheet}_{i}.png"))


class TestCountFrames:
    def test_counts_indexed_frames(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 7)
        assert contact_sheet.count_frames(tmp_path, "s") == 7

    def test_single_unindexed_sheet(self, tmp_path: Path) -> None:
        surf = pygame.Surface((16, 16))
        pygame.image.save(surf, str(tmp_path / "solo.png"))
        assert contact_sheet.count_frames(tmp_path, "solo") == 1

    def test_missing_sheet_is_zero(self, tmp_path: Path) -> None:
        assert contact_sheet.count_frames(tmp_path, "nope") == 0


class TestBuild:
    def test_creates_png(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 5)
        out = contact_sheet.build_contact_sheet(tmp_path, "s", tmp_path / "out")
        assert out.exists()
        assert out.name == "s_contact.png"

    def test_grid_dimensions_match_cols_and_cell(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 25)
        out = contact_sheet.build_contact_sheet(
            tmp_path, "s", tmp_path / "out", cols=10, cell=80
        )
        img = pygame.image.load(str(out))
        rows = math.ceil(25 / 10)
        assert img.get_size() == (10 * 80, rows * 80)

    def test_handles_count_not_divisible_by_cols(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 23)
        out = contact_sheet.build_contact_sheet(
            tmp_path, "s", tmp_path / "out", cols=10, cell=64
        )
        img = pygame.image.load(str(out))
        assert img.get_size() == (10 * 64, 3 * 64)  # 23 → 3 ряда

    def test_missing_sheet_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            contact_sheet.build_contact_sheet(tmp_path, "nope", tmp_path / "out")


class TestRangeAndHighlight:
    def test_parse_range_handles_ranges_and_singletons(self) -> None:
        assert contact_sheet._parse_range("0-3,42") == {0, 1, 2, 3, 42}

    def test_parse_range_empty(self) -> None:
        assert contact_sheet._parse_range(None) == set()
        assert contact_sheet._parse_range("") == set()

    def test_subset_filename_reflects_range(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 20)
        out = contact_sheet.build_contact_sheet(
            tmp_path, "s", tmp_path / "out", cols=6, cell=80, start=4, end=9
        )
        assert out.name == "s_4-9_contact.png"

    def test_subset_dimensions_only_cover_selected(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 20)
        out = contact_sheet.build_contact_sheet(
            tmp_path, "s", tmp_path / "out", cols=6, cell=80, start=4, end=9
        )
        img = pygame.image.load(str(out))
        assert img.get_size() == (6 * 80, 1 * 80)  # 6 кадров → 1 ряд

    def test_highlight_does_not_crash(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 6)
        out = contact_sheet.build_contact_sheet(
            tmp_path, "s", tmp_path / "out", highlight={1, 2}
        )
        assert out.exists()

    def test_end_clamped_to_total(self, tmp_path: Path) -> None:
        _make_frames(tmp_path, "s", 5)
        out = contact_sheet.build_contact_sheet(
            tmp_path, "s", tmp_path / "out", cols=10, cell=64, start=0, end=999
        )
        img = pygame.image.load(str(out))
        assert img.get_size() == (10 * 64, 1 * 64)  # только 5 кадров
