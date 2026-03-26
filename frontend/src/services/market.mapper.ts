import type { MarketInfo, ExchangeInfo } from "@/api/market.api"
import type { MarketDto, ExchangeDto } from "@/services/market.types"

export function toMarketDto(data: MarketInfo): MarketDto {
    return {
        id: data.id,
        symbol: data.symbol,
        exchange: data.exchange_code,

        baseAsset: data.base_asset,
        quoteAsset: data.quote_asset,
        name: data.asset_name,

        isWatchlisted: data.is_watchlisted,

        open_price: data.open_price == null ? null : Number(data.open_price),
        close_price: data.close_price == null ? null : Number(data.close_price),
        change: data.price_change_24h == null ? null : Number(data.price_change_24h),
        changeRate: data.price_change_rate_24h == null ? null : Number(data.price_change_rate_24h),

        high: data.high_24h == null ? null : Number(data.high_24h),
        low: data.low_24h == null ? null : Number(data.low_24h),
        volume: data.volume_24h == null ? null : Number(data.volume_24h),
    }
}

export function toExchangeDto(data: ExchangeInfo): ExchangeDto {
    return {
        id: data.id,
        code: data.code,
        name: data.name
    }
}