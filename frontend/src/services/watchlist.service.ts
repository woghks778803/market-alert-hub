import { watchlistApi } from '@/api/watchlist.api'

export async function createWatchlist(payload: {
  exchangeInstrumentId: number
  sortOrder?: number
}) {
  const env = await watchlistApi.create({
    exchange_instrument_id: payload.exchangeInstrumentId,
    sort_order: payload.sortOrder ?? 0,
  })

  if (!env.success || !env.data) {
    throw new Error('create_watchlist_failed')
  }

  return env.data
}

export async function removeWatchlist(id: number) {
  await watchlistApi.remove(id)
}
