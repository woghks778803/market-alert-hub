export type MarketDto = {
    id: number
    symbol: string
    exchange: string

    baseAsset: string
    quoteAsset: string
    name: string

    isWatchlisted: boolean

    openPrice: number | null
    closePrice: number | null
    change: number | null
    changeRate: number | null

    high: number | null
    low: number | null
    volume: number | null

    normalizedPrice: number | null
    normalizedVolume: number | null
}

export type ExchangeDto = {
    id: number,
    code: string
    name: string
}

export type CandleDto = {
    id: number
    tsOpen: number   // epoch ms
    open: number
    high: number
    low: number
    close: number
    volume: number
}

export type MarketListQuery = {
    search: string
    exchangeCodes?: string[]
    watchlistOnly?: boolean
    sort?: MarketSort
}

export type ExchangeListQuery = {
    limit?: number
    offset?: number
}

export type CandlesListQuery = {
    exchangeInstrumentId: number

    output?: string

    cursor?: string
    start?: string
    end?: string

    limit?: number
    order?: "asc" | "desc"
}

export enum MarketSort {
    VOLUME_DESC = "volume_desc",
    CHANGE_DESC = "change_desc",
    CHANGE_ASC = "change_asc",
    PRICE_DESC = "price_desc",
    PRICE_ASC = "price_asc",
}

export enum ChartTimeframe {
    MIN_1 = "1m",
    HOUR_1 = "1h",
    DAY_1 = "1d",
}

export enum CandleInterval {
    SEC_1 = "1s",
    MIN_1 = "1m",
    HOUR_1 = "1h",
    DAY_1 = "1d",
}

export enum TickerInterval {
    HOUR_24 = "24h",
}

export enum WsChannelType {
    CANDLE = "candle",
    TICKER = "ticker",
}

// UI 개념 객체는 Pascal
export const MarketSortLabel: Record<MarketSort, string> = {
    [MarketSort.VOLUME_DESC]: "거래대금 높은순",
    [MarketSort.CHANGE_DESC]: "상승률 높은순",
    [MarketSort.CHANGE_ASC]: "상승률 낮은순",
    [MarketSort.PRICE_DESC]: "가격 높은순",
    [MarketSort.PRICE_ASC]: "가격 낮은순",
}
// 설정 상수는 SCREAMING_SNAKE
export const TIMEFRAME_SECONDS: Record<ChartTimeframe, number> = {
    [ChartTimeframe.MIN_1]: 60,
    [ChartTimeframe.HOUR_1]: 3600,
    [ChartTimeframe.DAY_1]: 86400,
}

export const CANDLES_LIMIT: number = 3000