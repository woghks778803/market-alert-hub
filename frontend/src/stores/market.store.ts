import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WsMessage } from '@/services/ws/ws.client'
import { marketWs, type CandleSnapshotInfo, type TickerSnapshotInfo } from '@/services/ws/market.ws'
import * as marketService from '@/services/market.service'
import { createWatchlist, removeWatchlist } from '@/services/watchlist.service'

import { toCandleSnapshotDto, toTickerSnapshotDto } from '@/services/market.mapper'
import type {
  MarketSimpleDto,
  MarketDto,
  ExchangeSimpleDto,
  ExchangeDetailDto,
  InstrumentDetailDto,
  CandleDto,
  MarketSimpleListQuery,
  MarketListQuery,
  CandlesListQuery,
} from '@/services/market.types'
import {
  MarketSort,
  ChartTimeframe,
  CandleInterval,
  TickerInterval,
  WsChannelType,
  MarketSortLabel,
  CANDLES_MAX_LIMIT,
  CANDLES_LIMIT,
  TIMEFRAME_SECONDS,
} from '@/services/market.types'

export const useMarketStore = defineStore('market', () => {
  let searchTimer: ReturnType<typeof setTimeout> | null = null
  let marketListRequestId = 0

  const currentCandle = ref<CandleDto | null>(null)
  const candles = ref<CandleDto[]>([])

  const exchange = ref<ExchangeDetailDto | null>(null)
  const exchangeSimples = ref<ExchangeSimpleDto[]>([])
  const instrument = ref<InstrumentDetailDto | null>(null)
  const market = ref<MarketDto | null>(null)
  const markets = ref<MarketDto[]>([])
  const marketSimples = ref<MarketSimpleDto[]>([])

  const openSort = ref(false)
  const currentTimeframe = ref<ChartTimeframe>(ChartTimeframe.MIN_1)
  const currentSystemTab = ref<string[]>(['all'])

  const candleHasMore = ref(true)

  const marketSimpleListQuery = ref<MarketSimpleListQuery>({
    search: '',
  })

  const marketListQuery = ref<MarketListQuery>({
    search: '',
    exchangeCodes: [] as string[],
    watchlistOnly: false,
    sort: MarketSort.VOLUME_DESC,
  })

  // Partial 모든 필드를 선택(optional)
  const candlesListQuery = ref<Partial<CandlesListQuery>>({})

  const currentSortLabel = computed(() => {
    return MarketSortLabel[marketListQuery.value.sort ?? MarketSort.VOLUME_DESC]
  })

  async function fetchExchange(exchangeCode: string) {
    exchange.value = await marketService.getExchangeDetail(exchangeCode)
  }

  async function fetchExchangeSimples() {
    exchangeSimples.value = await marketService.getExchangeSimples()
  }

  async function fetchExchangeMarkets(exchangeCode: string) {
    markets.value = await marketService.getExchangeMarkets(exchangeCode)
  }

  async function fetchInstrument(instrumentSymbol: string) {
    instrument.value = await marketService.getInstrumentDetail(instrumentSymbol)
  }

  async function fetchInstrumentMarkets(instrumentSymbol: string) {
    markets.value = await marketService.getInstrumentMarkets(instrumentSymbol)
  }

  async function fetchMarket(exchangeCode: string, exchangeSymbol: string) {
    market.value = await marketService.getMarket(exchangeCode, exchangeSymbol)
  }

  async function fetchMarkets() {
    const requestId = ++marketListRequestId

    const rows = await marketService.getMarkets(marketListQuery.value)

    if (requestId !== marketListRequestId) return
    markets.value = rows
  }

  async function fetchMarketSimples() {
    marketSimples.value = await marketService.getMarketSimples(marketSimpleListQuery.value)
  }

  async function fetchCandles() {
    if (!market.value) return
    if (!candleHasMore.value) return
    if (candles.value.length >= CANDLES_MAX_LIMIT) {
      candleHasMore.value = false
      return
    }

    const previousOldestTsOpen = candles.value[0]?.tsOpen

    candlesListQuery.value.exchangeInstrumentId = market.value.exchangeInstrumentId
    candlesListQuery.value.output = currentTimeframe.value
    candlesListQuery.value.limit = CANDLES_LIMIT
    candlesListQuery.value.order = 'desc'

    const data = await marketService.getCandles(candlesListQuery.value as CandlesListQuery)
    const fetchedCount = data.length

    if (fetchedCount === 0) {
      candleHasMore.value = false
      return
    }

    const olderCandles = [...data]
      .reverse()
      .filter(
        (candle) =>
          previousOldestTsOpen === undefined ||
          candle.tsOpen < previousOldestTsOpen,
      )

    if (olderCandles.length === 0) {
      candleHasMore.value = false
      return
    }

    candles.value.unshift(...olderCandles)

    // 검색 캔들 수가 미달이거나 최대 캔들 수 이상인 경우
    if (
      fetchedCount < CANDLES_LIMIT ||
      candles.value.length >= CANDLES_MAX_LIMIT
    ) {
      candleHasMore.value = false
    }
    // console.log("Fetched candles:", data.length, "Total candles:", candles.value.length)
  }

  async function toggleWatchlist(item: MarketDto) {
    if (item.isWatchlisted) {
      await removeWatchlist(item.exchangeInstrumentId)
      item.isWatchlisted = false
    } else {
      await createWatchlist({ exchangeInstrumentId: item.exchangeInstrumentId })
      item.isWatchlisted = true
    }
  }

  function setMarketSearch(value: string) {
    if (searchTimer)
      clearTimeout(searchTimer)

    searchTimer = setTimeout(() => {
      marketListQuery.value.search = value
      fetchMarkets()
    }, 500)
  }

  function setMarketSimpleSearch(value: string) {
    if (searchTimer)
      clearTimeout(searchTimer)

    searchTimer = setTimeout(() => {
      marketSimpleListQuery.value.search = value
      fetchMarketSimples()
    }, 500)
  }

  function setMarketFilter(codes: string[]) {
    // 마지막 선택값
    const last = codes[codes.length - 1]
    let next: string[]

    if (last === 'all') {
      next = ['all']
    } else {
      next = codes.filter((v) => v !== 'all')
    }

    if (codes.length == 0) {
      next = ['all']
    }

    currentSystemTab.value = next

    const isAll = currentSystemTab.value.includes('all')
    const isWatchlist = currentSystemTab.value.includes('watchlist')

    marketListQuery.value.exchangeCodes = isAll
      ? []
      : currentSystemTab.value.filter((v) => v !== 'watchlist')
    marketListQuery.value.watchlistOnly = isWatchlist

    fetchMarkets()
  }

  function setSort(sort: MarketSort) {
    marketListQuery.value.sort = sort
    fetchMarkets()
  }

  // key 생성
  function buildMarketKey(
    channelType: WsChannelType,
    interval: CandleInterval | TickerInterval | ChartTimeframe,
    row: MarketDto
  ): string {
    return `${channelType}:${interval}:${row.exchangeCode}:${row.exchangeSymbol}`
  }

  // 구독
  function subscribeMarket(
    channelType: WsChannelType,
    interval: CandleInterval | TickerInterval | ChartTimeframe
  ) {
    const currentMarket = market.value
    if (!currentMarket) return

    const key = buildMarketKey(channelType, interval, currentMarket)
    marketWs.subscribe(channelType, key)
  }

  function unsubscribeMarket(
    channelType: WsChannelType,
  ) {
    marketWs.unSubscribe(channelType)
  }

  function subscribeMarkets() {
    marketWs.subscribeList(
      WsChannelType.CANDLE_LIST,
      markets.value.map(
        market =>
          buildMarketKey(WsChannelType.CANDLE, CandleInterval.SEC_1, market)
      ),
    )

    marketWs.subscribeList(
      WsChannelType.TICKER_LIST,
      markets.value.map(
        market =>
          buildMarketKey(WsChannelType.TICKER, TickerInterval.HOUR_24, market)
      ),
    )
  }

  // 구독 해제
  function unsubscribeMarkets() {
    marketWs.unSubscribeList(WsChannelType.CANDLE_LIST)
    marketWs.unSubscribeList(WsChannelType.TICKER_LIST)
  }

  function initWs(): void {
    marketWs.addHandler(
      [
        WsChannelType.TICKER,
        WsChannelType.TICKER_LIST,
        WsChannelType.CANDLE,
        WsChannelType.CANDLE_LIST,
      ],
      marketHandler,
    )
  }

  function cleanupWs() {
    marketWs.removeHandler(WsChannelType.TICKER_LIST)
    marketWs.removeHandler(WsChannelType.TICKER)
    marketWs.removeHandler(WsChannelType.CANDLE_LIST)
    marketWs.removeHandler(WsChannelType.CANDLE)
  }

  const marketHandler = (
    type: WsChannelType,
    data: WsMessage | WsMessage[],
  ): void => {
    switch (type) {
      case WsChannelType.TICKER:
        if (Array.isArray(data)) return
        applyTicker(data)
        return

      case WsChannelType.TICKER_LIST:
        if (!Array.isArray(data)) return
        applyTickers(data)
        return

      case WsChannelType.CANDLE:
        if (Array.isArray(data)) return
        applyCandle(data)
        return

      case WsChannelType.CANDLE_LIST:
        if (!Array.isArray(data)) return
        applyCandles(data)
        return
    }
  }

  function applyTicker(payload: WsMessage) {
    // console.log("applyTicker", payload)
    if (payload.type !== WsChannelType.TICKER) return
    const d = toTickerSnapshotDto(payload.data as TickerSnapshotInfo)
    if (!market.value) return

    market.value.normalizedPrice = Number(d.normalizedPrice)
    market.value.normalizedVolume = Number(d.normalizedVolume)
    market.value.high = Number(d.high)
    market.value.low = Number(d.low)
    market.value.changeRate = Number(d.priceChangeRate)
    market.value.volume = Number(d.volume)
  }

  function applyTickers(payload: WsMessage[]) {
    // console.log("applyTickers", payload)
    for (const item of payload) {
      if (item.type !== WsChannelType.TICKER) continue
      const d = toTickerSnapshotDto(item.data as TickerSnapshotInfo)

      const target = markets.value.find(
        (m) => m.exchangeCode === d.exchangeCode && m.exchangeSymbol === d.exchangeSymbol
      )

      if (!target) return

      target.normalizedPrice = Number(d.normalizedPrice)
      target.normalizedVolume = Number(d.normalizedVolume)
      target.change = Number(d.priceChange)
      target.changeRate = Number(d.priceChangeRate)
      target.volume = Number(d.volume)
    }

    // 추후 리스트 sorting 추가 예정
  }

  function applyCandle(payload: WsMessage) {
    // console.log("applyCandle", payload)
    if (payload.type !== WsChannelType.CANDLE) return

    const d = toCandleSnapshotDto(payload.data as CandleSnapshotInfo)
    if (!market.value) return
    market.value.closePrice = Number(d.close)

    const price = Number(d.close)
    const rawTime = Number(d.tsOpen) / 1000

    if (!isFinite(price) || !isFinite(rawTime)) return
    const intervalSec = TIMEFRAME_SECONDS[currentTimeframe.value]
    const candleTime = Math.floor(rawTime / intervalSec) * intervalSec

    // 최초
    if (!currentCandle.value) {
      currentCandle.value = {
        exchangeInstrumentId: market.value.exchangeInstrumentId,
        tsOpen: candleTime,
        open: price,
        high: price,
        low: price,
        close: price,
        volume: Number(d.volume) || 0,
      }
      return
    }

    const prev = currentCandle.value

    // 누적
    if (prev.tsOpen === candleTime) {
      currentCandle.value = {
        ...prev,
        high: Math.max(prev.high, price),
        low: Math.min(prev.low, price),
        close: price,
        volume: prev.volume + (Number(d.volume) || 0),
      }
      return
    }

    // 새 캔들
    currentCandle.value = {
      exchangeInstrumentId: market.value.exchangeInstrumentId,
      tsOpen: candleTime,
      open: price,
      high: price,
      low: price,
      close: price,
      volume: Number(d.volume) || 0,
    }
  }

  function applyCandles(payload: WsMessage[]) {
    // console.log("applyCandles", payload)
    for (const item of payload) {
      if (item.type !== WsChannelType.CANDLE) continue

      const d = toCandleSnapshotDto(item.data as CandleSnapshotInfo)

      const target = markets.value.find(
        (m) => m.exchangeCode === d.exchangeCode && m.exchangeSymbol === d.exchangeSymbol
      )
      if (!target) continue

      target.closePrice = Number(d.close)
    }
  }

  async function changeTimeFrame(next: ChartTimeframe) {
    if (currentTimeframe.value === next) return

    // 기존 해제
    // unsubscribeMarket(WsChannelType.CANDLE, currentTimeframe.value)

    clearCandles()
    // 변경
    currentTimeframe.value = next
    candlesListQuery.value.cursor = undefined
    candleHasMore.value = true

    await fetchCandles()

    // console.log(candles.value)

    // 새 구독
    // subscribeMarket(WsChannelType.CANDLE, currentTimeframe.value)
  }

  function clearCandles() {
    candles.value = []
    currentCandle.value = null
  }

  function resetMarket() {
    clearCandles()
    market.value = null
    markets.value = []
    marketSimples.value = []
    exchange.value = null
    exchangeSimples.value = []
    instrument.value = null
    currentTimeframe.value = ChartTimeframe.MIN_1
    candlesListQuery.value = {}
  }

  return {
    exchange,
    exchangeSimples,
    instrument,
    market,
    markets,
    marketSimples,
    candles,

    currentCandle,
    currentSortLabel,
    currentTimeframe,
    currentSystemTab,
    openSort,

    marketListQuery,
    candlesListQuery,
    marketSimpleListQuery,

    fetchExchange,
    fetchExchangeSimples,
    fetchExchangeMarkets,
    fetchInstrument,
    fetchInstrumentMarkets,

    fetchMarket,
    fetchMarkets,
    fetchMarketSimples,
    fetchCandles,

    resetMarket,
    toggleWatchlist,
    changeTimeFrame,

    setMarketSimpleSearch,
    setMarketSearch,
    setMarketFilter,
    setSort,

    subscribeMarket,
    unsubscribeMarket,
    subscribeMarkets,
    unsubscribeMarkets,
    initWs,
    cleanupWs,
  }
})
