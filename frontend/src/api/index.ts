import apiClient from './client'
import authClient from './authClient'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserProfile,
  GpxUploadResponse,
  AnalyzeConfig,
  AnalyzeResponse,
  PlanWithAnalysis,
  RacePlanCreate,
  RacePlanUpdate,
  RacePlanSummary,
  RacePlanRead,
  TemplateGpxFile,
} from '@/types'

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const authApi = {
  login(data: LoginRequest) {
    return authClient.post<TokenResponse>('/auth/login', data)
  },
  register(data: RegisterRequest) {
    return authClient.post<UserProfile>('/auth/register', data)
  },
  refresh() {
    return authClient.post<TokenResponse>('/auth/refresh')
  },
  logout() {
    return authClient.post('/auth/logout')
  },
}

// ---------------------------------------------------------------------------
// GPX upload
// ---------------------------------------------------------------------------

export const gpxApi = {
  /** Upload a GPX file and receive a file_id. Auth required. */
  upload(file: File) {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<GpxUploadResponse>('/routes/gpx', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** Fetch the list of public template GPX files. No auth required. */
  listTemplates() {
    return apiClient.get<TemplateGpxFile[]>('/templates')
  },
}

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------

export const analyzeApi = {
  /**
   * Run pace analysis with an uploaded file. No auth required.
   * Sends the GPX file + config in a single multipart request.
   */
  run(file: File, config: AnalyzeConfig) {
    const form = new FormData()
    form.append('file', file)
    form.append('config', JSON.stringify(config))
    return apiClient.post<AnalyzeResponse>('/routes/analyze', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /**
   * Run pace analysis using a template GPX file stored on the server.
   * Sends template_gpx_file_id + config as JSON. No auth required.
   */
  runWithTemplate(templateGpxFileId: string, config: AnalyzeConfig) {
    return apiClient.post<AnalyzeResponse>('/routes/analyze/template', {
      template_gpx_file_id: templateGpxFileId,
      config,
    })
  },

  /**
   * Re-run analysis using a previously uploaded user GPX file. Auth required.
   * Sends gpx_file_id + config as JSON.
   */
  runWithGpxFileId(gpxFileId: string, config: AnalyzeConfig) {
    return apiClient.post<AnalyzeResponse>('/routes/analyze/gpx-file', {
      gpx_file_id: gpxFileId,
      config,
    })
  },
}

// ---------------------------------------------------------------------------
// Race plans  (all require auth)
// ---------------------------------------------------------------------------

export const plansApi = {
  list() {
    return apiClient.get<RacePlanSummary[]>('/routes')
  },

  get(id: string) {
    return apiClient.get<PlanWithAnalysis>(`/routes/${id}`)
  },

  create(data: RacePlanCreate) {
    return apiClient.post<RacePlanSummary>('/routes', data)
  },

  update(id: string, data: RacePlanUpdate) {
    return apiClient.put<RacePlanSummary>(
      `/routes/${id}`,
      data,
    )
  },

  delete(id: string) {
    return apiClient.delete(`/routes/${id}`)
  },

  pdf(id: string) {
    return apiClient.post(`/routes/${id}/pdf`, null, { responseType: 'blob' })
  },
}
