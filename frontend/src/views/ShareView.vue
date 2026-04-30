<template>
  <v-container fluid class="pa-4" style="max-width: 1200px; margin: auto">
    <!-- Loading -->
    <div v-if="isLoading" class="text-center py-16">
      <v-progress-circular indeterminate color="primary" size="64" />
      <p class="text-body-1 mt-4">Loading race plan…</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-16">
      <v-icon icon="mdi-alert-circle-outline" size="80" color="error" />
      <p class="text-h6 mt-4">{{ error }}</p>
    </div>

    <!-- Loaded -->
    <template v-else-if="planData">
      <!-- Header -->
      <div class="d-flex align-center mb-4 flex-wrap" style="gap: 12px">
        <div>
          <div class="text-h5 font-weight-bold">{{ planData.plan.nickname }}</div>
          <v-chip
            size="small"
            color="primary"
            variant="tonal"
            prepend-icon="mdi-share-variant"
            class="mt-1"
          >
            Shared Race Plan
          </v-chip>
        </div>
        <v-spacer />
        <v-btn
          prepend-icon="mdi-file-pdf-box"
          variant="tonal"
          color="primary"
          @click="downloadPdf()"
        >
          Download PDF
        </v-btn>
      </div>

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

      <!-- Unit toggle -->
      <div class="d-flex align-center mb-3">
        <v-switch
          v-model="useImperial"
          label="Imperial (miles)"
          density="compact"
          color="primary"
          hide-details
        />
      </div>

      <!-- Map -->
      <v-card elevation="1" class="mb-4">
        <v-card-title class="text-subtitle-2 py-2 px-4">
          <v-icon icon="mdi-map" class="mr-1" />
          Route Map
        </v-card-title>
        <v-card-text class="pa-0">
          <!-- eslint-disable-next-line vue/no-v-html -->
          <iframe
            :srcdoc="planData.analysis.map_html"
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
      <v-card elevation="1">
        <v-card-title class="text-subtitle-2 py-2 px-4 d-flex align-center">
          <v-icon icon="mdi-table" class="mr-1" />
          Split Table
          <v-spacer />
          <v-checkbox
            v-if="hasMarkers"
            v-model="markersOnly"
            label="Markers only"
            density="compact"
            hide-details
            class="ml-2"
            style="max-width: 160px"
          />
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
            <span class="text-caption text-medium-emphasis">{{ item.note }}</span>
          </template>
        </v-data-table>
      </v-card>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { generatePdf } from '@/composables/usePdfExport'
import { plansApi } from '@/api'
import PlotlyChart from '@/components/PlotlyChart.vue'
import Plotly from 'plotly.js-dist-min'
import type { PlanWithAnalysis } from '@/types'

const route = useRoute()
const planId = route.params.planId as string

const planData = ref<PlanWithAnalysis | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const useImperial = ref(false)
const markersOnly = ref(false)

const elevationChartRef = ref<{ getDiv: () => HTMLDivElement | null } | null>(null)
const paceChartRef = ref<{ getDiv: () => HTMLDivElement | null } | null>(null)

const KM_TO_MILE = 0.621371
const M_TO_FT = 3.28084

onMounted(async () => {
  try {
    const { data } = await plansApi.getShare(planId)
    planData.value = data
  } catch {
    error.value = 'This race plan could not be found or is no longer available.'
  } finally {
    isLoading.value = false
  }
})

// ── Helpers ────────────────────────────────────────────────────────────────

function formatPace(minPerKm: number): string {
  let m = Math.floor(minPerKm)
  let s = Math.round((minPerKm - m) * 60)
  if (s === 60) { m += 1; s = 0 }
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatPaceImperial(minPerKm: number): string {
  return formatPace(minPerKm / KM_TO_MILE)
}

// ── Summary cards ───────────────────────────────────────────────────────────

const summaryCards = computed(() => {
  const s = planData.value?.analysis.summary
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

// ── Chart data ─────────────────────────────────────────────────────────────

const elevationChartData = computed(() => {
  const raw = planData.value?.analysis.elevation_chart_data
  if (!raw) return null
  return useImperial.value
    ? raw.map((p) => ({ x: p.x * KM_TO_MILE, y: p.y * M_TO_FT }))
    : raw
})

const paceChartData = computed(() => {
  const raw = planData.value?.analysis.pace_chart_data
  if (!raw) return null
  return useImperial.value
    ? raw.map((p) => ({ x: p.x * KM_TO_MILE, y: p.y / KM_TO_MILE }))
    : raw
})

const elevationXLabel = computed(() => useImperial.value ? 'Distance (miles)' : 'Distance (km)')
const elevationYLabel = computed(() => useImperial.value ? 'Elevation (ft)' : 'Elevation (m)')
const paceXLabel = computed(() => useImperial.value ? 'Distance (miles)' : 'Distance (km)')
const paceYLabel = computed(() => useImperial.value ? 'Pace (min/mile)' : 'Pace (min/km)')

// ── Split table ─────────────────────────────────────────────────────────────

const hasNotes = computed(() =>
  planData.value?.notes.some((n) => n.note.trim()) ?? false
)

const hasMarkers = computed(() =>
  planData.value?.analysis.split_table.some((r) => r.custom_marker) ?? false
)

const splitHeaders = computed(() => {
  const base: { title: string; key: string; width?: string; sortable?: boolean }[] = [
    { title: 'km', key: 'km', width: '48px' },
    { title: 'Pace', key: 'pace_min_per_km', width: '100px' },
    { title: 'Time', key: 'cumulative_time_hms', width: '90px' },
    { title: 'Clock', key: 'clock_time', width: '80px' },
    { title: 'Marker', key: 'custom_marker', width: '110px' },
  ]
  base.splice(1, 0, useImperial.value
    ? { title: 'Dist (mi)', key: 'total_distance_km', width: '70px' }
    : { title: 'Dist (km)', key: 'total_distance_km', width: '70px' }
  )
  base.splice(2, 0, useImperial.value
    ? { title: 'Elev (ft)', key: 'elevation_m', width: '80px' }
    : { title: 'Elev (m)', key: 'elevation_m', width: '80px' }
  )
  const hasCutoffs = planData.value?.analysis.split_table.some((r) => r.cutoff_time)
  if (hasCutoffs) {
    base.splice(7, 0, { title: 'Cutoff', key: 'cutoff_time', width: '80px' })
    base.splice(8, 0, { title: 'Buffer', key: 'cutoff_buffer_min', width: '80px' })
  }
  if (hasNotes.value) {
    base.push({ title: 'Notes', key: 'note' })
  }
  return base
})

const displayRows = computed(() => {
  if (!planData.value) return []
  const noteMap: Record<number, string> = {}
  for (const n of planData.value.notes) noteMap[n.km] = n.note

  const rows = planData.value.analysis.split_table.map((row) => ({
    ...row,
    note: noteMap[row.km] ?? '',
  }))

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
      : formatPace(row.pace_min_per_km),
  }))
})

// ── PDF generation ──────────────────────────────────────────────────────────

async function downloadPdf() {
  if (!planData.value) return
  const noteMap: Record<number, string> = {}
  for (const n of planData.value.notes) noteMap[n.km] = n.note

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
    routeName: planData.value.plan.nickname,
    summary: planData.value.analysis.summary,
    splits: planData.value.analysis.split_table,
    noteMap,
    useImperial: useImperial.value,
    markersOnly: markersOnly.value,
    elevationChartImg,
    paceChartImg,
  })
}
</script>


