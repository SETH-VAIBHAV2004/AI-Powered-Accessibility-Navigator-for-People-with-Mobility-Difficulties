import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.mobility_profile import MobilityProfile
from app.services.accounts import register_user
from app.services.profiles import (
    ProfileError,
    create_profile,
    delete_profile,
    list_profiles,
    set_default,
    update_profile,
)


def test_presets_are_seeded(app):
    with app.app_context():
        presets = db.session.scalars(
            select(MobilityProfile).where(MobilityProfile.is_preset.is_(True))
        ).all()
    names = {profile.name for profile in presets}
    assert names == {"Wheelchair", "Limited mobility", "General"}
    wheelchair = next(profile for profile in presets if profile.name == "Wheelchair")
    assert wheelchair.avoid_stairs is True
    assert wheelchair.min_width_m == pytest.approx(0.9)
    assert wheelchair.user_id is None
    assert "unknown details stay available" in wheelchair.to_public_dict()["summary"]


def test_personal_profile_can_be_selected_and_removed(app):
    with app.app_context():
        user = register_user("Asha Rao", "asha@university.edu", "a-long-password")
        created = create_profile(
            user,
            {
                "name": "Campus chair",
                "profile_type": "custom",
                "max_slope_degrees": "5",
                "min_width_m": "",
                "avoid_stairs": True,
                "block_on_verified_obstacles": True,
                "exclude_unknown": False,
                "walking_speed_mps": "0.9",
                "surface_preference": "firm",
                "weight_distance": "1",
                "weight_slope": "2",
                "weight_surface": "1",
                "weight_width": "1",
                "weight_ramp": "1",
                "weight_uncertainty": "1",
            },
        )
        set_default(user, created.id)
        assert user.default_profile_id == created.id
        presets, own = list_profiles(user)
        assert len(presets) == 3
        assert [profile.name for profile in own] == ["Campus chair"]
        delete_profile(user, created.id)
        assert user.default_profile_id is None
        assert db.session.get(MobilityProfile, created.id) is None


def test_preset_cannot_be_edited_and_can_be_copied(app):
    with app.app_context():
        user = register_user("Asha Rao", "asha@university.edu", "a-long-password")
        preset = db.session.scalar(
            select(MobilityProfile).where(MobilityProfile.name == "Wheelchair")
        )
        with pytest.raises(ProfileError) as caught:
            update_profile(user, preset.id, {"name": "Changed"})
        assert caught.value.status_code == 403
        copy = create_profile(user, {"copy_from": preset.id})
        assert copy.is_preset is False
        assert copy.user_id == user.id
        assert copy.avoid_stairs is True
        assert copy.name == "Wheelchair copy"
        copy = update_profile(user, copy.id, {"avoid_stairs": False, "name": "My route"})
        assert copy.avoid_stairs is False
        assert copy.name == "My route"


def test_another_users_profile_is_hidden(app):
    with app.app_context():
        owner = register_user("Asha Rao", "asha@university.edu", "a-long-password")
        other = register_user("Other Person", "other@university.edu", "a-long-password")
        created = create_profile(owner, _custom_payload())
        with pytest.raises(ProfileError) as caught:
            set_default(other, created.id)
        assert caught.value.status_code == 404


def test_limits_and_weights_are_validated(app):
    with app.app_context():
        user = register_user("Asha Rao", "asha@university.edu", "a-long-password")
        payload = _custom_payload()
        payload["max_slope_degrees"] = "40"
        payload["weight_slope"] = "-1"
        with pytest.raises(ProfileError) as caught:
            create_profile(user, payload)
        assert "max_slope_degrees" in caught.value.fields
        assert "weight_slope" in caught.value.fields


def _custom_payload():
    return {
        "name": "Campus chair",
        "profile_type": "custom",
        "max_slope_degrees": "5",
        "min_width_m": "",
        "avoid_stairs": True,
        "block_on_verified_obstacles": False,
        "exclude_unknown": True,
        "walking_speed_mps": "0.9",
        "surface_preference": "any",
        "weight_distance": "1",
        "weight_slope": "2",
        "weight_surface": "1",
        "weight_width": "0",
        "weight_ramp": "1",
        "weight_uncertainty": "1",
    }
