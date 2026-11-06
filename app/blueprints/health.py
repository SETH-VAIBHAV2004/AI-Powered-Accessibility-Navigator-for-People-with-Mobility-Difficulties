from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app.extensions import db, limiter

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
@limiter.exempt
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("database health check failed")
        return jsonify(status="error", database="unavailable"), 503
    return jsonify(status="ok", database="ok")
