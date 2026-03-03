<template>
  <AuthFormCard
    title="인증 메일 등록하기"
    :successMessage="successMessage"
    :errorMessage="errorMessage"
    :loading="sending"
    :disabled="!canSend"
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
      <template v-if="isCooldown">
        {{ cooldownSec }}초 후 다시 시도
      </template>
      <template v-else>
        재설정 링크 보내기
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
import { useEmailActionForm } from "@/composables/auth/useEmailActionForm";
import { mapCommonError } from "@/api/error/errorMapper"
import { mapEmailVerifyError } from "./emailVerifyErrorMapper"

const router = useRouter()
const authStore = useAuthStore();
const {
  fields,

  fieldErrors,
  errorMessage,
  successMessage,
  
  sending,
  canSend,
  send,

  isCooldown,
  cooldownSec,
  startCooldown,
  onInputChanged,
  onBlurValidate,
} = useEmailActionForm();


async function onSubmit() {
  try {
    await send(async () => {
      // await authStore.requestPasswordResetAction({ email: email.value.trim() });
      successMessage.value = "재설정 링크를 전송했습니다. 메일함을 확인해주세요.";
    });
  } catch (err: any) {
    console.error(err);
    const apiError = err?.response?.data?.error

    const r = mapEmailVerifyError(apiError)
    if(r){
      if (r.kind === "cooldown") {
        startCooldown(r.cooldownSec)
      }
      errorMessage.value = r.message
    }

    const commonMessage = mapCommonError(apiError)
    if (commonMessage) {
      errorMessage.value = commonMessage
      return
    }
  }
}

function goLogin() {
  router.push({ name: "Login" }).catch(() => {})
}
</script>