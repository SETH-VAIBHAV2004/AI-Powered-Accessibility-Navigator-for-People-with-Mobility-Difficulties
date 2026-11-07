import json

PROFILE_TYPES = ("wheelchair", "limited_mobility", "general", "custom")
SURFACE_PREFERENCES = ("any", "paved", "firm")
WEIGHT_KEYS = ("distance", "slope", "surface", "width", "ramp", "uncertainty")

PRESETS = (
    {
        "name": "Wheelchair",
        "profile_type": "wheelchair",
        "max_slope_degrees": 4.8,
        "min_width_m": 0.9,
        "avoid_stairs": True,
        "block_on_verified_obstacles": True,
        "exclude_unknown": False,
        "walking_speed_mps": 1.0,
        "surface_preference": "firm",
        "weights": {
            "distance": 1,
            "slope": 4,
            "surface": 3,
            "width": 3,
            "ramp": 2,
            "uncertainty": 2,
        },
    },
    {
        "name": "Limited mobility",
        "profile_type": "limited_mobility",
        "max_slope_degrees": 6,
        "min_width_m": None,
        "avoid_stairs": False,
        "block_on_verified_obstacles": True,
        "exclude_unknown": False,
        "walking_speed_mps": 0.8,
        "surface_preference": "paved",
        "weights": {
            "distance": 1,
            "slope": 3,
            "surface": 3,
            "width": 1,
            "ramp": 1,
            "uncertainty": 1,
        },
    },
    {
        "name": "General",
        "profile_type": "general",
        "max_slope_degrees": None,
        "min_width_m": None,
        "avoid_stairs": False,
        "block_on_verified_obstacles": True,
        "exclude_unknown": False,
        "walking_speed_mps": 1.25,
        "surface_preference": "any",
        "weights": {
            "distance": 1,
            "slope": 0.5,
            "surface": 0.5,
            "width": 0,
            "ramp": 0,
            "uncertainty": 0.25,
        },
    },
)


def weights_document(weights):
    return json.dumps(weights, sort_keys=True, separators=(",", ":"))
