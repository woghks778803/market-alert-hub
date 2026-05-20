export type WsMessage = {
  type?: string
  data?: unknown
  message?: string
}

class WsClient<T = unknown> {
  private ws: WebSocket | null = null

  private url: string
  private reconnectTimer: number | null = null
  private isConnected: boolean = false
  private handlers: Set<(data: WsMessage) => void>
  private onOpenHandlers: Set<() => void>
  private manuallyClosed = false


  constructor(url: string) {
    this.url = url
    this.handlers = new Set()
    this.onOpenHandlers = new Set()
  }

  connect() {
    // console.log("this.isConnected", this.isConnected)
    if (this.isConnected) return
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.isConnected = true
      // subscript handler 실행
      this.onOpenHandlers.forEach((h) => h())
      console.log('WS connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        // message handler 실행
        this.handlers.forEach((h) => h(data))
      } catch (e) {
        console.error(e)
      }
    }

    this.ws.onclose = () => {
      console.log('WS disconnected')
      this.isConnected = false
      if (!this.manuallyClosed) this.reconnect()
    }

    this.ws.onerror = (e) => {
      console.error('WS error', e)
      this.isConnected = false
    }
  }

  private reconnect() {
    if (this.reconnectTimer) return

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, 1000)
  }

  send(data: T) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return
    this.ws.send(JSON.stringify(data))
  }

  addHandler(handler: (data: WsMessage) => void) {
    this.handlers.add(handler)
  }

  removeHandler(handler: (data: WsMessage) => void) {
    this.handlers.delete(handler)
  }

  addOpenHandler(handler: () => void) {
    this.onOpenHandlers.add(handler)
  }

  removeOpenHandler(handler: () => void) {
    this.onOpenHandlers.delete(handler)
  }

  close() {
    this.manuallyClosed = true
    this.ws?.close()
    this.ws = null
    this.isConnected = false
  }
}

const WS_URL = import.meta.env.VITE_WS_BASE_URL
export const wsClient = new WsClient(WS_URL)
