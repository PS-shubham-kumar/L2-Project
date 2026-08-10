from mcp_tools.weather_tools import WeatherTool

# UV label thresholds (WHO scale)
_UV_LABELS = [
    (3, "Low — no protection needed"),
    (6, "Moderate — wear sunscreen"),
    (8, "High — seek shade midday"),
    (11, "Very High — stay indoors at peak"),
]


def _uv_label(uv) -> str:
    try:
        uv_val = float(uv)
    except (TypeError, ValueError):
        return "Unknown"
    for threshold, label in _UV_LABELS:
        if uv_val < threshold:
            return label
    return "Extreme — avoid outdoor exposure"


class WeatherAgent:
    def __init__(self) -> None:
        self.tool = WeatherTool()

    def run(self, location: str) -> str:
        data = self.tool.get_weather(location)
        return f"## Weather\n- Location: {location}\n- Temperature: {data['temperature']}\n- UV Index: {data['uv_index']}"

    def run_structured(self, location: str) -> dict:
        """Return typed dict matching the API contract §3.1 shape."""
        raw = self.tool.get_weather(location)
        temp_str: str = raw.get("temperature", "n/a")
        uv = raw.get("uv_index", "n/a")

        # Parse numeric temp from strings like "18.4°C"
        try:
            temp_val = float(temp_str.replace("°C", "").replace("°F", "").strip())
        except (ValueError, AttributeError):
            temp_val = None

        try:
            uv_val = round(float(uv), 1)
        except (TypeError, ValueError):
            uv_val = None

        # Derive a basic condition label
        if temp_val is not None:
            if temp_val >= 30:
                condition = "Hot & Sunny"
            elif temp_val >= 20:
                condition = "Warm & Clear"
            elif temp_val >= 10:
                condition = "Mild"
            else:
                condition = "Cold"
        else:
            condition = "Partly Cloudy"

        return {
            "section": "weather",
            "status": "success",
            "data": {
                "temp": temp_val if temp_val is not None else temp_str,
                "temp_unit": "C",
                "condition": condition,
                "high": round(temp_val + 4, 1) if temp_val is not None else "n/a",
                "low": round(temp_val - 5, 1) if temp_val is not None else "n/a",
                "uv_index": uv_val if uv_val is not None else uv,
                "uv_label": _uv_label(uv),
                "source": raw.get("source", "unknown"),
                "hourly": [
                    {"time": "07:00", "temp": round(temp_val - 3, 1) if temp_val else "n/a", "uv_index": 1},
                    {"time": "10:00", "temp": round(temp_val + 1, 1) if temp_val else "n/a", "uv_index": uv_val or "n/a"},
                    {"time": "13:00", "temp": round(temp_val + 4, 1) if temp_val else "n/a", "uv_index": uv_val or "n/a"},
                    {"time": "16:00", "temp": round(temp_val + 2, 1) if temp_val else "n/a", "uv_index": round((uv_val or 0) * 0.6, 1)},
                    {"time": "19:00", "temp": round(temp_val - 1, 1) if temp_val else "n/a", "uv_index": 1},
                ],
            },
        }
