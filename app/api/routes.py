
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import Snapshot, InsightResponse, ForecastResponse, ForecastPoint
from app.services.cache import cache
from app.services import vendor, ml
from app.services.recommend import health_recommendation
from datetime import datetime
from app.core.settings import settings

router = APIRouter()

@router.get("/search", response_model=Snapshot)
def search(city: str = Query(..., description="City name (e.g., Delhi)")):
    key = f"snapshot:{city.lower()}"
    cached, source = cache.get(key)
    if source == "cache_fresh" and cached:
        return {**cached, "source": "cache_fresh"}
    data = vendor.get_city_snapshot(city)
    if not data:
        raise HTTPException(status_code=404, detail="City not found (mock provider supports delhi, mumbai, bengaluru).")
    cache.set(key, data)
    final_source = "cache_stale" if source == "cache_stale" else "vendor_live"
    return {**data, "source": final_source}

@router.get("/insights/current", response_model=InsightResponse)
def current_insights(city: str):
    snap = search(city)
    rec = health_recommendation(snap["aqi"], snap["pollutants"].get("pm25"), snap.get("weather", {}).get("humidity_pct"))
    # anomaly check on recent history
    hist_key = f"history:{city.lower()}"
    hist_cached, src = cache.get(hist_key)
    if hist_cached is None or src == "cache_miss":
        hist_cached = vendor.get_city_history(city, hours=48)
        cache.set(hist_key, hist_cached)
    anomaly = ml.detect_anomaly(hist_cached)
    return {
        "snapshot": snap,
        "recommendation": rec,
        "anomaly": anomaly or None
    }

@router.get("/insights/forecast", response_model=ForecastResponse)
def forecast(city: str, horizon: int = 24):
    hist_key = f"history:{city.lower()}"
    hist_cached, src = cache.get(hist_key)
    if hist_cached is None or src == "cache_miss":
        hist_cached = vendor.get_city_history(city, hours=48)
        if not hist_cached:
            raise HTTPException(status_code=404, detail="City not found or no history (mock provider).")
        cache.set(hist_key, hist_cached)
    fcast = ml.forecast_aqi(hist_cached, horizon=horizon)
    points = [ForecastPoint(ts=p["ts"], aqi=p["aqi"]) for p in fcast]
    return {"city": city.title(), "horizon": horizon, "points": points}
