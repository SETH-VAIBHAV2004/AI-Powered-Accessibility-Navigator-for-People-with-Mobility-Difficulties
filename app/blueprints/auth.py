from flask import (
    Blueprint,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
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


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("pages.home"))
    errors = {}
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        user = authenticate(email, request.form.get("password"))
        if user is None:
            errors["form"] = "The email or password is incorrect."
        else:
            _start_session(user)
            return redirect(_next_or_home())
    return _form_response("login.html", errors, email=_text(email))


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for("pages.home"))
    errors = {}
    name = ""
    email = ""
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        try:
            user = register_user(name, email, request.form.get("password"))
        except AccountError as exc:
            errors = exc.fields
        else:
            _start_session(user)
            return redirect(url_for("pages.home"))
    return _form_response("register.html", errors, name=_text(name), email=_text(email))


@auth_bp.post("/logout")
@login_required
def logout_page():
    logout_user()
    return redirect(url_for("auth.login_page"))


def _start_session(user):
    session.clear()
    login_user(user, remember=False)


def _form_response(template, errors, **context):
    status = 400 if errors else 200
    body = render_template(template, errors=errors, next_target=_safe_next(), **context)
    return make_response(body, status)


def _next_or_home():
    target = _safe_next()
    if target:
        return target
    return url_for("pages.home")


def _safe_next():
    for source in (request.form, request.args):
        candidate = source.get("next")
        if _is_local_path(candidate):
            return candidate
    return ""


def _is_local_path(candidate):
    return (
        isinstance(candidate, str)
        and candidate.startswith("/")
        and not candidate.startswith("//")
        and "\\" not in candidate
    )


def _text(value):
    return value if isinstance(value, str) else ""
