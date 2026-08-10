"""Commute tool — real routing via TomTom Routing API.

get_route(location, destination, mode) -> dict:
    {
        "recommended_mode": str,
        "eta_minutes":      int,
        "distance_km":      float,
        "alerts":           list[str],
        "alternates": [
            { "mode": str, "eta_minutes": int, "distance_km": float,
              "polyline": [[lat,lon], ...] },
            ...
        ],
        "polyline":  [[lat, lon], ...],   # decoded from TomTom response
        "origin":    { "lat": float, "lon": float, "label": str },
        "dest":      { "lat": float, "lon": float, "label": str },
        "source":    str,
    }

Fallback path (no key / API error) returns a plausible advisory dict so
the rest of the system keeps working.
"""
from __future__ import annotations

import requests

from mcp_tools.framework_mcp import MCPToolRegistry
from services.config import Config

registry = MCPToolRegistry()

# TomTom travelMode values that map to our UI modes
_TT_MODES = {
    "drive":   "car",
    "transit": "bus",
    "bike":    "bicycle",
    "walk":    "pedestrian",
}

_FALLBACK_ADVICE = {
    "drive":   ("drive",   28, 18.0),
    "transit": ("transit", 42, 16.0),
    "bike":    ("bike",    55, 12.0),
}


# ── Geocoding ──────────────────────────────────────────────────────────────

def _geocode_tomtom(query: str, api_key: str) -> tuple[float, float, str] | None:
    """Resolve a free-text address to (lat, lon, formatted_label) via TomTom Search."""
    try:
        r = requests.get(
            "https://api.tomtom.com/search/2/geocode/{q}.json".format(
                q=requests.utils.quote(query)
            ),
            params={"key": api_key, "limit": 1},
            timeout=8,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if results:
            pos   = results[0]["position"]
            label = results[0].get("address", {}).get("freeformAddress", query)
            return pos["lat"], pos["lon"], label
    except Exception:
        pass
    return None


def _geocode_open_meteo(query: str) -> tuple[float, float, str] | None:
    """No-key geocoding fallback using Open-Meteo geocoding API."""
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if results:
            res = results[0]
            label = f"{res.get('name', query)}, {res.get('country', '')}"
            return res["latitude"], res["longitude"], label.strip(", ")
    except Exception:
        pass
    return None


def _geocode(query: str, api_key: str) -> tuple[float, float, str] | None:
    """Try TomTom geocoding first, fall back to Open-Meteo."""
    if api_key:
        result = _geocode_tomtom(query, api_key)
        if result:
            return result
    return _geocode_open_meteo(query)


# ── Polyline decoding ──────────────────────────────────────────────────────

def _decode_tomtom_polyline(points_list: list[dict]) -> list[list[float]]:
    """Convert TomTom's points array [{"latitude":..,"longitude":..}] to [[lat,lon],...]."""
    return [[p["latitude"], p["longitude"]] for p in points_list]


# ── Routing call ───────────────────────────────────────────────────────────

def _call_tomtom_route(
    origin_lat: float, origin_lon: float,
    dest_lat: float,   dest_lon: float,
    tt_mode: str,      api_key: str,
) -> dict | None:
    """Call TomTom Calculate Route and return the first route summary + points."""
    try:
        url = (
            f"https://api.tomtom.com/routing/1/calculateRoute/"
            f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}/json"
        )
        r = requests.get(
            url,
            params={
                "key":          api_key,
                "travelMode":   tt_mode,
                "traffic":      "true",
                "routeType":    "fastest",
                "maxAlternatives": 0,
            },
            timeout=12,
        )
        r.raise_for_status()
        data   = r.json()
        routes = data.get("routes", [])
        if not routes:
            return None

        route   = routes[0]
        summary = route.get("summary", {})
        legs    = route.get("legs", [])
        points: list[dict] = []
        for leg in legs:
            points.extend(leg.get("points", []))

        return {
            "eta_minutes": round(summary.get("travelTimeInSeconds", 0) / 60),
            "distance_km": round(summary.get("lengthInMeters", 0) / 1000, 1),
            "polyline":    _decode_tomtom_polyline(points),
            "traffic_delay_s": summary.get("trafficDelayInSeconds", 0),
        }
    except Exception:
        return None


# ── Registered tool ────────────────────────────────────────────────────────

@registry.tool(
    name="get_commute_route",
    description="Get real commute routing data between two locations",
)
def get_commute_route(location: str, destination: str = "") -> dict:
    """Return routing data for all supported modes.

    `location`    — origin (e.g. "Chicago, IL")
    `destination` — explicit destination; defaults to city centre of location
    """
    api_key = Config.TOMTOM_API_KEY

    # Geocode origin
    origin = _geocode(location, api_key) if location else None
    if not origin:
        origin = (41.8781, -87.6298, "Chicago, IL")   # default fallback
    orig_lat, orig_lon, orig_label = origin

    # Destination: use provided string or pick a recognisable downtown point
    dest_query = destination if destination else f"downtown {location or 'Chicago'}"
    dest = _geocode(dest_query, api_key)
    if not dest:
        # Offset 10 km north as a last resort so the route is non-trivial
        dest = (orig_lat + 0.09, orig_lon + 0.04, f"Downtown {location}")
    dest_lat, dest_lon, dest_label = dest

    # ── TomTom routing ─────────────────────────────────────────────────────
    if api_key:
        drive_data = _call_tomtom_route(orig_lat, orig_lon, dest_lat, dest_lon, "car",  api_key)
        bike_data  = _call_tomtom_route(orig_lat, orig_lon, dest_lat, dest_lon, "bicycle",    api_key)
        walk_data  = _call_tomtom_route(orig_lat, orig_lon, dest_lat, dest_lon, "pedestrian", api_key)

        if drive_data:
            delay_s  = drive_data.get("traffic_delay_s", 0)
            alerts   = [f"Traffic delay of ~{round(delay_s/60)} min on recommended route."] \
                       if delay_s > 300 else []

            alternates = []
            if bike_data:
                alternates.append({
                    "mode":        "bike",
                    "eta_minutes": bike_data["eta_minutes"],
                    "distance_km": bike_data["distance_km"],
                    "polyline":    bike_data["polyline"],
                })
            if walk_data:
                alternates.append({
                    "mode":        "walk",
                    "eta_minutes": walk_data["eta_minutes"],
                    "distance_km": walk_data["distance_km"],
                    "polyline":    walk_data["polyline"],
                })
            # Synthetic transit estimate (TomTom free tier lacks transit routing)
            alternates.insert(0, {
                "mode":        "transit",
                "eta_minutes": drive_data["eta_minutes"] + 12,
                "distance_km": drive_data["distance_km"],
                "polyline":    drive_data["polyline"],   # share drive polyline as approximation
            })

            return {
                "recommended_mode": "drive",
                "eta_minutes":      drive_data["eta_minutes"],
                "distance_km":      drive_data["distance_km"],
                "alerts":           alerts,
                "alternates":       alternates,
                "polyline":         drive_data["polyline"],
                "origin":           {"lat": orig_lat, "lon": orig_lon, "label": orig_label},
                "dest":             {"lat": dest_lat, "lon": dest_lon, "label": dest_label},
                "source":           "tomtom",
            }

    # ── Advisory fallback (no key or routing failed) ───────────────────────
    eta  = 28
    dist = 18.0
    return {
        "recommended_mode": "drive",
        "eta_minutes":      eta,
        "distance_km":      dist,
        "alerts":           [f"Leave 15–20 min early for {location} traffic."],
        "alternates": [
            {"mode": "transit", "eta_minutes": eta + 12, "distance_km": dist, "polyline": []},
            {"mode": "bike",    "eta_minutes": eta + 27, "distance_km": dist, "polyline": []},
        ],
        "polyline": [],
        "origin":   {"lat": orig_lat, "lon": orig_lon, "label": orig_label},
        "dest":     {"lat": dest_lat, "lon": dest_lon, "label": dest_label},
        "source":   "advisory",
    }


# Keep backward-compat name for any existing callers (CLI run())
@registry.tool(
    name="get_commute_advice",
    description="Plain-text commute advice (legacy CLI path)",
)
def get_commute_advice(location: str) -> str:
    data = get_commute_route(location)
    eta  = data["eta_minutes"]
    mode = data["recommended_mode"]
    if data["alerts"]:
        return data["alerts"][0]
    return f"Recommended: {mode} — approx. {eta} min to {data['dest']['label']}."


class CommuteTool:
    def get_commute_route(self, location: str, destination: str = "") -> dict:
        return registry.call("get_commute_route", location, destination)

    # legacy shim
    def get_commute_advice(self, location: str) -> str:
        return registry.call("get_commute_advice", location)
