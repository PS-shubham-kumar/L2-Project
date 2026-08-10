from mcp_tools.commute_tools import CommuteTool

# Mode icons for the UI (unicode fallback)
_MODE_META = {
    "drive": {"icon": "🚗", "label": "Drive"},
    "transit": {"icon": "🚌", "label": "Transit"},
    "bike": {"icon": "🚲", "label": "Bike"},
    "walk": {"icon": "🚶", "label": "Walk"},
}


class CommuteAgent:
    def __init__(self) -> None:
        self.tool = CommuteTool()

    def run(self, location: str) -> str:
        advice = self.tool.get_commute_advice(location)
        return f"## Commute\n- {advice}"

    def run_structured(self, location: str) -> dict:
        """Return typed dict matching the API contract §3.3 shape."""
        advice: str = self.tool.get_commute_advice(location)

        # Parse ETA clues from the advice text
        eta = 28  # sensible default
        import re
        nums = re.findall(r"\b(\d{1,3})\s*(?:min|minute)", advice, re.I)
        if nums:
            eta = int(nums[0])

        alerts = []
        if "extra buffer" in advice.lower() or "earlier" in advice.lower():
            alerts.append(advice)

        return {
            "section": "commute",
            "status": "success",
            "data": {
                "recommended_mode": "drive",
                "eta_minutes": eta,
                "alerts": alerts,
                "advice_text": advice,
                "alternates": [
                    {"mode": "transit", "eta_minutes": eta + 12},
                    {"mode": "bike", "eta_minutes": eta + 25},
                ],
                "mode_meta": _MODE_META,
            },
        }
