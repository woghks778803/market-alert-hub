import {
  wsClient,
  type WsMessage
} from '@/services/ws/ws.client'
import {
  WsChannelType,
} from '@/services/market.types'

export type WsHandler = (type: WsChannelType, data: WsMessage) => void

export interface TickerSnapshotInfo {
  ts: number

  price: string
  open: string
  high: string
  low: string

  volume: string

  price_change: string
  price_change_rate: string

  normalized_price: string
  normalized_volume: string

  exchange_code: string
  exchange_symbol: string
}

export interface CandleSnapshotInfo {
  ts_open: number

  open: string
  high: string
  low: string
  close: string

  volume: string

  exchange_code: string
  exchange_symbol: string
}

const WS_CHANNEL_TYPES = new Set<string>(
  Object.values(WsChannelType),
)

const isWsChannelType = (
  type: string,
): type is WsChannelType => {
  return WS_CHANNEL_TYPES.has(type)
}

class MarketWs {
  private listSubscriptions: Map<WsChannelType, Set<string>>
  private singleSubscriptions: Map<WsChannelType, string>
  private handlers: Record<string, WsHandler>

  constructor() {
    this.listSubscriptions = new Map<WsChannelType, Set<string>>()
    this.singleSubscriptions = new Map<WsChannelType, string>()
    this.handlers = {}
  }

  addHandler(types: WsChannelType[], handler: WsHandler) {
    for (const type of types) {
      this.handlers[type] = handler
    }
  }

  removeHandler(type: WsChannelType) {
    delete this.handlers[type]
  }

  subscribeList(
    channelType: WsChannelType,
    channels: Iterable<string>,
  ): void {
    const next = new Set(channels)
    const current = this.listSubscriptions.get(channelType)

    const isSame =
      current?.size === next.size &&
      [...next].every(channel => current.has(channel))

    if (isSame) return

    this.listSubscriptions.set(channelType, next)

    wsClient.send({
      type: 'SUBSCRIBE',
      channel_type: channelType,
      channels: [...next],
    })
  }

  unSubscribeList(
    channelType: WsChannelType,
  ) {
    if (!this.listSubscriptions.has(channelType)) return

    this.listSubscriptions.delete(channelType)

    wsClient.send({
      type: "UNSUBSCRIBE",
      channel_type: channelType,
    })
  }

  subscribe(
    channelType: WsChannelType,
    channel: string
  ) {
    const current = this.singleSubscriptions.get(channelType)

    if (current == channel) return

    this.singleSubscriptions.set(channelType, channel)

    wsClient.send({
      type: 'SUBSCRIBE',
      channel_type: channelType,
      channel,
    })
  }

  unSubscribe(
    channelType: WsChannelType,
  ) {
    const channel = this.singleSubscriptions.get(channelType)

    if (!channel) return

    this.singleSubscriptions.delete(channelType)

    wsClient.send({
      type: 'UNSUBSCRIBE',
      channel_type: channelType,
      channel
    })
  }

  handleMessage = (data: WsMessage) => {
    const type = data?.type
    if (!type) return

    switch (type) {
      case 'init':
        // 초기 연결 성공 (필요하면 로그)
        // console.log("WS INIT")
        return

      case 'error':
        console.error('WS ERROR:', data.message)
        return

      case 'pong':
        // ping 응답 (필요하면 사용)
        return

      default: {
        // -----------------------------
        // market 데이터 처리
        // -----------------------------
        if (!isWsChannelType(type)) return

        const payload = data?.data
        if (!payload) return
        const handler = this.handlers[type]
        if (!handler) return
        handler(type, payload)
      }
    }
  }

  private resubscribe = () => {
    for (const [channelType, channel] of this.singleSubscriptions) {
      wsClient.send({
        type: 'SUBSCRIBE',
        channel_type: channelType,
        channel,
      })
    }

    for (const [channelType, channels] of this.listSubscriptions) {
      wsClient.send({
        type: 'SUBSCRIBE',
        channel_type: channelType,
        channels: Array.from(channels),
      })
    }
  }

  init() {
    wsClient.addHandler(this.handleMessage)
    wsClient.addOpenHandler(this.resubscribe)
  }

  destroy() {
    wsClient.removeHandler(this.handleMessage)
    wsClient.removeOpenHandler(this.resubscribe)
  }
}

export const marketWs = new MarketWs()
