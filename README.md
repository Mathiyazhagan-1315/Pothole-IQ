# PotholeIQ

**AI that rates pothole severity from a photo and predicts which roads will fail after rain, giving cities a ranked repair list instead of a pile of complaints.**

Track: **AI + Climate** · ForgeHacks Online 2026

## Problem
Rain is the main driver of road failure. Cities handle potholes reactively: unverified complaints, no severity, duplicates, and repairs that follow whoever complains loudest.

## Solution
1. **Report**: photo + map pin (works on phones)
2. **Assess**: AI severity score 0-100 (OpenCV pipeline, optionally blended with Claude vision)
3. **Predict**: rain-linked risk from Open-Meteo (past 3 days + next 2 days)
4. **Prioritise**: transparent ranked queue, with duplicate merging within 25 m

`priority = 0.40 severity + 0.35 rain risk + 0.15 repeat reports + 0.10 age`  (55+ fix now, 35-54 soon)

## Run it
```bash
pip install -r requirements.txt
python seed.py          # optional demo data around Erode
python app.py           # http://localhost:5000
pytest -q               # 11 tests
```
Optional environment variables: `ANTHROPIC_API_KEY` (adds Claude vision), `AUTHORITY_PIN` (default `2026`), `RAIN_DEMO=1` (offline rainfall), `PORT`.

## Pages
- `/` live map with severity markers, predicted-risk halos, top-5 list and a **rain what-if slider**
- `/report` guided 3-step report with instant AI severity
- `/dashboard` ranked repair queue, stats, CSV export, **authority mode** (PIN) to update status
- `/how-it-works` methodology and limits

## Architecture
```
Browser (Leaflet) -> Flask API -> services/severity.py  (OpenCV [+ Claude vision])
                               -> services/rainfall.py  (Open-Meteo, cached, offline fallback)
                               -> services/scoring.py   (risk + priority, explainable)
                               -> SQLAlchemy / SQLite
```

## Honest limits
The OpenCV score is a heuristic, not a trained model. It works best on close, daylight photos and supports human inspection rather than replacing it. Rainfall risk is a weighted model, not a validated forecast.

## Built during the hackathon
Severity analysis, rainfall risk model, priority ranking, duplicate merging, dashboard, authority mode and tests. The base reporting app (Flask, SQLAlchemy, Leaflet map) existed beforehand.

## Authority mode (for judges)

The Repair queue page has an **Authority mode** button that lets you move reports from open to in progress to fixed.

1. Open the **Repair queue** page.
2. Click **Authority mode**.
3. Enter the PIN: `2026`

The PIN is set by the `AUTHORITY_PIN` environment variable (default `2026`).