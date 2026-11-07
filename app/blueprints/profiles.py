from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.profiles import (
    ProfileError,
    create_profile,
    delete_profile,
    list_profiles,
    profile_payload,
    set_default,
    update_profile,
)

profiles_bp = Blueprint("profiles", __name__)


@profiles_bp.get("/api/profiles")
@login_required
def list_api():
    presets, own = list_profiles(current_user)
    return jsonify(
        presets=[profile_payload(item, current_user) for item in presets],
        profiles=[profile_payload(item, current_user) for item in own],
        default_profile_id=current_user.default_profile_id,
    )


@profiles_bp.post("/api/profiles")
@login_required
def create_api():
    payload = _json_body()
    if payload is None:
        return jsonify(error="invalid_json"), 400
    try:
        profile = create_profile(current_user, payload)
    except ProfileError as exc:
        return _error(exc)
    return jsonify(profile=profile_payload(profile, current_user)), 201


@profiles_bp.put("/api/profiles/<int:profile_id>")
@login_required
def update_api(profile_id):
    payload = _json_body()
    if payload is None:
        return jsonify(error="invalid_json"), 400
    try:
        profile = update_profile(current_user, profile_id, payload)
    except ProfileError as exc:
        return _error(exc)
    return jsonify(profile=profile_payload(profile, current_user))


@profiles_bp.delete("/api/profiles/<int:profile_id>")
@login_required
def delete_api(profile_id):
    try:
        delete_profile(current_user, profile_id)
    except ProfileError as exc:
        return _error(exc)
    return jsonify(status="deleted")


@profiles_bp.post("/api/profiles/<int:profile_id>/default")
@login_required
def default_api(profile_id):
    try:
        profile = set_default(current_user, profile_id)
    except ProfileError as exc:
        return _error(exc)
    return jsonify(profile=profile_payload(profile, current_user))


def _json_body():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None
    return payload


def _error(exc):
    error = "invalid_profile"
    if exc.status_code == 404:
        error = "not_found"
    elif exc.status_code == 403:
        error = "forbidden"
    return jsonify(error=error, fields=exc.fields), exc.status_code
