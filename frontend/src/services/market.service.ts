import {
    marketApi,
    type MarketListRequest, type ExchangeListRequest, type CandlesListRequest
} from "@/api/market.api"
import { toMarketDto, toExchangeDto, toCandleDto } from "./market.mapper"
import type { MarketDto, ExchangeDto, CandleDto } from "./market.types"

export async function getMarket(exchange_code: string, symbol: string): Promise<MarketDto> {
    const env = await marketApi.getMarket(exchange_code, symbol)

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_market_response")
    }

    return toMarketDto(env.data)
}

export async function getMarkets(payload: MarketListRequest): Promise<MarketDto[]> {
    const env = await marketApi.getMarkets(payload)

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_market_list_response")
    }

    return env.data.map(toMarketDto)
}

export async function getExchanges(payload: ExchangeListRequest): Promise<ExchangeDto[]> {
    const env = await marketApi.getExchanges(payload)

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_exchange_list_response")
    }

    return env.data.map(toExchangeDto)
}

export async function getCandles(payload: CandlesListRequest): Promise<CandleDto[]> {
    const env = await marketApi.getCandles(payload)

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_candle_list_response")
    }

    return env.data.map(toCandleDto)
}