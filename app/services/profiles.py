from datetime import UTC, datetime

from sqlalchemy import select

from app.extensions import db
from app.models.mobility_profile import MobilityProfile
from app.profile_presets import PROFILE_TYPES, SURFACE_PREFERENCES, WEIGHT_KEYS


class ProfileError(Exception):
    def __init__(self, fields, status_code=400):
        self.fields = fields
        self.status_code = status_code
        super().__init__("invalid profile")


def list_profiles(user):
    presets = db.session.scalars(
        select(MobilityProfile)
        .where(MobilityProfile.is_preset.is_(True))
        .order_by(MobilityProfile.id)
    ).all()
    own = db.session.scalars(
        select(MobilityProfile)
        .where(MobilityProfile.user_id == user.id)
        .order_by(MobilityProfile.name, MobilityProfile.id)
    ).all()
    return presets, own


def create_profile(user, payload):
    source = _copy_source(user, payload.get("copy_from"))
    cleaned = _clean_payload(payload, source)
    profile = MobilityProfile(user_id=user.id, is_preset=False, **cleaned)
    now = datetime.now(UTC)
    profile.created_at = now
    profile.updated_at = now
    db.session.add(profile)
    db.session.commit()
    return profile


def get_owned_profile(user, profile_id):
    return _owned_profile(user, profile_id)


def update_profile(user, profile_id, payload):
    profile = _owned_profile(user, profile_id)
    cleaned = _clean_payload(payload, profile)
    for key, value in cleaned.items():
        setattr(profile, key, value)
    profile.updated_at = datetime.now(UTC)
    db.session.commit()
    return profile


def delete_profile(user, profile_id):
    profile = _owned_profile(user, profile_id)
    if user.default_profile_id == profile.id:
        user.default_profile_id = None
    db.session.delete(profile)
    db.session.commit()


def set_default(user, profile_id):
    profile = _visible_profile(user, profile_id)
    user.default_profile_id = profile.id
    db.session.commit()
    return profile


def profile_payload(profile, user):
    return profile.to_public_dict(in_use=user.default_profile_id == profile.id)


def _copy_source(user, raw_id):
    if raw_id in (None, ""):
        return None
    return _visible_profile(user, raw_id)


def _visible_profile(user, raw_id):
    profile_id = _parse_id(raw_id)
    profile = db.session.get(MobilityProfile, profile_id)
    if profile is None or not (profile.is_preset or profile.user_id == user.id):
        raise ProfileError({"profile": "That profile was not found."}, 404)
    return profile


def _owned_profile(user, raw_id):
    profile = _visible_profile(user, raw_id)
    if profile.is_preset:
        raise ProfileError(
            {"profile": "Starting points cannot be edited. Copy one into your own profile."},
            403,
        )
    return profile


def _parse_id(raw_id):
    try:
        profile_id = int(raw_id)
    except (TypeError, ValueError) as exc:
        raise ProfileError({"profile": "That profile was not found."}, 404) from exc
    if profile_id < 1:
        raise ProfileError({"profile": "That profile was not found."}, 404)
    return profile_id


def _clean_payload(payload, source):
    if not isinstance(payload, dict):
        raise ProfileError({"profile": "The profile details are missing."})
    errors = {}
    if "name" not in payload and source is not None:
        name = f"{source.name} copy"
    else:
        name = _text(payload.get("name"))
    if not name or len(name) > 80 or _has_control_character(name):
        errors["name"] = "Enter a name using 1 to 80 characters."

    profile_type = _text(payload.get("profile_type"))
    if not profile_type:
        profile_type = source.profile_type if source is not None else "custom"
    if profile_type not in PROFILE_TYPES:
        errors["profile_type"] = "Choose a profile type."

    slope, slope_error = _optional_number(
        payload.get("max_slope_degrees", _missing(source, "max_slope_degrees")),
        "Maximum slope",
        0,
        20,
    )
    if slope_error:
        errors["max_slope_degrees"] = slope_error
    width, width_error = _optional_number(
        payload.get("min_width_m", _missing(source, "min_width_m")),
        "Minimum width",
        0.5,
        3,
    )
    if width_error:
        errors["min_width_m"] = width_error

    speed, speed_error = _required_number(
        payload.get("walking_speed_mps", _missing(source, "walking_speed_mps")),
        "Walking speed",
        0.3,
        2,
    )
    if speed_error:
        errors["walking_speed_mps"] = speed_error

    surface = _text(payload.get("surface_preference")) or (
        source.surface_preference if source else "any"
    )
    if surface not in SURFACE_PREFERENCES:
        errors["surface_preference"] = "Choose a surface preference."

    weights, weight_errors = _weights(payload, source)
    errors.update(weight_errors)
    if errors:
        raise ProfileError(errors)

    return {
        "name": name,
        "profile_type": profile_type,
        "max_slope_degrees": slope,
        "min_width_m": width,
        "avoid_stairs": _field_bool(payload, "avoid_stairs", source, False),
        "block_on_verified_obstacles": _field_bool(
            payload, "block_on_verified_obstacles", source, True
        ),
        "exclude_unknown": _field_bool(payload, "exclude_unknown", source, False),
        "walking_speed_mps": speed,
        "surface_preference": surface,
        "weights": weights,
    }


def _weights(payload, source):
    errors = {}
    supplied = payload.get("weights")
    if supplied is None and source is not None and not any(
        key in payload for key in _weight_fields()
    ):
        return dict(source.weights), errors
    if isinstance(supplied, dict):
        raw = supplied
    else:
        raw = {key: payload.get(f"weight_{key}", _missing(source, None)) for key in WEIGHT_KEYS}
        if source is not None:
            for key in WEIGHT_KEYS:
                field = f"weight_{key}"
                if field not in payload and key not in (supplied or {}):
                    raw[key] = source.weights[key]
    cleaned = {}
    for key in WEIGHT_KEYS:
        number, error = _required_number(raw.get(key), f"{key.capitalize()} weight", 0, 20)
        if error:
            errors[f"weight_{key}"] = error
        else:
            cleaned[key] = number
    return cleaned, errors


def _weight_fields():
    return {f"weight_{key}" for key in WEIGHT_KEYS}


def _missing(source, attribute):
    if source is None or attribute is None:
        return None
    return getattr(source, attribute)


def _optional_number(value, label, low, high):
    if value is None or value == "":
        return None, None
    return _number_in_range(value, label, low, high, required=False)


def _required_number(value, label, low, high):
    if value is None or value == "":
        return None, f"Enter a {label.lower()}."
    return _number_in_range(value, label, low, high, required=True)


def _number_in_range(value, label, low, high, required):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label} must be a number."
    if number != number or number in (float("inf"), float("-inf")):
        return None, f"{label} must be a number."
    if not low <= number <= high:
        return None, f"{label} must be between {low:g} and {high:g}."
    if not required and number == "":
        return None, None
    return number, None


def _field_bool(payload, key, source, blank_default):
    if key not in payload or payload[key] is None:
        if source is not None:
            return bool(getattr(source, key))
        return blank_default
    return _bool(payload[key], blank_default)


def _bool(value, default):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "on", "yes"}
    return bool(value)


def _text(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        return ""
    return value.strip()


def _has_control_character(value):
    return any(ord(character) < 32 for character in value)


def load_default_profile(user):
    if user.default_profile_id is None:
        return None
    profile = db.session.get(MobilityProfile, user.default_profile_id)
    if profile is None or not (profile.is_preset or profile.user_id == user.id):
        user.default_profile_id = None
        db.session.commit()
        return None
    return profile

