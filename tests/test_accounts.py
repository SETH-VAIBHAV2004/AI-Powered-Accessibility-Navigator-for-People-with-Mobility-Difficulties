import pytest
from sqlalchemy import func, inspect, select

from app.extensions import db
from app.models.user import ROLE_USER, User
from app.services.accounts import AccountError, authenticate, register_user


def test_migration_creates_users(app):
    with app.app_context():
        tables = inspect(db.engine).get_table_names()
    assert "users" in tables


def test_register_stores_a_user_and_hashes_the_password(app):
    with app.app_context():
        user = register_user("Asha Rao", "Asha@University.edu", "a-long-password")
        stored = db.session.get(User, user.id)
        assert stored.email == "asha@university.edu"
        assert stored.role == ROLE_USER
        assert stored.password_hash != "a-long-password"
        assert stored.check_password("a-long-password")
        assert "password" not in stored.to_public_dict()


def test_duplicate_email_is_rejected(app):
    with app.app_context():
        register_user("Asha Rao", "asha@university.edu", "a-long-password")
        with pytest.raises(AccountError):
            register_user("Other Person", "ASHA@university.edu", "another-long-password")
        count = db.session.scalar(select(func.count()).select_from(User))
    assert count == 1


def test_short_password_and_control_character_are_rejected(app):
    with app.app_context():
        with pytest.raises(AccountError) as caught:
            register_user("Asha", "asha@university.edu", "short")
        assert "password" in caught.value.fields
        with pytest.raises(AccountError) as caught_name:
            register_user("Asha\nRao", "asha@university.edu", "a-long-password")
        assert "name" in caught_name.value.fields


def test_inactive_user_cannot_authenticate(app):
    with app.app_context():
        user = register_user("Asha Rao", "asha@university.edu", "a-long-password")
        user.is_active = False
        db.session.commit()
        assert authenticate("asha@university.edu", "a-long-password") is None
        assert authenticate("missing@university.edu", "a-long-password") is None
