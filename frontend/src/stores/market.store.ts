import { defineStore } from "pinia"
import { ref, computed } from "vue"
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

    async function fetchMarket(id: number) {
        market.value = await getMarket(id)
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
    }
})