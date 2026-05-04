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

export type ExchangeInfo = {
  id: number
  code: string
  name: string
}

export type MarketInfo = {
  exchange_instrument_id: number
  exchange_symbol: string
  exchange_code: string
  exchange_name: string

  base_symbol: string
  quote_symbol: string
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

export type SimpleMarketInfo = {
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
  // GET /markets/{exchange_code}/{symbol}
  async getMarket(exchange_code: string, symbol: string) {
    const { data } = await http.get<Envelope<MarketInfo>>(`/markets/${exchange_code}/${symbol}`)
    return data
  },

  // GET /markets
  async getMarkets(params?: MarketListRequest) {
    const { data } = await http.get<Envelope<MarketInfo[]>>('/markets', { params })
    return data
  },

  // GET /markets/exchange-instruments
  async getSimpleMarkets(params?: { search: string }) {
    const { data } = await http.get<Envelope<SimpleMarketInfo[]>>('/markets/exchange-instruments', {
      params,
    })
    return data
  },

  // GET /markets/exchanges
  async getExchanges(params?: ExchangeListRequest) {
    const { data } = await http.get<Envelope<ExchangeInfo[]>>('/markets/exchanges', { params })
    return data
  },

  // GET /markets/candles
  async getCandles(params?: CandlesListRequest) {
    const { data } = await http.get<Envelope<CandleInfo[]>>('/markets/candles', { params })
    return data
  },
}
