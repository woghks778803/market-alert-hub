import type {
  MarketSimpleInfo,
  MarketInfo,
  ExchangeSimpleInfo,
  ExchangeDetailInfo,
  InstrumentDetailInfo,
  CandleInfo,
  MarketListRequest,
  ExchangeListRequest,
  CandlesListRequest,
} from '@/api/market.api'
import type {
  CandleSnapshotInfo,
  TickerSnapshotInfo,
} from '@/services/ws/market.ws'
import type {
  CandleSnapshotDto,
  TickerSnapshotDto,
  MarketSimpleDto,
  MarketDto,
  ExchangeSimpleDto,
  ExchangeDetailDto,
  InstrumentDetailDto,
  CandleDto,
  MarketListQuery,
  ExchangeListQuery,
  CandlesListQuery,
} from '@/services/market.types'

export function toMarketDto(data: MarketInfo): MarketDto {
  return {
    exchangeInstrumentId: data.exchange_instrument_id,
    exchangeSymbol: data.exchange_symbol,
    exchangeCode: data.exchange_code,
    exchangeName: data.exchange_name,

    name: data.base_name,
    nameKo: data.base_name_ko,
    baseSymbol: data.base_symbol,
    quoteSymbol: data.quote_symbol,

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

export function toMarketSimpleDto(data: MarketSimpleInfo): MarketSimpleDto {
  return {
    label: data.exchange_name + ' · ' + data.exchange_symbol,
    exchangeInstrumentId: data.exchange_instrument_id,
    exchangeSymbol: data.exchange_symbol,
    exchangeName: data.exchange_name,
    baseSymbol: data.base_symbol,
    quoteSymbol: data.quote_symbol,
  }
}

export function toExchangeSimpleDto(data: ExchangeSimpleInfo): ExchangeSimpleDto {
  return {
    id: data.id,
    code: data.code,
    name: data.name,
  }
}

export function toExchangeDetailDto(data: ExchangeDetailInfo): ExchangeDetailDto {
  return {
    id: data.id,
    code: data.code,
    name: data.name,
    nameKo: data.name_ko,
    country: data.country,
    timezone: data.timezone,
    baseUrl: data.base_url,
    marketCount: data.market_count,
  }
}

export function toInstrumentDetailDto(data: InstrumentDetailInfo): InstrumentDetailDto {
  return {
    id: data.id,
    symbol: data.symbol,
    name: data.name,
    nameKo: data.name_ko,
    assetType: data.asset_type,
    exchangeCount: data.exchange_count,
    marketCount: data.market_count,
  }
}

export function toCandleDto(data: CandleInfo): CandleDto {
  return {
    exchangeInstrumentId: data.exchange_instrument_id,

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

// ----------- WS -----------------

export function toTickerSnapshotDto(
  data: TickerSnapshotInfo,
): TickerSnapshotDto {
  return {
    ts: data.ts,

    price: Number(data.price),
    open: Number(data.open),
    high: Number(data.high),
    low: Number(data.low),

    volume: Number(data.volume),

    priceChange: Number(data.price_change),
    priceChangeRate: Number(data.price_change_rate),

    normalizedPrice: Number(data.normalized_price),
    normalizedVolume: Number(data.normalized_volume),

    exchangeCode: data.exchange_code,
    exchangeSymbol: data.exchange_symbol,
  }
}

export function toCandleSnapshotDto(
  data: CandleSnapshotInfo,
): CandleSnapshotDto {
  return {
    tsOpen: data.ts_open,

    open: Number(data.open),
    high: Number(data.high),
    low: Number(data.low),
    close: Number(data.close),

    volume: Number(data.volume),

    exchangeCode: data.exchange_code,
    exchangeSymbol: data.exchange_symbol,
  }
}
