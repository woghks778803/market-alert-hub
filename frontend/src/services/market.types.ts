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

export enum MarketSort {
    VOLUME_DESC = "volume_desc",
    CHANGE_DESC = "change_desc",
    CHANGE_ASC = "change_asc",
    PRICE_DESC = "price_desc",
    PRICE_ASC = "price_asc",
}

export const MarketSortLabel: Record<MarketSort, string> = {
    [MarketSort.VOLUME_DESC]: "거래대금 높은순",
    [MarketSort.CHANGE_DESC]: "상승률 높은순",
    [MarketSort.CHANGE_ASC]: "상승률 낮은순",
    [MarketSort.PRICE_DESC]: "가격 높은순",
    [MarketSort.PRICE_ASC]: "가격 낮은순",
}