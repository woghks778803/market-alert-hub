import type { ResetPasswordRequest, ChangePasswordRequest, VerifyTokenRequest, ChangeEmailRequest, LoginRequest, RegisterRequest, StatusInfo, TokenInfo } from "@/api/auth.api"
import type { StatusDto, TokenDto, ResetPasswordQuery, ChangePasswordQuery, VerifyTokenQuery, ChangeEmailQuery, LoginQuery, RegisterQuery } from "@/services/auth.types"

export function toStatusDto(data: StatusInfo): StatusDto {
    return {
        id: data.id,
        role: data.role,
        emailVerified: data.email_verified,
        emaileEnrolled: data.email_enrolled,
    }
}

export function toTokenDto(data: TokenInfo): TokenDto {
    return {
        accessToken: data.access_token,
        tokenType: data.token_type,
    }
}

export function toChangePasswordRequest(q: ChangePasswordQuery): ChangePasswordRequest {
    return {
        current_password: q.currentPassword,
        new_password: q.newPassword
    }
}

export function toResetPasswordRequest(q: ResetPasswordQuery): ResetPasswordRequest {
    return {
        token: q.token,
        new_password: q.newPassword,
    }
}

export function toVerifyTokenRequest(q: VerifyTokenQuery): VerifyTokenRequest {
    return {
        token: q.token
    }
}

export function toChangeEmailRequest(q: ChangeEmailQuery): ChangeEmailRequest {
    return {
        new_email: q.newEmail
    }
}

export function toLoginRequest(q: LoginQuery): LoginRequest {
    return {
        email: q.email,
        password: q.password,
    }
}

export function toRegisterRequest(q: RegisterQuery): RegisterRequest {
    return {
        email: q.email,
        nickname: q.nickname,
        password: q.password,
        agree_service: q.agreeService,
        agree_privacy: q.agreePrivacy,
        agree_marketing: q.agreeMarketing,
    }
}