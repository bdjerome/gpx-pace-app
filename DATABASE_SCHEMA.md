**`template_gpx_files`**
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
file_name   TEXT NOT NULL           -- display name, e.g. "Tokyo Marathon"
gcs_path    TEXT NOT NULL           -- gs://bucket/templates/tokyo-marathon.gpx
description TEXT                    -- optional short description shown in the UI
distance_m  NUMERIC                 -- total route distance in metres (pre-computed)
created_at  TIMESTAMPTZ DEFAULT now()
```

These are platform-provided routes available to all users. No `user_id` — they are read-only and managed by admins only.

---

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
id                    UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id               UUID REFERENCES users(id) ON DELETE CASCADE
gpx_file_id           UUID REFERENCES gpx_files(id)            -- set if user uploaded their own GPX
template_gpx_file_id  UUID REFERENCES template_gpx_files(id)   -- set if using a platform template
nickname              TEXT NOT NULL
config                JSONB NOT NULL       -- pace, loops, start_time, decay, hills, markers, pace_unit
created_at            TIMESTAMPTZ DEFAULT now()
updated_at            TIMESTAMPTZ DEFAULT now()
CONSTRAINT gpx_source_check CHECK (
  (gpx_file_id IS NOT NULL)::int + (template_gpx_file_id IS NOT NULL)::int = 1
)
```

The `config` JSONB column stores the entire race configuration object. This avoids creating extra columns for every individual setting and makes it easy to evolve the config schema without database migrations.