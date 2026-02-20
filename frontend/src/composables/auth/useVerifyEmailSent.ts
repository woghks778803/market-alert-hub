import { computed, ref } from "vue"
import type { RouteLocationNormalizedLoaded } from "vue-router"
import { userApi } from "@/api/user.api"

export function useVerifyEmailSent(route: RouteLocationNormalizedLoaded) {
    const sending = ref(false)
    const lastSentAt = ref<number | null>(null)
    const canResend = computed(() => !sending.value)

    const loadingMe = ref(false)
    const meEmail = ref<string | null>(null)

    async function loadMe() {
        loadingMe.value = true
        try {
            const envelope = await userApi.me()
            const e = envelope?.data?.email
            meEmail.value = typeof e === "string" && e.trim() ? e.trim() : null
        } catch (err) {
            // 토큰 없거나 만료면 그냥 무시하고 query fallback
            meEmail.value = null
        } finally {
            loadingMe.value = false
        }
    }

    const email = computed(() => {
        if (meEmail.value) return meEmail.value
        const q = route.query.email
        return typeof q === "string" && q.trim() ? q.trim() : "user@example.com"
    })

    async function resend(onResend?: () => Promise<void> | void) {
        if (!canResend.value) return
        sending.value = true
        try {
            // TODO: API 호출은 여기서 붙이면 됨
            await onResend?.()
            lastSentAt.value = Date.now()
        } finally {
            sending.value = false
        }
    }

    return {
        // resend
        sending,
        canResend,
        lastSentAt,
        resend,

        // me/email
        loadingMe,
        meEmail,
        email,
        loadMe,
    }
}