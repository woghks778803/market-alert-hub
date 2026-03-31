import type { MarketInfo, ExchangeInfo, MarketListRequest, ExchangeListRequest, CandlesListRequest } from "@/api/market.api"
import type { MarketDto, ExchangeDto, CandleDto, MarketListQuery, ExchangeListQuery, CandlesListQuery } from "@/services/market.types"

export function toMarketDto(data: MarketInfo): MarketDto {
    return {
        id: data.id,
        symbol: data.symbol,
        exchange: data.exchange_code,

        baseAsset: data.base_asset,
        quoteAsset: data.quote_asset,
        name: data.asset_name,

        isWatchlisted: data.is_watchlisted,

        openPrice: data.open_price == null ? null : Number(data.open_price),
        closePrice: data.close_price == null ? null : Number(data.close_price),
        change: data.price_change_24h == null ? null : Number(data.price_change_24h),
        changeRate: data.price_change_rate_24h == null ? null : Number(data.price_change_rate_24h),

        high: data.high_24h == null ? null : Number(data.high_24h),
        low: data.low_24h == null ? null : Number(data.low_24h),
        volume: data.volume_24h == null ? null : Number(data.volume_24h),

        normalizedPrice: data.normalized_price == null ? null : Number(data.normalized_price),
        normalizedVolume: data.normalized_volume == null ? null : Number(data.normalized_volume),
    }
}

export function toExchangeDto(data: ExchangeInfo): ExchangeDto {
    return {
        id: data.id,
        code: data.code,
        name: data.name
    }
}
export function toCandleDto(data: any): CandleDto {
    return {
        id: data.id,

        tsOpen: new Date(data.ts_open).getTime(),

        open: Number(data.open),
        high: Number(data.high),
        low: Number(data.low),
        close: Number(data.close),

        volume: data.volume == null ? 0 : Number(data.volume),
    }
}

export function toMarketListRequest(q: MarketListQuery): MarketListRequest {
    return {
        search: q.search,
        exchange_codes: q.exchangeCodes,
        watchlist_only: q.watchlistOnly,
        sort: q.sort,
    }
}

export function toExchangeListRequest(q: ExchangeListQuery): ExchangeListRequest {
    return {
        limit: q.limit,
        offset: q.offset,
    }
}

export function toCandlesListRequest(q: CandlesListQuery): CandlesListRequest {
    return {
        exchange_instrument_id: q.exchangeInstrumentId,

        output: q.output,

        cursor: q.cursor,
        start: q.start,
        end: q.end,

        limit: q.limit,
        order: q.order,
    }
}

