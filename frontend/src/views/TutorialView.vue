<template>
  <v-container fluid class="pa-3 pa-sm-6">
    <v-row justify="center">
    <v-col cols="12" sm="11" md="9" lg="7">
    <p class="text-body-1 text-medium-emphasis mb-4">
      Omne Enduro was created to tackle the niche yet significant challenge of race planning for endurance events. Current race planning tools are non-existent or fall short when it comes to accounting for the complexities of elevation changes, fatigue over long distances, and the need for crew/families to support athletes at various points along the route. Omne Enduro fills this gap by providing a comprehensive solution that integrates GPS data, pacing algorithms, and user configured parameters. The end result is a comprehensive tool that outputs important strategy details in a simple and easy to understand format.
    </p>
  
    <h1 class="text-h5 text-sm-h4 font-weight-bold mb-2">How to use</h1>
    <p class="text-body-1 text-medium-emphasis mb-6">
      A step-by-step guide to planning your race using Omne Enduro.
    </p>

    <div class="steps-list">
      <div v-for="step in steps" :key="step.title" class="step-item">
        <div class="step-dot" :class="step.color ? `bg-${step.color}` : 'bg-primary'" />
        <v-card variant="outlined" class="step-card">
          <v-card-title class="text-subtitle-2 font-weight-bold py-1 px-3">{{ step.title }}</v-card-title>
          <v-card-text class="text-body-2 py-1 px-3" v-html="step.body" />
        </v-card>
      </div>
    </div>

    <v-divider class="my-8" />

    <h2 class="text-h6 font-weight-bold mb-4">Videos</h2>

    <!-- <h2 class="text-h6 font-weight-bold mb-4">Configuration reference</h2>

    <div style="overflow-x: auto;">
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
    </div> -->

    <v-divider class="my-8" />

    <h2 class="text-h6 font-weight-bold mb-3">Additional Information</h2>
    <!-- <v-list density="compact">
      <v-list-item v-for="tip in tips" :key="tip.title" :prepend-icon="tip.icon">
        <v-list-item-title class="font-weight-medium">{{ tip.title }}</v-list-item-title>
        <v-list-item-subtitle>{{ tip.body }}</v-list-item-subtitle>
      </v-list-item>
    </v-list> -->
    <div> 
      <h3 class="text-subtitle-1 font-weight-strong mb-2">Pacing Calculations</h3>
      <h4 class="text-subtitle-2 font-weight-strong mb-1">Pace Correction for Elevation</h4>
      <p class="text-body-2 mb-1">
        The hill adjustment feature automatically modifies your pace based on elevation changes:
      </p>
      <ul> 

        <li class="text-body-2 mb-2">
          <strong>Grade Calculation:</strong>
          <ul> 
            <li class="text-body-2 mb-2">
              Grade is calculated as the change in elevation divided by the distance for each kilometer segment, expressed as a percentage. For example, a 10m climb over 1km distance results in a 1% grade.
            </li>
            <li class="text-body-2 mb-2">
              Multiply grade with a factor to slow pace uphill
              <ul> 
                <li class="text-body-2 mb-2">
                  If grade > 20% then factor is 0.12 otherwise 0.08
                </li>
              </ul>
            </li>
          </ul>
        </li>

        <li class="text-body-2 mb-2">
          <strong>Downhill:</strong> Base pace is unaffected
        </li>
      </ul>

      <v-divider class="my-8" />

      <h3 class="text-subtitle-1 font-weight-strong mb-2">Custom Markers</h3>
      <h4 class="text-subtitle-2 font-weight-strong mb-1">Strategic Waypoints, Aid Stations, or Cutoff Markers</h4>
      <p class="text-body-2 mb-1">
        Add important points along your route:
      </p>
      <ul> 
        <li class="text-body-2 mb-2">
          <strong>Distances:</strong> Inherit the unit selected when setting your base pace — for example min/km distance units would be given in kilometres. This allows you to mark important waypoints such as aid stations, checkpoints, or personal distance marks.
        </li>
        <li class="text-body-2 mb-2">
          <strong>Nicknames:</strong> Custom labels for easy identification, could be Aid Station Names, or the name of a friend/family member you plan to meet at that point, etc.
        </li>
        <li class="text-body-2 mb-2">
          <strong>Cutoff times:</strong> Optionally set time limits for buffer calculations in the output split table. A negative buffer means your predicted arrival is after the cutoff, while a positive buffer indicates you are predicted to arrive before the cutoff. Adjust your base pace or decay settings and re-run until all buffers are positive.
          <ul>
          <li class="text-body-2 mb-2">
           Time must be in <code>HH:MM</code> 24 hour format so 00:00-24:00
            </li>
            </ul>
        </li>
      </ul>

      <v-divider class="my-8" />

    </div>
    </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
const steps = [
  {
    title: '1. Upload your GPX file',
    body: 'Drag and drop (or click <em>Browse…</em>) to load a <code>.gpx</code> file downloaded from your race website or exported from your GPS watch, Strava, Garmin Connect, etc.',
  },
  {
    title: '2. Set your base pace',
    body: 'Toggle between <code>min/km</code> or <code>min/mile</code> and then enter your target pace in <code>M:SS</code> format — for example <code>5:30</code> means 5 minutes 30 seconds per kilometre.',
  },
  {
    title: '3. Set your race start time',
    body: 'Enter the clock time for race start — e.g. <code>08:00</code> (24 hour format). The output split table will show predicted clock times throughout the race using this information.',
  },
  {
    title: '4. Enable adjustments (optional)',
    body: '<strong>Fatigue decay</strong> gradually slows your pace over the second half of the race. <strong>Hill adjustments</strong> will slow you on climbs based on segment grade. For more information, please see the <a href="#additional-info">Additional Info</a> section below.',
    color: 'secondary',
  },
  {
    title: '5. Add custom markers (optional)',
    body: 'Use the <em>Custom Markers</em> panel to mark aid stations, checkpoints, or personal distance marks. Enter the distance, which inherits the unit selected when setting your base pace, for example <code>min/km</code> distance units would be given in kilometres. Then give a nickname, and an optional cutoff time (<code>HH:MM</code> 24 hour format). The split table will highlight these rows and show your calculated buffer against any cutoffs. Optionally select "Show only custom markers in split table" to filter the output split table.',
    color: 'secondary',
  },
  {
    title: '6. Click Analyze Route',
    body: 'Summary output, map generation, elevation & pace graphs, and the split table will then output, typically in under 5 seconds.',
  },
  {
    title: '7. Save your plan (optional)',
    body: 'Create a free account to save your race configurations. Once saved you can reload and edit at any time, download outputs as pdf’s, or share as a link with family and friends.',
    color: 'secondary',
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

<style scoped>
.steps-list {
  position: relative;
  padding-left: 20px;
  border-left: 2px solid rgba(0, 0, 0, 0.12);
}

.step-item {
  position: relative;
  margin-bottom: 8px;
}

.step-dot {
  position: absolute;
  left: -31px;
  top: 10px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
}

.step-card {
  width: 100%;
}
</style>
