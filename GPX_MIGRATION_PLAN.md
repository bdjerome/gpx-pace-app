# GPX Pace Planner — Migration Plan
## Streamlit → Vue.js + FastAPI + PostgreSQL (Google Cloud)

---

## Overview

The current app is a monolithic Streamlit application where the UI, business logic, GPX processing, and file storage all live together in one Python process. The migration breaks this into three distinct layers:

| Layer | Current | Target |
|---|---|---|
| Frontend | Streamlit (Python) | Vue.js (TypeScript) |
| Backend | Streamlit (embedded) | FastAPI (Python) |
| Database | None (local filesystem) | PostgreSQL (Cloud SQL on GCP) |
| File Storage | Local `saved_routes/` folder | Google Cloud Storage |
| Hosting | Local / Streamlit Cloud | Google Cloud Run |

**Core logic that migrates as-is:** `pace_planner.py` and `misc_functions.py` move directly into the FastAPI backend with minimal changes. The GPX parsing, pace calculation, map generation, and PDF export are all pure Python and are backend concerns.

---

## Phase 1: Architecture & Project Setup

### Step 1 — Define the API Contract
Before writing any code, define what endpoints the FastAPI backend will expose and what data shapes they return. This contract is the handshake between your frontend and backend.

**Endpoints to design:**
- `POST /routes/analyze` — Accept a GPX file + race config, return full analysis results (split table, summary stats, map HTML)
- `GET /routes` — List all saved race plans for a user
- `GET /routes/{id}` — Fetch a specific saved race plan
- `POST /routes` — Save a new race plan (config + results) to the database
- `PUT /routes/{id}` — Update a saved race plan
- `DELETE /routes/{id}` — Delete a saved race plan
- `POST /routes/{id}/pdf` — Generate and return a PDF report for a saved plan
- `POST /auth/register` — User registration
- `POST /auth/login` — User login, returns JWT token

**Key design decisions to make:**
- What exactly gets stored in the database vs. re-computed on demand (storing full results vs. storing config and re-running analysis)
- Whether map HTML is returned from the API or rendered client-side using Leaflet.js

**Recommendation:** Store the analysis config (pace, loops, start time, markers, etc.) and the GPX file reference in the database. Re-run analysis on demand rather than storing the full split table — this keeps the database lean and ensures results stay consistent with the algorithm.

---

### Step 2 — Initialize the Monorepo Structure

Create a clean project structure that houses both the frontend and backend:

```
gpx-pace-planner/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── analyze.py
│   │   │   │   ├── plans.py
│   │   │   │   └── auth.py
│   │   ├── core/
│   │   │   ├── gpx/
│   │   │   │   ├── pace_planner.py   # migrated from current
│   │   │   │   └── misc_functions.py # migrated from current
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   └── session.py
│   │   └── services/
│   │       ├── storage.py    # GCS file uploads/downloads
│   │       └── pdf.py        # PDF generation service
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # Vue.js application
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── stores/           # Pinia state management
│   │   ├── api/              # API client (axios)
│   │   └── types/            # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── infra/                    # GCP infrastructure config
│   ├── cloudbuild.yaml
│   └── docker-compose.yml    # local development
└── README.md
```

---

## Phase 2: Backend Foundation

### Step 3 — Set Up FastAPI Project

Initialize the FastAPI application with the essential infrastructure:

- Install dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `python-multipart`, `python-jose`, `passlib`, `google-cloud-storage`
- Carry over existing GPX dependencies: `gpxpy`, `geopy`, `folium`, `pandas`, `numpy`, `matplotlib`, `reportlab`
- Configure `app/core/config.py` to read environment variables for DB connection string, GCS bucket name, JWT secret, etc. using `pydantic-settings`
- Set up CORS middleware to allow requests from the Vue.js frontend origin

### Step 4 — Design the Database Schema

Define the schema before writing any models or endpoints that touch the DB:

**`users`**
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
email       TEXT UNIQUE NOT NULL
hashed_pw   TEXT NOT NULL
display_name TEXT
created_at  TIMESTAMPTZ DEFAULT now()
```

**`gpx_files`**
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID REFERENCES users(id) ON DELETE CASCADE
file_name   TEXT NOT NULL           -- original filename
gcs_path    TEXT NOT NULL           -- gs://bucket/path/to/file.gpx
uploaded_at TIMESTAMPTZ DEFAULT now()
```

**`race_plans`**
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID REFERENCES users(id) ON DELETE CASCADE
gpx_file_id     UUID REFERENCES gpx_files(id)
nickname        TEXT NOT NULL
config          JSONB NOT NULL       -- pace, loops, start_time, decay, hills, markers, pace_unit
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()
```

The `config` JSONB column stores the entire race configuration object. This avoids creating extra columns for every individual setting and makes it easy to evolve the config schema without database migrations.

### Step 5 — Set Up SQLAlchemy Models, Pydantic Schemas, and DB Session

- Write SQLAlchemy ORM models in `db/models.py` matching the schema above
- Write Pydantic schemas in `db/schemas.py` for request/response validation on all endpoints
- Set up async SQLAlchemy session in `db/session.py` using `asyncpg` driver for non-blocking DB calls
- Set up Cloud SQL (PostgreSQL) on GCP:
    - Create a Cloud SQL PostgreSQL instance in the GCP project
    - Create a dedicated database and service account user for the application
    - Enable the Cloud SQL Auth Proxy for secure connections from Cloud Run (no public IP exposure needed)
    - Use Alembic for database migrations — initialize with `alembic init` and create the initial migration from the SQLAlchemy models
    - Store the DB connection string as a GCP Secret Manager secret; reference it in Cloud Run as an environment variable

### Step 6 — Implement JWT Auth

Auth is built before any protected endpoints so the `get_current_user` dependency is ready to use:

- Use `python-jose` for JWT encoding/decoding and `passlib[bcrypt]` for password hashing
- `POST /auth/register` — hash password, insert user record, return `{ user_id, email, display_name, created_at }`
- `POST /auth/login` — verify password against hash, return `access_token`, `refresh_token`, `token_type`, `expires_in`
- Create a reusable FastAPI dependency `get_current_user` that extracts and validates the JWT from the `Authorization: Bearer <token>` header
- Apply `get_current_user` as a dependency on all `/routes` and `/files` endpoints to enforce authentication

**Future enhancement:** Add OAuth2 (Google Sign-In) using `python-social-auth` or `authlib` — this fits well in a GCP environment.

---

## Phase 3: Backend Endpoints

### Step 7 — Migrate Core GPX Logic

Move `pace_planner.py` and `misc_functions.py` into `backend/app/core/gpx/` with these changes:

- **Remove all Streamlit imports** from `misc_functions.py` — remove the `dynamic_input_data_editor` wrapper function entirely (no longer needed; this was a Streamlit workaround)
- `GPXAnalyzer`, `PaceCalculator`, `MapVisualizer`, and `speed_calculation` migrate as-is — they have no Streamlit dependencies
- `create_static_map_image`, `generate_gpx_analysis_pdf`, unit conversion functions, `merge_custom_markers`, `calculate_time_difference`, and `plotly_elevation_plot`/`plotly_pace_plot` all migrate cleanly
- `generate_gpx_analysis_pdf` currently returns a `BytesIO` — this stays exactly the same; FastAPI will stream it with `StreamingResponse`
- For the Folium map (`MapVisualizer`), the `.save()` output is HTML — the API can return this as a string field in the JSON response, and the Vue frontend renders it in an `<iframe>` or via `v-html`

### Step 8 — Build the GPX Upload and Analysis Endpoints

**Design decision: guest-first analysis.** `POST /routes/analyze` accepts the raw GPX file and config in a single `multipart/form-data` request — no account required. GCS upload and the `gpx_files` DB record only happen when a logged-in user saves a plan (Step 9). This matches the original Streamlit UX where any visitor could drop a file and get results immediately.

#### `POST /routes/analyze` — Guest-accessible, no auth required

- Accept `multipart/form-data` with two parts:
  - `file`: the `.gpx` file bytes
  - `config`: a JSON string containing `{ loops, base_pace, race_start_time, decay, hill_mode, pace_unit, custom_markers }`
- Validate the file parses cleanly with `gpxpy` — return HTTP 422 if invalid
- Write bytes to a `tempfile.NamedTemporaryFile(suffix=".gpx")`, run the full pipeline:
  1. `GPXAnalyzer(tmp_path)` → `load_gpx()` → `map_adjustment(loops)` → `calculate_distances()` → `find_kilometer_markers()`
  2. `PaceCalculator(analyzer, base_pace)` → `calculate_pace(decay, hill_mode)` → `calculate_times()` → `calculate_clock_times(race_start_time)`
  3. `merge_custom_markers(analyzer.final_df, custom_markers, use_km=pace_unit=='km')`
  4. `MapVisualizer` → `create_base_map()` → `add_kilometer_markers_directional()` → capture HTML via `map._repr_html_()`
  5. `plotly_elevation_plot()` and `plotly_pace_plot()` → call `.to_json()` on each figure
- Clean up the temp file after analysis
- Serialize `final_df` km-marker rows to the split table list
- Compute summary stats: total distance, avg pace, total duration (from `cumulative_time_hms` on last row), elevation gain (sum of positive `segment_gain`)
- Return `AnalyzeResponse`:
  ```json
  {
    "split_table": [...],
    "summary": {
      "total_distance_km": 42.2,
      "avg_pace_min_per_km": 6.1,
      "total_duration_hms": "04:18:00",
      "elevation_gain_m": 850.0,
      "elevation_loss_m": 847.0
    },
    "map_html": "<html>...</html>",
    "elevation_chart_json": "{...plotly figure...}",
    "pace_chart_json": "{...plotly figure...}"
  }
  ```

#### `POST /routes/gpx` — Auth required, called only when saving a plan

- Accept `multipart/form-data` with the `.gpx` file
- Requires `get_current_user` dependency (JWT Bearer token)
- Validate GPX format with `gpxpy` — return HTTP 422 if invalid
- Upload to GCS at path `users/{user_id}/gpx/{file_id}/{filename}.gpx`
- Insert a `gpx_files` record in the DB
- Return `{ file_id, gpx_filename, file_size_bytes }`

**Frontend flow:**
1. Guest drops a GPX file → frontend calls `POST /routes/analyze` directly with the file + config → results displayed
2. Logged-in user hits "Save Plan" → frontend first calls `POST /routes/gpx` to upload the file and get a `file_id`, then calls `POST /routes` (Step 9) with the `file_id` + config to persist the plan

**Note on Plotly charts:** Return the raw Plotly figure as JSON via `.to_json()`. The Vue frontend renders it using `plotly.js` directly — this gives better interactivity than static images.

**Implementation steps:**
1. Add Pydantic schemas to `db/schemas.py`: `AnalyzeConfig`, `SplitRow`, `SummaryStats`, `AnalyzeResponse`, `GpxUploadResponse`
2. Create `backend/app/services/storage.py` with `upload_gpx_file()` and `download_gpx_file()`:
   - In GCP: create a private GCS bucket, set object paths to `users/{user_id}/gpx/{file_id}/{filename}.gpx`
   - Locally: include a stub controlled by a `USE_LOCAL_STORAGE=true` env var that reads/writes to `backend/tmp/` instead of GCS — no credentials needed for local dev
3. Create `backend/app/api/routes/gpx.py` with the `POST /routes/gpx` upload endpoint
4. Create `backend/app/api/routes/analyze.py` with the `POST /routes/analyze` endpoint
5. Register both routers in `main.py` under the `/routes` prefix

### Step 9 — Build the Race Plans CRUD Endpoints

These endpoints require auth and interact with the DB — built after models and `get_current_user` exist:

- `POST /routes` — Save a plan: store user_id (from JWT), nickname, gpx_file_id, and config JSONB. Return `{ route_id, nickname, created_at }`
- `GET /routes` — Return all plans for the authenticated user. Return array of `{ route_id, nickname, gpx_filename, created_at, updated_at }`
- `GET /routes/{id}` — Verify ownership (403 if mismatch), re-run analysis from stored config + GPX, return same shape as `POST /routes/analyze`
- `PUT /routes/{id}` — Verify ownership, update nickname/gpx_file_id/config fields. Return `{ route_id, nickname, created_at, updated_at }`
- `DELETE /routes/{id}` — Verify ownership, hard-delete the plan record, delete GPX file from GCS. Return `204 No Content`

### Step 10 — Build the PDF Export Endpoint

`POST /routes/{id}/pdf` (**DEFERRED** — TBD server-side vs client-side):

- Re-run analysis for the plan (same pipeline as Step 8)
- Call `generate_gpx_analysis_pdf()` — which already returns `BytesIO`
- Return with FastAPI's `StreamingResponse` and `media_type="application/pdf"`, with a `Content-Disposition: attachment` header so the browser triggers a download

---

## Phase 4: Frontend Development (Vue.js)

### Step 12 — Initialize the Vue.js Project

- Scaffold with `npm create vue@latest` using: TypeScript, Vue Router, Pinia, ESLint
- Install key dependencies:
  - `axios` — HTTP client for API calls
  - `plotly.js` — Charts (elevation and pace, matches what the backend returns)
  - `leaflet` or use an `<iframe>` for the Folium map HTML
  - `vue-pdf-embed` or trigger download directly from the PDF endpoint
  - A UI component library: **Vuetify** (Material Design) or **PrimeVue** for form inputs, tables, and layout

### Step 13 — Set Up Pinia Stores

Pinia replaces Streamlit's `st.session_state`. Create these stores:

- **`useAuthStore`** — Stores the JWT token and current user profile; persists to `localStorage`; exposes `login()`, `logout()`, `register()` actions
- **`useAnalysisStore`** — Stores the current analysis result (split table, summary stats, map HTML, chart data); exposes `runAnalysis()` action that calls `POST /routes/analyze`
- **`usePlansStore`** — Stores the list of saved race plans; exposes `fetchPlans()`, `savePlan()`, `deletePlan()` actions

### Step 14 — Build the Route Configuration View

This replaces the left and right column Streamlit form. Build a Vue view (`views/AnalyzeView.vue`) with:

**Route Selection section:**
- A file drop zone / file picker for GPX upload (accept `.gpx` only)
- A "Saved Routes" dropdown (populated from `GET /routes`) — only shown when user is logged in
- Route change detection that clears the current analysis results (replacing the `st.session_state` clearing logic)

**Analysis Configuration section (form):**
- Number input: loops (1–5)
- Radio: pace unit (min/km vs min/mile)
- Time input: base pace
- Time picker: race start time
- Checkboxes: enable fatigue decay, enable hill adjustments
- Expandable section: Custom Markers — an editable table with columns Distance, Nickname, Cutoff Time (replaces `st.data_editor`)
- "Analyze Route" submit button — disabled when no GPX file selected

On form submit, dispatch `useAnalysisStore.runAnalysis()` with the GPX file and all config values.

### Step 15 — Build the Results View

This replaces the entire bottom half of `app.py` (everything after "`if st.session_state.get('analysis_complete', False)`"). Build `views/ResultsView.vue` or embed as a section of `AnalyzeView.vue`:

**Summary Metrics row (4 cards):**
- Total Distance, Average Pace, Estimated Duration, Elevation Gain/Loss
- Metric/Imperial toggle (checkbox) — convert values client-side using the same conversion formulas from `misc_functions.py`

**Interactive Map:**
- Render the Folium HTML string returned by the API using `<iframe srcdoc="...">` — this preserves the existing Folium/Leaflet-based map with all markers and arrows
- Alternatively (future enhancement): replace Folium server-side generation with Leaflet.js client-side rendering for better performance and interactivity

**Pace Data Table:**
- Render the split table from the analysis result
- Show custom marker rows (aid stations, cutoffs) highlighted differently
- Show cutoff buffer column when cutoff times are present

**Charts:**
- Render the Plotly elevation chart using `plotly.js` with the figure JSON returned from the API
- Render the Plotly pace chart similarly

**Notes/Annotations:**
- Editable notes column per km marker (replaces the `dynamic_input_data_editor` wrapper)
- Notes are stored locally in `useAnalysisStore` and included when saving a race plan

**Actions:**
- "Save Plan" button → `POST /routes` with current config — only available when logged in
- "Download PDF" button → `GET /routes/{id}/pdf` or `POST /routes/analyze/pdf` — triggers file download

### Step 16 — Build the Saved Plans View

`views/PlansView.vue` — requires authentication:

- Table/card list of all saved race plans (name, route, created date)
- "Load" button per plan → fetches config, pre-fills the form in AnalyzeView, triggers analysis
- "Delete" button per plan → calls `DELETE /routes/{id}` with confirmation dialog
- "Rename" inline edit

### Step 17 — Build Auth Views

`views/LoginView.vue` and `views/RegisterView.vue`:

- Simple email/password forms
- On success, store JWT in Pinia `useAuthStore`, redirect to AnalyzeView
- Show/hide Saved Plans nav link based on auth state

### Step 18 — Build the Tutorial View

Port the tutorial from `pages/tutorial.py` (Streamlit) to a static Vue component `views/TutorialView.vue` as a structured markdown-style page with sections, screenshots/GIFs, and code examples. No backend needed.

---

## Phase 6: Deployment to Google Cloud

### Step 19 — Containerize Both Services

**Backend Dockerfile** (`backend/Dockerfile`):
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Frontend Dockerfile** (`frontend/Dockerfile`):
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
```

Write an `nginx.conf` that handles Vue Router's HTML5 history mode (all routes fall back to `index.html`) and proxies `/api/` requests to the backend service URL.

### Step 20 — Configure Cloud Build CI/CD

`infra/cloudbuild.yaml`:
- On push to `main`: build both Docker images, push to Google Artifact Registry, deploy backend to Cloud Run, deploy frontend to Cloud Run (or Firebase Hosting)
- Store build triggers in Cloud Build console connected to the GitHub repo
- Use substitution variables for project ID, region, and service names

### Step 21 — Deploy Backend to Cloud Run

- Create a Cloud Run service for the FastAPI backend
- Set environment variables from Secret Manager: `DATABASE_URL`, `GCS_BUCKET_NAME`, `JWT_SECRET`, `CORS_ORIGIN`
- Mount the Cloud SQL instance using the Cloud SQL Auth Proxy sidecar (built into Cloud Run via connection name)
- Set min-instances to 1 (avoids cold start delay on first request)

### Step 22 — Deploy Frontend to Cloud Run or Firebase Hosting

Two options:
- **Cloud Run** (Nginx container): More control, same infra as backend — deploy the frontend Docker image as a second Cloud Run service with a custom domain
- **Firebase Hosting**: Simpler for a static Vue build; `firebase deploy` after `npm run build`; automatically handles CDN, HTTPS, and custom domains

Recommended: **Firebase Hosting** for the frontend — it's purpose-built for SPAs, handles the Vue Router fallback configuration automatically, and integrates well with GCP.

---

## Phase 7: Testing & Validation

### Step 23 — Backend Unit Tests

Write `pytest` tests for:
- `GPXAnalyzer`: load a known GPX file, assert correct distances and km markers
- `PaceCalculator`: given known inputs, assert expected pace/time outputs
- `merge_custom_markers`: assert correct merging of custom markers into split table
- `generate_gpx_analysis_pdf`: assert PDF is generated and non-empty
- API endpoints: use FastAPI's `TestClient` to test `/analyze`, `/routes`, and auth endpoints with mock DB

### Step 25 — Frontend Component Tests

Use `vitest` + `@vue/test-utils`:
- Configuration form: assert form validation, disabled submit when no file
- Results view: snapshot test with mock analysis response
- Auth store: assert JWT token storage/retrieval from localStorage

### Step 26 — End-to-End Validation

Before go-live, do a manual side-by-side comparison:
- Upload the same GPX file to both the old Streamlit app and new Vue app with identical config
- Assert identical split tables, summary stats, and finish times
- Verify PDF output matches the Streamlit version
- Test the full CRUD flow: save a plan, reload it, modify it, delete it

---

## Phase 9: Go-Live Checklist

- [ ] All environment variables set in GCP Secret Manager and referenced in Cloud Run
- [ ] Cloud SQL instance has automated backups enabled
- [ ] GCS bucket has versioning enabled
- [ ] CORS is configured correctly (frontend origin only, not `*`)
- [ ] JWT secret is a strong random value (not a placeholder)
- [ ] HTTPS enforced on all Cloud Run services (default with GCP)
- [ ] Rate limiting added to `/routes/analyze` (GPX processing is CPU-intensive)
- [ ] Cloud Run max instances configured to avoid runaway costs
- [ ] Error tracking set up (GCP Cloud Logging or Sentry)
- [ ] Old Streamlit app kept running in parallel until validation is complete

---

## Migration Sequence Summary

| Phase | Steps | Key Output |
|---|---|---|
| Architecture | 1–2 | API contract defined, project scaffolded |
| Backend | 3–7 | FastAPI app with all endpoints working locally |
| Database | 8–10 | Cloud SQL schema, Alembic migrations, SQLAlchemy models |
| Auth | 11 | JWT authentication protecting all plan endpoints |
| File Storage | 12 | GCS upload/download working |
| Frontend | 13–19 | Complete Vue.js app consuming the FastAPI backend |
| Deployment | 20–23 | Both services live on GCP with CI/CD pipeline |
| Testing | 24–26 | Test coverage and side-by-side validation |
| Go-Live | — | Streamlit app decommissioned |
