<template>
  <AppCenterCard center>
    <div class="verify-title">인증 메일을 보냈어요</div>

    <div class="verify-desc">
      <div class="verify-email">{{ userStore.me?.email }}</div>
      <div>인증 링크를 전송했습니다</div>
      <div>메일함에서 링크를 눌러 가입을 완료하세요</div>
      <div class="verify-hint">메일이 안 보이면 스팸함을 확인해주세요</div>
    </div>

    <div
      v-if="successMessage"
      class="auth-success"
    >
      {{ successMessage }}
    </div>
    <div
      v-if="errorMessage"
      class="auth-error"
    >
      {{ errorMessage }}
    </div>

    <v-btn
      class="verify-btn"
      block
      size="large"
      variant="outlined"
      color="primary"
      :loading="loading"
      :disabled="!isReady || isCooldown"
      @click="onSubmit"
    >
      <template v-if="isCooldown"> {{ cooldownSec }}초 후 다시 시도 </template>
      <template v-else> 인증 메일 다시 보내기 </template>
    </v-btn>

    <button
      class="auth-link verify-login"
      type="button"
      @click="goLogin"
    >
      다른 계정으로 로그인
    </button>
  </AppCenterCard>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import AppCenterCard from '@/components/common/AppCenterCard.vue'
import { useRouter } from 'vue-router'
import { useCooldown } from '@/composables/common/useCooldown'
import { useUserStore } from '@/stores/user.store'
import { useAuthStore } from '@/stores/auth.store'
import { useAuthFlow } from '@/composables/auth/useAuthFlow'
import { useVerifyEmailSent } from '@/composables/auth/useVerifyEmailSent'
import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { getVerifyEmailSentError } from '@/composables/error/authError.message'

const router = useRouter()
const userStore = useUserStore()
const authStore = useAuthStore()
const { successMessage, errorMessage, resetMessages } = useVerifyEmailSent()
const { run, loading, isReady } = useAsyncAction()
const { logout } = useAuthFlow()

const { cooldownSec, isCooldown, startCooldown } = useCooldown()

onMounted(async () => {
  try {
    await run(async () => {
      await userStore.fetchMe()
    })
  } catch {
    userStore.clearMe()
  }
})

async function onSubmit() {
  if (isCooldown.value || !isReady.value) return

  resetMessages()
  try {
    await run(async () => {
      await authStore.resendEmailVerification()
      successMessage.value = '인증 메일이 전송되었습니다. 메일함을 확인해주세요.'
    })
  } catch (err) {
    const result = getVerifyEmailSentError(err)

    if (result.kind === 'cooldown') {
      startCooldown(result.cooldownSec)
      errorMessage.value = result.message
      return
    }

    if (result.kind === 'logout') {
      await logout()
      await router.push({ name: 'Login' }).catch(() => {})
      return
    }

    errorMessage.value = result.message
  }
}

async function goLogin() {
  await logout()
  router.push({ name: 'Login' }).catch(() => {})
}
</script>
