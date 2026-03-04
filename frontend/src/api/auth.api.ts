import { http } from "./http"
import type { Envelope } from "./types"

export type ResetPasswordRequest = {
    token: string,
    new_password: string,
}

export type VerifyTokenRequest = {
    token: string
}

export type ChangeEmailRequest = {
    new_email: string
}

export type OauthStartRequest = {
    provider: string;
    agree_service: boolean;
    agree_privacy: boolean;
    agree_marketing: boolean;
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
    // POST /auth/reissue
    async reissue() {
        const { data } = await http.post<Envelope<TokenOut>>("/auth/reissue");
        return data;
    },

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
    async verifyEmail(payload: VerifyTokenRequest) {
        const { data } = await http.post<Envelope<SimpleOk>>("/auth/verify-email", payload);
        return data;
    },

    // POST /auth/change-email
    async changeEmail(payload: ChangeEmailRequest) {
        const { data } = await http.post<Envelope<TokenOut>>("/auth/change-email", payload);
        return data;
    },

    // POST /auth/request-password-reset
    async requestPasswordReset(payload: { email: string }) {
        const { data } = await http.post<Envelope<SimpleOk>>("/auth/request-password-reset", payload);
        return data;
    },

    // POST /auth/change-password
    async resetPassword(payload: ResetPasswordRequest) {
        const { data } = await http.post<Envelope<SimpleOk>>("/auth/change-password", payload);
        return data;
    },

    // POST /auth/verify-password-reset
    async verifyPasswordReset(payload: VerifyTokenRequest) {
        const { data } = await http.post<Envelope<SimpleOk>>("/auth/verify-password-reset", payload);
        return data;
    },

    // GET /auth/oauth/callback
    async oauthCallback(code: string, state: string) {
        const { data } = await http.get<Envelope<TokenOut>>(
            "/auth/oauth/callback",
            {
                params: { code, state, provider: "kakao" }
            }
        )
        return data
    }

}
