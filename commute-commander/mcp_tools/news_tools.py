import requests
from xml.etree import ElementTree as ET

from mcp_tools.framework_mcp import MCPToolRegistry
from services.config import Config

registry = MCPToolRegistry()


@registry.tool(name="get_headlines", description="Fetch recent news headlines")
def get_headlines() -> list:
    api_key = Config.NEWSAPI_API_KEY
    if api_key:
        try:
            response = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"country": "us", "apiKey": api_key},
                timeout=10,
            )
            response.raise_for_status()
            articles = response.json().get("articles", [])
            items = [article.get("title", "") for article in articles[:5] if article.get("title")]
            if items:
                return items
        except Exception:
            pass

    try:
        response = requests.get("https://feeds.feedburner.com/ndtvnews-top-stories", timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        items = []
        for entry in root.findall('.//{*}item')[:5]:
            title = entry.find('{*}title')
            if title is not None:
                items.append(title.text)
        return items or ["No headlines available right now."]
    except Exception:
        return ["News unavailable right now."]


class NewsTool:
    def get_headlines(self) -> list:
        return registry.call("get_headlines")
