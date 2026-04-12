type UnauthorizedHandler = () => void

let unauthorizedHandler: UnauthorizedHandler | null = null

// App.vue에서 등록
export function onUnauthorized(fn: UnauthorizedHandler) {
    unauthorizedHandler = fn
}

// http(interceptor)에서 호출
export function emitUnauthorized() {
    unauthorizedHandler?.()
}