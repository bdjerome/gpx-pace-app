<template>
  <v-container fluid class="pa-4">
    <v-row>
      <!-- ---------------------------------------------------------------- -->
      <!-- LEFT COLUMN — configuration form                                  -->
      <!-- ---------------------------------------------------------------- -->
      <v-col cols="12" md="4">
        <v-card elevation="2" class="mb-4">
          <v-card-title class="text-subtitle-1 font-weight-bold py-3 px-4 bg-grey-lighten-4">
            <!-- <v-icon icon="mdi-map-marker-path" class="mr-2" /> -->
            Route Selection
          </v-card-title>
          <v-card-text>
            <!-- GPX file drop zone -->
            <div
              class="drop-zone pa-6 text-center rounded"
              :class="{ 'drop-zone--active': isDragging }"
              @dragover.prevent="isDragging = true"
              @dragleave="isDragging = false"
              @drop.prevent="handleDrop"
            >
              <v-icon icon="mdi-upload" size="36" color="primary" />
              <p class="mt-2 text-body-2">
                {{ analysis.gpxFilename ?? 'Drop a .gpx file here or click to browse' }}
              </p>
              <v-btn variant="outlined" size="small" class="mt-2" @click="triggerFilePicker">
                Browse…
              </v-btn>
              <input
                ref="fileInput"
                type="file"
                accept=".gpx"
                style="display: none"
                @change="handleFileSelect"
              />
            </div>

            <!-- Template GPX dropdown (all users) -->
            <v-autocomplete
              v-model="selectedTemplateId"
              :items="plans.templates"
              item-title="description"
              item-value="id"
              label="Or pick a template route"
              clearable
              prepend-inner-icon="mdi-map-outline"
              class="mt-4"
              density="compact"
              :hint="selectedTemplateDescription"
              persistent-hint
              @update:model-value="loadTemplate"
            />

            <!-- Saved routes dropdown (auth only) -->
            <v-autocomplete
              v-if="auth.isAuthenticated"
              v-model="selectedPlanId"
              :items="plans.plans"
              item-title="nickname"
              item-value="id"
              label="Load a saved plan"
              clearable
              prepend-inner-icon="mdi-bookmark-outline"
              class="mt-3"
              density="compact"
              @update:model-value="loadPlan"
            />
          </v-card-text>
        </v-card>

        <!-- Analysis configuration -->
        <v-card elevation="2">
          <v-card-title class="text-subtitle-1 font-weight-bold py-3 px-4 bg-grey-lighten-4">
            Analysis Configuration
          </v-card-title>
          <v-card-text>
            <v-form ref="formRef" @submit.prevent="submitAnalysis">
              <!-- Pace unit -->
              <p class="text-caption text-medium-emphasis mb-1">Pace Unit</p>
              <v-btn-toggle v-model="config.pace_unit" mandatory density="compact" class="mb-3">
                <v-btn value="min/km" size="small">min/km</v-btn>
                <v-btn value="min/mile" size="small">min/mile</v-btn>
              </v-btn-toggle>

              <!-- Base pace -->
              <v-text-field
                v-model="config.base_pace"
                label="Base Pace (M:SS)"
                placeholder="5:30"
                density="compact"
                :rules="[paceRule]"
                class="mb-2"
              />

              <!-- Race start time -->
              <v-text-field
                v-model="config.race_start_time"
                label="Race Start Time (HH:MM)"
                placeholder="08:00"
                density="compact"
                :rules="[timeRule]"
                class="mb-2"
              />

              <!-- Race date -->
              <v-menu v-model="dateMenu" :close-on-content-click="false" min-width="auto">
                <template #activator="{ props }">
                  <v-text-field
                    v-bind="props"
                    :model-value="config.race_date"
                    label="Race Date"
                    prepend-inner-icon="mdi-calendar"
                    readonly
                    clearable
                    density="compact"
                    class="mb-2"
                    @click:clear="config.race_date = undefined"
                  />
                </template>
                <v-date-picker
                  :model-value="raceDateObj"
                  show-adjacent-months
                  @update:model-value="onDateSelected"
                />
              </v-menu>

              <!-- Loops -->
              <v-number-input
                v-model="config.loops"
                label="Loops"
                :min="1"
                :max="10"
                density="compact"
                control-variant="stacked"
                class="mb-2"
              />

              <!-- Options -->
              <!-- <v-checkbox
                v-model="config.decay"
                label="Enable fatigue decay"
                density="compact"
                hide-details
                class="mb-2"
              /> -->
              <v-checkbox
                v-model="config.hill_mode"
                label="Enable hill adjustments"
                density="compact"
                hide-details
                class="mb-2"
              />

              <!-- Custom Markers -->
              <v-expansion-panels variant="accordion" class="mb-4">
                <v-expansion-panel>
                  <v-expansion-panel-title class="text-caption font-weight-bold">
                    Custom Markers ({{ config.custom_markers.length }})
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-checkbox
                      v-model="markersOnly"
                      label="Show only custom markers in split table"
                      density="compact"
                      class="text-caption"
                      hide-details
                    />
                    <v-data-table
                      :headers="markerHeaders"
                      :items="config.custom_markers"
                      density="compact"
                      hide-default-footer
                      class="marker-table"
                    >
                      <template #item.distance="{ item, index }">
                        <v-text-field
                          v-if="config.custom_markers[index]"
                          v-model.number="config.custom_markers[index]!.distance"
                          density="compact"
                          hide-details
                          type="number"
                          style="min-width: 70px"
                        />
                      </template>
                      <template #item.nickname="{ item, index }">
                        <v-text-field
                          v-if="config.custom_markers[index]"
                          v-model="config.custom_markers[index]!.nickname"
                          density="compact"
                          hide-details
                        />
                      </template>
                      <template #item.cutoff_time="{ item, index }">
                        <v-text-field
                          v-if="config.custom_markers[index]"
                          v-model="config.custom_markers[index]!.cutoff_time"
                          density="compact"
                          hide-details
                          placeholder="HH:MM"
                        />
                      </template>
                      <template #item.actions="{ index }">
                        <v-btn
                          icon="mdi-delete"
                          size="x-small"
                          variant="text"
                          color="error"
                          @click="removeMarker(index)"
                        />
                      </template>
                    </v-data-table>
                    <v-btn
                      size="small"
                      variant="tonal"
                      prepend-icon="mdi-plus"
                      class="mt-2"
                      @click="addMarker"
                    >
                      Add Marker
                    </v-btn>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>

              <v-btn
                type="submit"
                color="primary"
                block
                :loading="analysis.isLoading"
                :disabled="!analysis.gpxFile && !analysis.templateId && !analysis.gpxFileId"
                prepend-icon="mdi-play"
              >
                Analyze Route
              </v-btn>
            </v-form>

            <v-alert
              v-if="analysis.error"
              type="error"
              variant="tonal"
              class="mt-3"
              closable
              @click:close="analysis.error = null"
            >
              {{ analysis.error }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ---------------------------------------------------------------- -->
      <!-- RIGHT COLUMN — results                                            -->
      <!-- ---------------------------------------------------------------- -->
      <v-col cols="12" md="8">
        <!-- Empty state -->
        <div v-if="!analysis.result && !analysis.isLoading" class="text-center py-16">
          <v-icon icon="mdi-map-search-outline" size="80" color="grey-lighten-1" />
          <p class="text-h6 text-medium-emphasis mt-4">Upload a GPX file and run analysis to see results</p>
        </div>

        <!-- Loading spinner -->
        <div v-if="analysis.isLoading" class="text-center py-16">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="text-body-1 mt-4">Analyzing route…</p>
        </div>

        <!-- Results -->
        <template v-if="analysis.result">
          <!-- Summary cards -->
          <v-row class="mb-4">
            <v-col v-for="card in summaryCards" :key="card.label" cols="6" sm="3">
              <v-card variant="outlined">
                <v-card-text class="text-center pa-3">
                  <v-icon :icon="card.icon" color="primary" />
                  <div class="text-h6 font-weight-bold mt-1">{{ card.value }}</div>
                  <div class="text-caption text-medium-emphasis">{{ card.label }}</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- Unit toggle + actions -->
          <div class="d-flex flex-wrap align-center gap-2 mb-3">
            <v-switch
              v-model="useImperial"
              label="Imperial (miles)"
              density="compact"
              hide-details
              color="primary"
              style="min-width: 140px; flex-shrink: 0"
            />
            <v-spacer class="d-none d-sm-block" />
            <div class="d-flex flex-wrap gap-2">
              <v-btn
                v-if="selectedPlanId"
                variant="text"
                prepend-icon="mdi-share-variant-outline"
                size="small"
                @click="copyShareLink"
              >
                Copy Share Link
              </v-btn>
              <v-btn
                v-if="auth.isAuthenticated"
                variant="outlined"
                prepend-icon="mdi-content-save-outline"
                size="small"
                @click="openSaveDialog"
              >
                Save Plan
              </v-btn>
              <v-btn
                variant="outlined"
                prepend-icon="mdi-file-pdf-box"
                size="small"
                @click="downloadPdf"
              >
                Download PDF
              </v-btn>
            </div>
          </div>

          <!-- Map iframe -->
          <v-card elevation="1" class="mb-4">
            <v-card-title class="text-subtitle-2 py-2 px-4">
              
              Route Map
            </v-card-title>
            <v-card-text class="pa-0">
              <!-- eslint-disable-next-line vue/no-v-html -->
              <iframe
                :srcdoc="analysis.result.map_html"
                width="100%"
                height="450"
                frameborder="0"
                style="border: none"
                sandbox="allow-scripts allow-same-origin"
              />
            </v-card-text>
          </v-card>

          <!-- Charts -->
          <v-row class="mb-4">
            <v-col cols="12" md="6">
              <v-card elevation="1">
                <v-card-title class="text-subtitle-2 py-2 px-4">Elevation Profile</v-card-title>
                <v-card-text class="pa-2">
                  <PlotlyChart
                    ref="elevationChartRef"
                    :chart-data="elevationChartData"
                    :x-label="elevationXLabel"
                    :y-label="elevationYLabel"
                    :height="300"
                  />
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" md="6">
              <v-card elevation="1">
                <v-card-title class="text-subtitle-2 py-2 px-4">Pace Profile</v-card-title>
                <v-card-text class="pa-2">
                  <PlotlyChart
                    ref="paceChartRef"
                    :chart-data="paceChartData"
                    :x-label="paceXLabel"
                    :y-label="paceYLabel"
                    :height="300"
                  />
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- Split table -->
          <v-card elevation="1" class="split-table-card">
            <v-card-title class="text-subtitle-2 py-2 px-4">
              
              Split Table
            </v-card-title>
            <v-data-table
              :headers="splitHeaders"
              :items="displayRows"
              density="compact"
              :items-per-page="50"
            >
              <template #item.custom_marker="{ item }">
                <v-chip v-if="item.custom_marker" size="x-small" color="accent" label>
                  {{ item.custom_marker }}
                </v-chip>
              </template>
              <template #item.cutoff_buffer_min="{ item }">
                <span
                  v-if="item.cutoff_buffer_min !== null"
                  :class="item.cutoff_buffer_min < 0 ? 'text-error' : 'text-success'"
                >
                  {{ item.cutoff_buffer_min > 0 ? '+' : '' }}{{ item.cutoff_buffer_min?.toFixed(0) }} min
                </span>
              </template>
              <template #item.note="{ item }">
                <div class="note-cell">
                  <v-textarea
                    :model-value="item.note"
                    density="compact"
                    hide-details
                    placeholder="Add note…"
                    variant="plain"
                    auto-grow
                    rows="1"
                    @update:model-value="(v) => analysis.setNote(item.km, v)"
                  />
                </div>
              </template>
            </v-data-table>
          </v-card>
        </template>
      </v-col>
    </v-row>

    <!-- Save Plan Dialog -->
    <v-dialog v-model="saveDialog" max-width="400">
      <v-card>
        <v-card-title>{{ selectedPlanId ? 'Update Plan' : 'Save Plan' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="saveName" label="Plan name" autofocus density="compact" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="saveDialog = false">Cancel</v-btn>
          <v-btn
            v-if="selectedPlanId"
            variant="outlined"
            :loading="isSaving"
            @click="confirmSave('create')"
          >
            Save as New
          </v-btn>
          <v-btn
            color="primary"
            :loading="isSaving"
            @click="confirmSave(selectedPlanId ? 'update' : 'create')"
          >
            {{ selectedPlanId ? 'Update' : 'Save' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar feedback -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000" location="bottom right">
      {{ snackbarMessage }}
      <template #actions>
        <v-btn variant="text" @click="snackbar = false">Dismiss</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAnalysisStore } from '@/stores/analysis'
import { useAuthStore } from '@/stores/auth'
import { usePlansStore } from '@/stores/plans'
import { plansApi, gpxApi } from '@/api'
import PlotlyChart from '@/components/PlotlyChart.vue'
import { generatePdf } from '@/composables/usePdfExport'
import Plotly from 'plotly.js-dist-min'
import type { AnalyzeConfig, CustomMarker } from '@/types'

const analysis = useAnalysisStore()
const auth = useAuthStore()
const plans = usePlansStore()
const route = useRoute()

// ─── Chart refs (for PDF export) ─────────────────────────────────────────
const elevationChartRef = ref<{ getDiv: () => HTMLDivElement | null } | null>(null)
const paceChartRef = ref<{ getDiv: () => HTMLDivElement | null } | null>(null)

// ─── File handling ─────────────────────────────────────────────────────────
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

function triggerFilePicker() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) analysis.setGpxFile(file)
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file && file.name.endsWith('.gpx')) analysis.setGpxFile(file)
}

// ─── Configuration ─────────────────────────────────────────────────────────
const config = ref<AnalyzeConfig>({
  loops: 1,
  base_pace: '5:30',
  race_start_time: '08:00',
  decay: false,
  hill_mode: false,
  pace_unit: 'min/km',
  custom_markers: [],
})

const paceRule = (v: string) => /^\d+:\d{2}$/.test(v) || 'Format: M:SS (e.g. 5:30)'
const timeRule = (v: string) => /^\d{1,2}:\d{2}$/.test(v) || 'Format: HH:MM (e.g. 08:00)'

// ─── Date picker ────────────────────────────────────────────────────────────
const dateMenu = ref(false)

const raceDateObj = computed(() => {
  const d = config.value.race_date
  return d ? new Date(d + 'T00:00:00') : new Date()
})

function onDateSelected(date: Date) {
  config.value.race_date = date.toISOString().slice(0, 10)
  dateMenu.value = false
}

const markerHeaders = [
  { title: 'Distance', key: 'distance', width: '90px' },
  { title: 'Name', key: 'nickname' },
  { title: 'Cutoff', key: 'cutoff_time', width: '90px' },
  { title: '', key: 'actions', width: '40px', sortable: false },
]

const markersOnly = ref(false)

function addMarker() {
  config.value.custom_markers.push({ distance: 0, nickname: '', cutoff_time: undefined })
}
function removeMarker(index: number) {
  config.value.custom_markers.splice(index, 1)
}

// ─── Form submission ────────────────────────────────────────────────────────
const formRef = ref()

async function submitAnalysis() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  await analysis.runAnalysis(config.value)
}

// ─── Load template ────────────────────────────────────────────────────────
const selectedTemplateId = ref<string | null>(null)

const selectedTemplateDescription = computed(() => {
  if (!selectedTemplateId.value) return ''
  const t = plans.templates.find((t) => t.id === selectedTemplateId.value)
  if (!t) return ''
  const parts: string[] = []
  if (t.description) parts.push(t.description)
  if (t.distance_m) parts.push(`${Number(t.distance_m).toFixed(1)} mi`)
  return parts.join(' · ')
})

async function loadTemplate(id: string | null) {
  if (!id) {
    analysis.clearAll()
    return
  }
  // Clear any previously uploaded file — template takes over as the active GPX
  selectedPlanId.value = null
  const template = plans.templates.find((t) => t.id === id)
  if (template) {
    // setTemplateId handles nulling gpxFile, setting templateId, and clearing result
    analysis.setTemplateId(id, template.file_name)
  }
}

// ─── Load saved plan ───────────────────────────────────────────────────────
const selectedPlanId = ref<string | null>(null)

async function loadPlan(id: string | null) {
  if (!id) return
  try {
    const { data } = await plansApi.get(id)
    const c = data.plan.config
    config.value = {
      loops: c.loops,
      base_pace: c.pace,
      race_start_time: c.start_time,
      race_date: c.race_date ?? new Date().toISOString().slice(0, 10),
      decay: c.decay_enabled,
      hill_mode: c.hills_enabled,
      pace_unit: c.pace_unit as 'min/km' | 'min/mile',
      custom_markers: (c.markers as CustomMarker[]) ?? [],
    }
    // Restore the GPX source so the Analyze button is enabled for re-runs
    if (data.plan.template_gpx_file_id) {
      const tmpl = plans.templates.find((t) => t.id === data.plan.template_gpx_file_id)
      analysis.setTemplateId(data.plan.template_gpx_file_id, tmpl?.file_name)
      selectedTemplateId.value = data.plan.template_gpx_file_id
    } else if (data.plan.gpx_file_id) {
      const planSummary = plans.plans.find((p) => p.id === id)
      analysis.setGpxFileId(data.plan.gpx_file_id, planSummary?.gpx_filename ?? undefined)
    }
    // Load results directly — backend already re-ran the analysis
    analysis.result = data.analysis
    analysis.activePlanId = id
    analysis.loadNotes(data.notes ?? [])
  } catch {
    // error handled by axios interceptor
  }
}

// ─── Summary cards ──────────────────────────────────────────────────────────
const useImperial = ref(false)
const KM_TO_MILE = 0.621371
const M_TO_FT = 3.28084

const summaryCards = computed(() => {
  const s = analysis.result?.summary
  if (!s) return []
  const dist = useImperial.value
    ? `${(s.total_distance_km * KM_TO_MILE).toFixed(1)} mi`
    : `${s.total_distance_km.toFixed(1)} km`
  const pace = useImperial.value
    ? `${formatPaceImperial(s.avg_pace_min_per_km)} /mi`
    : `${formatPace(s.avg_pace_min_per_km)} /km`

    const elevation = useImperial.value
    ? `${(s.elevation_gain_m * M_TO_FT).toFixed(0)} ft`
    : `${s.elevation_gain_m.toFixed(0)} m`
  return [
    { label: 'Distance', value: dist, icon: 'mdi-map-marker-distance' },
    { label: 'Avg Pace', value: pace, icon: 'mdi-speedometer' },
    { label: 'Duration', value: s.total_duration_hms, icon: 'mdi-clock-outline' },
    { label: 'Elev Gain', value: elevation, icon: 'mdi-terrain' },
  ]
})

function formatPace(minPerKm: number): string {
  let m = Math.floor(minPerKm)
  let s = Math.round((minPerKm - m) * 60)
  if (s === 60) { m += 1; s = 0 }
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatPaceImperial(minPerKm: number): string {
  const minPerMile = minPerKm / KM_TO_MILE
  return `${formatPace(minPerMile)}`
}

// ─── Chart data (computed so unit toggle triggers re-render) ───────────────
const elevationChartData = computed(() => {
  const raw = analysis.result?.elevation_chart_data
  if (!raw) return null
  return useImperial.value
    ? raw.map((p) => ({ x: p.x * KM_TO_MILE, y: p.y * M_TO_FT }))
    : raw
})

const paceChartData = computed(() => {
  const raw = analysis.result?.pace_chart_data
  if (!raw) return null
  return useImperial.value
    ? raw.map((p) => ({ x: p.x * KM_TO_MILE, y: p.y / KM_TO_MILE }))
    : raw
})

const elevationXLabel = computed(() => useImperial.value ? 'Distance (miles)' : 'Distance (km)')
const elevationYLabel = computed(() => useImperial.value ? 'Elevation (ft)' : 'Elevation (m)')
const paceXLabel = computed(() => useImperial.value ? 'Distance (miles)' : 'Distance (km)')
const paceYLabel = computed(() => useImperial.value ? 'Pace (min/mile)' : 'Pace (min/km)')

// ─── Split table ───────────────────────────────────────────────────────────
const splitHeaders = computed(() => {
  const base = [
    { title: 'km', key: 'km', width: '48px' },
    // Dist column will be inserted next
    // { title: 'Elev (m)', key: 'elevation_m', width: '80px' },
    { title: 'Pace', key: 'pace_min_per_km', width: '100px' },
    { title: 'Time', key: 'cumulative_time_hms', width: '90px' },
    { title: 'Clock', key: 'clock_time', width: '80px' },
    { title: 'Marker', key: 'custom_marker', width: '110px' },
    { title: 'Notes', key: 'note' },
  ]
  // Insert Dist column after 'km'
  base.splice(1, 0, useImperial.value
    ? { title: 'Dist (mi)', key: 'total_distance_km', width: '70px' }
    : { title: 'Dist (km)', key: 'total_distance_km', width: '70px' }
  )
  base.splice(2,0, useImperial.value
    ? { title: 'Elev (ft)', key: 'elevation_m', width: '80px' }
    : { title: 'Elev (m)', key: 'elevation_m', width: '80px' }
  )
  const hasCutoffs = analysis.result?.split_table.some((r) => r.cutoff_time)
  if (hasCutoffs) {
    base.splice(7, 0, { title: 'Cutoff', key: 'cutoff_time', width: '80px' })
    base.splice(8, 0, { title: 'Buffer', key: 'cutoff_buffer_min', width: '80px' })
  }
  return base
})

const displayRows = computed(() => {
  const rows = analysis.splitTableWithNotes()
  const source = markersOnly.value
    ? rows.filter((row, i) => i === 0 || i === rows.length - 1 || !!row.custom_marker)
    : rows
  return source.map((row) => ({
    ...row,
    total_distance_km: useImperial.value
      ? (row.total_distance_km * KM_TO_MILE).toFixed()
      : row.total_distance_km.toFixed(2),
    elevation_m: useImperial.value
      ? (row.elevation_m * M_TO_FT).toFixed(0)
      : row.elevation_m.toFixed(0),
    pace_min_per_km: useImperial.value
      ? formatPaceImperial(row.pace_min_per_km)
      : `${formatPace(row.pace_min_per_km)}`,
  }))
})

// ─── Save plan ─────────────────────────────────────────────────────────────
const saveDialog = ref(false)
const saveName = ref('')
const isSaving = ref(false)

const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref<'success' | 'error'>('success')

function showSnackbar(message: string, color: 'success' | 'error') {
  snackbarMessage.value = message
  snackbarColor.value = color
  snackbar.value = true
}

function openSaveDialog() {
  if (selectedPlanId.value) {
    const plan = plans.plans.find((p) => p.id === selectedPlanId.value)
    saveName.value = plan?.nickname ?? analysis.gpxFilename?.replace('.gpx', '') ?? ''
  } else {
    saveName.value = analysis.gpxFilename?.replace('.gpx', '') ?? ''
  }
  saveDialog.value = true
}

function copyShareLink() {
  const url = `${window.location.origin}/share/${selectedPlanId.value}`
  navigator.clipboard.writeText(url)
  showSnackbar('Share link copied to clipboard!', 'success')
}

async function downloadPdf() {
  if (!analysis.result) return
  const routeName = selectedPlanId.value
    ? (plans.plans.find((p) => p.id === selectedPlanId.value)?.nickname ?? analysis.gpxFilename?.replace('.gpx', '') ?? 'GPX Analysis')
    : (analysis.gpxFilename?.replace('.gpx', '') ?? 'GPX Analysis')

  let elevationChartImg: string | undefined
  let paceChartImg: string | undefined

  const elevDiv = elevationChartRef.value?.getDiv()
  if (elevDiv) {
    try { elevationChartImg = await Plotly.toImage(elevDiv, { format: 'png', width: 700, height: 280 }) } catch {}
  }
  const paceDiv = paceChartRef.value?.getDiv()
  if (paceDiv) {
    try { paceChartImg = await Plotly.toImage(paceDiv, { format: 'png', width: 700, height: 280 }) } catch {}
  }

  await generatePdf({
    routeName,
    summary: analysis.result.summary,
    splits: analysis.result.split_table,
    noteMap: { ...analysis.rowNotes },
    useImperial: useImperial.value,
    markersOnly: markersOnly.value,
    elevationChartImg,
    paceChartImg,
  })
}

async function confirmSave(mode: 'create' | 'update' = 'create') {
  if (!saveName.value) return
  isSaving.value = true
  try {
    if (mode === 'update' && selectedPlanId.value) {
      // Update the existing plan's nickname + config only; GPX source stays the same.
      await plans.updatePlan(selectedPlanId.value, {
        nickname: saveName.value,
        config: {
          pace: config.value.base_pace,
          pace_unit: config.value.pace_unit,
          loops: config.value.loops,
          start_time: config.value.race_start_time,
          race_date: config.value.race_date,
          decay_enabled: config.value.decay,
          hills_enabled: config.value.hill_mode,
          markers: config.value.custom_markers,
        },
      })
      if (plans.error) {
        showSnackbar(plans.error, 'error')
      } else {
        saveDialog.value = false
        showSnackbar('Plan updated successfully!', 'success')
      }
    } else {
      // Create a new plan — resolve the GPX source reference.
      let gpxFileId: string | undefined
      let templateGpxFileId: string | undefined

      if (analysis.templateId) {
        templateGpxFileId = analysis.templateId
      } else if (analysis.gpxFileId) {
        // Already stored on the server from a previously loaded plan
        gpxFileId = analysis.gpxFileId
      } else if (analysis.gpxFile) {
        const { data } = await gpxApi.upload(analysis.gpxFile)
        gpxFileId = data.file_id
      } else {
        return // nothing to save
      }

      const newId = await plans.savePlan({
        nickname: saveName.value,
        gpx_file_id: gpxFileId,
        template_gpx_file_id: templateGpxFileId,
        config: {
          pace: config.value.base_pace,
          pace_unit: config.value.pace_unit,
          loops: config.value.loops,
          start_time: config.value.race_start_time,
          race_date: config.value.race_date,
          decay_enabled: config.value.decay,
          hills_enabled: config.value.hill_mode,
          markers: config.value.custom_markers,
        },
      })
      if (!newId) {
        showSnackbar(plans.error ?? 'Failed to save plan.', 'error')
      } else {
        // Point the "Load a saved plan" dropdown at the newly created plan so
        // subsequent "Save Plan" opens in Update mode for the fork.
        selectedPlanId.value = newId
        analysis.activePlanId = newId
        saveDialog.value = false
        await analysis.saveNotesNow()
        showSnackbar('Plan saved successfully!', 'success')
      }
    }
  } finally {
    isSaving.value = false
  }
}

// ─── Init ───────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([
    plans.fetchTemplates(),
    auth.isAuthenticated ? plans.fetchPlans() : Promise.resolve(),
  ])
  // If navigated here from PlansView, load the requested plan into local state.
  const planId = route.query.planId as string | undefined
  if (planId) {
    selectedPlanId.value = planId
    await loadPlan(planId)
  }
})
</script>

<style scoped>
.drop-zone {
  border: 2px dashed #bdbdbd;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}
.drop-zone:hover,
.drop-zone--active {
  border-color: #e65100;
  background-color: #fff3e0;
}
.marker-table :deep(.v-data-table__td) {
  padding: 2px 4px !important;
}

/* Split table — horizontal scroll on mobile */
.split-table-card :deep(.v-table__wrapper) {
  overflow-x: auto;
}

/* Notes column — allow text to wrap instead of truncating */
.split-table-card :deep(.note-cell) {
  min-width: 160px;
  white-space: normal;
  word-break: break-word;
}
</style>
