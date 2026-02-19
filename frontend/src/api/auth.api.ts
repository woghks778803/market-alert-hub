import { http } from "./http"
import type { Envelope } from "./types"

/**
 * ✅ 백엔드 스펙이 아직 확정이 아니라 "최소 DTO" 형태로만 둠
 * - 필드명은 나중에 백엔드 실제 스펙에 맞춰 수정
 */

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

    // POST /auth/register  (백엔드: status_code=201)
    async register(payload: RegisterRequest) {
        const { data } = await http.post<Envelope<TokenOut>>("/auth/register", payload);
        return data;
    },
}
