import pytest
from flask_migrate import upgrade

from app import create_app
from app.config import TestConfig


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "test.db"

    class Config(TestConfig):
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + database.as_posix()

    application = create_app(Config)
    with application.app_context():
        upgrade()
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf(client):
    def headers(extra=None):
        token = client.get("/api/auth/csrf").get_json()["csrf_token"]
        prepared = {"X-CSRFToken": token}
        if extra:
            prepared.update(extra)
        return prepared

    return headers
