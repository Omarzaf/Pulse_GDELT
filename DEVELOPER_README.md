# Sentinel Atlas Social Pulse — Developer Notes

This repository packages the Sentinel Atlas Social Pulse module and its
supporting FastAPI backend. The root `README.md` is the canonical public guide.

## Backend

1. `cd backend`
2. `python -m venv .venv`
3. Activate the virtual environment:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
4. `python -m pip install -r requirements-dev.txt`
5. Copy `.env.example` to `.env.local`; keep `HF_API_TOKEN` empty unless the
   optional external inference path is intentionally being tested.
6. `uvicorn app.main:app --reload --port 8000 --env-file .env.local`

The database is created by the startup path. This repo does not use Alembic;
`app.db.init_db()` calls `Base.metadata.create_all(...)` and creates the ignored
local file `sentinel_atlas.db`.

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

1. Copy the root `.env.example` to `.env.local`.
2. `pnpm install --frozen-lockfile`
3. `pnpm dev`
4. Open `http://127.0.0.1:5173`

If `VITE_SENTINEL_API_BASE_URL` is missing or the backend is unavailable, the news dashboard stays local-only. Social Pulse needs the backend endpoint and will not fabricate data.

## Push Readiness

- `pnpm typecheck` passes.
- `pnpm test` passes.
- `pnpm build` passes.
- `ruff check backend` and `black --check backend` pass from the repository root.
- `python -m pytest backend` passes inside the activated backend virtualenv.
- Networked background jobs and operator mutations remain disabled unless
  explicitly enabled.
- No fourth nav item.
- No country dropdown.
- No fake public-health data.
- No synthetic simulator UI.
- No generated disease risk.
- No Rt/R0 metrics.
- No country-risk shading.
- No individual-level health data.
- Social Pulse stays inside the selected-country panel.
