import { useUserStore } from '@/stores/user.store'
import { useAuthStore } from '@/stores/auth.store'
import type { ResetPasswordQuery, ChangePasswordQuery } from "@/services/auth.types"

export function useAuthFlow() {
    const userStore = useUserStore()
    const authStore = useAuthStore()

    async function logout(): Promise<void> {
        try {
            await authStore.logout()
        } catch (_) {
            // 무조건 무시
        } finally {
            authStore.clearStatus()

            userStore.clearMe()
            // channelStore.clear()  
        }
    }

    async function deactivate(): Promise<void> {
        try {
            await authStore.deactivate()
        } catch (_) {
            // 무조건 무시
        } finally {
            authStore.clearStatus()

            userStore.clearMe()
            // channelStore.clear()
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