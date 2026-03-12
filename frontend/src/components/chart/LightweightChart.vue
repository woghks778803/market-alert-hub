<template>
  <div ref="chartContainer" class="chart-container"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue"
import { createChart } from "lightweight-charts"

const chartContainer = ref(null)

let chart
let candleSeries

onMounted(() => {
  chart = createChart(chartContainer.value, {
    width: chartContainer.value.clientWidth,
    height: 300,
    layout: {
      background: { color: "#ffffff" },
      textColor: "#333"
    },
    grid: {
      vertLines: { color: "#f0f3fa" },
      horzLines: { color: "#f0f3fa" }
    }
  })

  candleSeries = chart.addCandlestickSeries()

  candleSeries.setData([
    { time: 1710000000, open: 58000, high: 58200, low: 57900, close: 58100 },
    { time: 1710000600, open: 58100, high: 58300, low: 58000, close: 58250 },
    { time: 1710001200, open: 58250, high: 58400, low: 58100, close: 58300 },
    { time: 1710001800, open: 58300, high: 58500, low: 58200, close: 58450 },
  ])
})

onBeforeUnmount(() => {
  chart.remove()
})
</script>

<style>
.chart-container {
  width: 100%;
  height: 300px;
}
</style>