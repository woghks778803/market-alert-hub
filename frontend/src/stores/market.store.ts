import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { marketWs } from "@/services/ws/market.ws"
import { getMarket, getMarkets, getExchanges } from "@/services/market.service"
import { createWatchlist, removeWatchlist } from "@/services/watchlist.service"
import type { MarketDto, ExchangeDto } from "@/services/market.types"
import { MarketSort, MarketSortLabel } from "@/services/market.types"

export const useMarketStore = defineStore("market", () => {
    const market = ref<MarketDto | null>(null)
    const markets = ref<MarketDto[]>([])
    const exchanges = ref<ExchangeDto[]>([])
    const search = ref("")
    const openSort = ref(false)

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

    function resetMarket() {
        market.value = null
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
    function buildMarketKey() {
        return market.value ? `${market.value.exchange}:${market.value.symbol}` : null
    }

    // 구독
    function subscribeMarket() {
        const key = buildMarketKey()
        if (key) {
            marketWs.subscribe(key)
        }
    }
    function unsubscribeMarket() {
        const key = buildMarketKey()
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
        if (type === "ticker" || type === "ticker_list") {
            applyTicker(data)
        } else if (type === "candle_list") {
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

    return {
        market,
        markets,
        exchanges,
        query,

        search,
        openSort,

        fetchMarket,
        fetchMarkets,
        fetchExchanges,

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