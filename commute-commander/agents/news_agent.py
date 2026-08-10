from __future__ import annotations

import re
from datetime import datetime, timezone
from mcp_tools.news_tools import NewsTool

# News sources we can loosely detect from common headline patterns
_SOURCE_HINTS = ["Reuters", "AP", "BBC", "CNN", "NDTV", "Tribune", "Times", "Post", "Guardian"]


def _guess_source(title: str) -> str:
    for hint in _SOURCE_HINTS:
        if hint.lower() in title.lower():
            return hint
    return "News"


def _strip_source_suffix(title: str) -> str:
    """Remove trailing ' - Source Name' that many feeds append."""
    return re.sub(r"\s[-–]\s[^-–]{2,40}$", "", title).strip()


class NewsAgent:
    def __init__(self) -> None:
        self.tool = NewsTool()

    def run(self) -> str:
        headlines = self.tool.get_headlines()
        joined = "\n".join(f"- {item}" for item in headlines[:3])
        return f"## News\n{joined}"

    def run_structured(self) -> dict:
        """Return typed dict matching the API contract §3.2 shape."""
        raw: list = self.tool.get_headlines()
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        headlines = []
        for item in raw[:5]:
            title = _strip_source_suffix(str(item))
            headlines.append(
                {
                    "title": title,
                    "source": _guess_source(title),
                    "url": None,
                    "timestamp": now_iso,
                }
            )

        return {
            "section": "news",
            "status": "success" if headlines else "error",
            "data": {"headlines": headlines},
        }
