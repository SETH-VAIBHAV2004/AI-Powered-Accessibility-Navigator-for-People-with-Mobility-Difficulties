from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from app.profile_presets import PRESETS, weights_document

revision = "0002_mobility_profiles"
down_revision = "0001_users"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "mobility_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("profile_type", sa.String(length=32), nullable=False),
        sa.Column("is_preset", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_slope_degrees", sa.Float(), nullable=True),
        sa.Column("min_width_m", sa.Float(), nullable=True),
        sa.Column("avoid_stairs", sa.Boolean(), nullable=False),
        sa.Column("block_on_verified_obstacles", sa.Boolean(), nullable=False),
        sa.Column("exclude_unknown", sa.Boolean(), nullable=False),
        sa.Column("walking_speed_mps", sa.Float(), nullable=False),
        sa.Column("surface_preference", sa.String(length=16), nullable=False),
        sa.Column("weights_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "profile_type IN ('wheelchair', 'limited_mobility', 'general', 'custom')",
            name="ck_mobility_profiles_type",
        ),
        sa.CheckConstraint(
            "surface_preference IN ('any', 'paved', 'firm')",
            name="ck_mobility_profiles_surface",
        ),
        sa.CheckConstraint(
            "(is_preset = 1 AND user_id IS NULL) OR (is_preset = 0 AND user_id IS NOT NULL)",
            name="ck_mobility_profiles_owner",
        ),
    )
    op.create_index("ix_mobility_profiles_user_id", "mobility_profiles", ["user_id"])
    now = datetime.now(UTC)
    op.bulk_insert(
        sa.table(
            "mobility_profiles",
            sa.column("user_id", sa.Integer()),
            sa.column("name", sa.String()),
            sa.column("profile_type", sa.String()),
            sa.column("is_preset", sa.Boolean()),
            sa.column("max_slope_degrees", sa.Float()),
            sa.column("min_width_m", sa.Float()),
            sa.column("avoid_stairs", sa.Boolean()),
            sa.column("block_on_verified_obstacles", sa.Boolean()),
            sa.column("exclude_unknown", sa.Boolean()),
            sa.column("walking_speed_mps", sa.Float()),
            sa.column("surface_preference", sa.String()),
            sa.column("weights_json", sa.Text()),
            sa.column("created_at", sa.DateTime()),
            sa.column("updated_at", sa.DateTime()),
        ),
        [
            {
                "user_id": None,
                "name": preset["name"],
                "profile_type": preset["profile_type"],
                "is_preset": True,
                "max_slope_degrees": preset["max_slope_degrees"],
                "min_width_m": preset["min_width_m"],
                "avoid_stairs": preset["avoid_stairs"],
                "block_on_verified_obstacles": preset["block_on_verified_obstacles"],
                "exclude_unknown": preset["exclude_unknown"],
                "walking_speed_mps": preset["walking_speed_mps"],
                "surface_preference": preset["surface_preference"],
                "weights_json": weights_document(preset["weights"]),
                "created_at": now,
                "updated_at": now,
            }
            for preset in PRESETS
        ],
    )
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("default_profile_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_users_default_profile_id",
            "mobility_profiles",
            ["default_profile_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_default_profile_id", type_="foreignkey")
        batch.drop_column("default_profile_id")
    op.drop_index("ix_mobility_profiles_user_id", table_name="mobility_profiles")
    op.drop_table("mobility_profiles")
