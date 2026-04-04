export type UserDto = {
    id: number
    email: string
    nickname: string
    createdAt: string
    lastLoginAt: string | null
    isMarketing: boolean
    isQuietHours: boolean
    providerCode: string | null
    providerDisplayName: string | null
}

export type ChangeUserSettingQuery = {
    isMarketing?: boolean
    isQuietHours?: boolean
}