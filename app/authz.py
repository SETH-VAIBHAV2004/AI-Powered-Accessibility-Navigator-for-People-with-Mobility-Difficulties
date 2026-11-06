from functools import wraps

from flask import jsonify, redirect, request, url_for
from flask_login import current_user
from werkzeug.exceptions import Forbidden

from app.models.user import ROLE_ADMIN


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith("/api/"):
                return jsonify(error="authentication_required"), 401
            return redirect(url_for("auth.login_page"))
        if current_user.role != ROLE_ADMIN:
            if request.path.startswith("/api/"):
                return jsonify(error="forbidden"), 403
            raise Forbidden()
        return view(*args, **kwargs)

    return wrapped
