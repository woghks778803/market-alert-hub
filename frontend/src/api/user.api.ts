import { http } from "./http"
import type { Envelope } from "./types"

export type UserInfo = {
    id: number
    email: string
    nickname: string
    created_at: string
    last_login_at: string | null
}

export const userApi = {
    // GET /user/me
    async getMe() {
        const { data } = await http.get<Envelope<UserInfo>>("/user/me")
        return data
    },

}