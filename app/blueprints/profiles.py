from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services.profiles import (
    ProfileError,
    create_profile,
    delete_profile,
    get_owned_profile,
    list_profiles,
    profile_payload,
    set_default,
    update_profile,
)

profiles_bp = Blueprint("profiles", __name__)

CHECKBOXES = ("avoid_stairs", "block_on_verified_obstacles", "exclude_unknown")
BLANK_FORM = {
    "name": "",
    "profile_type": "custom",
    "max_slope_degrees": "",
    "min_width_m": "",
    "avoid_stairs": False,
    "block_on_verified_obstacles": True,
    "exclude_unknown": False,
    "walking_speed_mps": "1",
    "surface_preference": "any",
    "weight_distance": "1",
    "weight_slope": "1",
    "weight_surface": "1",
    "weight_width": "1",
    "weight_ramp": "1",
    "weight_uncertainty": "1",
}


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


@profiles_bp.get("/profile")
@login_required
def profile_page():
    return _render_profile()


@profiles_bp.get("/profile/<int:profile_id>/edit")
@login_required
def edit_page(profile_id):
    try:
        profile = get_owned_profile(current_user, profile_id)
    except ProfileError as exc:
        _abort_from_profile_error(exc)
    return _render_profile(editing_id=profile.id, form=_form_from_profile(profile))


@profiles_bp.post("/profile")
@login_required
def create_page():
    payload = _form_payload(request.form)
    try:
        create_profile(current_user, payload)
    except ProfileError as exc:
        _abort_from_profile_error(exc)
        return _render_profile(form=_display_form(payload), errors=exc.fields), exc.status_code
    return redirect(url_for("profiles.profile_page"))


@profiles_bp.post("/profile/<int:profile_id>/update")
@login_required
def update_page(profile_id):
    payload = _form_payload(request.form)
    try:
        update_profile(current_user, profile_id, payload)
    except ProfileError as exc:
        _abort_from_profile_error(exc)
        return (
            _render_profile(
                editing_id=profile_id,
                form=_display_form(payload),
                errors=exc.fields,
            ),
            exc.status_code,
        )
    return redirect(url_for("profiles.profile_page"))


@profiles_bp.post("/profile/<int:profile_id>/delete")
@login_required
def delete_page(profile_id):
    try:
        delete_profile(current_user, profile_id)
    except ProfileError as exc:
        _abort_from_profile_error(exc)
    return redirect(url_for("profiles.profile_page"))


@profiles_bp.post("/profile/<int:profile_id>/default")
@login_required
def default_page(profile_id):
    try:
        set_default(current_user, profile_id)
    except ProfileError as exc:
        _abort_from_profile_error(exc)
    return redirect(url_for("profiles.profile_page"))


@profiles_bp.post("/profile/<int:profile_id>/copy")
@login_required
def copy_page(profile_id):
    try:
        profile = create_profile(current_user, {"copy_from": profile_id})
    except ProfileError as exc:
        _abort_from_profile_error(exc)
    return redirect(url_for("profiles.edit_page", profile_id=profile.id))


def _render_profile(editing_id=None, form=None, errors=None):
    presets, own = list_profiles(current_user)
    active = next(
        (item for item in (*presets, *own) if item.id == current_user.default_profile_id),
        None,
    )
    return render_template(
        "profile.html",
        presets=[profile_payload(item, current_user) for item in presets],
        profiles=[profile_payload(item, current_user) for item in own],
        active=None if active is None else profile_payload(active, current_user),
        editing_id=editing_id,
        form=BLANK_FORM if form is None else form,
        errors=errors or {},
    )


def _abort_from_profile_error(exc):
    if exc.status_code in {403, 404}:
        abort(exc.status_code)


def _form_payload(form):
    data = {
        key: form.get(key)
        for key in form
        if key not in {"csrf_token", "next"} and key not in CHECKBOXES
    }
    for key in CHECKBOXES:
        selected = form.getlist(key)
        data[key] = "true" if any(item in {"true", "on", "yes"} for item in selected) else "false"
    return data


def _display_form(payload):
    display = dict(payload)
    for key in CHECKBOXES:
        display[key] = payload.get(key) == "true"
    return display


def _form_from_profile(profile):
    form = {
        "name": profile.name,
        "profile_type": profile.profile_type,
        "max_slope_degrees": _number_text(profile.max_slope_degrees),
        "min_width_m": _number_text(profile.min_width_m),
        "avoid_stairs": profile.avoid_stairs,
        "block_on_verified_obstacles": profile.block_on_verified_obstacles,
        "exclude_unknown": profile.exclude_unknown,
        "walking_speed_mps": _number_text(profile.walking_speed_mps),
        "surface_preference": profile.surface_preference,
    }
    for key, value in profile.weights.items():
        form[f"weight_{key}"] = _number_text(value)
    return form


def _number_text(value):
    if value is None:
        return ""
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}"


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
