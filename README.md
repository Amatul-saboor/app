# Wind Forecast Accuracy Dashboard

A web app for a UK energy supplier's day-ahead buying team. It answers two questions:

1. **What wind did the forecast promise when we had to decide?** For any purchase decision in January 2026, it shows the wind forecast that was actually available at decision time, next to the wind that really blew.
2. **How far can the forecast be trusted?** It measures how wrong those forecasts were across all of January, and turns that into a safety margin a buyer can use.

**Live app:** https://app-seven-rouge-96.vercel.app

---

## Key result (January 2026, 09:20 decision cutoff)

| Metric | Value | Meaning |
|---|---|---|
| Typical miss (MAE) | 2,039 MW | 18.1% of average wind output |
| Bias | +1,748 MW | forecasts were too high in 84.9% of hours |
| Safety margin (P90) | 4,098 MW | planning for this much less wind covered the shortfall in 9 of 10 hours |
| RMSE | 2,505 MW | larger misses weighted more |

The forecast consistently promised more wind than was metered, and the gap grows on windy days (about +370 MW on the calmest fifth of hours, about +3,400 MW on the windiest fifth). This is consistent with wind farms being curtailed for grid constraints, which reduces metered output but may not be reflected in the forecast. Elexon's dataset definitions don't confirm this, so it is presented as a likely explanation, not a fact.

---

## How to run

### Option 1: Docker (recommended)

```bash
docker compose up --build
```
Open http://localhost:8080.

### Option 2: Run the two parts directly

Backend (Python 3.11+):
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 20+), in a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The dev server forwards `/api` requests to the backend on port 8000.

### Tests
```bash
cd backend
pytest
```

### Refreshing the data
The January 2026 data is downloaded from Elexon once and committed in `backend/data/`. To download it again:
```bash
cd backend
python -m scripts.ingest
```

---

## Files and directories

```
├── backend/                  Python API (FastAPI)
│   ├── app/
│   │   ├── config.py         Scope (January 2026 decisions), 09:20 default cutoff, UK timezone
│   │   ├── elexon_client.py  Calls the Elexon WINDFOR and FUELHH stream endpoints
│   │   ├── selection.py      Core rule: picks the forecast available at decision time
│   │   ├── metrics.py        MAE, RMSE, bias, nMAE, percentiles
│   │   ├── analysis.py       Builds the day view and the January summary
│   │   ├── data_store.py     Loads and indexes the saved Elexon data
│   │   └── main.py           API endpoints
│   ├── scripts/ingest.py     Downloads January data from Elexon into data/
│   ├── data/                 Saved Elexon snapshot (about 1 MB JSON)
│   ├── tests/                Unit and API tests (pytest)
│   ├── requirements.txt      Runtime dependencies
│   ├── requirements-dev.txt  Adds uvicorn and pytest for local work
│   └── Dockerfile
├── frontend/                 React + TypeScript (Vite) dashboard
│   ├── src/
│   │   ├── App.tsx           Page layout: day section and January accuracy section
│   │   ├── components/       DatePicker, DayChart (Recharts)
│   │   ├── api.ts            Calls the backend
│   │   ├── format.ts         Number and UK-time formatting
│   │   └── types.ts          API response types
│   ├── nginx.conf            Serves the app and forwards /api in Docker
│   └── Dockerfile
├── api/index.py              Vercel entrypoint that exposes the FastAPI app
├── vercel.json               Vercel build and routing config
├── requirements.txt          Python dependencies for Vercel
├── docker-compose.yml        Runs backend and frontend together
└── .github/workflows/ci.yml  Runs tests, lint and build on every push
```

---

## How the analysis works

### Data (Elexon only)
- **Forecasts:** [WINDFOR stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream). Hourly national wind forecasts, re-issued 8 times a day (02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UK time in January), each looking about 2.5 days ahead. The stream endpoint is queried by publish time, because the plain `/datasets/WINDFOR` endpoint returns only the most recent forecast and hides the history this analysis depends on.
- **Actuals:** [FUELHH stream](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream), `fuelType = WIND`, every 30 minutes. If a half-hour is republished, the latest value is kept.

### Scope: "purchase decisions made in January 2026"
A decision on day D buys power for day D+1. So decisions on 1–31 January cover **delivery days 2 January – 1 February** (744 hours). Forecasts published from 31 December onwards are downloaded so that every January decision has its forecasts.

### Which forecast counts (the core rule)
For each hour of the delivery day, the app uses the **most recently published forecast issued strictly before the decision cutoff**. Forecasts published later did not exist when the buyer committed, so using them would make the forecasts look more accurate than they really were.

- **Cutoff:** 09:20 UK time, the gate closure of the EPEX SPOT GB day-ahead auction. (Nord Pool's N2EX auction closes at 09:50.) The API accepts any cutoff via `?cutoff=HH:MM`.
- **Example:** for the decision on 14 Jan, the 07:30 forecast is used. The next one, at 09:30, came 10 minutes too late.
- If the latest forecast is missing an hour, that hour falls back to the newest earlier forecast that covers it.

### Matching forecast with actual
Forecasts are hourly; actuals are half-hourly. Each hourly forecast is compared with the **average of the two half-hours** in that hour. Hours missing a forecast or either half-hour are shown as gaps and left out of the metrics, never treated as zero. (January has no missing data.)

### Metrics (error = forecast − actual)
| Metric | Formula | Why |
|---|---|---|
| MAE | mean(\|error\|) | typical size of a miss, in MW |
| RMSE | √mean(error²) | punishes large misses, which cost buyers most |
| Bias | mean(error) | positive = forecasts too high = shortfall risk |
| nMAE | MAE ÷ mean(actual) | the miss relative to typical output |
| P10 / P90 | percentiles of error | P90 = how much less wind than forecast to plan for to be covered 90% of the time |

Per-hour percentage error (MAPE) is deliberately not used: on calm hours with very low output it becomes huge and distorts the average.

The shaded band on the day chart is `forecast − P90` to `forecast − P10` using January's errors. It describes how wrong the forecast was in the past, not a guaranteed future range.

---

## API

| Endpoint | Returns |
|---|---|
| `GET /api/health` | `{"status": "ok"}` |
| `GET /api/meta` | Decision dates, default cutoff, data sources |
| `GET /api/day?date=2026-01-14&cutoff=09:20` | Hour-by-hour forecast used, actual, error, publish time, plus that day's metrics |
| `GET /api/summary?cutoff=09:20` | January-wide metrics and data coverage |

`date` is the **decision** date (1–31 January 2026). `cutoff` is optional (default 09:20, UK time).

---

## Design decisions

- **Data is downloaded once, not on every request.** January 2026 is in the past, so its data is final. Serving a saved snapshot keeps the API fast and the demo independent of Elexon's availability, and suits Vercel's short-lived serverless functions.
- **Plain Python for the analysis** (no pandas). The dataset is about 18,000 forecast values, so the standard library is enough, and it keeps the serverless function small with fast cold starts.
- **Business rules live in the backend.** The frontend only displays results; selection and metrics are tested in Python.
- **Timezones:** all timestamps are stored in UTC, and decision days and cutoffs are defined in UK time (`Europe/London`), so clock-change days work correctly (tested).

## Deployment

The app is deployed on **Vercel** from this repository: every push to `main` rebuilds it. Vercel builds the React app as static files and runs `api/index.py` as a Python serverless function; `/api/*` requests are routed to it, so frontend and API share one domain. Docker is used for running the app locally and is not used by Vercel.

## Limitations and next steps

- Only January 2026, as the brief requires. Another month needs two dates changed in `config.py` and the ingest script rerun.
- For live use, the ingest script would run on a schedule (for example every 30 minutes) and the API would read from a small database.
- The safety-margin band uses January's own errors (in-sample). A production version should calculate it from a rolling past window.

## AI usage

AI tools (Claude Code) were used to help with exploring the Elexon API, writing code and tests, and drafting this README. The author understands the core logic and workflow of the application.
