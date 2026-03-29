import { http } from "./http"
import type { Envelope } from "./types"

export type ExchangeInfo = {
    id: number
    code: string
    name: string
}

export type MarketInfo = {
    id: number
    symbol: string
    exchange_code: string

    base_asset: string
    quote_asset: string
    asset_name: string

    is_watchlisted: boolean

    open_price: string | null
    close_price: string | null
    price_change_24h: string | null
    price_change_rate_24h: string | null

    high_24h: string | null
    low_24h: string | null
    volume_24h: string | null

    normalized_price: string | null
    normalized_volume: string | null
}

export type MarketListRequest = {
    exchange_codes?: string[]
    search?: string
    watchlist_only?: boolean
    sort?: string
}

export type ExchangeListRequest = {
    limit?: number
    offset?: number
}

export const marketApi = {

    // GET /markets/{exchange_instrument_id}
    // async getMarket(id: number) {
    //     const { data } = await http.get<Envelope<MarketInfo>>(
    //         `/markets/${id}`
    //     );
    //     return data;
    // },

    // GET /markets/{exchange_code}/{symbol}
    async getMarket(exchange_code: string, symbol: string) {
        const { data } = await http.get<Envelope<MarketInfo>>(
            `/markets/${exchange_code}/${symbol}`
        );
        return data;
    },

    // GET /markets
    async getMarkets(params?: MarketListRequest) {
        const { data } = await http.get<Envelope<MarketInfo[]>>(
            '/markets',
            { params }
        );
        return data;
    },

    // GET /markets/exchanges
    async getExchanges(params?: ExchangeListRequest) {
        const { data } = await http.get<Envelope<ExchangeInfo[]>>(
            '/markets/exchanges',
            { params }
        );
        return data;
    },
}
