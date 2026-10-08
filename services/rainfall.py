"""Rainfall via Open-Meteo (no key) with caching, offline demo fallback and what-if override."""
import time, math, requests
_cache = {}

def _demo(lat, lng):
    seed = abs(math.sin(lat * 12.9898 + lng * 78.233))
    return dict(past_3d_mm=round(18 + 40 * seed, 1), next_2d_mm=round(10 + 30 * (1 - seed), 1), source="demo")

def get_rainfall(lat, lng, cfg):
    key = (round(lat, 1), round(lng, 1))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < cfg["RAIN_CACHE_SECONDS"]:
        return hit[1]
    if cfg["RAIN_DEMO"]:
        data = _demo(lat, lng)
    else:
        try:
            r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=6, params={
                "latitude": lat, "longitude": lng, "daily": "precipitation_sum",
                "past_days": 3, "forecast_days": 2, "timezone": "auto"})
            r.raise_for_status()
            d = [x or 0 for x in r.json()["daily"]["precipitation_sum"]]
            data = dict(past_3d_mm=round(sum(d[:3]), 1), next_2d_mm=round(sum(d[3:5]), 1), source="open-meteo")
        except Exception:
            data = _demo(lat, lng); data["source"] = "demo (offline fallback)"
    _cache[key] = (time.time(), data)
    return data

def effective_mm(rain, override=None):
    """Recent rain counts fully, forecast rain at 60%. override = what-if simulator value."""
    return float(override) if override is not None else rain["past_3d_mm"] + 0.6 * rain["next_2d_mm"]
