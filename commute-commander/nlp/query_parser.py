import re
from typing import Dict, List

try:
    from transformers import pipeline
except ImportError:  # pragma: no cover - dependency may be absent in the environment
    pipeline = None


class QueryParser:
    """Beginner-friendly NLP parser with a transformer-backed section classifier."""

    def __init__(self) -> None:
        self.section_keywords = {
            "weather": ["weather", "forecast"],
            "uv": ["uv", "sun", "sunlight"],
            "news": ["news", "headlines"],
            "commute": ["commute", "traffic", "transit", "travel", "advice"],
            "breakfast": ["breakfast", "meal", "idea"],
        }
        self.ingredient_keywords = ["eggs", "egg", "toast", "banana", "oat", "oats", "milk", "cheese"]
        self.travel_words = ["leaving", "heading out", "going to work", "going", "leave", "out"]
        self.classifier = None

        if pipeline is not None:
            try:
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="valhalla/distilbart-mnli-12-3",
                )
            except Exception:  # pragma: no cover - model download may fail offline
                self.classifier = None

    def parse(self, query: str) -> Dict[str, object]:
        normalized = query.lower().strip()
        sections = self._extract_sections(normalized)
        location = self._extract_location(query)
        ingredients = self._extract_ingredients(normalized)
        time_constraint = self._extract_time_constraint(normalized)
        travel_intent = self._extract_travel_intent(normalized)

        return {
            "location": location,
            "sections": sections,
            "ingredients": ingredients,
            "time_constraint": time_constraint,
            "travel_intent": travel_intent,
            "raw_query": query,
        }

    def _extract_sections(self, normalized: str) -> List[str]:
        found = []
        for name, keywords in self.section_keywords.items():
            if any(keyword in normalized for keyword in keywords):
                found.append(name)

        if self.classifier is not None:
            try:
                result = self.classifier(
                    normalized,
                    candidate_labels=["weather", "uv", "news", "commute", "breakfast"],
                    hypothesis_template="The request is about {}.",
                )
                labels = [
                    label.lower()
                    for label, score in zip(result["labels"], result["scores"])
                    if score >= 0.25
                ]
                found = list(dict.fromkeys(found + labels))
            except Exception:
                pass

        if not found:
            found = ["weather", "news"]
        return found

    def _extract_location(self, query: str) -> str:
        match = re.search(r"from\s+([A-Z][a-zA-Z\s]+)", query)
        if match:
            return match.group(1).strip()
        return "current location"

    def _extract_ingredients(self, normalized: str) -> List[str]:
        found = []
        for ingredient in self.ingredient_keywords:
            if ingredient in normalized:
                found.append(ingredient)
        return found

    def _extract_time_constraint(self, normalized: str) -> str:
        match = re.search(r"(\d+)\s*-?\s*minute", normalized)
        if match:
            return f"{match.group(1)} minutes"
        return "no specific time"

    def _extract_travel_intent(self, normalized: str) -> List[str]:
        found = []
        for word in self.travel_words:
            if word in normalized:
                found.append(word)
        return found or ["daily routine"]
