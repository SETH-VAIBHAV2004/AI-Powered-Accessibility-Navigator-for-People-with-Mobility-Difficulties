import re


def test_sign_in_page_uses_local_assets_and_labels(client):
    response = client.get("/login")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'for="email"' in html
    assert 'id="email"' in html
    assert 'for="password"' in html
    assert "bootstrap.min.css" in html
    assert "css/app.css" in html
    assert "fonts.googleapis.com" not in html
    assert "cdn.jsdelivr.net" not in html
    assert "unpkg.com" not in html
    stylesheet = client.get("/static/css/app.css")
    assert b"min-height: 44px" in stylesheet.data
    font = client.get("/static/fonts/source-sans-3-latin-400.woff2")
    assert font.status_code == 200
    assert font.data[:4] == b"wOF2"


def test_registration_signs_in_and_shows_the_account(client):
    token = _token(client, "/register")
    response = client.post(
        "/register",
        data={
            "csrf_token": token,
            "name": "Asha Rao",
            "email": "asha@university.edu",
            "password": "a-long-password",
        },
        follow_redirects=True,
    )
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Hello, Asha Rao" in page
    assert "Account type: User" in page
    assert "not a guarantee" in page


def test_wrong_password_stays_on_the_form(client):
    token = _token(client, "/login")
    response = client.post(
        "/login",
        data={
            "csrf_token": token,
            "email": "asha@university.edu",
            "password": "wrong-password",
        },
    )
    assert response.status_code == 400
    page = response.get_data(as_text=True).lower()
    assert page.count("email or password is incorrect") == 1


def test_external_next_is_ignored(client):
    token = _token(client, "/register")
    client.post(
        "/register",
        data={
            "csrf_token": token,
            "name": "Asha Rao",
            "email": "asha@university.edu",
            "password": "a-long-password",
        },
    )
    client.post("/logout", data={"csrf_token": _token(client, "/")})
    login_token = _token(client, "/login")
    response = client.post(
        "/login",
        data={
            "csrf_token": login_token,
            "email": "asha@university.edu",
            "password": "a-long-password",
            "next": "https://evil.example/phish",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.location.endswith("/")
    assert "evil.example" not in response.location


def test_sign_out_returns_to_the_sign_in_page(client):
    token = _token(client, "/register")
    client.post(
        "/register",
        data={
            "csrf_token": token,
            "name": "Asha Rao",
            "email": "asha@university.edu",
            "password": "a-long-password",
        },
        follow_redirects=True,
    )
    response = client.post(
        "/logout",
        data={"csrf_token": _token(client, "/")},
        follow_redirects=True,
    )
    assert "Sign in" in response.get_data(as_text=True)
    assert "Hello, Asha Rao" not in response.get_data(as_text=True)


def test_html_and_api_not_found(client):
    page = client.get("/missing-page")
    assert page.status_code == 404
    assert "text/html" in page.content_type
    assert "Page not found" in page.get_data(as_text=True)
    api = client.get("/api/missing")
    assert api.status_code == 404
    assert api.get_json() == {"error": "not_found"}


def test_form_without_csrf_explains_the_failure(client):
    response = client.post(
        "/login",
        data={"email": "asha@university.edu", "password": "a-long-password"},
    )
    assert response.status_code == 400
    assert "Form expired" in response.get_data(as_text=True)


def _token(client, path):
    html = client.get(path).get_data(as_text=True)
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match is not None
    return match.group(1)
