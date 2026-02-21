import axios, { type AxiosError, type AxiosInstance } from "axios"

const ACCESS_TOKEN_KEY = "access_token"

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
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
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
