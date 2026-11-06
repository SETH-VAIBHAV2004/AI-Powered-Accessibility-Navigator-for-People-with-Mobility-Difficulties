import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.user import ROLE_USER, User

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DUMMY_PASSWORD_HASH = generate_password_hash("not-a-real-password", method="scrypt")


class AccountError(Exception):
    def __init__(self, fields, status_code=400):
        self.fields = fields
        self.status_code = status_code
        super().__init__("invalid account")


def validate_new_account(name, email, password):
    errors = {}
    clean_name = name.strip() if isinstance(name, str) else ""
    clean_email = email.strip().lower() if isinstance(email, str) else ""

    if not clean_name or len(clean_name) > 120 or _has_control_character(clean_name):
        errors["name"] = "Enter a name using 1 to 120 characters."
    if (
        not clean_email
        or len(clean_email) > 254
        or _has_control_character(clean_email)
        or EMAIL_PATTERN.fullmatch(clean_email) is None
    ):
        errors["email"] = "Enter a valid email address."
    if not isinstance(password, str) or not 10 <= len(password) <= 128:
        errors["password"] = "Use a password between 10 and 128 characters."
    elif clean_email and password.lower() == clean_email:
        errors["password"] = "Use a password that is different from your email."
    return clean_name, clean_email, errors


def register_user(name, email, password):
    clean_name, clean_email, errors = validate_new_account(name, email, password)
    if errors:
        raise AccountError(errors)
    if _email_taken(clean_email):
        raise AccountError({"email": "An account with this email already exists."}, 409)

    user = User(name=clean_name, email=clean_email, role=ROLE_USER, is_active=True)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AccountError({"email": "An account with this email already exists."}, 409) from None
    return user


def authenticate(email, password):
    clean_email = email.strip().lower() if isinstance(email, str) else ""
    candidate = password if isinstance(password, str) and len(password) <= 128 else ""
    user = db.session.scalar(select(User).where(User.email == clean_email))
    if user is None:
        check_password_hash(DUMMY_PASSWORD_HASH, candidate or "x")
        return None
    if not user.is_active or not user.check_password(candidate):
        return None
    return user


def _email_taken(email):
    return db.session.scalar(select(User.id).where(User.email == email)) is not None


def _has_control_character(value):
    return any(ord(character) < 32 for character in value)
