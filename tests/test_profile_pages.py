import re


def test_profile_page_requires_sign_in(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.location


def test_profile_page_lists_presets_and_saves_a_profile(client):
    _register(client)
    page = client.get("/profile")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "Wheelchair" in html
    assert "Limited mobility" in html
    assert "General" in html
    assert "not a universal standard" in html
    assert "In use:" in html

    token = _token(html)
    saved = client.post(
        "/profile",
        data={
            "csrf_token": token,
            "name": "Campus chair",
            "profile_type": "custom",
            "max_slope_degrees": "5",
            "min_width_m": "",
            "avoid_stairs": "true",
            "block_on_verified_obstacles": "true",
            "exclude_unknown": "false",
            "walking_speed_mps": "0.9",
            "surface_preference": "firm",
            "weight_distance": "1",
            "weight_slope": "2",
            "weight_surface": "1",
            "weight_width": "1",
            "weight_ramp": "1",
            "weight_uncertainty": "1",
        },
        follow_redirects=True,
    )
    saved_html = saved.get_data(as_text=True)
    assert "Campus chair" in saved_html
    assert "stairs are removed" in saved_html


def test_using_a_preset_marks_it_in_use(client):
    _register(client)
    html = client.get("/profile").get_data(as_text=True)
    action = re.search(r'action="(/profile/\d+/default)"', html).group(1)
    response = client.post(action, data={"csrf_token": _token(html)}, follow_redirects=True)
    page = response.get_data(as_text=True)
    assert "In use" in page
    assert "Wheelchair" in page


def test_editing_a_preset_is_refused(client):
    _register(client)
    html = client.get("/profile").get_data(as_text=True)
    preset_id = re.search(r"/profile/(\d+)/default", html).group(1)
    response = client.get(f"/profile/{preset_id}/edit")
    assert response.status_code == 403


def _register(client):
    html = client.get("/register").get_data(as_text=True)
    client.post(
        "/register",
        data={
            "csrf_token": _token(html),
            "name": "Asha Rao",
            "email": "asha@university.edu",
            "password": "a-long-password",
        },
        follow_redirects=True,
    )


def _token(html):
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)
