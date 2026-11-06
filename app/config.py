import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


def _env_float(name, default):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_HEADERS = ["X-CSRFToken", "X-CSRF-Token"]
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "60 per minute")
    TRUST_PROXY = os.environ.get("TRUST_PROXY", "0") == "1"
    OSM_USER_AGENT = os.environ.get(
        "OSM_USER_AGENT",
        "AccessibilityNavigator/0.1 (educational project; contact: unset)",
    )
    OVERPASS_URL = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    NOMINATIM_URL = os.environ.get("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
    # Corridor queries expand north, south, east, and west around the trip.
    # A single Overpass request cannot exceed this span on either axis.
    MAX_BBOX_SPAN_DEGREES = _env_float("MAX_BBOX_SPAN_DEGREES", 0.15)
    BBOX_MARGIN_METRES = _env_float("BBOX_MARGIN_METRES", 350)

    @staticmethod
    def validate():
        return None


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "sqlite:///" + (INSTANCE_DIR / "dev.db").as_posix()
    )

    @staticmethod
    def validate():
        secret = os.environ.get("SECRET_KEY", "")
        if len(secret) < 16:
            raise RuntimeError(
                "SECRET_KEY is missing or shorter than 16 characters. "
                "Copy .env.example to .env and set a long random value."
            )


class TestConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "test-secret-key-not-for-production"
    TRUST_PROXY = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = True
    RATELIMIT_ENABLED = False
    MAX_BBOX_SPAN_DEGREES = 0.15
    BBOX_MARGIN_METRES = 350.0


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")

    @staticmethod
    def validate():
        secret = os.environ.get("SECRET_KEY", "")
        if len(secret) < 32:
            raise RuntimeError("Production SECRET_KEY must be at least 32 characters.")
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url.startswith("mysql"):
            raise RuntimeError("Production DATABASE_URL must be a MySQL URL.")
        agent = os.environ.get("OSM_USER_AGENT", "")
        if "contact:" not in agent or "example.com" in agent or "unset" in agent:
            raise RuntimeError(
                "Production OSM_USER_AGENT must identify this application and a real contact."
            )


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestConfig,
    "production": ProductionConfig,
}


def resolve_config(name=None):
    selected = name or os.environ.get("APP_ENV", "development")
    try:
        config_class = CONFIGS[selected]
    except KeyError as exc:
        raise RuntimeError(f"Unknown APP_ENV: {selected}") from exc
    config_class.validate()
    return config_class


def apply_environment(app, config_class):
    """Read process environment at startup so values are not frozen at import."""
    if issubclass(config_class, TestConfig):
        return
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "")
    app.config["LOG_LEVEL"] = os.environ.get("LOG_LEVEL", "INFO")
    app.config["RATELIMIT_STORAGE_URI"] = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    app.config["RATELIMIT_DEFAULT"] = os.environ.get("RATELIMIT_DEFAULT", "60 per minute")
    app.config["TRUST_PROXY"] = os.environ.get("TRUST_PROXY", "0") == "1"
    app.config["OSM_USER_AGENT"] = os.environ.get(
        "OSM_USER_AGENT",
        "AccessibilityNavigator/0.1 (educational project; contact: unset)",
    )
    app.config["OVERPASS_URL"] = os.environ.get(
        "OVERPASS_URL", "https://overpass-api.de/api/interpreter"
    )
    app.config["NOMINATIM_URL"] = os.environ.get(
        "NOMINATIM_URL", "https://nominatim.openstreetmap.org"
    )
    app.config["MAX_BBOX_SPAN_DEGREES"] = _env_float("MAX_BBOX_SPAN_DEGREES", 0.15)
    app.config["BBOX_MARGIN_METRES"] = _env_float("BBOX_MARGIN_METRES", 350)
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    elif config_class is DevelopmentConfig:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + (INSTANCE_DIR / "dev.db").as_posix()


def load_local_env():
    if os.environ.get("APP_ENV", "development") != "testing":
        load_dotenv()
