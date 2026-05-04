import type { UserInfo, ChangeUserSettingRequest } from '@/api/user.api'
import type { UserDto, ChangeUserSettingQuery } from '@/services/user.types'

export function toUserDto(data: UserInfo): UserDto {
  return {
    id: data.id,
    email: data.email,
    nickname: data.nickname,
    createdAt: data.created_at,
    lastLoginAt: data.last_login_at,
    isMarketing: data.is_marketing,
    isQuietHours: data.is_quiet_hours,
    providerCode: data.provider_code,
    providerDisplayName: data.provider_display_name,
  }
}

export function toChangeEmailRequest(q: ChangeUserSettingQuery): ChangeUserSettingRequest {
  return {
    is_marketing: q.isMarketing,
    is_quiet_hours: q.isQuietHours,
  }
}
