import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { marketWs } from "@/services/ws/market.ws"
import { getMarket, getMarkets, getExchanges, getCandles } from "@/services/market.service"
import { createWatchlist, removeWatchlist } from "@/services/watchlist.service"
import type { MarketDto, ExchangeDto, CandleDto } from "@/services/market.types"
import { MarketSort, CandleInterval, TickerInterval, WsChannelType, MarketSortLabel } from "@/services/market.types"

export const useMarketStore = defineStore("market", () => {
    const lastCandleUpdate = ref<CandleDto | null>(null)
    const market = ref<MarketDto | null>(null)
    const markets = ref<MarketDto[]>([])
    const exchanges = ref<ExchangeDto[]>([])
    const search = ref("")
    const openSort = ref(false)
    const currentInterval = ref<CandleInterval>(CandleInterval.MIN_1)

    const query = ref({
        search: "",
        exchange_codes: [] as string[],
        watchlist_only: false,
        sort: "volume_desc" as MarketSort,
    })


    const currentSortLabel = computed(() => {
        return MarketSortLabel[query.value.sort]
    })

    async function fetchMarket(exchange_code: string, symbol: string) {
        market.value = await getMarket(exchange_code, symbol)
    }

    async function fetchMarkets() {
        markets.value = await getMarkets({
            search: query.value.search,
            exchange_codes: query.value.exchange_codes,
            watchlist_only: query.value.watchlist_only,
            sort: query.value.sort,
        })
    }

    async function fetchExchanges() {
        exchanges.value = await getExchanges({})
    }

    async function fetchCandles() {
        if (!market.value) return

        return await getCandles({
            exchange_instrument_id: market.value.id,

            output: currentInterval.value, // string 처리했으니까 그대로

            limit: 500,
            order: "desc",
        })
    }

    function resetMarket() {
        lastCandleUpdate.value = null
        market.value = null
        markets.value = []
        exchanges.value = []
    }

    async function toggleWatchlist(item: MarketDto) {
        console.log(item)
        if (item.isWatchlisted) {
            await removeWatchlist(item.id)
            item.isWatchlisted = false
        } else {
            await createWatchlist({ exchangeInstrumentId: item.id })
            item.isWatchlisted = true
        }
    }

    let timer: any

    function setSearch(value: string) {
        clearTimeout(timer)
        timer = setTimeout(() => {
            query.value.search = value
            fetchMarkets()
        }, 300)
    }

    function setExchange(codes: string[]) {
        const isAll = codes.includes("all")
        const isWatchlist = codes.includes("watchlist")

        if (isAll) {
            query.value.exchange_codes = []
        } else {
            query.value.exchange_codes = codes.filter(
                v => v !== "watchlist"
            )
        }

        query.value.watchlist_only = isWatchlist

        fetchMarkets()
    }

    function setSort(sort: MarketSort) {
        query.value.sort = sort
        fetchMarkets()
    }

    // key 생성
    function buildMarketKey(
        channelType: WsChannelType,
        interval: CandleInterval | TickerInterval = CandleInterval.SEC_1): string | null {
        return market.value ? `${channelType}:${interval}:${market.value.exchange}:${market.value.symbol}` : null
    }

    // 구독
    function subscribeMarket(
        channelType: WsChannelType,
        interval: CandleInterval | TickerInterval
    ) {
        const key = buildMarketKey(channelType, interval)
        if (key) {
            marketWs.subscribe(key)
        }
    }
    function unsubscribeMarket(
        channelType: WsChannelType,
        interval: CandleInterval | TickerInterval
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
        if (payload.type !== "candle") return

        const d = payload.data
        if (!market.value) return
        market.value.closePrice = Number(d.close)

        const price = Number(d.close)
        const rawTime = Number(d.ts_open) / 1000

        if (!isFinite(price) || !isFinite(rawTime)) return

        const candleTime = Math.floor(rawTime / 60) * 60

        // 🔥 최초
        if (!lastCandleUpdate.value) {
            lastCandleUpdate.value = {
                id: market.value.id,
                tsOpen: candleTime,
                open: price,
                high: price,
                low: price,
                close: price,
                volume: Number(d.volume) || 0,
            }
            return
        }

        const prev = lastCandleUpdate.value

        // 🔥 같은 분 → 누적
        if (prev.tsOpen === candleTime) {
            lastCandleUpdate.value = {
                ...prev,
                high: Math.max(prev.high, price),
                low: Math.min(prev.low, price),
                close: price,
                volume: prev.volume + (Number(d.volume) || 0),
            }
            return
        }

        // 🔥 새로운 분 → 새 캔들
        lastCandleUpdate.value = {
            id: market.value.id,
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

    function changeInterval(next: CandleInterval) {
        if (currentInterval.value === next) return

        // 기존 해제
        unsubscribeMarket(WsChannelType.CANDLE, currentInterval.value)
        // 변경
        currentInterval.value = next
        // 새 구독
        subscribeMarket(WsChannelType.CANDLE, currentInterval.value)
    }

    return {
        lastCandleUpdate,
        currentInterval,
        market,
        markets,
        exchanges,
        query,

        search,
        openSort,

        fetchMarket,
        fetchMarkets,
        fetchExchanges,
        fetchCandles,

        currentSortLabel,
        resetMarket,
        toggleWatchlist,

        setSearch,
        setExchange,
        setSort,

        subscribeMarket,
        unsubscribeMarket,
        subscribeMarkets,
        unsubscribeMarkets,
        initWs,
        cleanupWs
    }
})