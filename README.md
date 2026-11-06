# AI-Powered Accessibility Navigator

A web application that recommends pedestrian routes for wheelchair users, older people, and anyone whose walk needs to avoid stairs, steep slopes, narrow paths, or blocked ways.

A recommended route is a suggestion from mapped and reported data. It is not a statement that the route is safe or fully accessible. Missing attributes stay unknown.

## Where it works

There is no fixed campus. Each journey loads pedestrian ways for a corridor around the start and the destination, expanded north, south, east, and west by `BBOX_MARGIN_METRES`. One Overpass query cannot span more than `MAX_BBOX_SPAN_DEGREES` (default 0.15°, about 16 km) on either axis. A longer trip is loaded as successive bounded queries along that corridor. The default area cap is a usage limit for the public Overpass service, not a geographic restriction.

## Interface

The product is a navigation tool, not a brochure.

- The map fills the viewport. Search, profile, and route detail sit in a side panel on a wide screen and in a bottom sheet on a narrow screen.
- Chrome uses stone neutrals (`#1c1917` ink, `#f7f6f3` paper, `#ffffff` panels) and one blue accent (`#1d4e89`) for the primary action and the selected route.
- Type is Source Sans 3, self-hosted, with Segoe UI as the fallback. Base size is 16px. Bootstrap is the component base and is restyled; the default Bootstrap theme is not the look of this app.
- Confidence, warnings, and status use text and a line pattern (solid, dashed, or dotted). Colour is an extra cue.
- Touch targets are at least 44px. Focus is a visible 2px ring. Motion is limited to map movement and panel open/close.
- Leaflet and the typeface are served by this app. OpenStreetMap tiles stay on the OpenStreetMap tile host, with the required attribution.
- Admin screens are tables with filters and written status, not a wall of statistic cards.

Sign-in, registration, and the signed-in home screen are in place. The map, mobility profiles, and reports follow.

## What is included

The Flask application factory, configuration, JSON logging, CSRF, rate limiting, security headers, `GET /api/health`, Docker, Nginx, and CI. Accounts use server-side sessions. Registration creates a user. The first administrator is created with a command, not a public form. Pathway data and routing are not in this revision.

## Local setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```

Edit `.env`. Set `SECRET_KEY` to a long random string and `OSM_USER_AGENT` to a description that includes a contact address you control.

```powershell
$env:APP_ENV = "development"
python -m flask --app wsgi:app db upgrade
python -m flask --app wsgi:app run
```

Open `http://127.0.0.1:5000/`. Health check: `http://127.0.0.1:5000/api/health`.

Development stores SQLite at `instance/dev.db`. Tests apply the Alembic migrations to a temporary database. Production uses MySQL, and the container runs `flask db upgrade` before Gunicorn starts.

Create the first administrator in the same environment as the app. The password is read from the environment so it is not stored in the shell history as a command argument.

```powershell
$env:ADMIN_NAME = "Campus Admin"
$env:ADMIN_EMAIL = "admin@university.edu"
$env:ADMIN_PASSWORD = "a-long-password"
python -m flask --app wsgi:app create-admin
```

The command refuses to change the role of an email that already has an account. Passwords are stored with scrypt. A new password must be 10 to 128 characters. Sign-in failures use one message for an unknown email, a wrong password, and a deactivated account.

```powershell
ruff check .
pytest
```

## Docker

Create `.env` from `.env.example` with production values: `APP_ENV=production`, a `SECRET_KEY` of at least 32 characters, a real `OSM_USER_AGENT`, and the MySQL passwords. Compose builds `DATABASE_URL` for the app container.

```powershell
docker compose up --build
```

The site is published on port 8080. The app container applies database migrations, then Nginx proxies to Gunicorn. MySQL data is the named volume `mysql_data`. Run `create-admin` inside the app container, with `ADMIN_NAME`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` set for that one command.

TLS is expected in front of this stack (the host reverse proxy or a load balancer). The app sends HSTS only when the forwarded request is HTTPS. Set `TRUST_PROXY=1` only for that proxy, which Compose already does for the bundled Nginx.

Rate limits use in-process memory unless `RATELIMIT_STORAGE_URI` points at Redis. Run one Gunicorn worker, or add Redis, before relying on the limit under more than one worker.

## Operations

- Liveness: `GET /api/health` returns `200` with `{"status":"ok","database":"ok"}`. A database failure returns `503` and a log line, without the driver error in the response.
- Logs are JSON on stdout.
- Secrets stay in the environment. `.env` is not part of the image context that matters for git, and it must not be committed.
- Uploads, local databases, Overpass cache, and evaluation output are gitignored.

## Nominatim and Overpass

Server-side clients (later phases) send `OSM_USER_AGENT`, wait at least one second between requests, retry with backoff, and cache. Place search runs when the user submits a search, not on each keystroke. OpenStreetMap contributors are credited on the map.
