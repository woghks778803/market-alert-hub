import axios, { type AxiosError, type AxiosInstance } from "axios"
import type { Envelope } from "@/api/types"


const ACCESS_TOKEN_KEY = "access_token"

function resolveBaseURL() {
    const base = import.meta.env.VITE_API_BASE_URL
    return typeof base === "string" && base.trim() ? base : ""
}

export const http: AxiosInstance = axios.create({
    // baseURL: resolveBaseURL(),
    baseURL: "/api",
    timeout: 15_000,
    withCredentials: true, // 쿠키 전송 허용 
    paramsSerializer: {
        indexes: null,
        // 기본: exchange_codes[]=BINANCE&exchange_codes[]=UPBIT (PHP 스타일)
        // 변경: exchange_codes=BINANCE&exchange_codes=UPBIT (FastAPI 호환)
    },
    headers: {
        "Content-Type": "application/json",
    },
})

// --- Request: attach Authorization token ---
http.interceptors.request.use((config) => {
    return config
})

/* -------------------------
   Refresh 
-------------------------- */

let isRefreshing = false
let pendingQueue: Array<(error: unknown) => void> = []

function processQueue(error: unknown) {
    pendingQueue.forEach((cb) => cb(error))
    pendingQueue = []
}

async function refreshAccessToken(): Promise<string> {
    try {
        const { data } = await axios.post(
            `${resolveBaseURL()}/auth/reissue`,
            {},
            { withCredentials: true }
        )

        return data?.data
    } catch (err: any) {
        throw err
    }
}

// --- Response: keep minimal (no auto-redirect yet) ---
http.interceptors.response.use(
    (res) => res,
    async (err: AxiosError) => {
        const axiosError = err as AxiosError<Envelope<unknown>>
        const apiError = axiosError.response?.data?.error
        const originalRequest: any = err.config
        const status = err.response?.status

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
            originalRequest.url?.includes("/auth/reissue")
        ) {
            return Promise.reject(err)
        }

        originalRequest._retry = true

        if (isRefreshing) {
            // 이미 refresh 중이면 큐에 대기
            return new Promise((resolve, reject) => {
                pendingQueue.push((error) => {
                    if (error) {
                        return reject(err)
                    }

                    resolve(http(originalRequest))
                })
            })
        }

        try {
            isRefreshing = true
            await refreshAccessToken()
            processQueue(null)

            return http(originalRequest)
        } catch (refreshError) {
            processQueue(refreshError as Error)

            // refresh 실패 → 로그인 페이지로 보내는건 router에서 처리
            return Promise.reject(refreshError)
        } finally {
            isRefreshing = false
        }
    }
)
