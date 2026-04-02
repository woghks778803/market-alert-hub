<template>
  <AuthFormCard
    title="이메일 인증"
    :successMessage="successMessage"
    :errorMessage="errorMessage"
    :loading="loading"
    :disabled="!canSend || !isReady"
    @submit="onSubmit"
  >
    <template #description>
      가입에 사용할 이메일 주소를 입력하세요.<br />
      입력한 이메일로 인증 링크를 보내드립니다.
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
      <template v-if="isCooldown">
        {{ cooldownSec }}초 후 다시 시도
      </template>
      <template v-else>
        인증 메일 보내기
      </template>
    </template>

    <template #footer>
      <button class="auth-link auth-link--muted" @click="goLogin">
        로그인 화면으로 돌아가기
      </button>
    </template>
  </AuthFormCard>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router"
import AuthFormCard from "@/components/auth/AuthFormCard.vue"
import { useAuthStore } from "@/stores/auth.store";
import { useAsyncAction } from "@/composables/common/useAsyncAction";
import { useEmailActionForm } from "@/composables/auth/useEmailActionForm";
import { mapCommonError } from "@/composables/error/error.mapper"
import { mapEmailVerifyError } from "@/composables/error/emailVerifyError.mapper"

const router = useRouter()
const authStore = useAuthStore();
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
} = useEmailActionForm();
const { run, loading, isReady } = useAsyncAction()

async function onSubmit() {
  try {
    await handleSubmit(async () => {
      await run(async () => {
        await authStore.changeEmail({ newEmail: fields.value.email });
        router.push({ name: "VerifyEmailSent" }).catch(() => {})
      });
    })
  } catch (err: any) {
    
    const apiError = err?.response?.data?.error

    const r = mapEmailVerifyError(apiError)
    console.log("err", r)
    if(r){
      if (r.kind === "cooldown") {
        startCooldown(r.cooldownSec)
      }
      errorMessage.value = r.message
      return
    }

    const commonMessage = mapCommonError(apiError)
    if (commonMessage) {
      errorMessage.value = commonMessage
      return
    }
  }
}

async function goLogin() {
  await authStore.logout()
  router.push({ name: "Login" }).catch(() => {})
}
</script>