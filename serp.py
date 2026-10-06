"""SerpApi calls for Balcon Bridge (Google Maps + Google Scholar), cached on disk
so repeated demos don't burn the free 250 searches/month."""

import hashlib
import json
import os
from pathlib import Path

import serpapi

CACHE = Path(".cache")
CACHE.mkdir(exist_ok=True)


def _search(params: dict) -> dict:
    key = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:20]
    f = CACHE / f"serp_{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))

    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY is not set")
    res = serpapi.Client(api_key=api_key).search(params)
    data = res.as_dict() if hasattr(res, "as_dict") else dict(res)
    f.write_text(json.dumps(data), encoding="utf-8")
    return data


def geocode(area: str) -> tuple[float, float]:
    """Turn 'Dwarka Sector 12, Delhi' into (lat, lng) using Google Maps."""
    data = _search({"engine": "google_maps", "q": area, "type": "search"})
    gps = (data.get("place_results") or {}).get("gps_coordinates")
    if not gps and data.get("local_results"):
        gps = data["local_results"][0].get("gps_coordinates")
    if not gps:
        raise ValueError(f"Could not find '{area}' on the map. Try a more specific area.")
    return gps["latitude"], gps["longitude"]


def _places(query: str, lat: float, lng: float, kind: str) -> list[dict]:
    data = _search(
        {"engine": "google_maps", "q": query, "type": "search", "ll": f"@{lat},{lng},15z"}
    )
    out = []
    for r in data.get("local_results", []) or []:
        gps = r.get("gps_coordinates")
        if not gps:
            continue
        out.append(
            {
                "name": r.get("title", query),
                "kind": kind,
                "lat": gps["latitude"],
                "lng": gps["longitude"],
                "rating": r.get("rating"),
            }
        )
    return out


def find_places(lat: float, lng: float) -> tuple[list[dict], list[dict]]:
    """Returns (green_patches, nurseries) near the point."""
    patches, seen = [], set()
    for q, kind in (("park", "park"), ("garden", "garden")):
        for p in _places(q, lat, lng, kind):
            k = (p["name"], round(p["lat"], 4), round(p["lng"], 4))
            if k not in seen:
                seen.add(k)
                patches.append(p)
    nurseries = _places("plant nursery", lat, lng, "nursery")
    return patches, nurseries


def research() -> list[dict]:
    """A few papers on pollinator movement and urban green connectivity."""
    data = _search(
        {
            "engine": "google_scholar",
            "q": "pollinator foraging distance urban green space connectivity",
        }
    )
    out = []
    for r in (data.get("organic_results") or [])[:4]:
        out.append(
            {
                "title": r.get("title", ""),
                "link": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            }
        )
    return out
