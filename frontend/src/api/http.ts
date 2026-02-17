import axios, { type AxiosError, type AxiosInstance } from "axios"

/**
 * 토큰 저장 키: 기존 코드(getAccessToken)와 맞춤
 */
const ACCESS_TOKEN_KEY = "access_token"

export function getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setAccessToken(token: string) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function clearAccessToken() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
}

function resolveBaseURL() {
    const base = import.meta.env.VITE_API_BASE_URL
    return typeof base === "string" && base.trim() ? base : ""
}

export const http: AxiosInstance = axios.create({
    baseURL: resolveBaseURL(),
    timeout: 15_000,
    headers: {
        "Content-Type": "application/json",
    },
})

// --- Request: attach Authorization token ---
http.interceptors.request.use((config) => {
    const token = getAccessToken()
    if (token) {
        config.headers = config.headers ?? {}
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// --- Response: keep minimal (no auto-redirect yet) ---
http.interceptors.response.use(
    (res) => res,
    (err: AxiosError) => {
        // 여기서는 최소로 에러를 그대로 던짐 (UI에서 처리)
        return Promise.reject(err)
    }
)
