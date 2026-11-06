from sqlalchemy.exc import OperationalError


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "ok"}
    assert response.headers["Cache-Control"] == "no-store"


def test_health_reports_database_failure(client, monkeypatch):
    def fail(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("down"))

    monkeypatch.setattr("app.blueprints.health.db.session.execute", fail)
    response = client.get("/api/health")
    assert response.status_code == 503
    body = response.get_json()
    assert body["status"] == "error"
    assert body["database"] == "unavailable"
    assert "down" not in response.get_data(as_text=True)


def test_unknown_api_path_is_json(client):
    response = client.get("/api/missing")
    assert response.status_code == 404
    assert response.get_json() == {"error": "not_found"}
