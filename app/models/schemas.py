from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class Coordinates(BaseModel):
    lat: float
    lon: float

class Category(BaseModel):
    label: str
    code: str
    color: str

class Weather(BaseModel):
    # AQICN sometimes skips temp or humidity → make optional
    temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None

class Snapshot(BaseModel):
    city: str
    coordinates: Coordinates
    aqi: Optional[int]  # sometimes AQICN returns null
    category: Category
    pollutants: Dict[str, float]
    weather: Optional[Weather] = None  # make whole block optional
    updated_at: str
    source: str

class ForecastPoint(BaseModel):
    ts: str
    aqi: float
    lower: Optional[float] = None
    upper: Optional[float] = None

class ForecastResponse(BaseModel):
    city: str
    horizon: int
    points: List[ForecastPoint]

class InsightResponse(BaseModel):
    snapshot: Snapshot
    recommendation: str
    anomaly: Optional[str] = None
