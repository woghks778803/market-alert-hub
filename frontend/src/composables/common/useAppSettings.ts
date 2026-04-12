import { vuetify } from '@/plugins/vuetify'

enum BridgeType {
    THEME = "THEME",
    KEEP_SCREEN_ON = "KEEP_SCREEN_ON",
    VIBRATE = "VIBRATE",
    AUTH_LOGIN = "AUTH_LOGIN",
    AUTH_LOGOUT = "AUTH_LOGOUT",
}

export enum ThemeMode {
    SYSTEM = "system",
    LIGHT = "light",
    DARK = "dark"
}

export function useAppSettings() {

    const ThemeLabel: Record<ThemeMode, string> = {
        [ThemeMode.SYSTEM]: "시스템",
        [ThemeMode.LIGHT]: "라이트",
        [ThemeMode.DARK]: "다크",
    }

    const STORAGE_KEYS = {
        theme: "app.theme",
        vibrateEnabled: "app.vibrate_enabled",
        keepScreenOnEnabled: "app.keep_screen_on_enabled",
    } as const

    function postBridgeMessage(type: BridgeType, payload: Record<string, unknown>): void {
        // console.log("postBridgeMessage", type, payload)
        window.AppBridge?.postMessage(
            JSON.stringify({
                type,
                payload,
            }),
        )
    }

    function getBoolean(key: string, fallback = false): boolean {
        const raw = localStorage.getItem(key)
        if (raw === null) return fallback
        return raw === "true"
    }

    function setBoolean(key: string, value: boolean): void {
        localStorage.setItem(key, String(value))
    }

    function resolveIsDark(mode: ThemeMode): boolean {
        if (mode === ThemeMode.DARK) return true
        if (mode === ThemeMode.LIGHT) return false
        return window.matchMedia("(prefers-color-scheme: dark)").matches
    }

    function applyTheme(mode: ThemeMode): void {
        localStorage.setItem(STORAGE_KEYS.theme, mode)

        const isDark = resolveIsDark(mode)
        document.documentElement.classList.toggle(ThemeMode.DARK, isDark)

        vuetify.theme.global.name.value = isDark ? ThemeMode.DARK : ThemeMode.LIGHT
        postBridgeMessage(BridgeType.THEME, { mode })
    }

    function getSavedTheme(): ThemeMode {
        const raw = localStorage.getItem(STORAGE_KEYS.theme)
        if (raw === ThemeMode.LIGHT || raw === ThemeMode.DARK || raw === ThemeMode.SYSTEM) return raw
        return ThemeMode.SYSTEM
    }

    function applyVibrate(enabled: boolean): void {
        setBoolean(STORAGE_KEYS.vibrateEnabled, enabled)

        postBridgeMessage(BridgeType.VIBRATE, {
            enabled,
        })
    }

    function getSavedVibrateEnabled(): boolean {
        return getBoolean(STORAGE_KEYS.vibrateEnabled, true)
    }

    function applyKeepScreenOn(enabled: boolean): void {
        setBoolean(STORAGE_KEYS.keepScreenOnEnabled, enabled)

        postBridgeMessage(BridgeType.KEEP_SCREEN_ON, {
            enabled,
        })
    }

    function getSavedKeepScreenOnEnabled(): boolean {
        return getBoolean(STORAGE_KEYS.keepScreenOnEnabled, false)
    }

    function applyLogin(): void {
        postBridgeMessage(BridgeType.AUTH_LOGIN, {})
    }

    function applyLogout(): void {
        postBridgeMessage(BridgeType.AUTH_LOGOUT, {})
    }

    function initAppSettings(): void {
        applyTheme(getSavedTheme())
        applyVibrate(getSavedVibrateEnabled())
        applyKeepScreenOn(getSavedKeepScreenOnEnabled())
    }

    function watchSystemTheme(): void {
        const media = window.matchMedia("(prefers-color-scheme: dark)")

        const handler = () => {
            if (getSavedTheme() !== ThemeMode.SYSTEM) return
            document.documentElement.classList.toggle(ThemeMode.DARK, media.matches)
            postBridgeMessage(BridgeType.THEME, { mode: ThemeMode.SYSTEM })
        }

        media.addEventListener("change", handler) // change는 addEventListener 내부 이벤트
    }

    return {
        ThemeLabel,

        applyLogin,
        applyLogout,
        applyTheme,
        getSavedTheme,
        applyVibrate,
        getSavedVibrateEnabled,
        applyKeepScreenOn,
        getSavedKeepScreenOnEnabled,
        initAppSettings,
        watchSystemTheme
    }
}