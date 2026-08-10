import requests

from mcp_tools.framework_mcp import MCPToolRegistry
from services.config import Config

registry = MCPToolRegistry()


@registry.tool(name="get_weather", description="Fetch weather and UV information for a location")
def get_weather(location: str) -> dict:
    api_key = Config.OPENWEATHER_API_KEY
    if api_key:
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": location, "appid": api_key, "units": "metric"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            main = data.get("main", {})
            return {
                "temperature": f"{main.get('temp', 'n/a')}°C",
                "uv_index": data.get("uv", "n/a"),
                "source": "openweather",
            }
        except Exception:
            pass

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 41.8781,
                "longitude": -87.6298,
                "current": "temperature_2m,uv_index",
                "timezone": "auto",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        return {
            "temperature": f"{current.get('temperature_2m', 'n/a')}°C",
            "uv_index": current.get("uv_index", "n/a"),
            "source": "open-meteo",
        }
    except Exception:
        return {"temperature": "unavailable", "uv_index": "unavailable", "source": "fallback"}


class WeatherTool:
    def get_weather(self, location: str) -> dict:
        return registry.call("get_weather", location)
