import {
    marketApi,
    type MarketListRequest, type ExchangeListRequest
} from "@/api/market.api"
import { toMarketDto, toExchangeDto } from "./market.mapper"
import type { MarketDto, ExchangeDto } from "./market.types"

export async function getMarket(id: number): Promise<MarketDto> {
    const env = await marketApi.getMarket(id)

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