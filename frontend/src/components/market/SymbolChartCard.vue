<template>

  <v-card
    rounded="lg"
    variant="flat"
    class="sd-chart-card"
  >

    <v-card-text>
      <div class="sd-chart-title">
      차트
      </div>

      <div v-if="chartMounted" ref="chartContainer" class="sd-chart" ></div>

      <div v-else class="sd-chart-placeholder">

        <v-icon size="40">
        mdi-chart-bar
        </v-icon>

        <div class="sd-chart-text">
        TradingView Lightweight Charts 자리
        </div>

        <div class="sd-chart-sub">
        Chart Placeholder
        </div>

      </div>
      <TimeframeTabs />

    </v-card-text>

  </v-card>

</template>

<script setup lang="ts">
import TimeframeTabs from "./TimeframeTabs.vue"
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue"
import { createChart, type IChartApi, type ISeriesApi, type UTCTimestamp  } from "lightweight-charts"

const chartContainer = ref(null)
const chartMounted = ref(false)

let chart: IChartApi | null = null
let candleSeries: ISeriesApi<"Candlestick">

onMounted(() => {
  initChart()
})

function cleanup() {
  chart?.remove()
  chart = null
}

const initChart = async () => {
  chart?.remove()
  chart = null

  // DOM 업데이트를 끝낸 다음에 코드를 실행하게 하는 함수
  chartMounted.value = true
  await nextTick()

  try {
    if (!chartContainer.value) {
      throw new Error('CHART_CONTAINER_NOT_FOUND')
    }

    // 테스트용 강제 실패
    // throw new Error('TEST_CHART_INIT_ERROR')

    chart = createChart(chartContainer.value!)
    candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    candleSeries.setData([
      { time: 1710000000 as UTCTimestamp, open: 58000, high: 58200, low: 57900, close: 58100 },
      { time: 1710000600 as UTCTimestamp, open: 58100, high: 58300, low: 58000, close: 58250 },
      { time: 1710001200 as UTCTimestamp, open: 58250, high: 58400, low: 58100, close: 58300 },
      { time: 1710001800 as UTCTimestamp, open: 58400, high: 58300, low: 58100, close: 58300 },
    ])
  } catch (error) {
    cleanup()

    // 2. 실패하면 DOM 자체 제거
    chartMounted.value = false
    console.error(error)
  }
}

onBeforeUnmount(() => {
  cleanup()
})
</script>