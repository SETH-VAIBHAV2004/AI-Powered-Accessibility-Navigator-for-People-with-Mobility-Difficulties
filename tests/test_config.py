import pytest

from app.config import DevelopmentConfig, ProductionConfig, TestConfig, resolve_config


def test_area_is_not_a_fixed_campus():
    assert not hasattr(TestConfig, "STUDY_AREA_BBOX")
    assert TestConfig.MAX_BBOX_SPAN_DEGREES == 0.15
    assert TestConfig.BBOX_MARGIN_METRES == 350


def test_development_requires_a_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        resolve_config("development")


def test_development_accepts_a_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "development-secret-value")
    assert resolve_config("development") is DevelopmentConfig


def test_production_requires_mysql_and_a_real_user_agent(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///prod.db")
    monkeypatch.setenv(
        "OSM_USER_AGENT",
        "AccessibilityNavigator/0.1 (contact: campus@university.edu)",
    )
    with pytest.raises(RuntimeError, match="MySQL"):
        ProductionConfig.validate()


def test_production_rejects_placeholder_contact(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    monkeypatch.setenv("DATABASE_URL", "mysql+mysqlconnector://navigator:pw@db:3306/navigator")
    monkeypatch.setenv("OSM_USER_AGENT", "AccessibilityNavigator/0.1 (contact: you@example.com)")
    with pytest.raises(RuntimeError, match="OSM_USER_AGENT"):
        ProductionConfig.validate()


def test_production_accepts_complete_settings(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 32)
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+mysqlconnector://navigator:pw@db:3306/navigator",
    )
    monkeypatch.setenv(
        "OSM_USER_AGENT",
        "AccessibilityNavigator/0.1 (contact: navigator@university.edu)",
    )
    assert resolve_config("production") is ProductionConfig


def test_unknown_environment_is_rejected():
    with pytest.raises(RuntimeError, match="Unknown APP_ENV"):
        resolve_config("staging")
