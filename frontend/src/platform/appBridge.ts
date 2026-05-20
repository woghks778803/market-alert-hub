import { BridgeType } from '@/types/bridge.types'

export function postBridgeMessage(type: BridgeType, payload: Record<string, unknown>): void {
  // console.log("postBridgeMessage", type, payload)
  window.AppBridge?.postMessage(
    JSON.stringify({
      type,
      payload,
    })
  )
}