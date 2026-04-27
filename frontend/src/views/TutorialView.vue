<template>
  <v-container max-width="800" class="pa-6">
    <h1 class="text-h4 font-weight-bold mb-2">How to use GPX Pace Planner</h1>
    <p class="text-body-1 text-medium-emphasis mb-6">
      A step-by-step guide to planning your race pace from a GPX route file.
    </p>

    <v-timeline side="end" density="compact">
      <v-timeline-item
        v-for="step in steps"
        :key="step.title"
        :dot-color="step.color ?? 'primary'"
        size="small"
      >
        <template #opposite>
          <v-icon :icon="step.icon" :color="step.color ?? 'primary'" />
        </template>
        <v-card variant="outlined" class="mb-2">
          <v-card-title class="text-subtitle-1 font-weight-bold py-2 px-4">{{ step.title }}</v-card-title>
          <v-card-text class="text-body-2" v-html="step.body" />
        </v-card>
      </v-timeline-item>
    </v-timeline>

    <v-divider class="my-8" />

    <h2 class="text-h6 font-weight-bold mb-4">Configuration reference</h2>

    <v-table density="compact">
      <thead>
        <tr>
          <th>Setting</th>
          <th>Description</th>
          <th>Example</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in reference" :key="row.setting">
          <td><code>{{ row.setting }}</code></td>
          <td>{{ row.description }}</td>
          <td class="text-medium-emphasis">{{ row.example }}</td>
        </tr>
      </tbody>
    </v-table>

    <v-divider class="my-8" />

    <h2 class="text-h6 font-weight-bold mb-3">Tips &amp; common pitfalls</h2>
    <v-list density="compact">
      <v-list-item v-for="tip in tips" :key="tip.title" :prepend-icon="tip.icon">
        <v-list-item-title class="font-weight-medium">{{ tip.title }}</v-list-item-title>
        <v-list-item-subtitle>{{ tip.body }}</v-list-item-subtitle>
      </v-list-item>
    </v-list>
  </v-container>
</template>

<script setup lang="ts">
const steps = [
  {
    icon: 'mdi-file-upload-outline',
    title: '1. Upload your GPX file',
    body: 'Drag and drop (or click <em>Browse…</em>) to load a <code>.gpx</code> file exported from your GPS watch, Strava, Garmin Connect, Komoot, etc. The file is processed entirely on the server — nothing is stored unless you explicitly save a plan.',
  },
  {
    icon: 'mdi-tune',
    title: '2. Set your base pace',
    body: 'Enter your target pace in <code>M:SS</code> format — for example <code>5:30</code> means 5 minutes 30 seconds per kilometre. Switch to min/mile if you prefer imperial units.',
  },
  {
    icon: 'mdi-clock-start',
    title: '3. Set your race start time',
    body: 'Enter the clock time when the gun goes off — e.g. <code>08:00</code>. The split table will show predicted real-world clock times throughout the race alongside cumulative durations.',
  },
  {
    icon: 'mdi-terrain',
    title: '4. Enable optional adjustments',
    body: '<strong>Fatigue decay</strong> gradually slows your pace over the second half of the race. <strong>Hill adjustments</strong> speed you up on descents and slow you down on climbs based on segment grade.',
    color: 'secondary',
  },
  {
    icon: 'mdi-map-marker-plus',
    title: '5. Add custom markers (optional)',
    body: 'Use the <em>Custom Markers</em> panel to mark aid stations, checkpoints, or cutoff points. Enter the distance, a nickname, and an optional cutoff time (<code>HH:MM</code>). The split table will highlight these rows and show your buffer against any cutoffs.',
    color: 'secondary',
  },
  {
    icon: 'mdi-play',
    title: '6. Click Analyze Route',
    body: 'The backend runs the full pipeline: GPX parsing → pace calculation → map generation → chart rendering. Results appear in the right panel, typically in under 5 seconds.',
  },
  {
    icon: 'mdi-content-save-outline',
    title: '7. Save your plan (optional)',
    body: 'Create a free account to save your race configurations and reload them any time. Saved plans store your config — not the full results — and re-run analysis on demand so you always get up-to-date splits.',
    color: 'accent',
  },
]

const reference = [
  { setting: 'Base Pace', description: 'Target pace at which to run each kilometre', example: '5:30 (5 min 30 sec/km)' },
  { setting: 'Pace Unit', description: 'Whether paces are shown in km or miles', example: 'min/km or min/mile' },
  { setting: 'Loops', description: 'How many times the GPX loop is repeated (for looped courses)', example: '2' },
  { setting: 'Race Start Time', description: 'Real-world clock time when the race starts', example: '08:00' },
  { setting: 'Fatigue Decay', description: 'Gradually increases pace by ~2% over the second half of the race', example: 'On/Off toggle' },
  { setting: 'Hill Adjustments', description: "Adjusts pace per segment's elevation grade using a standard grade-adjusted pace model", example: 'On/Off toggle' },
  { setting: 'Custom Markers', description: 'User-defined waypoints at specific distances — aid stations, cutoffs, etc.', example: 'Aid Station at 21.1 km, cutoff 02:30' },
]

const tips = [
  {
    icon: 'mdi-information-outline',
    title: 'GPX files must include track points',
    body: 'Route-only GPX files (without track points) do not contain elevation data. Export a recorded activity or a route with elevation profile for best results.',
  },
  {
    icon: 'mdi-scale-balance',
    title: 'Base pace is your flat, ideal pace',
    body: "Don't account for hills in your base pace — enable hill adjustments instead and let the algorithm apply grade corrections automatically.",
  },
  {
    icon: 'mdi-repeat',
    title: 'Loops multiply the route distance',
    body: 'Setting Loops to 2 will analyse the route as if you run the GPX track twice back-to-back. Use this for out-and-back or looped course designs.',
  },
  {
    icon: 'mdi-timer-alert-outline',
    title: 'Cutoff buffers can go negative',
    body: 'A negative buffer means your predicted arrival is after the cutoff. Adjust your base pace or decay settings and re-run until all buffers are positive.',
  },
]
</script>
