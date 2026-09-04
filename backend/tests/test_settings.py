import pytest
from app.settings import DEFAULT_ALLOWED_ORIGINS, cors_settings, startup_jobs_enabled


def test_cors_defaults_to_local_origins_without_credentials(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("ALLOW_CREDENTIALS", raising=False)

    origins, allow_credentials = cors_settings()

    assert origins == list(DEFAULT_ALLOWED_ORIGINS)
    assert allow_credentials is False


def test_cors_rejects_wildcard_with_credentials(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("ALLOW_CREDENTIALS", "1")

    with pytest.raises(RuntimeError, match="requires explicit"):
        cors_settings()


def test_local_cors_preflight_returns_explicit_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "access-control-allow-credentials" not in response.headers


def test_background_jobs_are_opt_in(monkeypatch):
    monkeypatch.delenv("SENTINEL_ENABLE_STARTUP_JOBS", raising=False)
    monkeypatch.delenv("SENTINEL_DISABLE_STARTUP_JOBS", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    assert startup_jobs_enabled() is False

    monkeypatch.setenv("SENTINEL_ENABLE_STARTUP_JOBS", "1")

    assert startup_jobs_enabled() is True
