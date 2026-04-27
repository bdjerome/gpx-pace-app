<template>
  <v-container class="pa-4" max-width="900">
    <div class="d-flex align-center mb-4">
      <div>
        <h1 class="text-h5 font-weight-bold">My Race Plans</h1>
        <p class="text-body-2 text-medium-emphasis">Load, rename, or delete your saved race plans.</p>
      </div>
      <v-spacer />
      <v-btn prepend-icon="mdi-plus" color="primary" :to="{ name: 'analyze' }">New Analysis</v-btn>
    </div>

    <v-alert v-if="plans.error" type="error" variant="tonal" class="mb-4" closable>
      {{ plans.error }}
    </v-alert>

    <v-card elevation="2">
      <v-data-table
        :headers="headers"
        :items="plans.plans"
        :loading="plans.isLoading"
        item-value="id"
        no-data-text="No saved plans yet. Run an analysis and click 'Save Plan'."
      >
        <template #item.nickname="{ item }">
          <template v-if="editingId === item.id">
            <v-text-field
              v-model="editName"
              density="compact"
              hide-details
              autofocus
              @keyup.enter="saveRename(item.id)"
              @keyup.escape="cancelRename"
            />
          </template>
          <span v-else>{{ item.nickname }}</span>
        </template>

        <template #item.gpx_filename="{ item }">
          <span class="text-caption text-medium-emphasis">{{ item.gpx_filename ?? '—' }}</span>
        </template>

        <template #item.created_at="{ item }">
          <span style="white-space: nowrap">{{ formatDate(item.created_at) }}</span>
        </template>

        <template #item.updated_at="{ item }">
          <span style="white-space: nowrap">{{ formatDate(item.updated_at) }}</span>
        </template>

        <template #item.actions="{ item }">
          <template v-if="editingId === item.id">
            <v-btn icon="mdi-check" size="x-small" color="success" variant="text" @click="saveRename(item.id)" />
            <v-btn icon="mdi-close" size="x-small" variant="text" @click="cancelRename" />
          </template>
          <template v-else>
            <v-btn
              icon="mdi-play-circle-outline"
              size="x-small"
              color="primary"
              variant="text"
              title="Load plan"
              @click="loadPlan(item.id)"
            />
            <v-btn
              icon="mdi-pencil-outline"
              size="x-small"
              variant="text"
              title="Rename"
              @click="startRename(item)"
            />
            <v-btn
              icon="mdi-delete-outline"
              size="x-small"
              color="error"
              variant="text"
              title="Delete"
              @click="promptDelete(item)"
            />
          </template>
        </template>
      </v-data-table>
    </v-card>

    <!-- Delete confirmation dialog -->
    <v-dialog v-model="deleteDialog" max-width="380">
      <v-card>
        <v-card-title class="text-subtitle-1">Delete plan?</v-card-title>
        <v-card-text>
          <strong>{{ deletingPlan?.nickname }}</strong> will be permanently deleted.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="isDeleting" @click="confirmDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlansStore } from '@/stores/plans'
import { useAnalysisStore } from '@/stores/analysis'
import { plansApi } from '@/api'
import type { RacePlanSummary } from '@/types'

const plans = usePlansStore()
const analysis = useAnalysisStore()
const router = useRouter()

onMounted(() => plans.fetchPlans())

const headers = [
  { title: 'Name', key: 'nickname', minWidth: '160px' },
  { title: 'GPX File', key: 'gpx_filename' },
  { title: 'Created', key: 'created_at', width: '185px' },
  { title: 'Updated', key: 'updated_at', width: '185px' },
  { title: '', key: 'actions', width: '120px', sortable: false },
]

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

// ─── Load plan ─────────────────────────────────────────────────────────────
async function loadPlan(id: string) {
  try {
    const { data } = await plansApi.get(id)
    if (data.analysis) {
      analysis.result = data.analysis
    }
    router.push({ name: 'analyze' })
  } catch {
    // error handled globally
  }
}

// ─── Rename ─────────────────────────────────────────────────────────────────
const editingId = ref<string | null>(null)
const editName = ref('')

function startRename(plan: RacePlanSummary) {
  editingId.value = plan.id
  editName.value = plan.nickname
}

async function saveRename(id: string) {
  if (!editName.value) return
  await plans.renamePlan(id, editName.value)
  editingId.value = null
}

function cancelRename() {
  editingId.value = null
}

// ─── Delete ─────────────────────────────────────────────────────────────────
const deleteDialog = ref(false)
const deletingPlan = ref<RacePlanSummary | null>(null)
const isDeleting = ref(false)

function promptDelete(plan: RacePlanSummary) {
  deletingPlan.value = plan
  deleteDialog.value = true
}

async function confirmDelete() {
  if (!deletingPlan.value) return
  isDeleting.value = true
  await plans.deletePlan(deletingPlan.value.id)
  isDeleting.value = false
  deleteDialog.value = false
}
</script>
