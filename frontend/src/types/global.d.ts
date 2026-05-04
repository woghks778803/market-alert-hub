interface AppBridge {
  postMessage: (message: string) => void
}

declare global {
  interface Window {
    AppBridge?: AppBridge
  }
}

export {}
