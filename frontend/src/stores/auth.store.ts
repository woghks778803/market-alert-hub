import { defineStore } from "pinia"
import { ref, computed } from "vue"

const LS_KEY = "access_token"

export const useAuthStore = defineStore("auth", () => {
    // --- state
    const accessToken = ref<string | null>(
        localStorage.getItem(LS_KEY)
    )

    const isAuthenticated = computed(() => !!accessToken.value)


    function getToken() {
        return accessToken.value
    }

    function setToken(token: string) {
        accessToken.value = token
        localStorage.setItem(LS_KEY, token)
    }

    function clearToken() {
        accessToken.value = null
        localStorage.removeItem(LS_KEY)
    }

    return {
        accessToken,
        isAuthenticated,

        getToken,
        setToken,
        clearToken,
    }
})