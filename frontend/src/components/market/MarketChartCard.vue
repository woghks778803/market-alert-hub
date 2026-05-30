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
      <TimeframeTabs 
        :model-value="currentTimeframe"
        @update:model-value="handleChangeTimeframe"
      />
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { storeToRefs } from 'pinia'
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  TickMarkType,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
  type Time,
} from 'lightweight-charts'

import { getDecimalPlaces } from '@/utils/number'
import TimeframeTabs from '@/components/market/TimeframeTabs.vue'
import type { MarketDto, ChartTimeframe } from '@/services/market.types'
import { TIMEFRAME_SECONDS } from '@/services/market.types'
import { useMarketStore } from '@/stores/market.store'
import { ThemeMode } from '@/composables/common/useAppSettings'

const marketStore = useMarketStore()
const { candles, currentCandle, currentTimeframe, candlesListQuery } = storeToRefs(marketStore)

const chartContainer = ref<HTMLDivElement | null>(null)
const chartMounted = ref(false)

const isAutoScale = ref(true)
const isLogScale = ref(false)
const isResetTimeScale = ref(false)

let chart: IChartApi | null = null
let candleSeries: ISeriesApi<'Candlestick'> | null = null
let volumeSeries: ISeriesApi<'Histogram'> | null = null
let chartTimer: ReturnType<typeof setTimeout> | null = null
let currentPricePrecision = 2

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

function toLocalDate(time: Time): Date {
  if (typeof time !== 'number') {
    throw new Error(`Unsupported chart time: ${String(time)}`)
  }

  return new Date(time * 1000)
}

function cleanup() {
  if (chartContainer.value) {
    chartContainer.value.removeEventListener('pointerup', applyAutoScale)
    chartContainer.value.removeEventListener('pointercancel', applyAutoScale)
    chartContainer.value.removeEventListener('dblclick', applyAutoScale)

    chartContainer.value = null
  }

  chart?.remove()

  chart = null
  candleSeries = null
  volumeSeries = null
}

function nextFrame(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => resolve())
  })
}

function applyAutoScale(): void {
  requestAnimationFrame(() => {
    if (!chart) return

    isAutoScale.value =
      chart.priceScale('right', 0).options().autoScale
  })
}

function applyPricePrecision(nextPrecision: number) {
  const precision = Math.min(nextPrecision, 12)

  // 같은 종목 내에서는 정밀도를 낮추지 않는다.
  if (!candleSeries || precision <= currentPricePrecision) return

  currentPricePrecision = precision

  candleSeries.applyOptions({
    priceFormat: {
      type: 'price',
      precision,
      minMove: 10 ** -precision,
    },
  })
}

function applyPriceScale() {
  if (!chart) return

  chart.priceScale('right', 0).applyOptions({
    autoScale: isAutoScale.value,
    mode: isLogScale.value ? 1 : 0,
  })
}

function toggleAuto() {
  if (!candleSeries) return

  isAutoScale.value = !isAutoScale.value
  applyPriceScale()
}

function toggleLog() {
  if (!candleSeries) return

  isLogScale.value = !isLogScale.value
  applyPriceScale()
}

async function handleChangeTimeframe(
  next: ChartTimeframe,
): Promise<void> {
  if (currentTimeframe.value === next) return

  isResetTimeScale.value = true

  try {
    await marketStore.changeTimeFrame(next)

    // candles 변경에 따른 series.setData() 반영 대기
    await nextTick()
    await nextFrame()

    // 최신 캔들이 보이는 위치로 즉시 이동
    chart?.timeScale().scrollToPosition(0, false)

    // 위치 변경으로 발생하는 range 이벤트까지 차단
    await nextFrame()
  } finally {
    isResetTimeScale.value = false
  }
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

    chart = createChart(chartContainer.value, {
      autoSize: true,
      kineticScroll: {
        touch: false,
        mouse: false,
      },
      layout: {
        panes: {
          enableResize: true,
          separatorColor: isDark ? '#334155' : '#e5e7eb',
          separatorHoverColor: isDark ? '#475569' : '#d1d5db',
        },
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

    chartContainer.value.addEventListener('pointerup', applyAutoScale)
    chartContainer.value.addEventListener('pointercancel', applyAutoScale)
    chartContainer.value.addEventListener('dblclick', applyAutoScale)

    chart.timeScale().applyOptions({
      timeVisible: true,
      secondsVisible: false,
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
          console.log("222")
          props.candleRun(async () => {
            candlesListQuery.value.cursor = new Date(oldest * 1000).toISOString()
            await marketStore.fetchCandles()
          })
        }
      }, 300)
    })

    candleSeries = chart.addSeries(
      CandlestickSeries,
      {
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderUpColor: '#26a69a',
        borderDownColor: '#ef5350',
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      },
      0,
    )

    volumeSeries = chart.addSeries(
      HistogramSeries,
      {
        priceFormat: {
          type: 'volume',
        },
      },
      1,
    )

    const panes = chart.panes()

    panes[0]?.setStretchFactor(4)
    panes[1]?.setStretchFactor(1)
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

    currentPricePrecision = 2

    candleSeries?.applyOptions({
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    })

    props.candleRun(async () => {
      await marketStore.fetchCandles()
    })
  },
  { immediate: true }
)

watch(
  () => candles.value.length,
  async (m) => {
    if (!m || !candleSeries || !volumeSeries) return
    // console.log('candles length changed, updating chart data for:', m)

    if (!candles || candles.value.length === 0) {
      console.warn('No candles data available for market:', m)
      return
    }

    let precision = 2

    const sorted = candles.value.map((c) => {
      const open = Number(c.open)
      const high = Number(c.high)
      const low = Number(c.low)
      const close = Number(c.close)

      precision = Math.max(
        precision,
        getDecimalPlaces(open),
        getDecimalPlaces(high),
        getDecimalPlaces(low),
        getDecimalPlaces(close),
      )

      return {
        time: (new Date(c.tsOpen).getTime() / 1000) as UTCTimestamp,
        open,
        high,
        low,
        close,
      }
    })

    applyPricePrecision(precision)
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
    if (!c || !candleSeries || !volumeSeries) return
    // console.log("currentCandle changed, updating chart data for:", c, candleSeries)

    const open = Number(c.open)
    const high = Number(c.high)
    const low = Number(c.low)
    const close = Number(c.close)

    applyPricePrecision(
      Math.max(
        getDecimalPlaces(open),
        getDecimalPlaces(high),
        getDecimalPlaces(low),
        getDecimalPlaces(close),
      ),
    )

    candleSeries.update({
      time: c.tsOpen as UTCTimestamp,
      open,
      high,
      low,
      close,
    })

    volumeSeries.update({
      time: c.tsOpen as UTCTimestamp,
      value: Number(c.volume),
      color: Number(c.close) >= Number(c.open) ? '#26a69a' : '#ef5350',
    })
  }
)
</script>
