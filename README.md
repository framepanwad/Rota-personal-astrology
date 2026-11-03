# ROTA Personal Astrology v2

This is a functional full-stack prototype, not a static mockup.

## Features
- Swiss Ephemeris (Moshier mode) planetary longitude calculations
- Tropical zodiac
- Ascendant and Whole Sign house calculation
- Traditional planetary house rulers
- Planet-in-house table
- Transit positions for a selected date
- Major transit-to-natal aspects (0/60/90/120/180°, 5° orb)
- Applying/separating estimate from next-day movement
- Local browser storage for birth profile

## Run on your computer
Requires Python 3.10+.
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```
Open http://127.0.0.1:8000

## Deploy to Render
1. Create a GitHub repository and upload all files in this folder.
2. Sign in to Render and create a new Blueprint using the repository.
3. Render reads `render.yaml`, installs dependencies and starts the FastAPI app.
4. Open the HTTPS URL; on iPhone Safari choose Share → Add to Home Screen.

## Birth data
Default profile is 29 Jan 1996, 19:13, Udon Thani, Thailand (lat 17.4138, lon 102.7872, UTC+7). Verify the recorded birth time and coordinates before relying on the chart. If entering another location, update latitude, longitude and UTC offset manually. Historical DST/time-zone rules are not automatically resolved in this prototype.

## Accuracy and limitations
Calculations use Swiss Ephemeris through its built-in Moshier ephemeris mode. This is a genuine astronomical calculation, but it is not the same as loading the full Swiss ephemeris data files. House calculation uses Swiss Ephemeris Whole Sign mode. Transit aspects are evaluated at 12:00 local time; applying/separating is estimated by comparing the following day. The Ask tab currently returns chart facts and a rule-based summary, not an LLM-generated interpretation. AI integration is a separate next step.

Swiss Ephemeris is dual-licensed (AGPL or professional license). Review licensing obligations before commercial distribution. This package is a personal prototype, not validated for paid client readings.
