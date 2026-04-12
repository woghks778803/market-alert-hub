import type { ResetPasswordQuery, ChangePasswordQuery } from "@/services/auth.types"
import { useUserStore } from '@/stores/user.store'
import { useAuthStore } from '@/stores/auth.store'
import { useAppSettings } from "@/composables/common/useAppSettings"

export function useAuthFlow() {
    const userStore = useUserStore()
    const authStore = useAuthStore()
    const {
        applyLogout,
    } = useAppSettings()


    async function logout(): Promise<void> {
        try {
            await authStore.logout()

            authStore.clearStatus()
            userStore.clearMe()
            applyLogout()
        } catch (_) {
            // 무조건 무시
        }
    }

    async function deactivate(): Promise<void> {
        try {
            await authStore.deactivate()

            authStore.clearStatus()
            userStore.clearMe()
        } catch (_) {
            // 무조건 무시
        }
    }

    async function resetPassword(payload: ResetPasswordQuery): Promise<void> {
        await authStore.resetPassword(payload)

        authStore.clearStatus()
        userStore.clearMe()
    }

    async function changePassword(payload: ChangePasswordQuery): Promise<void> {
        await authStore.changePassword(payload)

        authStore.clearStatus()
        userStore.clearMe()
    }

    return {
        logout,
        deactivate,
        resetPassword,
        changePassword,
    }
}