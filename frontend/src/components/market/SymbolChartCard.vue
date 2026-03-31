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
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from "vue"
import { storeToRefs } from "pinia"
import { createChart, type IChartApi, type ISeriesApi, type UTCTimestamp  } from "lightweight-charts"
import { useMarketStore } from "@/stores/market.store"
import type { MarketDto } from "@/services/market.types"
import  { TIMEFRAME_SECONDS } from "@/services/market.types"

const marketStore = useMarketStore()
const chartContainer = ref(null)
const chartMounted = ref(false)
const isLoading = ref(false)
const { candles, currentCandle, currentTimeframe, candlesListQuery  } = storeToRefs(marketStore)

let chart: IChartApi | null = null
let candleSeries: ISeriesApi<"Candlestick">
let chartTimer: any


const props = defineProps<{
  market: MarketDto | null,
}>()

onMounted(async () => {
  initChart()
})

onBeforeUnmount(() => {
  cleanup()
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

    chart.timeScale().subscribeVisibleTimeRangeChange((range) => {
      if (!range) return
    
      const from = Number(range.from) 
      const oldest = candles.value[0]?.tsOpen / 1000

      if (!oldest) return

      const intervalSec = TIMEFRAME_SECONDS[currentTimeframe.value]
      const threshold = intervalSec * 30
      
      if (chartTimer) clearTimeout(chartTimer);

      chartTimer = setTimeout(async () => {
        if (isLoading.value) return

        if (from <= oldest + threshold) {
          isLoading.value = true
          try{
            candlesListQuery.value.cursor = new Date(oldest * 1000).toISOString()
            await marketStore.fetchCandles()
          } finally {
            isLoading.value = false
          }
        }

      }, 300)
    })

  } catch (error) {
    cleanup()

    // 2. 실패하면 DOM 자체 제거
    chartMounted.value = false
    console.error(error)
  }
}

watch(
  () => props.market,
  async (m) => {
    if (!m) return
    await marketStore.fetchCandles()
  },
  { immediate: true }
)

watch(
  () => candles.value.length,
  async (m) => {
    if (!m || !candleSeries) return
    console.log("candles length changed, updating chart data for:", m)

    if(!candles || candles.value.length === 0) {
      console.warn("No candles data available for market:", m)
      return
    }

    const sorted = candles.value.map((c) => ({
      time: (new Date(c.tsOpen).getTime() / 1000) as UTCTimestamp,
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
    }))

    candleSeries.setData(
      sorted
    )
  },
  { immediate: true }
)

watch(
  () => currentCandle.value,
  (c) => {
    if (!c || !candleSeries) return
    // console.log("currentCandle changed, updating chart data for:", c, candleSeries)

    candleSeries.update({
      time: c.tsOpen as UTCTimestamp,
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
    })
  }
)



</script>