import { vuetify } from '@/plugins/vuetify'
import { postBridgeMessage } from '@/platform/appBridge'
import { BridgeType } from '@/types/bridge.types'

export enum ThemeMode {
  SYSTEM = 'system',
  LIGHT = 'light',
  DARK = 'dark',
}

export enum SoundMode {
  DEFAULT = 'default',
  SILENT = 'silent',
}

export function useAppSettings() {
  const ThemeLabel: Record<ThemeMode, string> = {
    [ThemeMode.SYSTEM]: '시스템',
    [ThemeMode.LIGHT]: '라이트',
    [ThemeMode.DARK]: '다크',
  }

  const NotificationSoundLabel: Record<SoundMode, string> = {
    [SoundMode.DEFAULT]: '기본',
    [SoundMode.SILENT]: '무음',
  }

  const STORAGE_KEYS = {
    theme: 'app.theme',
    notificationSound: 'app.notification_sound',
    vibrateEnabled: 'app.vibrate_enabled',
    keepScreenOnEnabled: 'app.keep_screen_on_enabled',
  } as const

  function getBoolean(key: string, fallback = false): boolean {
    const raw = localStorage.getItem(key)
    if (raw === null) return fallback
    return raw === 'true'
  }

  function setBoolean(key: string, value: boolean): void {
    localStorage.setItem(key, String(value))
  }

  function resolveIsDark(mode: ThemeMode): boolean {
    if (mode === ThemeMode.DARK) return true
    if (mode === ThemeMode.LIGHT) return false
    return window.matchMedia('(prefers-color-scheme: dark)').matches
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

  function applyNotificationSound(mode: SoundMode): void {
    localStorage.setItem(STORAGE_KEYS.notificationSound, mode)

    postBridgeMessage(BridgeType.NOTIFICATION_SOUND, { mode })
  }

  function getSavedNotificationSound(): SoundMode {
    const raw = localStorage.getItem(STORAGE_KEYS.notificationSound)
    if (raw === SoundMode.DEFAULT || raw === SoundMode.SILENT) return raw
    return SoundMode.DEFAULT
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
    applyKeepScreenOn(getSavedKeepScreenOnEnabled())
  }

  function watchSystemTheme(): void {
    const media = window.matchMedia('(prefers-color-scheme: dark)')

    const handler = () => {
      if (getSavedTheme() !== ThemeMode.SYSTEM) return
      document.documentElement.classList.toggle(ThemeMode.DARK, media.matches)
      postBridgeMessage(BridgeType.THEME, { mode: ThemeMode.SYSTEM })
    }

    media.addEventListener('change', handler) // change는 addEventListener 내부 이벤트
  }

  return {
    ThemeLabel,
    NotificationSoundLabel,

    applyLogin,
    applyLogout,
    applyTheme,
    getSavedTheme,
    applyNotificationSound,
    getSavedNotificationSound,
    applyKeepScreenOn,
    getSavedKeepScreenOnEnabled,
    applyVibrate,
    getSavedVibrateEnabled,
    initAppSettings,
    watchSystemTheme,
  }
}
