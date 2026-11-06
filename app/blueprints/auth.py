from flask import Blueprint, jsonify, redirect, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import generate_csrf

from app.extensions import db, limiter, login_manager
from app.models.user import User
from app.services.accounts import AccountError, authenticate, register_user

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    if user_id is None or not str(user_id).isdigit():
        return None
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify(error="authentication_required"), 401
    return redirect(url_for("auth.login_page"))


@auth_bp.post("/api/auth/register")
@limiter.limit("10 per minute")
def register_api():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="invalid_json"), 400
    try:
        user = register_user(payload.get("name"), payload.get("email"), payload.get("password"))
    except AccountError as exc:
        return jsonify(error="invalid_account", fields=exc.fields), exc.status_code
    _start_session(user)
    return jsonify(user=user.to_public_dict()), 201


@auth_bp.post("/api/auth/login")
@limiter.limit("10 per minute")
def login_api():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="invalid_json"), 400
    user = authenticate(payload.get("email"), payload.get("password"))
    if user is None:
        return jsonify(error="invalid_credentials"), 401
    _start_session(user)
    return jsonify(user=user.to_public_dict())


@auth_bp.post("/api/auth/logout")
@login_required
def logout_api():
    logout_user()
    return jsonify(status="signed_out")


@auth_bp.get("/api/auth/csrf")
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@auth_bp.get("/api/auth/me")
def me():
    if not current_user.is_authenticated:
        return jsonify(error="authentication_required"), 401
    return jsonify(user=current_user.to_public_dict())


def _start_session(user):
    session.clear()
    login_user(user, remember=False)
