import json
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.profile_presets import WEIGHT_KEYS


class MobilityProfile(db.Model):
    __tablename__ = "mobility_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(80))
    profile_type: Mapped[str] = mapped_column(String(32))
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    max_slope_degrees: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_width_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    avoid_stairs: Mapped[bool] = mapped_column(Boolean, default=False)
    block_on_verified_obstacles: Mapped[bool] = mapped_column(Boolean, default=True)
    exclude_unknown: Mapped[bool] = mapped_column(Boolean, default=False)
    walking_speed_mps: Mapped[float] = mapped_column(Float)
    surface_preference: Mapped[str] = mapped_column(String(16), default="any")
    weights_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    @property
    def weights(self):
        stored = json.loads(self.weights_json)
        return {key: stored[key] for key in WEIGHT_KEYS}

    @weights.setter
    def weights(self, value):
        self.weights_json = json.dumps(
            {key: value[key] for key in WEIGHT_KEYS},
            sort_keys=True,
            separators=(",", ":"),
        )

    def to_public_dict(self, in_use=False):
        return {
            "id": self.id,
            "name": self.name,
            "profile_type": self.profile_type,
            "is_preset": self.is_preset,
            "in_use": in_use,
            "max_slope_degrees": self.max_slope_degrees,
            "min_width_m": self.min_width_m,
            "avoid_stairs": self.avoid_stairs,
            "block_on_verified_obstacles": self.block_on_verified_obstacles,
            "exclude_unknown": self.exclude_unknown,
            "walking_speed_mps": self.walking_speed_mps,
            "surface_preference": self.surface_preference,
            "weights": self.weights,
            "summary": describe_limits(self),
        }


def describe_limits(profile):
    slope = (
        "no maximum slope"
        if profile.max_slope_degrees is None
        else f"slope limited to {profile.max_slope_degrees:g} degrees"
    )
    width = (
        "no minimum width"
        if profile.min_width_m is None
        else f"width at least {profile.min_width_m:g} m"
    )
    stairs = "stairs are removed" if profile.avoid_stairs else "stairs are kept"
    obstacles = (
        "verified obstacles block the path"
        if profile.block_on_verified_obstacles
        else "verified obstacles do not block the path"
    )
    unknown = (
        "unknown stairs, width, or slope are removed"
        if profile.exclude_unknown
        else "unknown details stay available and are marked unknown"
    )
    return f"{stairs}; {slope}; {width}; {obstacles}; {unknown}."
