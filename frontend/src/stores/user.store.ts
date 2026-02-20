import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { userApi } from "@/api/user.api"

export const useUserStore = defineStore("user", () => {
    // --- state
    const me = ref<any | null>(null)         // DTO 타입 있으면 바꿔
    const loadingMe = ref(false)
    const meLoadedOnce = ref(false)
    const meError = ref<unknown | null>(null)

    // 중복 fetch 방지(동시에 여러 컴포넌트가 호출해도 1번만)
    let inflight: Promise<any | null> | null = null

    // --- getters
    const isAuthed = computed(() => !!me.value)

    // --- actions
    async function fetchMe(opts?: { force?: boolean }) {
        const force = !!opts?.force

        if (!force && meLoadedOnce.value && me.value) {
            return me.value
        }

        if (inflight) return inflight

        loadingMe.value = true
        meError.value = null

        inflight = (async () => {
            try {
                const envelope = await userApi.me()
                const data = envelope?.data ?? null

                // 여기에서 data shape 검증이 필요하면 최소한만
                me.value = data
                meLoadedOnce.value = true
                return me.value
            } catch (err) {
                // 토큰 만료/401 등은 호출측에서 fallback 하게 두는 게 실무에서 흔함
                me.value = null
                meLoadedOnce.value = true
                meError.value = err
                return null
            } finally {
                loadingMe.value = false
                inflight = null
            }
        })()

        return inflight
    }

    function clearMe() {
        me.value = null
        meLoadedOnce.value = false
        meError.value = null
        loadingMe.value = false
        inflight = null
    }

    return {
        me,
        loadingMe,
        meLoadedOnce,
        meError,
        isAuthed,
        fetchMe,
        clearMe,
    }
})