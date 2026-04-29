<template>
  <div ref="chartDiv" :style="{ height: `${height}px`, width: '100%' }" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import Plotly from 'plotly.js-dist-min'

interface ChartPoint {
  x: number
  y: number
}

const props = defineProps<{
  chartData: ChartPoint[] | null | undefined
  xLabel: string
  yLabel: string
  height?: number
}>()

const chartDiv = ref<HTMLDivElement | null>(null)
const height = computed(() => props.height ?? 300)

function render() {
  if (!chartDiv.value || !props.chartData?.length) return
  Plotly.react(
    chartDiv.value,
    [
      {
        x: props.chartData.map((p) => p.x),
        y: props.chartData.map((p) => p.y),
        type: 'scatter',
        mode: 'lines',
        line: { color: '#3498DB', width: 2 },
      },
    ],
    {
      height: height.value,
      margin: { t: 20, l: 60, r: 10, b: 50 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      xaxis: { title: { text: props.xLabel }, showgrid: true, gridcolor: 'lightgrey', zeroline: false },
      yaxis: { title: { text: props.yLabel }, showgrid: true, gridcolor: 'lightgrey', zeroline: false },
    },
    { responsive: true },
  )
}

onMounted(render)
watch([() => props.chartData, () => props.xLabel, () => props.yLabel], render)

onBeforeUnmount(() => {
  if (chartDiv.value) Plotly.purge(chartDiv.value)
})
</script>
