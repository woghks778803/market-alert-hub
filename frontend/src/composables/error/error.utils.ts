import type { ApiError } from '@/api/types'

export type ApiErrorMapper<T> = (error: ApiError | null) => T | null
export type ApiErrorFallbackMapper<T> = (error: ApiError | null) => T

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isApiError(value: unknown): value is ApiError {
  if (!isRecord(value)) return false

  const target = value.target

  return (
    typeof value.code === 'string' &&
    typeof value.message === 'string' &&
    'target' in value &&
    (typeof target === 'string' || target === null)
  )
}

export function extractApiError(err: unknown): ApiError | null {
  if (!err) return null

  // service에서 throw env.error 한 경우
  if (isApiError(err)) {
    return err
  }

  if (!isRecord(err)) return null

  // axios error 형태: err.response.data.error
  const response = err.response
  if (isRecord(response)) {
    const data = response.data

    if (isRecord(data)) {
      const error = data.error

      if (isApiError(error)) {
        return error
      }
    }
  }

  // 혹시 err 자체가 { error: ApiError } 형태인 경우
  const error = err.error
  if (isApiError(error)) {
    return error
  }

  return null
}

export function resolveApiError<T>(
  err: unknown,
  mapper: ApiErrorMapper<T>,
  fallbackMapper: ApiErrorFallbackMapper<T>,
): T {
  const apiError = extractApiError(err)

  return mapper(apiError) ?? fallbackMapper(apiError)
}