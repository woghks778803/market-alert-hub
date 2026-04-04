import {
    marketApi,
} from "@/api/market.api"

import { toMarketDto, toExchangeDto, toCandleDto, toMarketListRequest, toCandlesListRequest, toExchangeListRequest } from "@/services/market.mapper"
import type { MarketDto, ExchangeDto, CandleDto, MarketListQuery, ExchangeListQuery, CandlesListQuery } from "@/services/market.types"

export async function getMarket(exchange_code: string, symbol: string): Promise<MarketDto> {
    const env = await marketApi.getMarket(exchange_code, symbol)

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_market_response")
    }

    return toMarketDto(env.data)
}

export async function getMarkets(payload: MarketListQuery): Promise<MarketDto[]> {
    const env = await marketApi.getMarkets(toMarketListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_market_list_response")
    }

    return env.data.map(toMarketDto)
}

export async function getExchanges(payload: ExchangeListQuery): Promise<ExchangeDto[]> {
    const env = await marketApi.getExchanges(toExchangeListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_exchange_list_response")
    }

    return env.data.map(toExchangeDto)
}

export async function getCandles(payload: CandlesListQuery): Promise<CandleDto[]> {
    const env = await marketApi.getCandles(toCandlesListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_candle_list_response")
    }

    return env.data.map(toCandleDto)
}