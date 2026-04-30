import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { marketWs } from "@/services/ws/market.ws"
import * as marketService from "@/services/market.service"
import { createWatchlist, removeWatchlist } from "@/services/watchlist.service"
import type { SimpleMarketDto, MarketDto, ExchangeDto, CandleDto, SimpleMarketListQuery, MarketListQuery, ExchangeListQuery, CandlesListQuery } from "@/services/market.types"
import { MarketSort, ChartTimeframe, CandleInterval, TickerInterval, WsChannelType, MarketSortLabel, CANDLES_MAX_LIMIT, CANDLES_LIMIT, TIMEFRAME_SECONDS } from "@/services/market.types"

export const useMarketStore = defineStore("market", () => {
    let searchTimer: any
    const currentCandle = ref<CandleDto | null>(null)
    const candles = ref<CandleDto[]>([])

    const market = ref<MarketDto | null>(null)
    const markets = ref<MarketDto[]>([])
    const simpleMarkets = ref<SimpleMarketDto[]>([])
    const exchanges = ref<ExchangeDto[]>([])


    const openSort = ref(false)
    const currentTimeframe = ref<ChartTimeframe>(ChartTimeframe.MIN_1)
    const currentSystemTab = ref<string[]>(["all"])

    const simpleMarketListQuery = ref<SimpleMarketListQuery>({
        search: "",
    })

    const marketListQuery = ref<MarketListQuery>({
        search: "",
        exchangeCodes: [] as string[],
        watchlistOnly: false,
        sort: MarketSort.VOLUME_DESC,
    })

    const exchangeListQuery = ref<ExchangeListQuery>({})

    // Partial 모든 필드를 선택(optional)
    const candlesListQuery = ref<Partial<CandlesListQuery>>({})


    const currentSortLabel = computed(() => {
        return MarketSortLabel[marketListQuery.value.sort ?? MarketSort.VOLUME_DESC]
    })

    async function fetchMarket(exchange_code: string, symbol: string) {
        // console.log("Fetching market for:", exchange_code, symbol)
        market.value = await marketService.getMarket(exchange_code, symbol)
    }

    async function fetchMarkets() {
        markets.value = await marketService.getMarkets(marketListQuery.value)
    }

    async function fetchSimpleMarkets() {
        simpleMarkets.value = await marketService.getSimpleMarkets(simpleMarketListQuery.value)
        console.log("fetchSimpleMarkets", simpleMarkets)
    }

    async function fetchExchanges() {
        exchanges.value = await marketService.getExchanges(exchangeListQuery.value)
    }

    async function fetchCandles() {
        // console.log("Fetching candles for market:", market.value)
        if (!market.value) return
        if (candles.value.length >= CANDLES_MAX_LIMIT) return

        candlesListQuery.value.exchangeInstrumentId = market.value.exchangeInstrumentId
        candlesListQuery.value.output = currentTimeframe.value
        candlesListQuery.value.limit = CANDLES_LIMIT
        candlesListQuery.value.order = "desc"

        const data = await marketService.getCandles(candlesListQuery.value as CandlesListQuery)

        if (data.length === 0) return

        candles.value.unshift(...data.reverse())
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
        clearTimeout(searchTimer)

        searchTimer = setTimeout(() => {
            marketListQuery.value.search = value
            fetchMarkets()
        }, 500)
    }

    function setSimpleMarketSearch(value: string) {
        // console.log("value", value)
        clearTimeout(searchTimer)

        searchTimer = setTimeout(() => {
            simpleMarketListQuery.value.search = value
            fetchSimpleMarkets()
        }, 500)
    }

    function setMarketFilter(codes: string[]) {

        // 마지막 선택값
        const last = codes[codes.length - 1]
        let next: string[]

        if (last === "all") {
            next = ["all"]
        } else {
            next = codes.filter(v => v !== "all")
        }

        if (codes.length == 0) {
            next = ["all"]
        }

        currentSystemTab.value = next

        const isAll = currentSystemTab.value.includes("all")
        const isWatchlist = currentSystemTab.value.includes("watchlist")

        marketListQuery.value.exchangeCodes = isAll ? [] : currentSystemTab.value.filter(v => v !== "watchlist")
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
        interval: CandleInterval | TickerInterval | ChartTimeframe): string | null {
        return market.value ? `${channelType}:${interval}:${market.value.exchange}:${market.value.symbol}` : null
    }

    // 구독
    function subscribeMarket(
        channelType: WsChannelType,
        interval: CandleInterval | TickerInterval | ChartTimeframe
    ) {
        const key = buildMarketKey(channelType, interval)
        if (key) {
            marketWs.subscribe(key)
        }
    }

    function unsubscribeMarket(
        channelType: WsChannelType,
        interval: CandleInterval | TickerInterval | ChartTimeframe
    ) {
        const key = buildMarketKey(channelType, interval)
        if (key) {
            marketWs.unSubscribe(key)
        }
    }

    function subscribeMarkets() {
        marketWs.subscribe("candle_list")
        marketWs.subscribe("ticker_list")
    }

    // 구독 해제
    function unsubscribeMarkets() {
        marketWs.unSubscribe("candle_list")
        marketWs.unSubscribe("ticker_list")
    }

    function initWs() {
        marketWs.addHandler(["ticker", "ticker_list"], tickerHandler)
        marketWs.addHandler(["candle", "candle_list"], candleHandler)
    }

    function cleanupWs() {
        marketWs.removeHandler("ticker_list")
        marketWs.removeHandler("ticker")
        marketWs.removeHandler("candle_list")
        marketWs.removeHandler("candle")
    }

    const tickerHandler = (type: string, data: any) => {
        if (type === "ticker") {
            applyTicker(data)
        } else if (type === "ticker_list") {
            applyTickers(data)
        }
    }

    const candleHandler = (type: string, data: any) => {
        if (type === "candle") {
            applyCandle(data)
        } else if (type === "candle_list") {
            applyCandles(data)
        }
    }

    function applyTicker(payload: any) {
        // console.log("applyTicker", payload)
        if (payload.type !== "ticker") return
        const d = payload.data
        if (!market.value) return

        market.value.normalizedPrice = Number(d.normalized_price)
        market.value.normalizedVolume = Number(d.normalized_volume)
        market.value.high = Number(d.high)
        market.value.low = Number(d.low)
        market.value.changeRate = Number(d.price_change_rate)
        market.value.volume = Number(d.volume)

    }

    function applyTickers(payload: any) {
        // console.log("applyTickers", payload)
        for (const item of payload) {
            if (item.type !== "ticker") continue
            const d = item.data

            const target = markets.value.find(
                m =>
                    m.exchange === d.exchange_code &&
                    m.symbol === d.exchange_symbol
            )

            if (!target) return

            target.normalizedPrice = Number(d.normalized_price)
            target.normalizedVolume = Number(d.normalized_volume)
            target.change = Number(d.price_change)
            target.changeRate = Number(d.price_change_rate)
            target.volume = Number(d.volume)
        }

        // 추후 리스트 sorting 추가 예정
    }

    function applyCandle(payload: any) {
        // console.log("applyCandle", payload)
        if (payload.type !== "candle") return

        const d = payload.data
        if (!market.value) return
        market.value.closePrice = Number(d.close)

        const price = Number(d.close)
        const rawTime = Number(d.ts_open) / 1000

        if (!isFinite(price) || !isFinite(rawTime)) return
        const intervalSec = TIMEFRAME_SECONDS[currentTimeframe.value]
        const candleTime = Math.floor(rawTime / intervalSec) * intervalSec

        // 🔥 최초
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

        // 🔥 같은 분 → 누적
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

        // 🔥 새로운 분 → 새 캔들
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

    function applyCandles(payload: any) {
        // console.log("applyCandles", payload)
        for (const item of payload) {
            if (item.type !== "candle") continue

            const d = item.data

            const target = markets.value.find(
                m =>
                    m.exchange === d.exchange_code &&
                    m.symbol === d.exchange_symbol
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
        exchanges.value = []
        currentTimeframe.value = ChartTimeframe.MIN_1
        candlesListQuery.value = {}
    }

    return {
        candles,
        market,
        markets,
        simpleMarkets,
        exchanges,

        currentCandle,
        currentSortLabel,
        currentTimeframe,
        currentSystemTab,
        openSort,

        marketListQuery,
        candlesListQuery,
        simpleMarketListQuery,

        fetchMarket,
        fetchMarkets,
        fetchSimpleMarkets,
        fetchExchanges,
        fetchCandles,

        resetMarket,
        toggleWatchlist,
        changeTimeFrame,

        setSimpleMarketSearch,
        setMarketSearch,
        setMarketFilter,
        setSort,

        subscribeMarket,
        unsubscribeMarket,
        subscribeMarkets,
        unsubscribeMarkets,
        initWs,
        cleanupWs
    }
})