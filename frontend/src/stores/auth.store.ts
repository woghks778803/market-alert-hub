import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { TokenDto, ChangeEmailQuery, LoginQuery, RegisterQuery, ResetPasswordQuery, ChangePasswordQuery, VerifyTokenQuery } from "@/services/auth.types"
import { LS_KEY } from "@/services/auth.types"
import * as authSevice from "@/services/auth.service";

import { useUserStore } from "@/stores/user.store";



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


    /*
        Action
    */
    async function reissue() {
        const token = await authSevice.reissue();
        setToken(token.accessToken);
        return token.accessToken;
    }

    async function login(payload: LoginQuery): Promise<string> {
        const token = await authSevice.login(payload);
        setToken(token.accessToken);
        return token.accessToken;
    }

    async function register(payload: RegisterQuery): Promise<string | null> {
        const token = await authSevice.register(payload);
        if (token) setToken(token.accessToken);
        return token.accessToken;
    }

    // async function verifyEmail(payload: VerifyTokenQuery): Promise<void> {
    //     await authSevice.verifyEmail(payload);
    // }

    async function verifyPasswordReset(payload: VerifyTokenQuery): Promise<void> {
        await authSevice.verifyPasswordReset(payload);
    }

    async function resendEmailVerification(): Promise<void> {
        await authSevice.resendEmailVerification();
    }

    async function requestPasswordReset(payload: { email: string }): Promise<void> {
        await authSevice.requestPasswordReset(payload);
    }

    async function resetPassword(payload: ResetPasswordQuery): Promise<void> {
        const userStore = useUserStore()

        await authSevice.resetPassword(payload);

        clearToken();
        userStore.clearMe()
    }

    async function changePassword(payload: ChangePasswordQuery): Promise<void> {
        const userStore = useUserStore()

        await authSevice.changePassword(payload);

        clearToken();
        userStore.clearMe()
    }

    async function changeEmail(payload: ChangeEmailQuery): Promise<string | null> {
        const token = await authSevice.changeEmail(payload);
        setToken(token.accessToken);
        return token.accessToken;
    }

    async function logout(): Promise<void> {
        const userStore = useUserStore()

        try {
            await authSevice.logout();
        } catch (_) {
            // 무조건 무시
        } finally {
            clearToken();
            userStore.clearMe()
        }
    }

    async function deactivate(): Promise<void> {
        const userStore = useUserStore()

        try {
            await authSevice.deactivate();
        } catch (_) {
            // 무조건 무시
        } finally {
            clearToken();
            userStore.clearMe()
        }
    }

    return {
        accessToken,
        isAuthenticated,

        getToken,
        setToken,
        clearToken,

        reissue,
        login,
        register,
        resendEmailVerification,
        requestPasswordReset,
        resetPassword,
        changePassword,
        changeEmail,
        logout,
        deactivate,
        // verifyEmail,
        verifyPasswordReset,
    };
});