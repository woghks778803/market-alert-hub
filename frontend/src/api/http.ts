import axios, { type AxiosError, type AxiosInstance } from "axios"
import type { Envelope } from "@/api/types"


const ACCESS_TOKEN_KEY = "access_token"

function resolveBaseURL() {
    const base = import.meta.env.VITE_API_BASE_URL
    return typeof base === "string" && base.trim() ? base : ""
}

export const http: AxiosInstance = axios.create({
    baseURL: resolveBaseURL(),
    timeout: 15_000,
    withCredentials: true, // 쿠키 전송 허용 
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

/* -------------------------
   Refresh 
-------------------------- */

let isRefreshing = false
let pendingQueue: Array<(token: string | null) => void> = []

function processQueue(token: string | null) {
    pendingQueue.forEach((cb) => cb(token))
    pendingQueue = []
}

async function refreshAccessToken(): Promise<string> {
    const { data } = await axios.post(
        `${resolveBaseURL()}/auth/refresh-token`,
        {},
        { withCredentials: true }
    )

    const newToken = data?.data?.access_token
    if (!newToken) throw new Error("invalid_refresh_response")

    localStorage.setItem(ACCESS_TOKEN_KEY, newToken)
    return newToken
}

// --- Response: keep minimal (no auto-redirect yet) ---
http.interceptors.response.use(
    (res) => res,
    async (err: AxiosError) => {
        const axiosError = err as AxiosError<Envelope<unknown>>
        const apiError = axiosError.response?.data?.error
        const originalRequest: any = err.config
        const status = err.response?.status


        console.log("status:", status)

        if (status !== 401 || originalRequest._retry) {
            return Promise.reject(err)
        }

        if (
            apiError?.code !== "unauthorized" &&
            apiError?.target !== "token"
        ) {
            return Promise.reject(err)
        }

        if (
            originalRequest.url?.includes("/auth/login") ||
            originalRequest.url?.includes("/auth/refresh-token")
        ) {
            return Promise.reject(err)
        }

        originalRequest._retry = true

        if (isRefreshing) {
            // 이미 refresh 중이면 큐에 대기
            return new Promise((resolve, reject) => {
                pendingQueue.push((token) => {
                    if (!token) {
                        reject(err)
                        return
                    }

                    originalRequest.headers = originalRequest.headers ?? {}
                    originalRequest.headers.Authorization = `Bearer ${token}`
                    resolve(http(originalRequest))
                })
            })
        }

        try {
            isRefreshing = true
            const newToken = await refreshAccessToken()

            processQueue(newToken)

            originalRequest.headers = originalRequest.headers ?? {}
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return http(originalRequest)

        } catch (refreshError) {
            processQueue(null)

            // refresh 실패 → 로그인 페이지로 보내는건 router에서 처리
            return Promise.reject(refreshError)
        } finally {
            isRefreshing = false
        }
    }
)
