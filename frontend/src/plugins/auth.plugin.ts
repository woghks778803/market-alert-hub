import type { App } from 'vue'
import { onUnauthorized } from '@/events/auth.events'
import { useAuthStore } from '@/stores/auth.store'
import { useAppSettings } from '@/composables/common/useAppSettings'
import { router } from '@/routes'

export function createAuthPlugin(pinia: any) {
    return {
        install(app: App) {
            onUnauthorized(() => {
                const authStore = useAuthStore(pinia)
                const { applyLogout } = useAppSettings()

                authStore.clearStatus()
                applyLogout()
                router.replace({ name: "Login" })
            })
        },
    }
}