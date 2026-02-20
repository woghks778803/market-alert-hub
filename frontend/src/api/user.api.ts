import { http } from "./http"
import type { Envelope } from "./types"

export type userInfo = {
    id: number
    email: string
    nickname: string
    created_at: string
    last_login_at: string | null
}

export const userApi = {
    // GET /user/me
    async me() {
        const { data } = await http.get<Envelope<userInfo>>("/user/me")
        return data
    },

}