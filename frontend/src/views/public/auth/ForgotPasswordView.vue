<template>
  <CenterCardShell>
    <div class="auth-head">
      <div class="auth-head__title">비밀번호 찾기</div>
      <div class="auth-head__desc">
        가입하신 이메일 주소를 입력하시면<br />
        비밀번호 재설정 링크를 보내드립니다.
      </div>
    </div>

    <div v-if="successMessage" class="auth-success">
      {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="auth-error">
      {{ errorMessage }}
    </div>

    <div class="auth-field">
      <div class="auth-label">이메일 주소</div>
      <v-text-field
        v-model="email"
        placeholder="example@email.com"
        variant="outlined"
        density="comfortable"
        hide-details="auto"
        :error="!!fieldErrors.email"
        :error-messages="fieldErrors.email ? [fieldErrors.email] : []"
        @update:model-value="onInputChanged"
        @blur="onBlurValidate"
      />
    </div>

    <v-btn
      block
      color="primary"
      class="auth-btn"
      size="large"
      :loading="sending"
      :disabled="!canSend"
      @click="onSubmit"
    >
      <template v-if="isCooldown">
        {{ cooldownSec }}초 후 다시 시도
      </template>
      <template v-else>
        재설정 링크 보내기
      </template>
    </v-btn>

    <div class="auth-footer">
      <button class="auth-link auth-link--muted" @click="goLogin">
        로그인 화면으로 돌아가기
      </button>
    </div>
  </CenterCardShell>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router"
import CenterCardShell from "@/components/CenterCardShell.vue"
import { useAuthStore } from "@/stores/auth.store";
import { useForgotPasswordForm } from "@/composables/auth/useForgotPasswordForm";

const router = useRouter()
const authStore = useAuthStore();
const {
  email,

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
} = useForgotPasswordForm();


async function onSubmit() {
  try {
    await send(async () => {
      await authStore.requestPasswordResetAction({ email: email.value.trim() });
      successMessage.value = "재설정 링크를 전송했습니다. 메일함을 확인해주세요.";
    });
  } catch (err: any) {
    console.error(err);
    const e = err?.response?.data?.error
    if (!e) {
      errorMessage.value = "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
      return
    }

    if (e?.code === "rate_limited" && e?.target === "resend_password_reset") {
      const sec = e?.details?.cooldown_remaining_sec
      if (typeof sec === "number") {
        startCooldown(sec)
        errorMessage.value = "잠시 후 다시 시도해주세요."
        return
      }
    }
    
    errorMessage.value = "요청 처리에 실패했습니다. 다시 시도해주세요.";
  }
}

function goLogin() {
  router.push({ name: "Login" }).catch(() => {})
}
</script>