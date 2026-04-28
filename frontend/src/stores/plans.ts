import { defineStore } from 'pinia'
import { ref } from 'vue'
import { plansApi, gpxApi } from '@/api'
import type { RacePlanSummary, RacePlanCreate, RacePlanUpdate, TemplateGpxFile } from '@/types'

export const usePlansStore = defineStore('plans', () => {
  const plans = ref<RacePlanSummary[]>([])
  const templates = ref<TemplateGpxFile[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Fetch list of plans for current user
  async function fetchPlans() {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await plansApi.list()
      plans.value = data
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail ?? axiosErr.message ?? 'Failed to load plans.'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTemplates() {
    try {
      const { data } = await gpxApi.listTemplates()
      templates.value = data
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail ?? axiosErr.message ?? 'Failed to load templates.'
    }
  }

  async function savePlan(payload: RacePlanCreate): Promise<string | null> {
    error.value = null
    try {
      const { data } = await plansApi.create(payload)
      await fetchPlans() // refresh list
      return data.id
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail ?? axiosErr.message ?? 'Failed to save plan.'
      return null
    }
  }

  async function deletePlan(id: string): Promise<boolean> {
    try {
      await plansApi.delete(id)
      plans.value = plans.value.filter((p) => p.id !== id)
      return true
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail ?? axiosErr.message ?? 'Failed to delete plan.'
      return false
    }
  }

  async function renamePlan(id: string, nickname: string): Promise<boolean> {
    try {
      await plansApi.update(id, { nickname })
      const plan = plans.value.find((p) => p.id === id)
      if (plan) plan.nickname = nickname
      return true
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail ?? axiosErr.message ?? 'Failed to rename plan.'
      return false
    }
  }

  async function updatePlan(id: string, data: RacePlanUpdate): Promise<boolean> {
    error.value = null
    try {
      await plansApi.update(id, data)
      await fetchPlans()
      return true
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string }
      error.value = axiosErr.response?.data?.detail ?? axiosErr.message ?? 'Failed to update plan.'
      return false
    }
  }

  return { plans, templates, isLoading, error, fetchPlans, fetchTemplates, savePlan, updatePlan, deletePlan, renamePlan }
})
