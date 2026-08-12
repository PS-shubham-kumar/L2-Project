import re
from typing import Dict, List


class QueryParser:
    """Keyword-based NLP parser for intent, location, destination, ingredients, and time.

    Extracts structured intent from free-text user queries including:
      - sections (weather, news, commute, breakfast)
      - origin location (city the user is in / starting from)
      - destination (place the user is going to — used for commute routing)
      - ingredients (for breakfast recipes)
      - time constraint (e.g. "10 minutes")
      - travel intent words
    """

    def __init__(self) -> None:
        # Use whole-word patterns to avoid substring false-positives (e.g. "eat" inside "weather")
        self.section_keywords = {
            "weather":   [r"\bweather\b", r"\bforecast\b", r"\btemperature\b", r"\btemp\b",
                          r"\brain\b", r"\bsunny\b", r"\bcloudy\b", r"\buv\b", r"\bsun\b"],
            "news":      [r"\bnews\b", r"\bheadlines\b", r"\bheadline\b", r"\blatest\b",
                          r"\bupdate\b", r"\bupdates\b"],
            "commute":   [r"\bcommute\b", r"\bcommuting\b", r"\btraffic\b", r"\btransit\b",
                          r"\btravel\b", r"\broute\b", r"\bdrive\b", r"\bdriving\b",
                          r"\bbus\b", r"\btrain\b", r"\bbike\b", r"\bcycling\b",
                          r"\bwalk\b", r"\bwalking\b", r"\beta\b",
                          r"\bgoing to\b", r"\bheading to\b", r"\bheading out to\b", r"\bheading out\b", r"\bdrop me\b"],
            "breakfast": [r"\bbreakfast\b", r"\bmeal\b", r"\brecipe\b", r"\beat\b", r"\bfood\b",
                          r"\bcook\b", r"\bquick bite\b", r"\beggs?\b", r"\btoast\b",
                          r"\boats\b", r"\bporridge\b"],
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
        destination     = self._extract_destination(query)
        ingredients     = self._extract_ingredients(normalized)
        time_constraint = self._extract_time_constraint(normalized)
        travel_intent   = self._extract_travel_intent(normalized)

        # If no explicit origin location was found but destination was extracted,
        # treat destination as the location (e.g. "heading out to Bangalore"
        # means the user wants info ABOUT Bangalore).
        if destination and (not location or location == "current location"):
            location = destination
            destination = ""  # clear to avoid trivial self-route

        # If destination matches location, clear it (degenerate route)
        if destination and location and destination.lower() == location.lower():
            destination = ""

        return {
            "location":        location,
            "destination":     destination,
            "sections":        sections,
            "ingredients":     ingredients,
            "time_constraint": time_constraint,
            "travel_intent":   travel_intent,
            "raw_query":       query,
        }

    def _extract_sections(self, normalized: str) -> List[str]:
        found = []
        for name, patterns in self.section_keywords.items():
            if any(re.search(pat, normalized) for pat in patterns):
                found.append(name)

        # "briefing" / "full" / "everything" → all four sections
        if not found or any(w in normalized for w in ("briefing", "full", "everything", "all")):
            if not found:
                found = ["weather", "news", "commute", "breakfast"]

        return list(dict.fromkeys(found))  # deduplicate, preserve order

    def _extract_destination(self, query: str) -> str:
        """Extract the commute destination from patterns like 'to <Place>', 'heading to <Place>',
        'going to <Place>', 'drop me at <Place>', 'office in <Place>'.
        Returns empty string if no destination is detected.
        """
        _dest_noise = {"work", "office", "school", "college", "home", "my", "the"}

        # Pattern 1: "from <origin> to <destination>" — capture after 'to', case-insensitive
        match = re.search(
            r"\bfrom\s+[\w][\w\s,]+?\s+to\s+([\w][\w\s,]+?)(?:\s+(?:today|tomorrow|this|please|and|,|$)|\s*$)",
            query, re.IGNORECASE,
        )
        if match:
            return match.group(1).strip().rstrip(",").title()

        # Pattern 2: "heading out to <Place>" / "heading to <Place>" / "going to <Place>"
        match = re.search(
            r"\b(?:heading(?:\s+out)?|going)\s+to\s+([\w][\w\s,]+?)(?:\s+(?:today|tomorrow|this|please|and|how|,|$)|\s*$)",
            query, re.IGNORECASE,
        )
        if match:
            dest = match.group(1).strip().rstrip(",")
            if dest.lower() not in _dest_noise:
                return dest.title()

        # Pattern 3: "to <Place>" (standalone, not part of "going to work")
        match = re.search(
            r"(?<![\w])to\s+([A-Z][a-zA-Z\s,]+?)(?:\s+(?:today|tomorrow|this|please|and|how|,|$)|\s*$)",
            query,
        )
        if match:
            dest = match.group(1).strip().rstrip(",")
            if dest.lower() not in _dest_noise:
                return dest

        # Pattern 4: case-insensitive "to <word(s)>" fallback
        match = re.search(
            r"\bto\s+([a-zA-Z][a-zA-Z]{2,}(?:\s+[a-zA-Z][a-zA-Z]+)*)",
            query, re.IGNORECASE,
        )
        if match:
            dest = match.group(1).strip().rstrip(",")
            if dest.lower() not in _dest_noise:
                return dest.title()

        # Pattern 5: "drop me at <Place>" / "drop me off at <Place>"
        match = re.search(
            r"\bdrop\s+(?:me\s+)?(?:off\s+)?at\s+([\w][\w\s,]+?)(?:\s+(?:today|tomorrow|this|and|,|$)|\s*$)",
            query, re.IGNORECASE,
        )
        if match:
            return match.group(1).strip().rstrip(",").title()

        return ""

    def _extract_location(self, query: str) -> str:
        # "from/in/for/at <City>" — stop before common noise words
        # Intentionally avoid matching after "to" (that's destination)
        match = re.search(
            r"\b(?:from|in|for|at)\s+([A-Z][a-zA-Z\s,]+?)(?:\s+(?:to|today|tomorrow|this|give|get|show|tell|please|and|,|$))",
            query,
        )
        if match:
            return match.group(1).strip().rstrip(",")

        # Fallback: first capitalised proper-noun word that isn't a noise word
        # Exclude contractions (words containing apostrophes like "I'm")
        _noise = {"Give", "Get", "Show", "Tell", "Please", "Today", "Tomorrow",
                  "Weather", "News", "Commute", "Breakfast", "Full", "Quick", "I"}
        words = query.split()
        for i, w in enumerate(words):
            clean = w.rstrip('.,!?')
            if (clean[0].isupper() and clean not in _noise
                    and len(clean) > 2 and "'" not in clean):
                loc = clean
                if i + 1 < len(words):
                    next_w = words[i+1].rstrip('.,!?')
                    if next_w[0].isupper() and next_w not in _noise and "'" not in next_w:
                        loc = f"{clean} {next_w}"
                return loc

        return "current location"

    def _extract_ingredients(self, normalized: str) -> List[str]:
        found = []
        for ingredient in self.ingredient_keywords:
            if re.search(rf"\b{re.escape(ingredient)}\b", normalized):
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
