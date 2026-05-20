import { authApi } from '@/api/auth.api'

import {
  toStatusDto,
  toResetPasswordRequest,
  toChangePasswordRequest,
  toVerifyTokenRequest,
  toChangeEmailRequest,
  toLoginRequest,
  toRegisterRequest,
} from '@/services/auth.mapper'
import type {
  StatusDto,
  ChangeEmailQuery,
  LoginQuery,
  RegisterQuery,
  ResetPasswordQuery,
  ChangePasswordQuery,
  VerifyTokenQuery,
} from '@/services/auth.types'

// TODO: ApiError → DomainError 변환 필요

// export async function verifyEmail(payload: VerifyTokenQuery): Promise<void> {
//     const env = await authApi.verifyEmail(toVerifyTokenRequest(payload))

//     if (!env.success) {
//         throw env.error ?? new Error("verify_email_failed")
//     }
// }

/** verify password reset */
export async function verifyPasswordReset(payload: VerifyTokenQuery): Promise<void> {
  const env = await authApi.verifyPasswordReset(toVerifyTokenRequest(payload))

  if (!env.success) {
    throw env.error ?? new Error('verify_password_reset_failed')
  }
}

/** resend email */
export async function resendEmailVerification(): Promise<void> {
  const env = await authApi.resendEmailVerification()

  if (!env.success) {
    throw env.error ?? new Error('resend_email_failed')
  }
}

/** request password reset */
export async function requestPasswordReset(payload: { email: string }): Promise<void> {
  const env = await authApi.requestPasswordReset(payload)

  if (!env.success) {
    throw env.error ?? new Error('request_password_reset_failed')
  }
}

/** reset password */
export async function resetPassword(payload: ResetPasswordQuery): Promise<void> {
  const env = await authApi.resetPassword(toResetPasswordRequest(payload))

  if (!env.success) {
    throw env.error ?? new Error('reset_password_failed')
  }
}

/** reset password */
export async function changePassword(payload: ChangePasswordQuery): Promise<void> {
  const env = await authApi.changePassword(toChangePasswordRequest(payload))

  if (!env.success) {
    throw env.error ?? new Error('change_password_failed')
  }
}

/** logout */
export async function logout(): Promise<void> {
  const env = await authApi.logout()

  if (!env.success) {
    throw env.error ?? new Error('logout_failed')
  }
}

/** deactivate */
export async function deactivate(): Promise<void> {
  const env = await authApi.deactivate()

  if (!env.success) {
    throw env.error ?? new Error('deactivate_failed')
  }
}

/** change email */
export async function changeEmail(payload: ChangeEmailQuery): Promise<StatusDto> {
  const env = await authApi.changeEmail(toChangeEmailRequest(payload))

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_change_email_response')
  }

  return toStatusDto(env.data)
}

/**  */
export async function checkStatus(): Promise<StatusDto> {
  const env = await authApi.checkStatus()

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_status_response')
  }

  return toStatusDto(env.data)
}

/** reissue */
export async function reissue(): Promise<StatusDto> {
  const env = await authApi.reissue()

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_reissue_response')
  }

  return toStatusDto(env.data)
}

/** login */
export async function login(payload: LoginQuery): Promise<StatusDto> {
  const env = await authApi.login(toLoginRequest(payload))

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_login_response')
  }

  return toStatusDto(env.data)
}

/** register */
export async function register(payload: RegisterQuery): Promise<StatusDto> {
  const env = await authApi.register(toRegisterRequest(payload))

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_register_response')
  }

  return toStatusDto(env.data)
}
