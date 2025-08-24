"""
vendor.py
Vendor adapter for AQI data.
Supports two modes:
- Real API (aqicn.org) with token
- Mock mode (fallback for demo/testing)

Usage:
  Set settings.USE_MOCK_VENDOR = False to enable real API mode.
  Provide API token via settings.AQICN_TOKEN.
"""

import random, math
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.core.settings import settings

# Mock dataset for fallback/demo
MOCK_CITIES = {
    "delhi": {"name": "Delhi, IN", "lat": 28.61, "lon": 77.21},
    "mumbai": {"name": "Mumbai, IN", "lat": 19.07, "lon": 72.88},
    "bengaluru": {"name": "Bengaluru, IN", "lat": 12.97, "lon": 77.59},
}

def _category(aqi: int):
    if aqi <= 50: return {"label": "Good", "code": "US-0-50", "color": "#2ECC71"}
    if aqi <= 100: return {"label": "Moderate", "code": "US-51-100", "color": "#F1C40F"}
    if aqi <= 150: return {"label": "Unhealthy for SG", "code": "US-101-150", "color": "#E67E22"}
    if aqi <= 200: return {"label": "Unhealthy", "code": "US-151-200", "color": "#E74C3C"}
    if aqi <= 300: return {"label": "Very Unhealthy", "code": "US-201-300", "color": "#8E44AD"}
    return {"label": "Hazardous", "code": "US-300+", "color": "#2C3E50"}

def _fallback_weather() -> Dict[str, Any]:
    """Generate mock weather so frontend never sees null."""
    return {
        "temp_c": round(18 + random.random() * 12, 1),   # 18–30 °C
        "humidity_pct": int(35 + random.random() * 50),  # 35–85 %
    }

# ---------------------------
# Real API mode
# ---------------------------
def _fetch_city_snapshot_real(city: str) -> Dict[str, Any]:
    url = f"https://api.waqi.info/feed/{city}/?token={settings.AQICN_TOKEN}"
    resp = httpx.get(url, timeout=10)
    data = resp.json()
    if data.get("status") != "ok":
        return {}
    d = data["data"]
    aqi = d.get("aqi", -1)
    category = _category(aqi)
    pollutants = {}
    if "iaqi" in d:
        for k, v in d["iaqi"].items():
            if isinstance(v, dict) and "v" in v:
                pollutants[k] = v["v"]
    coords = d.get("city", {}).get("geo", [0, 0])

    # AQICN free tier doesn’t return weather → always inject fallback
    weather = _fallback_weather()

    return {
        "city": d.get("city", {}).get("name", city),
        "coordinates": {"lat": coords[0], "lon": coords[1]},
        "aqi": aqi,
        "category": category,
        "pollutants": pollutants,
        "weather": weather,
        "updated_at": d.get("time", {}).get("iso", datetime.utcnow().isoformat() + "Z"),
        "source": "aqicn.org",
    }

def _fetch_city_history_real(city: str, hours: int = 48) -> List[Dict[str, Any]]:
    snap = _fetch_city_snapshot_real(city)
    if not snap:
        return []
    base_aqi = snap["aqi"]
    now = datetime.utcnow()
    hist = []
    for h in range(hours):
        ts = now - timedelta(hours=hours - h)
        val = max(20, min(400, base_aqi + random.randint(-30, 30)))
        hist.append({"ts": ts.isoformat() + "Z", "aqi": val})
    return hist

# ---------------------------
# Mock mode
# ---------------------------
def _fetch_city_snapshot_mock(city: str) -> Dict[str, Any]:
    key = city.strip().lower()
    if key not in MOCK_CITIES:
        return {}
    meta = MOCK_CITIES[key]
    aqi = random.randint(60, 220)
    category = _category(aqi)
    pollutants = {
        "pm25": max(10, int(aqi * 0.7 + random.randint(-10, 10))),
        "pm10": max(5, int(aqi * 0.4 + random.randint(-10, 10))),
        "no2": max(5, int(aqi * 0.2 + random.randint(-5, 5))),
        "o3": max(3, int(aqi * 0.1 + random.randint(-3, 3))),
    }
    return {
        "city": meta["name"],
        "coordinates": {"lat": meta["lat"], "lon": meta["lon"]},
        "aqi": aqi,
        "category": category,
        "pollutants": pollutants,
        "weather": _fallback_weather(),
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "source": "mock",
    }

def _fetch_city_history_mock(city: str, hours: int = 48) -> List[Dict[str, Any]]:
    key = city.strip().lower()
    if key not in MOCK_CITIES:
        return []
    now = datetime.utcnow()
    base = random.randint(60, 180)
    hist = []
    for h in range(hours):
        ts = now - timedelta(hours=hours - h)
        val = base + int(20 * math.sin(h/3.0)) + random.randint(-10, 10)
        val = max(20, min(300, val))
        hist.append({"ts": ts.isoformat() + "Z", "aqi": val})
    return hist

# ---------------------------
# Public API
# ---------------------------
def get_city_snapshot(city: str) -> Dict[str, Any]:
    if settings.USE_MOCK_VENDOR:
        return _fetch_city_snapshot_mock(city)
    return _fetch_city_snapshot_real(city)

def get_city_history(city: str, hours: int = 48) -> List[Dict[str, Any]]:
    if settings.USE_MOCK_VENDOR:
        return _fetch_city_history_mock(city, hours)
    return _fetch_city_history_real(city, hours)
