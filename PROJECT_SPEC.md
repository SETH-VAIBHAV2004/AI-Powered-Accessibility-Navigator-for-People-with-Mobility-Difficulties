# AI-Powered Accessibility Navigator for People with Mobility Difficulties

**Project domain:** Assistive Technology, Smart Mobility, GIS and Path Planning  
**SDG alignment:** SDG 10 – Reduced Inequalities; SDG 11 – Sustainable Cities and Communities  
**Recommended prototype area:** A college campus or a small neighborhood

## 1. Project overview

The AI-Powered Accessibility Navigator is a web-based navigation system designed to help wheelchair users, elderly people and people with limited mobility find pedestrian routes that better match their accessibility needs.

Conventional navigation systems often prioritize the shortest or fastest route. However, a short route may contain stairs, steep slopes, narrow paths, uneven surfaces or missing ramps. This project considers pathway accessibility information and individual mobility preferences before recommending a route.

The system will display an interactive map, accept a starting point and destination, calculate an accessibility-aware route, explain why the route was selected and allow users to report temporary obstacles.

**Important:** This is a prototype, not a guarantee that a route is safe or fully accessible. Map information may be incomplete or outdated. Missing accessibility information must be shown as unknown rather than assumed accessible.

## 2. Problem statement

Existing pedestrian navigation may prioritize distance or travel time without adequately representing the needs of people with mobility difficulties. Pathways can contain stairs, steep slopes, narrow sections, rough surfaces, missing ramps or temporary obstructions. Accessibility information may be incomplete or outdated. A route planner is needed that combines pathway-level accessibility attributes with individual mobility requirements and communicates uncertainty.

## 3. Aim

To design and implement a personalized accessibility-aware navigation system that uses pedestrian map data, pathway accessibility attributes and graph-based algorithms to recommend more suitable routes.

## 4. Objectives

1. Build a pedestrian pathway network for a selected campus or neighborhood.
2. Collect accessibility attributes such as stairs, ramps, slope, width, surface and kerb information.
3. Create user mobility profiles with configurable preferences and hard constraints.
4. Develop an accessibility cost function for pathway segments.
5. Implement and compare Dijkstra's and A* path-planning algorithms.
6. Display recommended routes and accessibility details on an interactive map.
7. Allow users to submit time-stamped reports about blocked or inaccessible paths.
8. Evaluate the system against distance-only routing using measurable metrics.

## 5. Intended users

- Wheelchair users.
- Elderly people who prefer gentler or shorter walking routes.
- People with temporary mobility limitations.
- Caregivers or companions planning a journey.
- Campus or facility administrators reviewing accessibility reports.

## 6. Main system workflow

1. The user opens the application and allows location access, or enters a starting point manually.
2. The user selects a destination on the map or through place search.
3. The user chooses a mobility profile or adjusts preferences.
4. The backend loads pedestrian paths and accessibility attributes.
5. The route engine applies hard constraints and calculates pathway costs.
6. The map displays a recommended route, alternatives, distance, estimated travel time and warnings.
7. The user can report a newly discovered obstacle.
8. Reports are stored with timestamps and verification status. Verified, non-expired reports can influence later route calculations.

## 7. Minimum viable product and advanced features

### Build these first

- Interactive map with start and destination selection.
- Browser current-location support with permission.
- Small pedestrian graph for the selected campus.
- Manually verified accessibility attributes.
- Personalized accessibility cost calculation.
- Dijkstra or A* route generation.
- Route display with distance and explanation.
- Basic obstacle-report form.
- Comparison with conventional shortest-path routing.

### Add later, if time permits

- Live position tracking and route recalculation.
- Crowd-sourced obstacle reports with moderation and expiry.
- Confidence labels for verified, reported and unknown data.
- Alternative route ranking.
- Image-based surface or obstacle classification.
- Voice prompts and accessible interface controls.
- Administrator dashboard and accessibility heatmap.

Build the route engine first on a small, verified network. Add advanced features only after it works.

## 8. Proposed technology stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend | HTML, CSS, JavaScript, Bootstrap | User interface |
| Interactive map | Leaflet | Map, markers and route display |
| Base map data | OpenStreetMap | Geographic map data and tiles |
| Current location | Browser Geolocation API | Device location with permission |
| Place search | Nominatim | Address/place to coordinates |
| Pedestrian data | Overpass API | Query OSM paths and tags |
| Backend | Python Flask | APIs and application logic |
| Routing graph | NetworkX | Graph representation and path algorithms |
| Algorithms | Dijkstra, A* | Route calculation |
| Database | MySQL or SQLite | Users, profiles, pathways and reports |
| Data processing | Pandas, NumPy | Cleaning and preparing pathway data |

## 9. System architecture

```text
                  WEB / MOBILE BROWSER
  ---------------------------------------------------
  Login | Mobility Profile | Map | Search | Reports
  ---------------------------------------------------
                         |
                    HTTPS / JSON
                         |
                    FLASK BACKEND
  ---------------------------------------------------
  Authentication | Route API | Accessibility API
  Geocoding Proxy | Obstacle Report API
  ---------------------------------------------------
                         |
              ACCESSIBILITY ROUTE ENGINE
  ---------------------------------------------------
  Pedestrian Graph | Constraint Filter | Cost Model
  Dijkstra / A* | Alternative Routes | Explanation
  ---------------------------------------------------
                         |
                      DATABASE
  ---------------------------------------------------
  Users | Profiles | Path Segments | Reports | Logs
  ---------------------------------------------------
                         |
                 EXTERNAL MAP SERVICES
  ---------------------------------------------------
  OpenStreetMap | Nominatim | Overpass API
  Browser Geolocation | Optional Routing Provider
  ---------------------------------------------------
```

## 10. Real-time map integrations

### Recommended integration combination

**Leaflet + OpenStreetMap tiles + browser Geolocation API + Nominatim + Overpass API + your own NetworkX route engine.**

These services perform different jobs. Leaflet displays the map; OpenStreetMap supplies geographic data; Geolocation supplies the device's position; Nominatim searches addresses; Overpass retrieves mapped features; NetworkX calculates your custom accessibility-aware route.

### 10.1 Leaflet — interactive map

Documentation: https://leafletjs.com/

Leaflet displays the map, supports zoom and pan, places start and destination markers, draws recommended and alternative routes, and shows obstacle markers. Leaflet is not a routing engine and does not determine whether a path is wheelchair accessible.

Basic example:

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<div id="map" style="height: 550px;"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  // Example centre only. Replace with your study-area coordinates.
  const map = L.map("map").setView([13.0827, 80.2707], 16);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  let startMarker = null;
  let destinationMarker = null;
  let routeLayer = null;

  map.on("click", (event) => {
    if (!startMarker) {
      startMarker = L.marker(event.latlng).addTo(map)
        .bindPopup("Starting point");
    } else if (!destinationMarker) {
      destinationMarker = L.marker(event.latlng).addTo(map)
        .bindPopup("Destination");
    }
  });

  function displayRoute(latLngs) {
    if (routeLayer) map.removeLayer(routeLayer);
    routeLayer = L.polyline(latLngs, {
      color: "blue",
      weight: 6
    }).addTo(map);
    map.fitBounds(routeLayer.getBounds());
  }
</script>
```

The coordinates are only an example map centre. This code displays a map; it does not yet call the Flask route API.

### 10.2 Browser Geolocation API — current location

Documentation: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API

Use `getCurrentPosition()` to get a location once, or `watchPosition()` to receive updates while the user moves.

```javascript
function locateUser() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by this browser.");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;

      L.marker([lat, lon]).addTo(map)
        .bindPopup("Your current location").openPopup();

      map.setView([lat, lon], 18);
    },
    (error) => {
      alert("Unable to get location. Allow location access or enter it manually.");
      console.error(error);
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
  );
}
```

For live movement, use `watchPosition()` and update the marker. Recalculate routes only when the user has moved meaningfully or the route has become unsuitable.

- The browser asks the user for permission.
- Geolocation generally requires HTTPS in deployment; localhost is normally allowed for development.
- Provide manual location entry if permission is denied.
- Explain why location is used. Avoid storing precise location history unless necessary and consented to.

### 10.3 Nominatim — place search and geocoding

Documentation: https://nominatim.org/  
Public service policy: https://operations.osmfoundation.org/policies/nominatim/

Geocoding converts a typed place or address into latitude and longitude. Reverse geocoding converts coordinates into a readable address.

Example search URL:

```text
https://nominatim.openstreetmap.org/search?q=SRM+Institute+of+Science+and+Technology&format=jsonv2&limit=5
```

Example JavaScript:

```javascript
async function searchPlace(placeName) {
  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.search = new URLSearchParams({
    q: placeName,
    format: "jsonv2",
    limit: "5"
  });

  const response = await fetch(url);
  if (!response.ok) throw new Error("Place search failed");

  const results = await response.json();
  return results.map(item => ({
    name: item.display_name,
    lat: Number(item.lat),
    lon: Number(item.lon)
  }));
}
```

Public Nominatim restrictions include a maximum of one request per second, no client-side autocomplete on the public service, caching where appropriate, and compliance with its identification and usage policy. Do not use it for systematic whole-area downloads. For larger use, select a suitable provider or operate your own service. For a student prototype, use a search button rather than requesting on every keystroke.

### 10.4 Overpass API — retrieve OpenStreetMap pedestrian features

Documentation: https://wiki.openstreetmap.org/wiki/Overpass_API

Overpass queries OpenStreetMap data. It can retrieve mapped pedestrian paths and accessibility tags inside a selected bounding box.

Example query for a small study area:

```overpass
[out:json][timeout:25];
(
  way["highway"="footway"](13.08,80.26,13.09,80.28);
  way["highway"="pedestrian"](13.08,80.26,13.09,80.28);
);
out geom;
```

The four values represent south latitude, west longitude, north latitude and east longitude. Replace them with the bounding box around your study area.

Useful OpenStreetMap tags:

| Tag | Meaning |
|---|---|
| `highway=footway` | Pedestrian path |
| `highway=pedestrian` | Pedestrian way or area |
| `wheelchair=yes/no/limited` | Wheelchair access information |
| `ramp=yes/no` | Ramp information, when mapped |
| `incline=*` | Incline information, when mapped |
| `surface=*` | Surface type |
| `smoothness=*` | Surface smoothness |
| `width=*` | Pathway width |
| `kerb=*` | Kerb information |
| `tactile_paving=*` | Tactile paving |
| `highway=steps` | Steps |

Not every path has these tags. A missing tag means **unknown**, not accessible. Tags can be recorded on nodes, ways or relations, so inspect the actual OSM structure.

Example Python request:

```python
import requests

query = """
[out:json][timeout:25];
(
  way["highway"="footway"](13.08,80.26,13.09,80.28);
  way["highway"="pedestrian"](13.08,80.26,13.09,80.28);
);
out geom;
"""

response = requests.post(
    "https://overpass-api.de/api/interpreter",
    data={"data": query},
    timeout=40
)
response.raise_for_status()

osm_data = response.json()
print("Retrieved elements:", len(osm_data.get("elements", [])))
```

Use small bounded queries, cache responses and avoid repeatedly requesting the same area. Public Overpass servers are shared and may be busy or rate-limited. For repeated or larger use, consider a suitable provider or self-hosting.

### 10.5 Routing engines — important distinction

**Recommended: use your own NetworkX route engine.**

A general road-routing service may return a route based on its own profile. It may not apply your custom accessibility costs or user-specific constraints.

- **NetworkX:** Best for a custom pedestrian graph and accessibility cost function. https://networkx.org/
- **OSRM:** Routing API over OpenStreetMap data. Standard profiles are not automatically wheelchair-accessibility engines. https://project-osrm.org/docs/
- **GraphHopper:** Routing APIs and configurable profiles; check current plan and profile capabilities. https://www.graphhopper.com/
- **openrouteservice:** Directions and geospatial APIs; check available profiles, restrictions and service limits. https://openrouteservice.org/

Use external routing as a baseline or supporting service. Use NetworkX for routes whose edge costs you control.

### 10.6 What is actually real-time?

| Feature | Real-time capability | Implementation |
|---|---|---|
| User's current position | Yes, with device permission | Geolocation `watchPosition()` |
| Moving user marker | Yes | Update Leaflet marker |
| New obstacle report | Near real-time | Save through Flask and refresh route data |
| Route recalculation | On demand or event-triggered | Re-run route engine |
| Base map | Provider-dependent | Map tile service |
| Accessibility of every path | Not automatically | OSM tags, surveys or verified reports |
| Live lift/ramp status | Only if a live source exists | Facility/operator feed; otherwise show unknown |
| Live traffic | Provider-dependent | Not required for initial prototype |

OpenStreetMap is a community-maintained geographic database, not a guaranteed live feed of sidewalk conditions. Your obstacle-reporting feature can provide fresh local updates, but reports need timestamps, verification and expiry rules.

## 11. Accessibility data model

Represent the pedestrian network as a graph:

- **Node:** An intersection, entrance, crossing or route junction.
- **Edge:** A traversable pathway connecting two nodes.
- **Edge attributes:** Distance, slope, width, surface, stairs, ramp, kerb and confidence.

Example pathway record:

| Field | Example |
|---|---|
| Segment ID | P001 |
| Start node | N001 |
| End node | N002 |
| Distance | 85 m |
| Stairs | No |
| Ramp | Yes |
| Slope | 4 degrees |
| Width | 1.5 m |
| Surface | Paved |
| Verification | Field verified |
| Last updated | Timestamp |

Keep original source tags as well as normalized values so the origin of each attribute can be traced.

## 12. Personalized accessibility cost function

A simple model can calculate a cost for each pathway edge:

```text
Edge Cost =
    distance_weight × normalized_distance
  + slope_weight × slope_penalty
  + surface_weight × surface_penalty
  + width_weight × width_penalty
  + ramp_weight × ramp_penalty
  + uncertainty_weight × uncertainty_penalty
```

Then:

```text
Total Route Cost = Sum of all edge costs in the route
```

Example profile rules:

- **Wheelchair profile:** Stairs are prohibited; paths below the user's chosen minimum width can be prohibited.
- **Limited-mobility profile:** Steep slopes and rough surfaces receive higher penalties.
- **General pedestrian profile:** Distance may receive a higher weight.

Weights must be configurable and calibrated through testing or user feedback. Do not present arbitrary weights as universal accessibility standards.

**Hard constraints vs. soft penalties:**

- Hard constraint: remove an edge if it violates a requirement, such as stairs being prohibited for a wheelchair profile.
- Soft penalty: keep an edge but increase its cost, such as for a slightly uneven surface.
- Unknown values: warn the user, reduce route confidence or allow unverified paths to be excluded.

## 13. Path-planning algorithms

### Dijkstra's algorithm

- Finds the minimum total cost path in a graph with non-negative edge weights.
- Suitable for a campus-scale graph.
- Uses your accessibility cost as the edge weight.

### A* algorithm

- Uses the cost so far plus a heuristic estimate to the destination.
- Can reduce search effort when the heuristic is suitable.
- For an optimal result, the heuristic must be admissible and consistent for the chosen cost model.

### Recommended experiment

Compare:

1. Shortest-distance Dijkstra route.
2. Accessibility-cost Dijkstra route.
3. Accessibility-cost A* route.

Measure route length, accessibility violations, computation time and route feasibility using the same graph and test cases.

## 14. Database design

MySQL is suitable; SQLite can be used for an early prototype.

### `users`

- `user_id` — primary key
- `name`
- `email`
- `password_hash`
- `created_at`

### `mobility_profiles`

- `profile_id` — primary key
- `user_id` — foreign key
- `profile_type`
- `max_slope`
- `min_width`
- `avoid_stairs`
- `surface_preference`
- `preferences_json`

### `path_nodes`

- `node_id` — primary key
- `latitude`
- `longitude`
- `node_type`

### `path_segments`

- `segment_id` — primary key
- `start_node_id`
- `end_node_id`
- `distance_m`
- `slope`
- `width_m`
- `surface`
- `has_stairs`
- `has_ramp`
- `wheelchair_access`
- `data_source`
- `verification_status`
- `last_verified_at`

### `obstacle_reports`

- `report_id` — primary key
- `user_id` — nullable foreign key if anonymous reporting is supported
- `latitude`
- `longitude`
- `segment_id` — nullable foreign key
- `obstacle_type`
- `description`
- `image_path` — optional
- `reported_at`
- `expires_at`
- `verification_status`

### `route_history` (optional)

- `route_id`
- `user_id`
- `start_latitude`
- `start_longitude`
- `end_latitude`
- `end_longitude`
- `profile_id`
- `created_at`
- `algorithm`
- `distance_m`
- `total_accessibility_cost`

Store only necessary data. Avoid continuous location history by default.

## 15. Suggested Flask API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/register` | Create user account |
| POST | `/api/login` | Authenticate user |
| GET | `/api/profile` | Retrieve mobility profile |
| PUT | `/api/profile` | Update mobility preferences |
| GET | `/api/map/paths` | Retrieve pedestrian paths for an area |
| GET | `/api/geocode` | Optional geocoding proxy |
| POST | `/api/route` | Calculate accessibility-aware route |
| POST | `/api/reports` | Submit obstacle report |
| GET | `/api/reports` | Retrieve active reports in an area |
| PATCH | `/api/reports/{id}/verify` | Verify or reject report (admin) |
| GET | `/api/health` | Check application status |

Example route request:

```json
{
  "start": {"lat": 13.0827, "lon": 80.2707},
  "destination": {"lat": 13.0850, "lon": 80.2730},
  "profile": {
    "type": "wheelchair",
    "avoid_stairs": true,
    "max_slope": 6,
    "min_width": 1.2
  },
  "algorithm": "astar"
}
```

Example response shape (illustrative values):

```json
{
  "status": "success",
  "route": {
    "coordinates": [
      [13.0827, 80.2707],
      [13.0832, 80.2711],
      [13.0850, 80.2730]
    ],
    "distance_m": 310,
    "total_cost": 42.5,
    "warnings": ["One pathway segment has unverified surface information"],
    "explanation": [
      "Avoids mapped stairs",
      "Uses pathways meeting the selected width constraint"
    ]
  }
}
```

## 16. Obstacle reporting and dynamic updates

Users can report:

- Blocked sidewalk.
- Construction or temporary closure.
- Broken or missing ramp.
- Damaged or uneven surface.
- Lift or facility out of service, where relevant.
- Other accessibility barrier.

Each report should include location, category, short description, optional photo, report time, verification status and expiry/review time.

Suggested report states:

`PENDING → VERIFIED → ACTIVE → EXPIRED`

A moderator or administrator can verify reports. A report should not permanently block a route. Temporary obstacles should expire or be reviewed after a configurable period.

For the first version, refresh obstacle markers and route data after a successful report. Later, use WebSockets or Server-Sent Events if multiple users need updates without refreshing.

## 17. User interface pages

1. **Home:** Project introduction and login/register.
2. **Login/Register:** Account access.
3. **Mobility profile:** Preferences and constraints.
4. **Navigation:** Map, search, start and destination selection.
5. **Route results:** Recommended and alternative routes, distance, warnings and explanation.
6. **Report obstacle:** Location, category, description and optional photo.
7. **My reports:** Report status and history.
8. **Admin dashboard:** Review reports, update pathway data and view accessibility issues.

### Accessibility requirements for the application itself

- Large readable text and high-contrast controls.
- Keyboard-accessible forms and map controls where possible.
- Clear labels and icons; do not rely on color alone.
- Comfortable touch targets.
- Manual location option.
- Text directions in addition to map lines.
- Understandable warnings for screen-reader users.

## 18. Suggested project folder structure

```text
accessibility-navigator/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
│
├── routes/
│   ├── auth.py
│   ├── profile.py
│   ├── navigation.py
│   └── reports.py
│
├── services/
│   ├── osm_service.py
│   ├── geocoding_service.py
│   ├── graph_builder.py
│   ├── accessibility_scoring.py
│   └── route_engine.py
│
├── models/
│   ├── user.py
│   ├── pathway.py
│   └── obstacle.py
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── profile.html
│   ├── navigation.html
│   └── reports.html
│
├── static/
│   ├── css/
│   ├── js/
│   │   ├── map.js
│   │   ├── geolocation.js
│   │   └── navigation.js
│   └── images/
│
├── data/
│   └── sample_campus_network.json
│
└── tests/
    ├── test_scoring.py
    ├── test_routes.py
    └── test_api.py
```

## 19. Python packages and setup

Suggested `requirements.txt`:

```text
Flask
Flask-SQLAlchemy
Flask-Login
Flask-Cors
mysql-connector-python
requests
networkx
pandas
numpy
python-dotenv
```

Optional packages:

```text
osmnx
geopandas
shapely
pytest
Pillow
```

Install on Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Use environment variables for database credentials and secret keys. Never commit `.env` or passwords to a public repository.

## 20. Testing and performance evaluation

Compare the proposed system with a conventional shortest-distance route planner using the same map and origin-destination pairs.

| Metric | Meaning |
|---|---|
| Route distance (metres) | Total route length |
| Computation time (ms) | Time to calculate a route |
| Accessibility violations | Segments violating selected hard constraints |
| Constraint satisfaction (%) | Share of evaluated segments satisfying known hard constraints |
| Data completeness (%) | Share of segments with required attributes recorded |
| Route feasibility | Whether a path exists under the selected constraints |
| User feedback | Rating or feedback on route usefulness |

Formulas:

```text
Constraint Satisfaction (%) =
  (Segments satisfying known hard constraints /
   Segments evaluated) × 100

Data Completeness (%) =
  (Segments with required attributes recorded /
   Total segments) × 100
```

Do not report invented performance values. Collect results from your own test network and document the number of routes, profiles and test cases.

### Example experiment

- Select 10 origin-destination pairs on the campus.
- Test each pair with wheelchair and limited-mobility profiles.
- Run shortest-distance Dijkstra.
- Run accessibility-aware Dijkstra.
- Run accessibility-aware A*.
- Record distance, computation time, constraint violations and route feasibility.
- Discuss cases where no accessible route exists or map data is incomplete.

## 21. Four-month implementation plan

| Period | Work |
|---|---|
| Month 1 | Literature review, requirements, study-area selection, field survey and database design |
| Month 2 | Map integration, graph creation, accessibility data processing and Dijkstra/A* |
| Month 3 | Flask application, user profiles, interactive map, route display and obstacle reporting |
| Month 4 | Testing, algorithm comparison, result analysis, documentation and final presentation |

## 22. Expected outcomes

- Working web-based accessibility navigation prototype.
- Interactive map with start, destination and route visualization.
- Pedestrian graph containing accessibility attributes.
- Personalized route generation using Dijkstra or A*.
- Explanations and warnings for route recommendations.
- Obstacle reporting and status management.
- Experimental comparison with conventional shortest-path routing.
- Small documented accessibility dataset for the selected study area.

## 23. Novelty and proposed research contribution

The proposed implementation combines:

1. **Personalized accessibility profiles:** Route constraints and preferences differ by user.
2. **Multi-factor accessibility scoring:** Distance, slope, width, surface and barriers influence route cost.
3. **Dynamic obstacle reporting:** Recent, verified reports can affect route availability.
4. **Confidence-aware routing:** Distinguishes verified, reported and unknown path attributes.
5. **Explainable recommendations:** Shows why a route was selected or a segment avoided.
6. **Comparative evaluation:** Tests against distance-only routing using measurable accessibility and performance metrics.

These are proposed contributions to implement and evaluate, not claims that no previous research has explored them. Establish novelty through the literature review.

## 24. SDG contribution

### SDG 10 — Reduced Inequalities

- Supports independent mobility for people with disabilities.
- Helps users identify routes that better match their mobility requirements.
- Makes accessibility barriers more visible.

### SDG 11 — Sustainable Cities and Communities

- Supports inclusive access to public spaces.
- Helps identify locations where pedestrian infrastructure needs improvement.
- Encourages more accessible campus and neighborhood environments.

## 25. Risks, limitations and mitigation

| Risk / limitation | Mitigation |
|---|---|
| Missing accessibility tags in OSM | Conduct a local survey; mark missing values unknown |
| Incorrect or outdated obstacle report | Add timestamps, verification and expiry |
| GPS inaccuracy | Allow manual location selection and show accuracy |
| No feasible accessible route | Explain that no route satisfying the constraints was found |
| External API downtime or rate limits | Cache permitted data and provide manual fallback |
| Public map service restrictions | Follow provider policies or choose a suitable provider |
| Incorrect slope or width measurements | Record measurement source and verification date |
| Route appears accessible but is not | Show uncertainty; never guarantee safety |

## 26. Security, privacy and responsible use

- Ask permission before accessing device location.
- Use HTTPS in deployment.
- Hash passwords using a suitable password-hashing library.
- Validate and sanitize user input.
- Restrict report moderation to authorized administrators.
- Limit photo uploads by file type and size; do not trust file extensions alone.
- Avoid storing continuous location history by default.
- Provide a way to remove user-submitted reports or account data where appropriate.
- Clearly show data freshness and uncertainty.
- Do not describe an unverified route as guaranteed safe or accessible.

## 27. Recommended development sequence

1. Select a small campus map and manually list 20–50 pathway segments.
2. Create database tables for nodes, segments, accessibility attributes and reports.
3. Build a NetworkX graph and test Dijkstra on sample coordinates.
4. Add accessibility constraints and cost calculation.
5. Implement A* and compare its results with Dijkstra.
6. Build the Leaflet map and allow users to select start and destination.
7. Connect the frontend to Flask's `/api/route` endpoint.
8. Add browser geolocation and place search.
9. Add obstacle reporting, verification and expiry.
10. Run experiments, prepare tables and charts, and document limitations.

**First milestone:** Calculate a route between two manually selected campus locations using a verified graph. Add external map data after this route engine works.

## 28. Useful official documentation and resources

### Map and geospatial tools

- Leaflet: https://leafletjs.com/reference.html
- OpenStreetMap: https://www.openstreetmap.org/
- OSM copyright and attribution: https://www.openstreetmap.org/copyright
- OSM tile usage policy: https://operations.osmfoundation.org/policies/tiles/
- Nominatim usage policy: https://operations.osmfoundation.org/policies/nominatim/
- Overpass API: https://wiki.openstreetmap.org/wiki/Overpass_API
- Browser Geolocation API: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API

### Routing and graph tools

- NetworkX: https://networkx.org/documentation/stable/
- OSRM API: https://project-osrm.org/docs/
- openrouteservice: https://openrouteservice.org/
- GraphHopper: https://www.graphhopper.com/

### Development tools

- Flask: https://flask.palletsprojects.com/
- MySQL: https://dev.mysql.com/doc/
- Python: https://docs.python.org/3/

### Research starting points

- Kasemsuppakorn and Karimi (2009), *Personalised routing for wheelchair navigation*, Journal of Location Based Services. https://doi.org/10.1080/17489720902837936
- Neis and Zielstra (2014), *Generation of a tailored routing network for disabled people based on collaboratively collected geodata*, Applied Geography. https://doi.org/10.1016/j.apgeog.2013.12.004
- Rahaman et al. (2017), *CAPRA: A contour-based accessible path routing algorithm*. https://doi.org/10.1016/j.ins.2016.12.041

Verify full author lists, publication details and relevance through your institution's library or publisher before including papers in the final bibliography.

## 29. Final project definition

**Title:** AI-Powered Accessibility Navigator for People with Mobility Difficulties

**Short description:** A web-based intelligent navigation system that combines device location, OpenStreetMap-based pedestrian data, personalized accessibility constraints, graph-based path planning and user-reported obstacles to recommend more suitable routes for people with mobility difficulties.

**Recommended stack:** Python, Flask, MySQL, Leaflet, OpenStreetMap, browser Geolocation, Nominatim, Overpass API, NetworkX, Dijkstra and A*.

**Study area:** A selected college campus or small neighborhood.

**Core research comparison:** Conventional shortest-distance routing versus personalized accessibility-aware routing.

**Primary SDGs:** SDG 10 and SDG 11.
