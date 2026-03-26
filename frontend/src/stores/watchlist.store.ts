import { defineStore } from "pinia"
import { ref } from "vue"
import { createWatchlist, removeWatchlist } from "@/services/watchlist.service"

export const useWatchlistStore = defineStore("watchlist", () => {
    const items = ref<Set<number>>(new Set())

    async function add(id: number) {
        await createWatchlist({ exchangeInstrumentId: id })
        items.value.add(id)
    }

    async function remove(id: number) {
        await removeWatchlist(id)
        items.value.delete(id)
    }

    function isWatchlisted(id: number) {
        return items.value.has(id)
    }

    return {
        items,
        add,
        remove,
        isWatchlisted,
    }
})