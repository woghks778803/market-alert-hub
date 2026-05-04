// import type { App } from 'vue'
import type { Pinia } from 'pinia'
import { router } from '@/routes'
import { onUnauthorized } from '@/events/auth.events'
import { useAuthStore } from '@/stores/auth.store'
import { useAppSettings } from '@/composables/common/useAppSettings'

export function createAuthPlugin(pinia: Pinia) {
  return {
    install() { // (app: App)
      onUnauthorized(() => {
        const authStore = useAuthStore(pinia)
        const { applyLogout } = useAppSettings()

        authStore.clearStatus()
        applyLogout()
        router.replace({ name: 'Login' })
      })
    },
  }
}
