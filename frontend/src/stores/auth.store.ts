import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { authApi, type RegisterRequest, type LoginRequest } from "@/api/auth.api"
import { setAccessToken, getAccessToken, clearAccessToken } from "@/api/http"

export const useAuthStore = defineStore("auth", () => {
    // --- state
    const accessToken = ref<string | null>(
        getAccessToken()
    )
    const loggingIn = ref(false)
    const loginError = ref<string | null>(null)
    const registering = ref(false)
    const registerError = ref<string | null>(null)
    // --- getters
    const isAuthenticated = computed(() => !!accessToken.value)

    // --- actions

    async function login(payload: LoginRequest) {
        loginError.value = null
        loggingIn.value = true

        try {
            const env = await authApi.login(payload)
            const token = env?.data?.access_token

            if (!token) {
                loginError.value = "로그인 응답이 올바르지 않습니다."
                return null
            }

            setToken(token)
            return token
        } catch (err) {
            loginError.value = "이메일 또는 비밀번호가 올바르지 않습니다!."
            throw err
        } finally {
            loggingIn.value = false
        }
    }

    async function register(payload: RegisterRequest) {
        registerError.value = null
        registering.value = true
        try {
            const env = await authApi.register(payload)
            const token = env?.data?.access_token

            if (!token) {
                registerError.value = "회원가입 응답이 올바르지 않습니다."
                return null
            }
            setToken(token)
            return token
        } catch (err) {
            registerError.value = "회원가입에 실패했습니다. 다시 시도해주세요.";
            throw err
        } finally {
            registering.value = false
        }
    }

    // ✅ 서버 로그아웃 시도 + 로컬 토큰 정리 (서버 실패해도 로컬은 정리)
    async function logout() {
        try {
            await authApi.logout()
        } catch {
            // ignore
        } finally {
            clearToken()
        }
    }

    function clearToken() {
        accessToken.value = null
        clearAccessToken()
    }

    function setToken(token: string) {
        accessToken.value = token
        setAccessToken(token)
    }

    return {
        accessToken,
        isAuthenticated,

        loggingIn,
        loginError,
        login,

        registering,
        registerError,
        register,

        logout,

        setToken,
        clearToken,
    }
})