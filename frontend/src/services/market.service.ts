import { marketApi } from '@/api/market.api'

import {
  toMarketSimpleDto,
  toMarketDto,
  toExchangeSimpleDto,
  toExchangeDetailDto,
  toInstrumentDetailDto,
  toCandleDto,
  toMarketListRequest,
  toCandlesListRequest,
} from '@/services/market.mapper'
import type {
  MarketSimpleDto,
  MarketDto,
  ExchangeSimpleDto,
  ExchangeDetailDto,
  InstrumentDetailDto,
  CandleDto,
  MarketListQuery,
  CandlesListQuery,
} from '@/services/market.types'

export async function getMarket(exchangeCode: string, exchangeSymbol: string): Promise<MarketDto> {
  const env = await marketApi.getMarket(exchangeCode, exchangeSymbol)

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_market_response')
  }

  return toMarketDto(env.data)
}

export async function getMarkets(payload: MarketListQuery): Promise<MarketDto[]> {
  const env = await marketApi.getMarkets(toMarketListRequest(payload))

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_market_list_response')
  }

  return env.data.map(toMarketDto)
}

export async function getMarketSimples(payload: { search: string }): Promise<MarketSimpleDto[]> {
  const env = await marketApi.getMarketSimples(payload)

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_market_simple_list_response')
  }

  return env.data.map(toMarketSimpleDto)
}

export async function getExchangeSimples(): Promise<ExchangeSimpleDto[]> {
  const env = await marketApi.getExchangeSimples()

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_exchange_simple_list_response')
  }

  return env.data.map(toExchangeSimpleDto)
}

export async function getExchangeDetail(exchangeCode: string): Promise<ExchangeDetailDto> {
  const env = await marketApi.getExchangeDetail(exchangeCode)

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_exchange_detail_response')
  }

  return toExchangeDetailDto(env.data)
}

export async function getExchangeMarkets(exchangeCode: string): Promise<MarketDto[]> {
  const env = await marketApi.getExchangeMarkets(exchangeCode)

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_exchange_market_list_response')
  }

  return env.data.map(toMarketDto)
}

export async function getInstrumentDetail(instrumentSymbol: string): Promise<InstrumentDetailDto> {
  const env = await marketApi.getInstrumentDetail(instrumentSymbol)

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_instrument_detail_response')
  }

  return toInstrumentDetailDto(env.data)
}

export async function getInstrumentMarkets(instrumentSymbol: string): Promise<MarketDto[]> {
  const env = await marketApi.getInstrumentMarkets(instrumentSymbol)

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_instrument_market_list_response')
  }

  return env.data.map(toMarketDto)
}

export async function getCandles(payload: CandlesListQuery): Promise<CandleDto[]> {
  const env = await marketApi.getCandles(toCandlesListRequest(payload))

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_candle_list_response')
  }

  return env.data.map(toCandleDto)
}


// ----------- WS -----------------
