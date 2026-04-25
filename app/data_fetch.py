"""
Data fetch module — Overpass API (OpenStreetMap POI data).

Handles rate-limiting and transient failures with:
  - Two mirror URLs tried in order
  - 3 retries with exponential back-off
  - Graceful empty-list fallback so the analysis pipeline never crashes
"""

import time
import requests

# Primary + fallback Overpass mirrors
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

_HEADERS = {"User-Agent": "SiteSense-AI/3.0 (retail-location-intelligence)"}


def fetch_pois(lat: float, lon: float, radius: int = 1000) -> list:
    """
    Fetch amenity POI nodes from Overpass API within the given radius.

    Returns a list of OSM element dicts (may be empty if all mirrors fail).
    Never raises — the caller always gets a list.
    """
    query = f"""
[out:json][timeout:25];
(
  node(around:{radius},{lat},{lon})["amenity"];
  node(around:{radius},{lat},{lon})["shop"];
  node(around:{radius},{lat},{lon})["public_transport"];
);
out body;
"""

    for url in OVERPASS_URLS:
        for attempt in range(3):
            try:
                resp = requests.post(
                    url,
                    data={"data": query},
                    headers=_HEADERS,
                    timeout=30,
                )
                resp.raise_for_status()           # non-2xx → HTTPError
                text = resp.text.strip()
                if not text:
                    raise ValueError("Empty response body from Overpass")
                data = resp.json()                # JSONDecodeError if not JSON
                return data.get("elements", [])

            except (requests.HTTPError, requests.Timeout) as e:
                wait = 2 ** attempt               # 1s, 2s, 4s
                print(f"[data_fetch] {url} attempt {attempt+1} failed ({e}) — "
                      f"retrying in {wait}s…")
                time.sleep(wait)

            except (ValueError, requests.RequestException) as e:
                print(f"[data_fetch] {url} attempt {attempt+1} error: {e}")
                break                             # bad response — try next mirror

    # All mirrors exhausted — return empty list so scoring continues with 0s
    print("[data_fetch] WARNING: All Overpass mirrors failed. Returning empty POI list.")
    return []
