import { http } from "./http"
import type { Envelope } from "./types"

export type WatchlistCreateRequest = {
    exchange_instrument_id: number
    sort_order?: number
}

export type WatchlistItemRead = {
    id: number
    exchange_instrument_id: number
    sort_order: number
}

export const watchlistApi = {
    // POST /watchlists
    async create(payload: WatchlistCreateRequest) {
        const { data } = await http.post<Envelope<WatchlistItemRead>>(
            "/watchlists", payload
        );
        return data;
    },

    // POST /watchlists/{exchange_instrument_id}
    async remove(exchangeInstrumentId: number) {
        const { data } = await http.delete(
            `/watchlists/${exchangeInstrumentId}`
        );
        return data;
    },
} 