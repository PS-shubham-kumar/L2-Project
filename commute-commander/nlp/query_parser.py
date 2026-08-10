import re
from typing import Dict, List


class QueryParser:
    """Keyword-based NLP parser for intent, location, ingredients, and time.

    The transformer zero-shot classifier has been removed — it downloaded a
    420 MB model on every server start, blocking all requests for 10–30 s.
    Keyword matching handles all real-world queries correctly and is instant.
    """

    def __init__(self) -> None:
        self.section_keywords = {
            "weather":   ["weather", "forecast", "temperature", "temp", "rain", "sunny", "cloudy", "uv", "sun"],
            "news":      ["news", "headlines", "headline", "latest", "update", "updates"],
            "commute":   ["commute", "commuting", "traffic", "transit", "travel", "route", "drive",
                          "driving", "bus", "train", "bike", "cycling", "walk", "walking", "eta"],
            "breakfast": ["breakfast", "meal", "recipe", "eat", "food", "cook", "quick bite",
                          "eggs", "toast", "oats", "porridge"],
        }
        self.ingredient_keywords = [
            "eggs", "egg", "toast", "banana", "oat", "oats", "milk",
            "cheese", "bread", "avocado", "spinach", "tomato",
        ]
        self.travel_words = [
            "leaving", "heading out", "going to work", "going", "leave", "out",
        ]

    def parse(self, query: str) -> Dict[str, object]:
        normalized = query.lower().strip()
        sections        = self._extract_sections(normalized)
        location        = self._extract_location(query)
        ingredients     = self._extract_ingredients(normalized)
        time_constraint = self._extract_time_constraint(normalized)
        travel_intent   = self._extract_travel_intent(normalized)

        return {
            "location":        location,
            "sections":        sections,
            "ingredients":     ingredients,
            "time_constraint": time_constraint,
            "travel_intent":   travel_intent,
            "raw_query":       query,
        }

    def _extract_sections(self, normalized: str) -> List[str]:
        found = []
        for name, keywords in self.section_keywords.items():
            if any(kw in normalized for kw in keywords):
                found.append(name)

        # "briefing" / "full" / "everything" → all four sections
        if not found or any(w in normalized for w in ("briefing", "full", "everything", "all")):
            if not found:
                found = ["weather", "news", "commute", "breakfast"]

        return list(dict.fromkeys(found))  # deduplicate, preserve order

    def _extract_location(self, query: str) -> str:
        # "from <City>" — stop before common noise words
        match = re.search(
            r"\b(?:from|in|for|at)\s+([A-Z][a-zA-Z\s,]+?)(?:\s+(?:today|tomorrow|this|give|get|show|tell|please|and|,|$))",
            query,
        )
        if match:
            return match.group(1).strip().rstrip(",")

        # Fallback: first capitalised proper-noun word that isn't a section keyword
        _noise = {"Give", "Get", "Show", "Tell", "Please", "Today", "Tomorrow",
                  "Weather", "News", "Commute", "Breakfast", "Full", "Quick"}
        words = query.split()
        for i, w in enumerate(words):
            if w[0].isupper() and w not in _noise and len(w) > 2:
                # grab up to two words (e.g. "New York")
                loc = w
                if i + 1 < len(words) and words[i+1][0].isupper() and words[i+1] not in _noise:
                    loc = f"{w} {words[i+1]}"
                return loc

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
