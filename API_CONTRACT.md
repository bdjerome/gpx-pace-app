
**Endpoints to design:**

- `POST /routes/gpx` — Upload a GPX file to GCP storage
    - Auth: optional (unauthenticated users can analyze; authenticated users can also save)
    - Inputs: multipart/form-data
        - file (binary .gpx file, max 10MB)
    - Outputs = { file_id, gpx_filename, file_size_bytes }
    - Errors:
        - 400 Bad Request if file is not valid GPX format
        - 413 Payload Too Large if file exceeds size limit
    - Note: file_id is then passed to POST /routes/analyze and POST /routes

- `POST /routes/analyze` — Run pace analysis on a GPX file
    - Auth: optional (public endpoint — no JWT required, supports one-off analysis without an account)
    - Inputs:
        - file_id (string, from POST /routes/gpx)
        - config (json object: pace, loops, start_time, markers, pace_unit, enable_decay, enable_hills)
    - Outputs:
        - split_table (array of objects, one row per km marker):
            - { km_number, total_distance, pace, grade, cumulative_time_hms, clock_time, custom_marker }
        - summary_stats:
            - { total_distance_km, avg_pace_min_per_km, finish_time_hms, elevation_gain_m, elevation_loss_m }
        - map_info:
            - route_points (array of { lat, lng, elevation, total_distance, pace, grade } — full polyline)
            - km_markers (array of { lat, lng, km_number, total_distance, pace, cumulative_time_hms } — labeled pins)

- `GET /routes` — List all saved race plans for a user
    - Inputs = user_id (string UUID, from JWT auth context)
    - Outputs = Lightweight list for route selection UI
        - Array of: { route_id, nickname, gpx_filename, created_at, updated_at }

- `GET /routes/{id}` — Fetch a specific saved race plan and re-run analysis
    - Auth: required — JWT user_id must match the route owner (403 Forbidden otherwise)
    - Inputs = route_id (path param)
    - Outputs = Full analysis results, re-computed from stored config + GPX pointer
        - Same response shape as POST /routes/analyze
        - (config, gpx_file_id, split_table, summary_stats, map_info)
    - Errors: 404 Not Found if route_id does not exist, 403 Forbidden if route belongs to another user

- `POST /routes` — Save a new race plan (config + GPX pointer only, no results)
    - Inputs:
        - nickname (string)
        - gpx_file_id (string, pointer to file in GCP storage)
        - config (json object: pace, loops, start_time, markers, pace_unit, enable_decay, enable_hills)
    - Outputs = { route_id, nickname, created_at }
    - Note: Analysis results are NOT stored — they are re-computed on GET /routes/{id}

- `PUT /routes/{id}` — Update a saved race plan
    - Auth: required — JWT user_id must match the route owner (403 Forbidden otherwise)
    - Inputs:
        - nickname (string, optional)
        - gpx_file_id (string, optional — only if changing the GPX file)
        - config (json object, optional — only fields being updated)
    - Outputs = { route_id, nickname, created_at, updated_at }
    - Errors: 404 Not Found if route_id does not exist, 403 Forbidden if route belongs to another user

- `DELETE /routes/{id}` — Delete a saved race plan
    - Auth: required — JWT user_id must match the route owner (403 Forbidden otherwise)
    - Inputs = route_id (path param)
    - Outputs = 204 No Content (hard delete — record is permanently removed)
    - Errors: 404 Not Found if route_id does not exist, 403 Forbidden if route belongs to another user

- `POST /routes/{id}/pdf` — Generate and return a PDF report for a saved plan
    - **DEFERRED** — TBD: determine whether PDF generation happens server-side (API returns binary PDF) or client-side (frontend renders and exports)

- `POST /auth/register` — Create a new user account
    - Inputs:
        - email (string)
        - password (string, min 8 chars — hashed server-side with bcrypt, never stored in plaintext)
        - display_name (string, optional)
    - Outputs = { user_id, email, display_name, created_at }
    - Note: Does NOT return a token — user must call /auth/login after registering
    - Errors: 409 Conflict if email already exists

- `POST /auth/login` — Authenticate and receive access tokens
    - Inputs:
        - email (string)
        - password (string)
    - Outputs:
        - access_token (JWT, short-lived — e.g. 15 min) — sent in Authorization header as `Bearer <token>` on all protected requests
        - refresh_token (long-lived — e.g. 7 days) — used to get a new access_token without re-entering credentials
        - token_type: "bearer"
        - expires_in (seconds)
    - Errors: 401 Unauthorized if credentials are invalid
    - Note: The JWT payload encodes user_id — this is how protected endpoints like GET /routes know which user is making the request without needing user_id in the request body

- `POST /auth/refresh` — Exchange a refresh token for a new access token
    - **DEFERRED** — needed before production but not required for initial build
    - Inputs: refresh_token
    - Outputs: new access_token, new refresh_token (rotation), expires_in
