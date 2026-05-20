import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  StatusDto,
  ChangeEmailQuery,
  LoginQuery,
  RegisterQuery,
  ResetPasswordQuery,
  ChangePasswordQuery,
  VerifyTokenQuery,
} from '@/services/auth.types'
import * as authSevice from '@/services/auth.service'

export const useAuthStore = defineStore('auth', () => {
  const authStatus = ref<StatusDto | null>(null)

  function getStatus(): StatusDto | null {
    return authStatus.value
  }

  function clearStatus() {
    authStatus.value = null
  }

  /*
        Action
    */
  async function reissue(): Promise<StatusDto | null> {
    authStatus.value = await authSevice.reissue()
    return authStatus.value
  }

  async function login(payload: LoginQuery): Promise<StatusDto | null> {
    authStatus.value = await authSevice.login(payload)
    return authStatus.value
  }

  async function register(payload: RegisterQuery): Promise<StatusDto | null> {
    authStatus.value = await authSevice.register(payload)
    return authStatus.value
  }

  // async function verifyEmail(payload: VerifyTokenQuery): Promise<void> {
  //     await authSevice.verifyEmail(payload);
  // }

  async function verifyPasswordReset(payload: VerifyTokenQuery): Promise<void> {
    await authSevice.verifyPasswordReset(payload)
  }

  async function resendEmailVerification(): Promise<void> {
    await authSevice.resendEmailVerification()
  }

  async function requestPasswordReset(payload: { email: string }): Promise<void> {
    await authSevice.requestPasswordReset(payload)
  }

  async function resetPassword(payload: ResetPasswordQuery): Promise<void> {
    await authSevice.resetPassword(payload)
  }

  async function changePassword(payload: ChangePasswordQuery): Promise<void> {
    await authSevice.changePassword(payload)
  }

  async function changeEmail(payload: ChangeEmailQuery): Promise<StatusDto | null> {
    authStatus.value = await authSevice.changeEmail(payload)
    return authStatus.value
  }

  async function logout(): Promise<void> {
    await authSevice.logout()
  }

  async function deactivate(): Promise<void> {
    await authSevice.deactivate()
  }

  return {
    getStatus,
    clearStatus,

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
  }
})
