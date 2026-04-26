# Sentinel Atlas Social Pulse Handoff

This repo contains the latest working Social Pulse tab implementation for Sentinel Atlas.
It is packaged as a self-contained React + FastAPI feature repo so a full stack developer can move the tab into the final product layout.

This is the latest top-level Social Pulse app, not the older nested `apart-forecasting-tool-main` copy.

## What The Tab Does

Social Pulse is a selected-country panel that turns public behavioral and media signals into an aggregate 0-100 concern score. It stays country-first: the user selects a country on the map, then the right-side country panel shows latest public news plus the Social Pulse section.

The Social Pulse section includes:

- A composite `social_pulse_score`.
- A `low`, `moderate`, `elevated`, or `high` pulse level.
- Four independent signal scores: Reddit fear, Wikipedia spike, search fear, and news sentiment.
- A 7-day / 30-day chart toggle.
- A 30-day baseline line.
- An evidence drawer with source links.
- A red pulse animation on the map when a country has 2+ elevated signals and score >= 55.

## Change History

1. Started with a country-first public news dashboard.
   - Added map-based country selection.
   - Kept the side navigation limited to `World Dashboard`, `Sources`, and `Time Series`.
   - Avoided a separate News nav item and avoided country dropdown selection.

2. Added public news ingestion.
   - Backend added FastAPI endpoints for latest and historical country news.
   - SQLite stores articles and ingest runs.
   - Sources include Google News RSS, ReliefWeb, WHO Disease Outbreak News, and ProMED where available.
   - Frontend shows real-source headlines only, or an empty state if no reports are found.

3. Hardened news handling.
   - Added safety filtering for individual-level health data and risky public-alert or wet-lab content.
   - Added translation fallback behavior so failed translation does not break ingestion.
   - Added country extraction rules that store unknown-country articles but keep them out of country-specific endpoints.
   - Preserved exact empty states:
     - `No news feed connected yet.`
     - `No public news reports found in the last 48 hours.`

4. Replaced the old historical-news panel with Social Pulse.
   - Added `src/components/SocialPulse/SocialPulsePanel.tsx`.
   - Updated `src/components/News/CountryNewsSidebar.tsx` to render Social Pulse for the selected country.
   - Kept latest 48-hour public news above the Social Pulse section.
   - Removed the historical-news display from the selected-country panel.

5. Added Social Pulse backend storage and API.
   - Added `backend/app/models/sentiment.py`.
   - Added Social Pulse table registration in `backend/app/db.py`.
   - Added `backend/app/api/sentiment.py`.
   - Added `GET /api/countries/{iso3}/social-pulse`.
   - Added `POST /api/social-pulse/compute-all`.
   - Added `GET /api/countries/elevated?threshold=55`.

6. Added the four Social Pulse signal services.
   - `backend/app/services/sentiment/reddit_scraper.py`
   - `backend/app/services/sentiment/wikipedia_trends.py`
   - `backend/app/services/sentiment/trends_fear.py`
   - `backend/app/services/sentiment/news_sentiment.py`
   - `backend/app/services/sentiment/hf_client.py`
   - `backend/app/services/sentiment/aggregator.py`

7. Added the convergence rule.
   - Each signal is normalized to 0-100.
   - Weighted score is computed as Reddit 25%, Wikipedia 20%, Search 30%, News 25%.
   - If fewer than 2 signals are elevated above 50, the composite score is dampened by 0.70.
   - This avoids flagging a country from one noisy source.

8. Added the map pulse alert.
   - `src/components/Map/WorldMap.tsx` fetches `/api/countries/elevated?threshold=55`.
   - Countries returned by that endpoint get the `pulse-alert` class.
   - `src/styles.css` contains the red pulse animation.

9. Added demo data and tests.
   - `backend/scripts/seed_demo_data.py` seeds 35 days of DRC/COD Social Pulse history.
   - `backend/tests/test_sentiment_api.py` verifies latest pulse and elevated-country filtering.
   - Frontend tests verify the selected-country panel no longer shows historical-news copy.

## Key Integration Files

Frontend:

- `src/components/SocialPulse/SocialPulsePanel.tsx`
- `src/components/News/CountryNewsSidebar.tsx`
- `src/components/Map/WorldMap.tsx`
- `src/styles.css`
- `src/state/DashboardContext.tsx`
- `src/data/adapters/countryNewsAdapter.ts`

Backend:

- `backend/app/api/sentiment.py`
- `backend/app/models/sentiment.py`
- `backend/app/services/sentiment/aggregator.py`
- `backend/app/services/sentiment/*.py`
- `backend/app/main.py`
- `backend/app/db.py`
- `backend/scripts/seed_demo_data.py`

Tests:

- `src/App.test.tsx`
- `backend/tests/test_sentiment_api.py`
- `backend/tests/test_news_api.py`

## API Contract

### Get Social Pulse For A Country

```http
GET /api/countries/{iso3}/social-pulse?days=30
```

Response shape:

```json
{
  "iso3": "COD",
  "latest": {
    "social_pulse_score": 72.8,
    "pulse_level": "elevated",
    "signals_elevated": 4,
    "reddit_score": 70,
    "wikipedia_score": 74,
    "trends_fear_score": 75,
    "news_sentiment_score": 72,
    "computed_at": "2026-04-26T12:00:00+00:00"
  },
  "evidence": [
    {
      "title": "Evidence headline",
      "url": "https://example.org/source",
      "source": "Wikipedia Pageviews",
      "sentiment_score": 0.78
    }
  ],
  "history": [
    {
      "date": "2026-04-26",
      "social_pulse": 72.8,
      "reddit": 70,
      "wikipedia": 74,
      "trends": 75,
      "news": 72,
      "level": "elevated",
      "signals_elevated": 4
    }
  ],
  "days": 30
}
```

### Get Elevated Countries For Map Pulse

```http
GET /api/countries/elevated?threshold=55
```

Response shape:

```json
{
  "elevated": [
    {
      "iso3": "COD",
      "score": 72.8,
      "level": "elevated",
      "signals_elevated": 4
    }
  ]
}
```

## Local Run Steps

Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
SENTINEL_DISABLE_STARTUP_JOBS=1 uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open:

```text
http://localhost:5173
```

## Demo Data

To seed a 35-day DRC/COD Social Pulse story, run this from the repository root:

```bash
source backend/venv/bin/activate
python -m backend.scripts.seed_demo_data
```

If running with a different existing virtual environment:

```bash
python -m backend.scripts.seed_demo_data
```

The frontend should then show DRC/COD as elevated and pulse it on the map.

## Environment

Root `.env.local`:

```bash
VITE_SENTINEL_API_BASE_URL=http://localhost:8000
```

Backend environment:

```bash
HF_API_TOKEN=hf_your_token_here
SENTINEL_DISABLE_STARTUP_JOBS=1
```

`HF_API_TOKEN` is optional for local demo. Without it, the backend uses keyword fallback scoring for text sentiment.

## Verification

Frontend:

```bash
npm test
npm run build
```

Backend:

```bash
cd backend
pytest
```

## Integration Notes For The Final Layout

- Keep Social Pulse inside the selected-country workflow. Do not add a separate top-level Social Pulse or News navigation item unless the final product design explicitly changes that information architecture.
- Keep map country selection as the source of truth for `iso3`.
- Preserve the backend contract above if the final layout uses a different UI framework.
- The pulse map behavior only needs `/api/countries/elevated?threshold=55`.
- The tab should render source-backed data or a clear unavailable state. Do not add fake headlines, fake outbreaks, fake R0/Rt values, or synthetic disease-risk shading.
- The current implementation is a feature-ready handoff, not a polished final design system pass.
