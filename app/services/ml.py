
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def _parse_history(history: List[Dict[str, Any]]) -> pd.Series:
    df = pd.DataFrame(history)
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts")
    return pd.Series(df["aqi"].values, index=df["ts"])

def forecast_aqi(history: List[Dict[str, Any]], horizon: int = 24) -> List[Dict[str, Any]]:
    if len(history) < 10:
        # naive: repeat last value
        last = history[-1]["aqi"] if history else 100
        base_ts = datetime.utcnow()
        return [{"ts": (base_ts + pd.Timedelta(hours=i+1)).isoformat() + "Z", "aqi": float(last)} for i in range(horizon)]
    series = _parse_history(history)
    try:
        model = ExponentialSmoothing(series, trend="add", seasonal=None, initialization_method="estimated")
        fit = model.fit(optimized=True)
        fcast = fit.forecast(horizon)
        out = []
        for ts, val in fcast.items():
            out.append({"ts": ts.isoformat() + "Z", "aqi": float(val)})
        return out
    except Exception:
        last = series.iloc[-1]
        base_ts = series.index[-1]
        return [{"ts": (base_ts + pd.Timedelta(hours=i+1)).isoformat() + "Z", "aqi": float(last)} for i in range(horizon)]

def detect_anomaly(history: List[Dict[str, Any]]) -> str:
    if len(history) < 24:
        return ""
    series = _parse_history(history).astype(float)
    X = series.values.reshape(-1, 1)
    clf = IsolationForest(contamination=0.1, random_state=42)
    y = clf.fit_predict(X)
    if y[-1] == -1:
        # Simple message for now
        return "Unusual spike detected in the latest hour."
    return ""

def smooth_nowcast(value: float, prev_value: float = None, alpha: float = 0.5) -> float:
    if prev_value is None:
        return value
    return alpha * value + (1 - alpha) * prev_value
