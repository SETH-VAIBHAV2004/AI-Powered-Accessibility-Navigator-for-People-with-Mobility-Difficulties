from flask import jsonify

from app.authz import admin_required
from app.extensions import db
from app.models.user import ROLE_ADMIN, User


def test_register_login_me_and_logout(client, csrf):
    created = client.post(
        "/api/auth/register",
        json={
            "name": "Asha Rao",
            "email": "asha@university.edu",
            "password": "a-long-password",
            "role": "admin",
        },
        headers=csrf(),
    )
    assert created.status_code == 201
    body = created.get_json()["user"]
    assert body["role"] == "user"
    assert "password" not in body
    assert "password_hash" not in body

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["user"]["email"] == "asha@university.edu"

    signed_out = client.post("/api/auth/logout", headers=csrf())
    assert signed_out.status_code == 200
    assert client.get("/api/auth/me").status_code == 401

    signed_in = client.post(
        "/api/auth/login",
        json={"email": "Asha@University.edu", "password": "a-long-password"},
        headers=csrf(),
    )
    assert signed_in.status_code == 200
    assert signed_in.get_json()["user"]["id"] == body["id"]


def test_login_failure_is_generic(client, csrf):
    response = client.post(
        "/api/auth/login",
        json={"email": "nobody@university.edu", "password": "a-long-password"},
        headers=csrf(),
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "invalid_credentials"}


def test_duplicate_registration_returns_409(client, csrf):
    payload = {
        "name": "Asha Rao",
        "email": "asha@university.edu",
        "password": "a-long-password",
    }
    assert client.post("/api/auth/register", json=payload, headers=csrf()).status_code == 201
    client.post("/api/auth/logout", headers=csrf())
    again = client.post("/api/auth/register", json=payload, headers=csrf())
    assert again.status_code == 409
    assert again.get_json()["fields"]["email"]


def test_api_rejects_missing_csrf_and_invalid_json(client, csrf):
    missing = client.post(
        "/api/auth/login",
        json={"email": "asha@university.edu", "password": "a-long-password"},
    )
    assert missing.status_code == 400
    assert missing.get_json()["error"] == "csrf_failed"

    invalid = client.post(
        "/api/auth/login",
        data="[]",
        headers=csrf({"Content-Type": "application/json"}),
    )
    assert invalid.status_code == 400
    assert invalid.get_json()["error"] == "invalid_json"


def test_admin_route_checks_role(app):
    @admin_required
    def secret():
        return jsonify(status="ok")

    app.add_url_rule("/api/admin/ping", "admin_ping", secret)
    client = app.test_client()

    assert client.get("/api/admin/ping").status_code == 401

    created = client.post(
        "/api/auth/register",
        json={"name": "Asha Rao", "email": "asha@university.edu", "password": "a-long-password"},
        headers=_csrf(client),
    )
    assert created.status_code == 201
    assert client.get("/api/admin/ping").status_code == 403

    with app.app_context():
        user = db.session.get(User, created.get_json()["user"]["id"])
        user.role = ROLE_ADMIN
        db.session.commit()

    assert client.get("/api/admin/ping").status_code == 200


def _csrf(client):
    token = client.get("/api/auth/csrf").get_json()["csrf_token"]
    return {"X-CSRFToken": token}
