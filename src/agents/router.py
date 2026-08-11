from typing import Dict, List


class Router:
    """Simple intent router that directs requests to specialist agents."""

    def __init__(self) -> None:
        self.routes: Dict[str, List[str]] = {
            "weather": ["weather"],
            "uv": ["weather"],
            "news": ["news"],
            "commute": ["commute"],
            "breakfast": ["breakfast"],
        }

    def route(self, sections: List[str]) -> List[str]:
        selected: List[str] = []
        for section in sections:
            selected.extend(self.routes.get(section, []))
        return list(dict.fromkeys(selected))
