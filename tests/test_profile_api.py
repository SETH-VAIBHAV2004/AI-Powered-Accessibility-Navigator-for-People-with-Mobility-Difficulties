def test_profile_api_creates_selects_and_rejects_presets(client, csrf):
    _register(client, csrf)
    listed = client.get("/api/profiles")
    assert listed.status_code == 200
    body = listed.get_json()
    assert [item["name"] for item in body["presets"]] == [
        "Wheelchair",
        "Limited mobility",
        "General",
    ]
    wheelchair = body["presets"][0]
    assert wheelchair["is_preset"] is True

    created = client.post("/api/profiles", json=_payload(), headers=csrf())
    assert created.status_code == 201
    profile_id = created.get_json()["profile"]["id"]

    selected = client.post(f"/api/profiles/{wheelchair['id']}/default", headers=csrf())
    assert selected.status_code == 200
    assert selected.get_json()["profile"]["in_use"] is True
    assert client.get("/api/profiles").get_json()["default_profile_id"] == wheelchair["id"]

    blocked = client.put(
        f"/api/profiles/{wheelchair['id']}",
        json={"name": "Changed"},
        headers=csrf(),
    )
    assert blocked.status_code == 403

    removed = client.delete(f"/api/profiles/{profile_id}", headers=csrf())
    assert removed.status_code == 200
    names = [item["name"] for item in client.get("/api/profiles").get_json()["profiles"]]
    assert names == []


def test_profile_api_requires_sign_in_and_hides_other_profiles(client, csrf):
    assert client.get("/api/profiles").status_code == 401
    _register(client, csrf, email="asha@university.edu")
    created = client.post("/api/profiles", json=_payload(), headers=csrf())
    profile_id = created.get_json()["profile"]["id"]
    client.post("/api/auth/logout", headers=csrf())
    _register(client, csrf, email="other@university.edu")
    hidden = client.put(f"/api/profiles/{profile_id}", json={"name": "Taken"}, headers=csrf())
    assert hidden.status_code == 404


def test_profile_api_reports_field_errors(client, csrf):
    _register(client, csrf)
    payload = _payload()
    payload["walking_speed_mps"] = "9"
    response = client.post("/api/profiles", json=payload, headers=csrf())
    assert response.status_code == 400
    assert "walking_speed_mps" in response.get_json()["fields"]


def _register(client, csrf, email="asha@university.edu"):
    response = client.post(
        "/api/auth/register",
        json={"name": "Asha Rao", "email": email, "password": "a-long-password"},
        headers=csrf(),
    )
    assert response.status_code == 201
    return response


def _payload():
    return {
        "name": "Campus chair",
        "profile_type": "custom",
        "max_slope_degrees": 5,
        "min_width_m": None,
        "avoid_stairs": True,
        "block_on_verified_obstacles": True,
        "exclude_unknown": False,
        "walking_speed_mps": 0.9,
        "surface_preference": "firm",
        "weights": {
            "distance": 1,
            "slope": 2,
            "surface": 1,
            "width": 1,
            "ramp": 1,
            "uncertainty": 1,
        },
    }
