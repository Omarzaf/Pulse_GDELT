import os

from fastapi import HTTPException, status

DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)


def _enabled(name: str) -> bool:
    """Return whether an opt-in environment flag is explicitly enabled."""
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def cors_settings() -> tuple[list[str], bool]:
    """Return explicit CORS origins and reject credentialed wildcards."""
    raw_origins = os.getenv("ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if not origins:
        origins = list(DEFAULT_ALLOWED_ORIGINS)

    allow_credentials = _enabled("ALLOW_CREDENTIALS")
    if allow_credentials and "*" in origins:
        raise RuntimeError("Credentialed CORS requires explicit ALLOWED_ORIGINS")

    return origins, allow_credentials


def startup_jobs_enabled() -> bool:
    """Return whether networked background ingestion was explicitly enabled."""
    return (
        _enabled("SENTINEL_ENABLE_STARTUP_JOBS")
        and not _enabled("SENTINEL_DISABLE_STARTUP_JOBS")
        and "PYTEST_CURRENT_TEST" not in os.environ
    )


def require_mutations_enabled() -> None:
    """Reject ingestion and recomputation unless an operator opts in."""
    if not _enabled("SENTINEL_ENABLE_MUTATIONS"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operator-triggered ingestion and computation are disabled",
        )
