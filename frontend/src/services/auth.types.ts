export type StatusDto = {
  id: number
  role: string
  emailVerified: boolean
  emaileEnrolled: boolean
}

export type TokenDto = {
  accessToken: string
  tokenType: 'bearer' | string
  // user_id?: number
}

export type ChangePasswordQuery = {
  currentPassword: string
  newPassword: string
}

export type ResetPasswordQuery = {
  token: string
  newPassword: string
}

export type VerifyTokenQuery = {
  token: string
}

export type ChangeEmailQuery = {
  newEmail: string
}

export type LoginQuery = {
  email: string
  password: string
}

export type RegisterQuery = {
  email: string
  nickname: string
  password: string

  // 약관 동의
  agreeService: boolean
  agreePrivacy: boolean
  agreeMarketing: boolean
}

export enum OAuthCode {
  KAKAO = 'KAKAO',
}
