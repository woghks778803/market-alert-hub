import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { LoginRequest, RegisterRequest, VerifyTokenRequest, ResetPasswordRequest } from "@/api/auth.api";
import {
    login as loginService,
    register as registerService,
    resendEmailVerification as resendEmailVerificationService,
    requestPasswordReset as requestPasswordResetService,
    logout as logoutService,
    verifyEmail as verifyEmailService,
    verifyPasswordReset as verifyPasswordResetService,
    resetPassword as resetPasswordService,
} from "@/services/auth.service";

const LS_KEY = "access_token";

export const useAuthStore = defineStore("auth", () => {
    const accessToken = ref<string | null>(localStorage.getItem(LS_KEY));

    const isAuthenticated = computed(() => !!accessToken.value);

    function getToken(): string | null {
        return accessToken.value;
    }

    function setToken(token: string) {
        accessToken.value = token;
        localStorage.setItem(LS_KEY, token);
    }

    function clearToken() {
        accessToken.value = null;
        localStorage.removeItem(LS_KEY);
    }

    async function loginAction(payload: LoginRequest): Promise<string> {
        const token = await loginService(payload);
        setToken(token);
        return token;
    }

    async function registerAction(payload: RegisterRequest): Promise<string | null> {
        const token = await registerService(payload);
        if (token) setToken(token);
        return token;
    }

    async function verifyEmailAction(payload: VerifyTokenRequest): Promise<void> {
        await verifyEmailService(payload);
    }

    async function verifyPasswordResetAction(payload: VerifyTokenRequest): Promise<void> {
        await verifyPasswordResetService(payload);
    }

    async function resendEmailVerificationAction(): Promise<void> {
        await resendEmailVerificationService();
    }

    async function requestPasswordResetAction(payload: { email: string }): Promise<void> {
        await requestPasswordResetService(payload);
    }

    async function resetPasswordAction(payload: ResetPasswordRequest): Promise<void> {
        await resetPasswordService(payload);
    }

    async function logoutAction(): Promise<void> {
        try {
            await logoutService();
        } catch (_) {
            // 무조건 무시
        } finally {
            console.log("Clearing token on logout");
            clearToken();
        }
    }

    return {
        accessToken,
        isAuthenticated,

        getToken,
        setToken,
        clearToken,

        loginAction,
        registerAction,
        resendEmailVerificationAction,
        requestPasswordResetAction,
        resetPasswordAction,
        logoutAction,
        verifyEmailAction,
        verifyPasswordResetAction,
    };
});