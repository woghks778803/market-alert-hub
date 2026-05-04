import { wsClient, type WsMessage } from './ws.client'
export type WsHandler = (type: string, data: WsMessage) => void

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

class MarketWs {
  // private markets: Set<string>
  private subscriptions: Set<string>
  private handlers: Record<string, WsHandler>

  constructor() {
    // this.markets = new Set()
    this.subscriptions = new Set()
    this.handlers = {}
  }

  addHandler(types: string[], handler: WsHandler) {
    for (const type of types) {
      this.handlers[type] = handler
    }
  }

  removeHandler(type: string) {
    delete this.handlers[type]
  }

  // subscribeList(markets: Set<string>) {
  //     console.log("markets", markets)
  //     markets.forEach(m => this.markets.add(m))
  //     wsClient.send({
  //         type: "SUBSCRIBE_LIST",
  //         markets: Array.from(markets),
  //     })
  // }

  // unSubscribeList(markets: Set<string>) {
  //     markets.forEach(m => this.markets.delete(m))
  //     wsClient.send({
  //         type: "UNSUBSCRIBE_LIST",
  //         markets: Array.from(markets),
  //     })
  // }

  subscribe(key: string) {
    if (this.subscriptions.has(key)) return
    this.subscriptions.add(key)
    wsClient.send({
      type: 'SUBSCRIBE',
      channel: key,
    })
  }

  unSubscribe(key: string) {
    if (!this.subscriptions.has(key)) return
    this.subscriptions.delete(key)
    wsClient.send({
      type: 'UNSUBSCRIBE',
      channel: key,
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
        const payload = data?.data
        if (!payload) return
        const handler = this.handlers[type]
        if (!handler) return
        handler(type, payload)
      }
    }
  }

  resubscribe = () => {
    wsClient.send({
      type: 'SUBSCRIBE_LIST',
      channels: Array.from(this.subscriptions),
    })
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
