# Developer README

This handoff repo packages the Sentinel Atlas Social Pulse tab and its supporting FastAPI backend.

## Backend

1. `cd backend`
2. `python -m venv venv`
3. Activate the virtual environment:
   - macOS/Linux: `source venv/bin/activate`
   - Windows PowerShell: `venv\\Scripts\\Activate.ps1`
4. `pip install -r requirements.txt`
5. Optional: set `HF_API_TOKEN` in `backend/.env` or your shell.
6. For demo/local work, set `SENTINEL_DISABLE_STARTUP_JOBS=1` to avoid automatic hourly fetches while testing.
7. `SENTINEL_DISABLE_STARTUP_JOBS=1 uvicorn app.main:app --reload --port 8000`

The database is created by the startup path. This repo does not use Alembic yet; `app.db.init_db()` calls `Base.metadata.create_all(...)` and creates `sentinel_atlas.db`.

Useful backend endpoints:

- `GET /health`
- `GET /api/countries/{iso3}/news/latest?hours=48&limit=5`
- `GET /api/countries/{iso3}/news/history?days=30&limit=50`
- `GET /api/news`
- `POST /api/ingest/news`
- `GET /api/ingest/news/runs`
- `GET /api/countries/{iso3}/social-pulse?days=30`
- `POST /api/social-pulse/compute-all`
- `GET /api/countries/elevated?threshold=55`

Seed demo Social Pulse data from the repository root:

```bash
source backend/venv/bin/activate
python -m backend.scripts.seed_demo_data
```

## Frontend

1. Create `.env.local` at the repo root.
2. Set `VITE_SENTINEL_API_BASE_URL=http://localhost:8000`.
3. `npm install`
4. `npm run dev`
5. Open `http://localhost:5173`

If `VITE_SENTINEL_API_BASE_URL` is missing or the backend is unavailable, the news dashboard stays local-only. Social Pulse needs the backend endpoint and will not fabricate data.

## Push Readiness

- `npm test` passes.
- `npm run build` passes.
- `cd backend && pytest` passes inside the activated backend virtualenv.
- No fourth nav item.
- No country dropdown.
- No fake public-health data.
- No synthetic simulator UI.
- No generated disease risk.
- No Rt/R0 metrics.
- No country-risk shading.
- No individual-level health data.
- Social Pulse stays inside the selected-country panel.
