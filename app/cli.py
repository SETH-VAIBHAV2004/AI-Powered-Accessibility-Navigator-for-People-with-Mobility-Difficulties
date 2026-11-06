import os
import sys

from app.extensions import db
from app.models.user import ROLE_ADMIN
from app.services.accounts import AccountError, register_user


def register_cli(app):
    @app.cli.command("create-admin")
    def create_admin():
        """Create an administrator. Reads ADMIN_NAME, ADMIN_EMAIL, and ADMIN_PASSWORD."""
        name = os.environ.get("ADMIN_NAME")
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")
        if not name or not email or not password:
            print(
                "Set ADMIN_NAME, ADMIN_EMAIL, and ADMIN_PASSWORD, then run this command again.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        try:
            user = register_user(name, email, password)
        except AccountError as exc:
            if exc.status_code == 409:
                print(
                    "An account with this email already exists. Its role was left unchanged.",
                    file=sys.stderr,
                )
                raise SystemExit(1) from None
            for message in exc.fields.values():
                print(message, file=sys.stderr)
            raise SystemExit(2) from None
        user.role = ROLE_ADMIN
        db.session.commit()
        print(f"Administrator account created for {user.email}.")
