import apiClient from './client'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserProfile,
  GpxUploadResponse,
  AnalyzeConfig,
  AnalyzeResponse,
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
    return apiClient.post<TokenResponse>('/auth/login', data)
  },
  register(data: RegisterRequest) {
    return apiClient.post<UserProfile>('/auth/register', data)
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
}

// ---------------------------------------------------------------------------
// Race plans  (all require auth)
// ---------------------------------------------------------------------------

export const plansApi = {
  list() {
    return apiClient.get<RacePlanSummary[]>('/routes')
  },

  get(id: string) {
    return apiClient.get<RacePlanRead & { analysis: AnalyzeResponse }>(`/routes/${id}`)
  },

  create(data: RacePlanCreate) {
    return apiClient.post<{ route_id: string; nickname: string; created_at: string }>('/routes', data)
  },

  update(id: string, data: RacePlanUpdate) {
    return apiClient.put<{ route_id: string; nickname: string; created_at: string; updated_at: string }>(
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
