import pytest

from app import create_app
from app.config import Config


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_create_app_rejects_short_secret_key(monkeypatch):
    monkeypatch.setattr(Config, "SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError, match="SECRET_KEY must be at least 32 characters"):
        create_app()
    