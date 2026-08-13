"""Tests for the reflection engine (Phase 8C — Criterion 4).

Validates:
- Hot weather + bike → recommendation changes
- Cold weather + walking → alert added
- High UV + outdoor commute → alert added
- Long commute + slow breakfast → note added
- No conflicts → confirmation logged
- Reflection always returns a ReflectionResult
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from agents.reflection import ReflectionEngine, ReflectionResult


def _make_weather(temp: float, uv: float = 3.0, condition: str = "Warm") -> dict:
    return {
        "section": "weather",
        "status": "success",
        "data": {
            "temp": temp,
            "temp_unit": "C",
            "condition": condition,
            "uv_index": uv,
            "uv_label": "Low",
            "high": temp + 3,
            "low": temp - 3,
            "source": "test",
            "hourly": [],
        },
    }


def _make_commute(mode: str = "drive", eta: int = 25, dist: float = 12.0) -> dict:
    return {
        "section": "commute",
        "status": "success",
        "data": {
            "recommended_mode": mode,
            "eta_minutes": eta,
            "distance_km": dist,
            "alerts": [],
            "alternates": [],
            "polyline": [],
            "origin": {"lat": 0, "lon": 0, "label": "A"},
            "dest": {"lat": 0.1, "lon": 0.1, "label": "B"},
            "source": "test",
            "mode_label": mode.capitalize(),
        },
    }


def _make_breakfast(name: str = "Scrambled Eggs", prep: int = 10) -> dict:
    return {
        "section": "breakfast",
        "status": "success",
        "data": {
            "recipe_name": name,
            "prep_time_minutes": prep,
            "ingredients_used": ["eggs"],
            "steps": ["Cook eggs."],
            "alternates": [],
        },
    }


class TestReflectionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ReflectionEngine()

    def test_returns_reflection_result(self):
        """Should always return a ReflectionResult."""
        result = self.engine.reflect({}, {})
        self.assertIsInstance(result, ReflectionResult)

    def test_hot_weather_changes_bike_to_drive(self):
        """Rule 1: 38°C + bike → switch to drive."""
        sections = {
            "weather": _make_weather(38),
            "commute": _make_commute("bike"),
        }
        result = self.engine.reflect(sections, {})
        self.assertGreater(len(result.changes_made), 0)
        # Verify commute was actually mutated
        mode = sections["commute"]["data"]["recommended_mode"]
        self.assertEqual(mode, "drive")

    def test_normal_weather_drive_no_change(self):
        """No rule fires for 22°C + drive."""
        sections = {
            "weather": _make_weather(22),
            "commute": _make_commute("drive"),
        }
        result = self.engine.reflect(sections, {})
        self.assertEqual(len(result.changes_made), 0)
        self.assertGreater(len(result.confirmations), 0)

    def test_cold_weather_walk_adds_alert(self):
        """Rule 2: 0°C + walk → add cold weather alert."""
        sections = {
            "weather": _make_weather(0),
            "commute": _make_commute("walk"),
        }
        result = self.engine.reflect(sections, {})
        self.assertGreater(len(result.changes_made), 0)
        alerts = sections["commute"]["data"]["alerts"]
        self.assertTrue(any("Freezing" in a or "🥶" in a for a in alerts))

    def test_high_uv_bike_adds_alert(self):
        """Rule 3: UV 9.5 + bike → add UV warning."""
        sections = {
            "weather": _make_weather(25, uv=9.5),
            "commute": _make_commute("bike"),
        }
        result = self.engine.reflect(sections, {})
        # Should have UV alert (might also trigger other rules)
        uv_changes = [c for c in result.changes_made if "UV" in c]
        self.assertGreater(len(uv_changes), 0)

    def test_long_commute_slow_breakfast_adds_note(self):
        """Rule 4: 50-min commute + 20-min breakfast → time-saving note."""
        sections = {
            "commute": _make_commute("drive", eta=50),
            "breakfast": _make_breakfast("Omelette", prep=20),
        }
        result = self.engine.reflect(sections, {})
        time_changes = [c for c in result.changes_made if "time" in c.lower() or "commute" in c.lower()]
        self.assertGreater(len(time_changes), 0)
        self.assertIn("reflection_note", sections["breakfast"]["data"])

    def test_short_commute_quick_breakfast_confirmed(self):
        """No rule fires for 15-min commute + 5-min breakfast."""
        sections = {
            "commute": _make_commute("drive", eta=15),
            "breakfast": _make_breakfast("Toast", prep=5),
        }
        result = self.engine.reflect(sections, {})
        # Should confirm compatibility
        self.assertGreater(len(result.confirmations), 0)

    def test_empty_sections_confirmed(self):
        """Empty sections → default confirmation."""
        result = self.engine.reflect({}, {})
        self.assertGreater(len(result.confirmations), 0)
        self.assertEqual(len(result.changes_made), 0)

    def test_weather_only_no_crash(self):
        """Weather only → should not crash on missing commute/breakfast."""
        sections = {"weather": _make_weather(25)}
        result = self.engine.reflect(sections, {})
        self.assertIsInstance(result, ReflectionResult)

    def test_reflection_at_least_one_change_on_extreme_data(self):
        """Full extreme scenario: 40°C, UV 10, biking, 60-min commute, 25-min breakfast."""
        sections = {
            "weather": _make_weather(40, uv=10.0),
            "commute": _make_commute("bike", eta=60),
            "breakfast": _make_breakfast("Hot Porridge", prep=25),
        }
        result = self.engine.reflect(sections, {})
        # Should fire multiple rules
        self.assertGreater(len(result.changes_made), 0,
                          "Reflection should change at least one answer on extreme data")


if __name__ == "__main__":
    unittest.main()
