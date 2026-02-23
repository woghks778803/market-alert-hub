import { http } from "./http"
import type { Envelope } from "./types"

export type VerifyEmailRequest = {
    token: string
}

export type LoginRequest = {
    email: string
    password: string
}

export type RegisterRequest = {
    email: string;
    nickname: string;
    password: string;

    // 약관 동의
    agree_service: boolean;
    agree_privacy: boolean;
    agree_marketing: boolean;
}

export type TokenOut = {
    access_token: string
    token_type: "bearer" | string
    // user_id?: number
}

export type SimpleOk = {
    ok: boolean
}

export const authApi = {
    // POST /auth/login
    async login(payload: LoginRequest) {
        const { data } = await http.post<Envelope<TokenOut>>("/auth/login", payload)
        return data
    },

    // POST /auth/logout
    async logout() {
        const { data } = await http.post<Envelope<SimpleOk>>("/auth/logout")
        return data
    },

    // POST /auth/register 
    async register(payload: RegisterRequest) {
        const { data } = await http.post<Envelope<TokenOut>>("/auth/register", payload);
        return data;
    },

    // POST /auth/resend-email-verification
    async resendEmailVerification() {
        const { data } = await http.post<Envelope<SimpleOk>>("/auth/resend-email-verification");
        return data;
    },

    // POST /auth/verify-email 
    async verifyEmail(payload: VerifyEmailRequest) {
        const { data } = await http.post<Envelope<SimpleOk>>("/auth/verify-email", payload);
        return data;
    },
}
