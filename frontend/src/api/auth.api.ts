import { http } from './http'
import type { Envelope, SimpleOk } from './types'

export type StatusInfo = {
  id: number
  role: string
  email_verified: boolean
  email_enrolled: boolean
}

export type TokenInfo = {
  access_token: string
  token_type: 'bearer' | string
  // user_id?: number
}

export type ChangePasswordRequest = {
  current_password: string
  new_password: string
}

export type ResetPasswordRequest = {
  token: string
  new_password: string
}

export type VerifyTokenRequest = {
  token: string
}

export type ChangeEmailRequest = {
  new_email: string
}

export type LoginRequest = {
  email: string
  password: string
}

export type RegisterRequest = {
  email: string
  nickname: string
  password: string

  // 약관 동의
  agree_service: boolean
  agree_privacy: boolean
  agree_marketing: boolean
}

export type OauthCallbackRequest = {
  code?: string
  state?: string
  provider?: string
}

export const authApi = {
  // POST /auth/reissue
  async reissue() {
    const { data } = await http.post<Envelope<StatusInfo>>('/auth/reissue')
    return data
  },

  // POST /auth/login
  async login(payload: LoginRequest) {
    const { data } = await http.post<Envelope<StatusInfo>>('/auth/login', payload)
    return data
  },

  // POST /auth/logout
  async logout() {
    const { data } = await http.post<Envelope<SimpleOk>>('/auth/logout')
    return data
  },

  // DELETE /auth/deactivate
  async deactivate() {
    const { data } = await http.delete<Envelope<SimpleOk>>('/auth/deactivate')
    return data
  },

  // POST /auth/register
  async register(payload: RegisterRequest) {
    const { data } = await http.post<Envelope<StatusInfo>>('/auth/register', payload)
    return data
  },

  // POST /auth/resend-email-verification
  async resendEmailVerification() {
    const { data } = await http.post<Envelope<SimpleOk>>('/auth/resend-email-verification')
    return data
  },

  // GET /auth/verify-email
  // async verifyEmail(params: VerifyTokenRequest) {
  //     const { data } = await http.get<Envelope<SimpleOk>>("/auth/verify-email", { params });
  //     return data;
  // },

  // POST /auth/change-email
  async changeEmail(payload: ChangeEmailRequest) {
    const { data } = await http.post<Envelope<StatusInfo>>('/auth/change-email', payload)
    return data
  },

  // POST /auth/request-password-reset
  async requestPasswordReset(payload: { email: string }) {
    const { data } = await http.post<Envelope<SimpleOk>>('/auth/request-password-reset', payload)
    return data
  },

  // POST /auth/reset-password
  async resetPassword(payload: ResetPasswordRequest) {
    const { data } = await http.post<Envelope<SimpleOk>>('/auth/reset-password', payload)
    return data
  },

  // POST /auth/change-password
  async changePassword(payload: ChangePasswordRequest) {
    const { data } = await http.post<Envelope<SimpleOk>>('/auth/change-password', payload)
    return data
  },

  // POST /auth/verify-password-reset
  async verifyPasswordReset(payload: VerifyTokenRequest) {
    const { data } = await http.post<Envelope<SimpleOk>>('/auth/verify-password-reset', payload)
    return data
  },

  // GET /auth/status
  async checkStatus() {
    const { data } = await http.get<Envelope<StatusInfo>>('/auth/status')
    return data
  },
}
