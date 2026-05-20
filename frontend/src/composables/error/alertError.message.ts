import { mapCommonError } from '@/composables/error/error.mapper'
import { mapChangeAlertStatusError, mapChangeAlertError, mapCreateAlertError } from '@/composables/error/alertError.mapper'
import { resolveApiError } from '@/composables/error/error.utils'

export function getChangeAlertStatusError(err: unknown): string {
  return resolveApiError(err, mapChangeAlertStatusError, mapCommonError)
}

export function getChangeAlertError(err: unknown): string {
  return resolveApiError(err, mapChangeAlertError, mapCommonError)
}

export function getCreateAlertError(err: unknown): string {
  return resolveApiError(err, mapCreateAlertError, mapCommonError)
}