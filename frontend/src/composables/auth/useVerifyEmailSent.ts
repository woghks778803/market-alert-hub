import { computed, ref } from "vue"
import type { RouteLocationNormalizedLoaded } from "vue-router"
import { userApi } from "@/api/user.api"

export function useVerifyEmailSent(route: RouteLocationNormalizedLoaded) {
    const successMessage = ref<string | null>(null)
    const errorMessage = ref<string | null>(null)
    const sending = ref(false)
    const cooldownSec = ref(0)
    let timer: number | null = null

    const isCooldown = computed(() => cooldownSec.value > 0)
    const canResend = computed(() => !sending.value && !isCooldown.value)

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

    function startCooldown(sec: number) {
        cooldownSec.value = sec

        if (timer) {
            clearInterval(timer)
            timer = null
        }

        timer = window.setInterval(() => {
            if (cooldownSec.value <= 1) {
                cooldownSec.value = 0
                if (timer) {
                    clearInterval(timer)
                    timer = null
                }
            } else {
                cooldownSec.value -= 1
            }
        }, 1000)
    }

    async function resend(onResend?: () => Promise<void> | void) {
        if (!canResend.value) return
        sending.value = true
        successMessage.value = null
        errorMessage.value = null

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
        resend,
        cooldownSec,
        isCooldown,
        startCooldown,

        // me/email
        loadingMe,
        meEmail,
        email,
        loadMe,
    }
}