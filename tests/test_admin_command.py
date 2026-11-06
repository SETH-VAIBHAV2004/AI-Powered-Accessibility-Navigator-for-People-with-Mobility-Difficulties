from sqlalchemy import select

from app.extensions import db
from app.models.user import ROLE_ADMIN, User


def test_create_admin(app, monkeypatch):
    monkeypatch.setenv("ADMIN_NAME", "Asha Admin")
    monkeypatch.setenv("ADMIN_EMAIL", "Admin@University.edu")
    monkeypatch.setenv("ADMIN_PASSWORD", "a-long-admin-password")
    runner = app.test_cli_runner()
    created = runner.invoke(args=["create-admin"])
    assert created.exit_code == 0
    assert "a-long-admin-password" not in created.output
    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == "admin@university.edu"))
        assert user.role == ROLE_ADMIN
        assert user.check_password("a-long-admin-password")
    duplicate = runner.invoke(args=["create-admin"])
    assert duplicate.exit_code == 1


def test_create_admin_rejects_missing_or_weak_values(app, monkeypatch):
    monkeypatch.delenv("ADMIN_NAME", raising=False)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    runner = app.test_cli_runner()
    missing = runner.invoke(args=["create-admin"])
    assert missing.exit_code == 2

    monkeypatch.setenv("ADMIN_NAME", "Asha Admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@university.edu")
    monkeypatch.setenv("ADMIN_PASSWORD", "short")
    weak = runner.invoke(args=["create-admin"])
    assert weak.exit_code == 2
    assert "short" not in weak.output
