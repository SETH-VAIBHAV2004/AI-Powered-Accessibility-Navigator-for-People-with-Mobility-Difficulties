def test_security_headers(client):
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "geolocation=(self)" in response.headers["Permissions-Policy"]
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_on_https(client):
    response = client.get("/api/health", base_url="https://localhost")
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
