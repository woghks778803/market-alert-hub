<template>
  <AuthFormCard
    title="비밀번호 찾기"
    :success-message="successMessage"
    :error-message="errorMessage"
    :loading="loading"
    :disabled="!canSend || !isReady"
    @submit="onSubmit"
  >
    <template #description>
      가입하신 이메일 주소를 입력하시면<br />
      비밀번호 재설정 링크를 보내드립니다.
    </template>

    <v-text-field
      v-model="fields.email"
      placeholder="example@email.com"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      :error="!!fieldErrors.email"
      :error-messages="fieldErrors.email ? [fieldErrors.email] : []"
      @update:model-value="onInputChanged"
      @blur="onBlurValidate"
    />

    <template #button>
      <template v-if="isCooldown"> {{ cooldownSec }}초 후 다시 시도 </template>
      <template v-else> 재설정 메일 보내기 </template>
    </template>

    <template #footer>
      <button
        class="auth-link auth-link--muted"
        @click="goLogin"
      >
        로그인 화면으로 돌아가기
      </button>
    </template>
  </AuthFormCard>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import AuthFormCard from '@/components/auth/AuthFormCard.vue'
import { useAuthStore } from '@/stores/auth.store'
import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { useEmailActionForm } from '@/composables/auth/useEmailActionForm'
import { getForgotPasswordError } from '@/composables/error/authError.message'

const router = useRouter()
const authStore = useAuthStore()
const {
  fields,

  fieldErrors,
  errorMessage,
  successMessage,

  canSend,
  handleSubmit,

  isCooldown,
  cooldownSec,
  startCooldown,
  onInputChanged,
  onBlurValidate,
} = useEmailActionForm()
const { run, loading, isReady } = useAsyncAction()

async function onSubmit() {
  try {
    await handleSubmit(async () => {
      await run(async () => {
        await authStore.requestPasswordReset({ email: fields.value.email })
        successMessage.value = '재설정 링크를 전송했습니다. 메일함을 확인해주세요.'
      })
    })
  } catch (err) {

    const result = getForgotPasswordError(err)
    if (result?.kind === 'cooldown') {
      startCooldown(result.cooldownSec)
      errorMessage.value = result.message
      return
    }

    errorMessage.value = result.message
  }
}

function goLogin() {
  router.push({ name: 'Login' }).catch(() => {})
}
</script>
