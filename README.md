# Sentinel Atlas Social Pulse

Sentinel Atlas Social Pulse is a React and FastAPI research module that
aggregates source-linked public news and behavioral signals for country-level
exploration. The GitHub repository keeps its historical `Pulse_GDELT` slug, but
the product, package, interface, and API use this single public name.

## Status

This is a maintained integration prototype, not a production early-warning
service. It can render the frontend against a locally operated API and can
ingest public sources when an operator explicitly enables networked actions.
It does not provide medical advice, event forecasts, or individual risk scores.

There is no verified public deployment. Run it locally using the steps below.

## What It Does

For a selected country, the module can present:

- recent source-linked public news;
- a composite 0–100 Social Pulse research signal;
- Reddit, Wikipedia, Google Trends, and news-sentiment components;
- 7-day and 30-day history;
- source evidence associated with a stored snapshot; and
- an elevated-state map cue when at least two signals exceed the configured
  threshold.

The score is an exploratory convergence heuristic. It is not a probability,
causal estimate, verified incident count, or country-risk rating.

## Architecture

- `src/`: React 19 and TypeScript frontend
- `backend/app/`: FastAPI API, SQLAlchemy models, source adapters, and signal
  aggregation
- `backend/tests/`: isolated API and safety tests
- `backend/scripts/seed_demo_data.py`: local synthetic demo-state generator

SQLite is local state. The default file, `sentinel_atlas.db`, is ignored and
must never be committed.

## Setup

Prerequisites:

- Node.js 22
- pnpm 11.10.0, selected by the `packageManager` field
- Python 3.11+

Install the frontend:

```bash
pnpm install --frozen-lockfile
cp .env.example .env.local
cp backend/.env.example backend/.env.local
```

Install the backend:

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-dev.txt
```

The example files contain no credentials. `HF_API_TOKEN` is optional and must
remain in local environment configuration.

## Local Use

Start the API with networked ingestion and mutations disabled:

```bash
source backend/.venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000 --env-file .env.local
```

In a second terminal:

```bash
pnpm dev
```

Open `http://127.0.0.1:5173`.

To load the local synthetic DRC/COD demonstration without contacting upstream
sources:

```bash
source backend/.venv/bin/activate
python -m backend.scripts.seed_demo_data
```

## Verification

```bash
pnpm typecheck
pnpm test
pnpm build

source backend/.venv/bin/activate
ruff check backend
black --check backend
python -m pytest backend
```

Tests use an in-memory database and do not need external credentials or live
source access.

## API Surface

Read endpoints include:

- `GET /health`
- `GET /api/countries/{iso3}/news/latest`
- `GET /api/countries/{iso3}/news/history`
- `GET /api/news`
- `GET /api/ingest/news/runs`
- `GET /api/countries/{iso3}/social-pulse`
- `GET /api/countries/elevated`

Operator endpoints are disabled by default:

- `POST /api/ingest/news`
- `POST /api/social-pulse/compute-all`

Set `SENTINEL_ENABLE_MUTATIONS=1` only in an operator-controlled environment.
That switch is not authentication. Any internet-facing deployment must place
the mutation endpoints behind authentication, authorization, rate limits, and
request logging that excludes sensitive content.

## Network And Background Work

Potential upstreams include Google News RSS, ReliefWeb, WHO Disease Outbreak
News, ProMED, public Reddit endpoints, Wikipedia Pageviews, Google Trends, and
the optional Hugging Face Inference API. Adapters are best-effort and upstream
availability, access rules, response formats, and rate limits can change.

Background ingestion is off by default. `SENTINEL_ENABLE_STARTUP_JOBS=1`
explicitly opts into startup work and hourly refreshes. Operators remain
responsible for upstream terms, robots guidance, rate limits, attribution, and
deployment resource controls.

## CORS And Deployment Defaults

Local origins are the only defaults. Production origins must be listed exactly
in the comma-separated `ALLOWED_ORIGINS` variable. Credentialed CORS is off by
default; setting `ALLOW_CREDENTIALS=1` while allowing `*` makes the application
fail at startup.

Do not deploy the SQLite development configuration as a multi-instance service.
Do not expose operator endpoints without a separate authentication layer. No
production deployment is performed or implied by this repository.

## Source Credibility And Provenance

Every displayed article retains a source URL. Credibility labels are configured
source-tier heuristics: they describe the expected provenance of a publisher or
feed, not independent verification of an article, the truth of a claim, event
likelihood, or country risk. Empty or unavailable data must remain visibly
unavailable; the application must not invent headlines or signals.

See [DATA_AND_SOURCE_NOTICE.md](DATA_AND_SOURCE_NOTICE.md) for source and rights
boundaries.

## Privacy And Safety

- Store aggregate public-source observations only.
- Do not ingest or expose names, contact details, medical record identifiers,
  or other individual-level health information.
- Safety filters reduce obvious risk but do not replace human review.
- Keep credentials, local databases, raw response dumps, and private operator
  logs outside Git.
- Do not interpret the interface as health, travel, security, or policy advice.

## Limitations

- Source access is incomplete and can fail or change without notice.
- Country extraction, translation, sentiment, and keyword fallbacks can be
  wrong or culturally biased.
- A composite score can amplify shared source bias and cannot establish causal
  relationships.
- Stored snapshots become stale unless a human-operated ingestion process is
  running.
- The current SQLite architecture is for local evaluation, not production
  concurrency or durability.

## Contributions And Support

Use GitHub issues for reproducible bugs, source corrections, or documentation
gaps. For research corrections, include the source URL, access date, affected
record or screen, and requested change. Use GitHub private vulnerability
reporting for security issues. Repository-specific guidance overrides inherited
account defaults; no response-time guarantee is implied.

## Maintainer

Maintained by Muhammad Umar Zafar.

## License

Original software is licensed under the [MIT License](LICENSE). Public-source
material, publisher content, trademarks, API responses, and other third-party
material are not relicensed by this repository; see
[DATA_AND_SOURCE_NOTICE.md](DATA_AND_SOURCE_NOTICE.md).
