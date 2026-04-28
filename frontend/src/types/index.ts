// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface UserProfile {
  id: string
  email: string
  display_name: string | null
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  display_name?: string
}

// ---------------------------------------------------------------------------
// Analysis config
// ---------------------------------------------------------------------------

export interface CustomMarker {
  distance: number // km or miles depending on pace_unit
  nickname: string
  cutoff_time?: string // "HH:MM" or "HH:MM:SS"
}

export interface AnalyzeConfig {
  loops: number
  base_pace: string // "M:SS" e.g. "5:30"
  race_start_time: string // "HH:MM"
  decay: boolean
  hill_mode: boolean
  pace_unit: 'min/km' | 'min/mile'
  custom_markers: CustomMarker[]
}

// ---------------------------------------------------------------------------
// Analysis results
// ---------------------------------------------------------------------------

export interface SplitRow {
  km: number
  total_distance_km: number
  elevation_m: number
  pace_min_per_km: number
  cumulative_time_hms: string
  clock_time: string | null
  custom_marker: string | null
  cutoff_time: string | null
  cutoff_buffer_min: number | null
}

export interface SummaryStats {
  total_distance_km: number
  avg_pace_min_per_km: number
  total_duration_hms: string
  elevation_gain_m: number
  elevation_loss_m: number
}

export interface AnalyzeResponse {
  split_table: SplitRow[]
  summary: SummaryStats
  map_html: string
  elevation_chart_json: string | null
  pace_chart_json: string | null
}

// ---------------------------------------------------------------------------
// GPX upload
// ---------------------------------------------------------------------------

export interface GpxUploadResponse {
  file_id: string
  gpx_filename: string
  file_size_bytes: number
}

// ---------------------------------------------------------------------------
// Race plans
// ---------------------------------------------------------------------------

export interface RaceConfig {
  pace: string
  pace_unit: 'min/km' | 'min/mile'
  loops: number
  start_time: string
  decay_enabled: boolean
  hills_enabled: boolean
  markers: CustomMarker[]
}

export interface RacePlanSummary {
  id: string
  nickname: string
  gpx_file_id: string | null
  template_gpx_file_id: string | null
  gpx_filename: string | null
  created_at: string
  updated_at: string
}

export interface RacePlanCreate {
  nickname: string
  gpx_file_id?: string
  template_gpx_file_id?: string
  config: RaceConfig
}

export interface RacePlanUpdate {
  nickname?: string
  gpx_file_id?: string
  template_gpx_file_id?: string
  config?: Partial<RaceConfig>
}

export interface RacePlanRead {
  id: string
  user_id: string
  nickname: string
  gpx_file_id: string | null
  template_gpx_file_id: string | null
  config: RaceConfig
  created_at: string
  updated_at: string
}

export interface PlanWithAnalysis {
  plan: RacePlanRead
  analysis: AnalyzeResponse
}

// ---------------------------------------------------------------------------
// Template GPX files (public, no auth required)
// ---------------------------------------------------------------------------

export interface TemplateGpxFile {
  id: string
  file_name: string
  description: string | null
  distance_m: string | null   // Postgres NUMERIC serialized as string
  created_at: string
}
