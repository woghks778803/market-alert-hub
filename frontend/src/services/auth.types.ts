export type TokenDto = {
    accessToken: string
    tokenType: "bearer" | string
    // user_id?: number
}

export type ChangePasswordQuery = {
    currentPassword: string,
    newPassword: string,
}

export type ResetPasswordQuery = {
    token: string,
    newPassword: string,
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
    email: string;
    nickname: string;
    password: string;

    // 약관 동의
    agreeService: boolean;
    agreePrivacy: boolean;
    agreeMarketing: boolean;
}

export const LS_KEY = "access_token";

export enum OAuthCode {
    KAKAO = "KAKAO",
}

