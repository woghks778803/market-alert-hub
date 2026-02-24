import { computed, ref } from "vue"
import type { RouteLocationNormalizedLoaded } from "vue-router"

export function useVerifyEmailSent(route: RouteLocationNormalizedLoaded) {
    const successMessage = ref<string | null>(null)
    const errorMessage = ref<string | null>(null)
    const sending = ref(false)

    const canResend = computed(() => !sending.value)

    async function send(onResend?: () => Promise<void> | void) {
        if (!canResend.value) return
        successMessage.value = null
        errorMessage.value = null

        sending.value = true
        try {
            // TODO: API 호출은 여기서 붙이면 됨
            await onResend?.()
        } finally {
            sending.value = false
        }
    }

    return {
        successMessage,
        errorMessage,

        // resend
        sending,
        canResend,
        send,
    }
}