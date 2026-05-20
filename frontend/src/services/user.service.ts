import { userApi } from '@/api/user.api'
import { toUserDto, toChangeEmailRequest } from '@/services/user.mapper'
import type { UserDto, ChangeUserSettingQuery } from '@/services/user.types'

export async function getMe(): Promise<UserDto> {
  const env = await userApi.getMe()

  if (!env.success || !env.data) {
    throw env.error ?? new Error('invalid_me_response')
  }

  return toUserDto(env.data)
}

export async function changeMeSetting(payload: ChangeUserSettingQuery): Promise<void> {
  const env = await userApi.changeMeSetting(toChangeEmailRequest(payload))

  if (!env.success) {
    throw env.error ?? new Error('change_password_failed')
  }
}
