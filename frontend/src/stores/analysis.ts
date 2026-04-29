import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analyzeApi, plansApi } from '@/api'
import type { AnalyzeConfig, AnalyzeResponse, PlanNote, SplitRow } from '@/types'

export const useAnalysisStore = defineStore('analysis', () => {
  /** The GPX file currently loaded in the form */
  const gpxFile = ref<File | null>(null)
  const gpxFilename = ref<string | null>(null)

  /** Template GPX file id when using a template instead of an uploaded file */
  const templateId = ref<string | null>(null)

  /** Stored user GPX file id (set when loading a saved plan with a user-uploaded file) */
  const gpxFileId = ref<string | null>(null)

  /** Results from the last successful /routes/analyze call */
  const result = ref<AnalyzeResponse | null>(null)

  /** Per-row notes keyed by km number (not persisted to backend yet) */
  const rowNotes = ref<Record<number, string>>({})

  const activePlanId = ref<string | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  let _saveTimer: ReturnType<typeof setTimeout> | null = null

  function setGpxFile(file: File) {
    gpxFile.value = file
    gpxFilename.value = file.name
    templateId.value = null
    gpxFileId.value = null
    clearResult()
  }

  function setTemplateId(id: string, filename?: string) {
    templateId.value = id
    gpxFile.value = null
    gpxFileId.value = null
    gpxFilename.value = filename ?? null
    clearResult()
  }

  function setGpxFileId(id: string, filename?: string) {
    gpxFileId.value = id
    gpxFile.value = null
    templateId.value = null
    gpxFilename.value = filename ?? null
    clearResult()
  }

  function clearResult() {
    result.value = null
    rowNotes.value = {}
    activePlanId.value = null
    error.value = null
  }

  function clearAll() {
    gpxFile.value = null
    gpxFilename.value = null
    templateId.value = null
    gpxFileId.value = null
    clearResult()
  }

  function loadNotes(notes: PlanNote[]) {
    rowNotes.value = {}
    for (const n of notes) rowNotes.value[n.km] = n.note
  }

  function setNote(km: number, note: string) {
    rowNotes.value[km] = note
    if (!activePlanId.value) return
    if (_saveTimer) clearTimeout(_saveTimer)
    _saveTimer = setTimeout(() => saveNotesNow(), 600)
  }

  async function saveNotesNow() {
    if (!activePlanId.value) return
    if (_saveTimer) { clearTimeout(_saveTimer); _saveTimer = null }
    const notes = Object.entries(rowNotes.value)
      .filter(([, v]) => v.trim())
      .map(([km, note]) => ({ km: Number(km), note }))
    await plansApi.saveNotes(activePlanId.value, notes)
  }

  /** Enrich split_table with any notes stored locally */
  function splitTableWithNotes(): (SplitRow & { note: string })[] {
    if (!result.value) return []
    return result.value.split_table.map((row) => ({
      ...row,
      note: rowNotes.value[row.km] ?? '',
    }))
  }

  async function runAnalysis(config: AnalyzeConfig) {
    const hasFile = !!gpxFile.value
    const hasTemplate = !!templateId.value
    const hasGpxFileId = !!gpxFileId.value
    if (!hasFile && !hasTemplate && !hasGpxFileId) {
      error.value = 'No GPX file or template selected.'
      return
    }
    isLoading.value = true
    error.value = null
    try {
      const { data } = hasFile
        ? await analyzeApi.run(gpxFile.value!, config)
        : hasTemplate
          ? await analyzeApi.runWithTemplate(templateId.value!, config)
          : await analyzeApi.runWithGpxFileId(gpxFileId.value!, config)
      result.value = data
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail ?? axiosErr.message ?? 'Analysis failed.'
    } finally {
      isLoading.value = false
    }
  }

  return {
    gpxFile,
    gpxFilename,
    templateId,
    gpxFileId,
    result,
    rowNotes,
    activePlanId,
    isLoading,
    error,
    setGpxFile,
    setTemplateId,
    setGpxFileId,
    clearResult,
    clearAll,
    loadNotes,
    setNote,
    saveNotesNow,
    splitTableWithNotes,
    runAnalysis,
  }
})
