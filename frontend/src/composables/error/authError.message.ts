import type { ApiError } from '@/api/types'
import { mapCommonError } from '@/composables/error/error.mapper'
import {
  mapLoginError,
  mapRegisterError,
  mapOauthError,
  mapEmailVerifyError,
  mapForgotPasswordError,
  mapResetPasswordError,
  mapChangePasswordError,
  mapVerifyEmailSentError,
  type EmailVerifyErrorResult,
  type ForgotPasswordErrorResult,
  type ResetPasswordErrorResult,
  type VerifyEmailSentErrorResult,
  type OauthErrorQuery,
} from '@/composables/error/authError.mapper'
import { resolveApiError } from '@/composables/error/error.utils'

function mapCommonMessageResult(error: ApiError | null): { kind: 'message'; message: string } {
  const message = mapCommonError(error)

  return {
    kind: 'message',
    message,
  }
}

function mapCommonEmailVerifyError(error: ApiError | null): EmailVerifyErrorResult {
  return mapCommonMessageResult(error)
}

function mapCommonForgotPasswordError(error: ApiError | null): ForgotPasswordErrorResult {
  return mapCommonMessageResult(error)
}

function mapCommonResetPasswordError(error: ApiError | null): ResetPasswordErrorResult {
  return mapCommonMessageResult(error)
}

function mapCommonVerifyEmailSentError(error: ApiError | null): VerifyEmailSentErrorResult {
  return mapCommonMessageResult(error)
}

export function getLoginError(err: unknown): string {
  return resolveApiError(err, mapLoginError, mapCommonError)
}

export function getRegisterError(err: unknown): string {
  return resolveApiError(err, mapRegisterError, mapCommonError)
}

export function getChangePasswordError(err: unknown): string {
  return resolveApiError(err, mapChangePasswordError, mapCommonError)
}

export function getEmailVerifyError(err: unknown): EmailVerifyErrorResult {
  return resolveApiError(
    err,
    mapEmailVerifyError,
    mapCommonEmailVerifyError,
  )
}

export function getForgotPasswordError(err: unknown): ForgotPasswordErrorResult {
  return resolveApiError(
    err,
    mapForgotPasswordError,
    mapCommonForgotPasswordError,
  )
}

export function getResetPasswordError(err: unknown): ResetPasswordErrorResult {
  return resolveApiError(
    err,
    mapResetPasswordError,
    mapCommonResetPasswordError,
  )
}

export function getVerifyEmailSentError(err: unknown): VerifyEmailSentErrorResult {
  return resolveApiError(
    err,
    mapVerifyEmailSentError,
    mapCommonVerifyEmailSentError,
  )
}

export function getOauthError(query: OauthErrorQuery): string {
  return mapOauthError(query)
}