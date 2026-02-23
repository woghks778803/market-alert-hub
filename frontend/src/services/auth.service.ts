import { useAuthStore } from "@/stores/auth.store"
import { authApi, type RegisterRequest, type LoginRequest, type VerifyEmailRequest } from "@/api/auth.api"

export async function verifyEmail(payload: VerifyEmailRequest) {
    // 실패하면 그대로 throw → View에서 메시지 처리
    const env = await authApi.verifyEmail(payload)
    const result = env?.success
    if (!result) {
        throw new Error("verify_email_failed")
    }
}

export async function resendEmailVerification() {
    // 실패하면 그대로 throw → View에서 메시지 처리
    await authApi.resendEmailVerification()
}

export async function logout() {
    const authStore = useAuthStore()

    try {
        await authApi.logout()
    } catch (err: any) {
        // 서버 실패해도 로컬은 정리
    } finally {
        authStore.clearToken()
    }
}

export async function login(payload: LoginRequest) {
    const authStore = useAuthStore()

    const env = await authApi.login(payload)
    const token = env?.data?.access_token
    if (!token) throw new Error("invalid_login_response")

    authStore.setToken(token)
    return token
}

export async function register(payload: RegisterRequest) {
    const authStore = useAuthStore()

    const env = await authApi.register(payload)
    const token = env?.data?.access_token
    if (!token) throw new Error("invalid_register_response")

    authStore.setToken(token)
    return token
}



