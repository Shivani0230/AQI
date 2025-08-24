
# AirSight+ (Python) – Starter

Python-first implementation using **FastAPI** with:
- LRU cache (TTL)
- Mock AQI vendor adapter (swap later for aqicn.org)
- Forecast (ExponentialSmoothing)
- Anomaly detection (IsolationForest)
- Health recommendations (rule-based)
- Minimal HTML UI (Jinja2 + vanilla JS)

## Run locally

```bash
cd backend
# 1. create & activate venv
python -m venv .venv
source .venv/bin/activate        # mac/linux
.venv\Scripts\activate           # windows

# 2. install deps
pip install -r requirements.txt

# 3. set env variables
export AQICN_TOKEN="your_aqicn_token"     # or set in .env (preferred)
export USE_MOCK_VENDOR="false"             # set to "true" for demo mode

# 4. run dev server
uvicorn app.main:app --reload --port 8000

# 5. open browser
http://127.0.0.1:8000

## Notes

- Mock cities supported: `Delhi`, `Mumbai`, `Bengaluru`.
- Replace `app/services/vendor.py` with a real provider adapter when you have an API key.
- Caching is LRU+TTL and returns `source` as `cache_fresh`, `cache_stale`, or `vendor_live`.
- Forecast uses Holt-Winters (exponential smoothing) for quick setup (no external data).

## Next steps (for the full project)

- Add fuzzy search (rapidfuzz) and multilingual aliases.
- Add Redis and MongoDB for geo & history.
- Add comparison endpoint and a React UI (optional).
- Implement route/travel planning agent with geospatial routes.
```
