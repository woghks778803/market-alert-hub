import { http } from './http'
import type { Envelope } from './types'

export type CandleInfo = {
  exchange_instrument_id: number
  ts_open: number // datetime → epoch(ms)
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type ExchangeSimpleInfo = {
  id: number
  code: string
  name: string
}

export type ExchangeDetailInfo = {
  id: number
  code: string
  name: string
  name_ko: string | null
  country: string | null
  timezone: string
  base_url: string | null
  market_count: number
}

export type InstrumentDetailInfo = {
  id: number
  symbol: string
  name: string
  name_ko: string | null
  asset_type: string
  exchange_count: number
  market_count: number
}

export type MarketInfo = {
  exchange_instrument_id: number
  exchange_symbol: string
  exchange_code: string
  exchange_name: string

  base_name: string
  base_name_ko: string
  base_symbol: string
  quote_symbol: string

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

export type MarketSimpleInfo = {
  exchange_instrument_id: number
  exchange_symbol: string
  base_symbol: string
  quote_symbol: string
  exchange_name: string
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

export type CandlesListRequest = {
  exchange_instrument_id: number

  output?: string

  cursor?: string // ISO8601
  start?: string // ISO8601
  end?: string // ISO8601

  limit?: number
  order?: 'asc' | 'desc'
}

export const marketApi = {
  // GET /markets
  async getMarkets(params?: MarketListRequest) {
    const { data } = await http.get<Envelope<MarketInfo[]>>('/markets', { params })
    return data
  },

  // GET /markets/exchange-instruments
  async getMarketSimples(params?: { search: string }) {
    const { data } = await http.get<Envelope<MarketSimpleInfo[]>>('/markets/exchange-instruments', {
      params,
    })
    return data
  },

  // GET /markets/exchanges
  async getExchangeSimples() {
    const { data } = await http.get<Envelope<ExchangeSimpleInfo[]>>('/markets/exchanges')
    return data
  },

  // GET /markets/exchanges/{exchange_code}
  async getExchangeDetail(exchangeCode: string) {
    const { data } = await http.get<Envelope<ExchangeDetailInfo>>(`/markets/exchanges/${exchangeCode}`)
    return data
  },

  // GET /markets/exchanges/{exchange_code}/markets
  async getExchangeMarkets(exchangeCode: string) {
    const { data } = await http.get<Envelope<MarketInfo[]>>(`/markets/exchanges/${exchangeCode}/markets`)
    return data
  },

  // GET /markets/instruments/{instrument_symbol}
  async getInstrumentDetail(instrumentSymbol: string) {
    const { data } = await http.get<Envelope<InstrumentDetailInfo>>(`/markets/instruments/${instrumentSymbol}`)
    return data
  },

  // GET /markets/instruments/{instrument_symbol}/markets
  async getInstrumentMarkets(instrumentSymbol: string) {
    const { data } = await http.get<Envelope<MarketInfo[]>>(`/markets/instruments/${instrumentSymbol}/markets`)
    return data
  },

  // GET /markets/{exchange_code}/{market_code}
  async getMarket(exchangeCode: string, exchangeSymbol: string) {
    const { data } = await http.get<Envelope<MarketInfo>>(`/markets/${exchangeCode}/${exchangeSymbol}`)
    return data
  },

  // GET /markets/candles
  async getCandles(params?: CandlesListRequest) {
    const { data } = await http.get<Envelope<CandleInfo[]>>('/markets/candles', { params })
    return data
  },
}
