import { authApi, type RegisterRequest, type LoginRequest, type VerifyEmailRequest, type ResetPasswordRequest } from "@/api/auth.api"

export async function verifyEmail(payload: VerifyEmailRequest) {
    // 실패하면 그대로 throw → View에서 메시지 처리
    const env = await authApi.verifyEmail(payload)
    const result = env?.success
    if (!result) {
        throw new Error("verify_email_failed")
    }
}

export async function resendEmailVerification() {
    await authApi.resendEmailVerification()
}

export async function requestPasswordReset(payload: { email: string }) {
    await authApi.requestPasswordReset(payload)
}

export async function resetPassword(payload: ResetPasswordRequest) {
    await authApi.resetPassword(payload)
}

export async function logout() {
    await authApi.logout()
}

export async function login(payload: LoginRequest) {
    const env = await authApi.login(payload)
    const token = env?.data?.access_token
    if (!token) throw new Error("invalid_login_response")
    return token
}

export async function register(payload: RegisterRequest) {
    const env = await authApi.register(payload)
    const token = env?.data?.access_token
    if (!token) throw new Error("invalid_register_response")
    return token
}



