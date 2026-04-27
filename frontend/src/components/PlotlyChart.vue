<template>
  <div ref="chartDiv" :style="{ height: `${height}px`, width: '100%' }" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps<{
  figureJson: string | null | undefined
  height?: number
}>()

const chartDiv = ref<HTMLDivElement | null>(null)
const height = props.height ?? 300

function render() {
  if (!chartDiv.value || !props.figureJson) return
  try {
    const figure = JSON.parse(props.figureJson)
    Plotly.react(chartDiv.value, figure.data ?? [], {
      ...figure.layout,
      margin: { t: 20, l: 40, r: 10, b: 40 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
    })
  } catch {
    // malformed JSON — silently skip
  }
}

onMounted(render)
watch(() => props.figureJson, render)

onBeforeUnmount(() => {
  if (chartDiv.value) Plotly.purge(chartDiv.value)
})
</script>
