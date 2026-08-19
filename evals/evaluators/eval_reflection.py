"""Evaluator for Cross-Domain Reflection and Consistency Rules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from agents.reflection import ReflectionEngine

DATASET_PATH = Path(__file__).resolve().parent.parent / "datasets" / "reflection_matrix.json"


def evaluate_reflection_matrix(dataset_path: Path | None = None) -> Dict[str, Any]:
    """Run reflection consistency matrix benchmark."""
    path = dataset_path or DATASET_PATH
    with open(path, "r", encoding="utf-8") as f:
        dataset: List[Dict[str, Any]] = json.load(f)

    engine = ReflectionEngine()
    total = len(dataset)
    passed_cases = 0
    details: List[Dict[str, Any]] = []

    for item in dataset:
        qid = item["id"]
        desc = item.get("description", "")
        sections = item["sections"]
        intent = item.get("intent", {})
        exp_overrides = item.get("expected_overrides_count", 0)
        exp_mode = item.get("expected_mode_override")
        exp_alert = item.get("expected_alert_substring")
        exp_note = item.get("expected_note_substring")
        min_conf = item.get("min_confirmations", 0)

        # Run reflection
        result = engine.reflect(sections, intent)

        case_ok = True

        # Check override count
        if len(result.changes_made) != exp_overrides:
            case_ok = False

        # Check mode override
        if exp_mode:
            commute_mode = sections.get("commute", {}).get("data", {}).get("recommended_mode")
            if commute_mode != exp_mode:
                case_ok = False

        # Check alert substring in commute data
        if exp_alert:
            alerts = sections.get("commute", {}).get("data", {}).get("alerts", [])
            if not any(exp_alert.lower() in a.lower() for a in alerts):
                case_ok = False

        # Check note substring in meal/breakfast data
        if exp_note:
            note = sections.get("breakfast", {}).get("data", {}).get("reflection_note", "")
            if exp_note.lower() not in note.lower():
                case_ok = False

        # Check confirmations count
        if min_conf and len(result.confirmations) < min_conf:
            case_ok = False

        if case_ok:
            passed_cases += 1

        details.append({
            "id": qid,
            "description": desc,
            "changes_made": result.changes_made,
            "confirmations": result.confirmations,
            "passed": case_ok,
        })

    accuracy = round(passed_cases / total, 4) if total > 0 else 1.0

    return {
        "category": "reflection_matrix",
        "total_test_cases": total,
        "passed_cases": passed_cases,
        "accuracy": accuracy,
        "passed": accuracy >= 0.95,
        "details": details,
    }


if __name__ == "__main__":
    res = evaluate_reflection_matrix()
    print(json.dumps(res, indent=2))
