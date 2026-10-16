from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    database_path = tmp_path / "test-tasks.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database_path),
            "SECRET_KEY": "test-only-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
