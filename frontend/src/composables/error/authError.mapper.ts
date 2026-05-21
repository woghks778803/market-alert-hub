import type { ApiError } from '@/api/types'

export type EmailVerifyErrorResult =
  | { kind: 'cooldown'; cooldownSec: number; message: string }
  | { kind: 'message'; message: string }

export type ForgotPasswordErrorResult =
  | { kind: 'cooldown'; cooldownSec: number; message: string }
  | { kind: 'message'; message: string }

export type VerifyEmailSentErrorResult =
  | { kind: 'cooldown'; cooldownSec: number; message: string }
  | { kind: 'logout'; message?: string }
  | { kind: 'message'; message: string }

export type ResetPasswordErrorResult =
  | { kind: 'fail_mode'; message?: string }
  | { kind: 'message'; message: string }

export type OauthErrorQuery = {
  code: string
  target: string
}

function pickCooldownSec(details: Record<string, unknown> | null | undefined): number | null {
  const d = details
  const sec = d?.cooldown_remaining_sec
  return typeof sec === 'number' && Number.isFinite(sec) && sec >= 0 ? sec : null
}

export function mapEmailVerifyError(error?: ApiError | null): EmailVerifyErrorResult | null {
  if (!error) {
    return { kind: 'message', message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.' }
  }

  // 이미 사용중인 이메일
  if (error.code === 'conflict' && error.target === 'new_email') {
    return { kind: 'message', message: '이미 사용 중인 이메일입니다.' }
  }

  // 입력값 검증 실패
  if (error.code === 'validation_error') {
    return { kind: 'message', message: '입력 정보를 다시 확인해주세요.' }
  }

  // 쿨다운
  if (error.code === 'rate_limited' && error.target === 'resend_email_verification') {
    const sec = pickCooldownSec(error.details)
    if (sec !== null) {
      return { kind: 'cooldown', cooldownSec: sec, message: '잠시 후 다시 시도해주세요.' }
    }
    return { kind: 'message', message: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.' }
  }

  // 그 외
  return null
  // return { kind: "message", message: "요청 처리에 실패했습니다. 다시 시도해주세요." }
}

export function mapForgotPasswordError(error?: ApiError | null): ForgotPasswordErrorResult | null {
  if (!error) {
    return { kind: 'message', message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.' }
  }

  if (error.code === 'forbidden' && error.target === 'oauth_account') {
    return { kind: 'message', message: '소셜 로그인 이용자는 비밀번호를 변경할 수 없습니다.' }
  }

  if (error.code === 'forbidden' && error.target === 'status.suspended') {
    return { kind: 'message', message: '이용이 제한된 계정입니다.' }
  } else if (error.code === 'forbidden' && error.target === 'status.deleted') {
    return { kind: 'message', message: '탈퇴 처리중인 계정입니다.' }
  }

  // 쿨다운
  if (error.code === 'rate_limited' && error.target === 'resend_password_reset') {
    const sec = pickCooldownSec(error.details)
    if (sec !== null) {
      return { kind: 'cooldown', cooldownSec: sec, message: '잠시 후 다시 시도해주세요.' }
    }
    return { kind: 'message', message: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.' }
  }

  // 그 외
  return null
  // return { kind: "message", message: "요청 처리에 실패했습니다. 다시 시도해주세요." }
}

export function mapChangePasswordError(error: ApiError | null): string | null {
  if (!error) {
    return '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
  }

  if ((error.code === 'forbidden' || error.code === 'unauthorized') && error.target === 'user') {
    return '현재 비밀번호가 올바르지 않습니다.'
  }

  if (error.code === 'rate_limited') {
    return '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'
  }

  return null
}

export function mapLoginError(error?: ApiError | null): string | null {
  if (!error) {
    return '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
  }

  if (error.code === 'validation_error' && error.target === 'terms') {
    return '약관 동의가 필요합니다.'
  }

  if (error.code === 'forbidden' && error.target === 'oauth_account') {
    return '이미 사용중인 이메일입니다. 소셜 로그인을 사용해주세요.'
  }

  if (error.code === 'forbidden' && error.target === 'role') {
    return '권한이 없습니다.'
  }

  if (error.code === 'forbidden' && error.target === 'status.suspended') {
    return '이용이 제한된 계정입니다.'
  } else if (error.code === 'forbidden' && error.target === 'status.deleted') {
    return '탈퇴 처리중인 계정입니다.'
  }

  if (error.code === 'unauthorized' && error.target === 'email') {
    return '이메일 정보에 문제가 있습니다. 고객센터에 문의해주세요.'
  }

  // 401 기본 로그인 실패
  if (error.code === 'unauthorized') {
    return '로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.'
  }

  return null
}

export function mapOauthError(error?: OauthErrorQuery | null): string {
  if (!error) {
    return '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
  }

  const { code, target } = error

  if (code === 'validation_error' && target === 'state') {
    return '로그인 요청이 만료되었습니다. 다시 로그인해주세요.'
  }

  if (code === 'internal_error' && target === 'state') {
    return '로그인 처리 중 문제가 발생했습니다. 다시 시도해주세요.'
  }

  if (code === 'internal_error' && target === 'user') {
    return '로그인 처리 중 오류가 발생했습니다.'
  }

  if (code === 'forbidden' && target === 'status.suspended') {
    return '이용이 제한된 계정입니다.'
  } else if (code === 'forbidden' && target === 'status.deleted') {
    return '탈퇴 처리중인 계정입니다.'
  }

  if (code === 'not_found' && target === 'oauth') {
    return '지원하지 않는 로그인 제공자입니다.'
  }

  // oauth callback error (카카오)
  if (code === 'access_denied' && target === 'oauth') {
    return '로그인이 취소되었습니다.'
  }

  if (code === 'invalid_request' && target === 'oauth') {
    return '잘못된 로그인 요청입니다.'
  }

  if (code === 'server_error' && target === 'oauth') {
    return '카카오 로그인 처리 중 오류가 발생했습니다.'
  }

  // 그 외
  return '로그인 처리에 실패했습니다. 다시 시도해주세요.'
}

export function mapRegisterError(error?: ApiError | null): string | null {
  if (!error) {
    return '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
  }

  // 이미 사용중인 이메일
  if (error.code === 'conflict' && error.target === 'email') {
    return '이미 사용 중인 이메일입니다.'
  }

  // 값 검증 실패
  if (error.code === 'forbidden' && error.target === 'status.suspended') {
    return '이용이 제한된 계정입니다.'
  } else if (error.code === 'forbidden' && error.target === 'status.deleted') {
    return '탈퇴 처리중인 계정입니다.'
  }

  // 요청 과다
  if (error.code === 'rate_limited') {
    return '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'
  }

  return null
  // return "회원가입에 실패했습니다. 입력 정보를 확인해주세요."
}

export function mapResetPasswordError(error?: ApiError | null): ResetPasswordErrorResult | null {
  if (!error) {
    return { kind: 'message', message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.' }
  }

  // 토큰 문제(만료/위조/이미 사용됨 등) → 화면을 fail 모드로
  if (error.code === 'unauthorized' && error.target === 'token') {
    return { kind: 'fail_mode' }
  }

  // 검증 실패(입력값 문제)
  if (error.code === 'validation_error') {
    return { kind: 'message', message: '입력값을 확인해주세요.' }
  }

  // 기본
  return null
}

export function mapVerifyEmailSentError(
  error?: ApiError | null
): VerifyEmailSentErrorResult | null {
  if (!error) {
    return { kind: 'message', message: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.' }
  }

  // 재발송 쿨다운
  if (error.code === 'rate_limited' && error.target === 'resend_email_verification') {
    const sec = pickCooldownSec(error.details)
    if (sec !== null) {
      return { kind: 'cooldown', cooldownSec: sec, message: '잠시 후 다시 시도해주세요.' }
    }
    return { kind: 'message', message: '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.' }
  }

  // 이미 인증됨(또는 중복 요청)
  if (error.code === 'conflict' && error.target === 'email') {
    return { kind: 'message', message: '이미 인증된 이메일입니다.' }
  }

  // 이메일 정보 문제
  if (error.code === 'unauthorized' && error.target === 'email') {
    return { kind: 'message', message: '이메일 정보에 문제가 있습니다. 고객센터에 문의해주세요.' }
  }

  // 로그인 상태/토큰 문제 → 로그아웃 처리 필요
  if (error.code === 'unauthorized' && (error.target === 'user' || error.target === 'token')) {
    return { kind: 'logout' }
  }

  return null
}