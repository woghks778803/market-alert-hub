<template>
  <v-card
    rounded="lg"
    variant="flat"
    class="sd-chart-card"
  >
    <v-card-text>
      <div class="sd-chart-header">
        <div class="sd-chart-title">차트</div>

        <div class="sd-chart-actions">
          <v-btn
            size="x-small"
            :color="isAutoScale ? 'primary' : 'grey'"
            @click="toggleAuto"
            >A</v-btn
          >
          <v-btn
            size="x-small"
            :color="isLogScale ? 'primary' : 'grey'"
            @click="toggleLog"
            >L</v-btn
          >
        </div>
      </div>

      <div
        v-if="chartMounted"
        ref="chartContainer"
        class="sd-chart"
        :class="{ collapsed: props.collapsed }"
      ></div>

      <div
        v-else
        class="sd-chart-placeholder"
      >
        <v-icon size="40"> mdi-chart-bar </v-icon>

        <div class="sd-chart-text">TradingView Lightweight Charts 자리</div>

        <div class="sd-chart-sub">Chart Placeholder</div>
      </div>
      <TimeframeTabs />
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import TimeframeTabs from './TimeframeTabs.vue'
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { createChart, TickMarkType, type IChartApi, type ISeriesApi, type UTCTimestamp, type Time } from 'lightweight-charts'
import { useMarketStore } from '@/stores/market.store'
import type { MarketDto } from '@/services/market.types'
import { TIMEFRAME_SECONDS } from '@/services/market.types'
import { ThemeMode } from '@/composables/common/useAppSettings'

const marketStore = useMarketStore()
const { candles, currentCandle, currentTimeframe, candlesListQuery } = storeToRefs(marketStore)

const chartContainer = ref<HTMLDivElement | null>(null)
const chartMounted = ref(false)

const isAutoScale = ref(true)
const isLogScale = ref(false)

let chart: IChartApi | null = null
let candleSeries: ISeriesApi<'Candlestick'>
let volumeSeries: ISeriesApi<'Histogram'>
let chartTimer: ReturnType<typeof setTimeout> | null = null

const props = defineProps<{
  market: MarketDto | null
  collapsed: boolean
  candleRun: <T>(fn: () => Promise<T>) => Promise<T | null | undefined>
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

function applyPriceScale() {
  chart?.priceScale('right').applyOptions({
    autoScale: isAutoScale.value,
    mode: isLogScale.value ? 1 : 0,
  })
}

function toggleAuto() {
  isAutoScale.value = !isAutoScale.value
  applyPriceScale()
}

function toggleLog() {
  isLogScale.value = !isLogScale.value
  applyPriceScale()
}

function toLocalDate(time: Time): Date {
  if (typeof time !== 'number') {
    throw new Error(`Unsupported chart time: ${String(time)}`)
  }

  return new Date(time * 1000)
}

const initChart = async () => {
  cleanup()

  // DOM 업데이트를 끝낸 다음에 코드를 실행하게 하는 함수
  chartMounted.value = true
  await nextTick()

  try {
    if (!chartContainer.value) {
      throw new Error('CHART_CONTAINER_NOT_FOUND')
    }

    // 테스트용 강제 실패
    // throw new Error('TEST_CHART_INIT_ERROR')
    const isDark = document.documentElement.classList.contains(ThemeMode.DARK)

    chart = createChart(chartContainer.value!, {
      autoSize: true,
      layout: {
        background: {
          color: isDark ? '#0f172a' : '#ffffff',
        },
        textColor: isDark ? '#9ca3af' : '#374151',
      },
      localization: { // 차트 전체의 지역화/표시 형식 설정
        locale: navigator.language,

        // 크로스헤어 하단의 날짜·시간
        timeFormatter: (time: Time) => {
          const d = toLocalDate(time)

          const yyyy = d.getFullYear()
          const mm = String(d.getMonth() + 1).padStart(2, '0')
          const dd = String(d.getDate()).padStart(2, '0')
          const hh = String(d.getHours()).padStart(2, '0')
          const min = String(d.getMinutes()).padStart(2, '0')

          return `${yyyy}.${mm}.${dd} ${hh}:${min}`
        },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,

        // 차트 하단 x축 눈금
        tickMarkFormatter: (
          time: Time,
          tickMarkType: TickMarkType,
        ) => {
          const d = toLocalDate(time)

          const yyyy = d.getFullYear()
          const mm = String(d.getMonth() + 1).padStart(2, '0')
          const dd = String(d.getDate()).padStart(2, '0')
          const hh = String(d.getHours()).padStart(2, '0')
          const min = String(d.getMinutes()).padStart(2, '0')

          console.log("tickMarkType", tickMarkType)

          switch (tickMarkType) {
            case TickMarkType.Year:
              return String(yyyy)

            case TickMarkType.Month:
              return `${mm}월`

            case TickMarkType.DayOfMonth:
              return `${mm}.${dd}`

            case TickMarkType.Time:
              return `${hh}:${min}`

            case TickMarkType.TimeWithSeconds:
              return `${hh}:${min}`

            default:
              return `${mm}.${dd}`
          }
        },
      },
    })

    candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })

    chart.timeScale().applyOptions({
      timeVisible: true,
      secondsVisible: false,
    })

    chart.priceScale('volume').applyOptions({
      visible: true,
      borderVisible: false,
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    chart.priceScale('right').applyOptions({
      scaleMargins: {
        top: 0,
        bottom: 0.2,
      },
    })

    chart.timeScale().subscribeVisibleTimeRangeChange((range) => {
      if (!range) return

      const from = Number(range.from)
      const oldest = candles.value[0]?.tsOpen / 1000

      if (!oldest) return

      const intervalSec = TIMEFRAME_SECONDS[currentTimeframe.value]
      const threshold = intervalSec * 30

      if (chartTimer) clearTimeout(chartTimer)

      chartTimer = setTimeout(async () => {
        if (from <= oldest + threshold) {
          props.candleRun(async () => {
            candlesListQuery.value.cursor = new Date(oldest * 1000).toISOString()
            await marketStore.fetchCandles()
          })
        }
      }, 300)
    })
  } catch {
    cleanup()

    // 2. 실패하면 DOM 자체 제거
    chartMounted.value = false
  }
}


watch(
  () => props.market,
  async (m) => {
    if (!m) return

    props.candleRun(async () => {
      await marketStore.fetchCandles()
    })
  },
  { immediate: true }
)

watch(
  () => candles.value.length,
  async (m) => {
    if (!m || !candleSeries) return
    console.log('candles length changed, updating chart data for:', m)

    if (!candles || candles.value.length === 0) {
      console.warn('No candles data available for market:', m)
      return
    }

    const sorted = candles.value.map((c) => ({
      time: (new Date(c.tsOpen).getTime() / 1000) as UTCTimestamp,
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
    }))

    candleSeries.setData(sorted)

    volumeSeries.setData(
      candles.value.map((c) => ({
        time: (new Date(c.tsOpen).getTime() / 1000) as UTCTimestamp,
        value: Number(c.volume),
        color: Number(c.close) >= Number(c.open) ? '#26a69a' : '#ef5350',
      }))
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

    volumeSeries.update({
      time: c.tsOpen as UTCTimestamp,
      value: Number(c.volume),
      color: Number(c.close) >= Number(c.open) ? '#26a69a' : '#ef5350',
    })
  }
)
</script>
