import { http } from './http'
import type { Envelope, SimpleOk } from './types'

export type UserInfo = {
  id: number
  email: string
  nickname: string
  created_at: string
  last_login_at: string | null
  is_marketing: boolean
  is_quiet_hours: boolean
  provider_code: string | null
  provider_display_name: string | null
}

export type ChangeUserSettingRequest = {
  is_marketing?: boolean
  is_quiet_hours?: boolean
}

export const userApi = {
  // GET /users/me
  async getMe() {
    const { data } = await http.get<Envelope<UserInfo>>('/users/me')
    return data
  },

  // PATCH /users/setting
  async changeMeSetting(payload: ChangeUserSettingRequest) {
    const { data } = await http.patch<Envelope<SimpleOk>>('/users/setting', payload)
    return data
  },
}
