<template>
  <CenterCardShell center>
    <div class="verify-title">인증 메일을 보냈어요</div>

    <div class="verify-desc">
      <div class="verify-email">{{ userStore.me?.email }}</div>
      <div>인증 링크를 전송했습니다</div>
      <div>메일함에서 링크를 눌러 가입을 완료하세요</div>
      <div class="verify-hint">메일이 안 보이면 스팸함을 확인해주세요</div>
    </div>

    <div v-if="successMessage" class="auth-success">
      {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="auth-error">
      {{ errorMessage }}
    </div>

    <v-btn
      class="verify-btn"
      block
      size="large"
      variant="outlined"
      color="primary"
      :loading="sending"
      :disabled="!canResend || isCooldown"
      @click="onSubmit"
    >
      <template v-if="isCooldown">
        {{ cooldownSec }}초 후 다시 시도
      </template>
      <template v-else>
        인증메일 다시 보내기
      </template>
    </v-btn>

    <button class="auth-link verify-login" type="button" @click="goLogin">
      다른 계정으로 로그인
    </button>
  </CenterCardShell>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import CenterCardShell from "@/components/CenterCardShell.vue"
import { useRouter, useRoute } from "vue-router"
import { useCooldown } from "@/composables/common/useCooldown"
import { useUserStore } from "@/stores/user.store";
import { useAuthStore } from "@/stores/auth.store";
import { useVerifyEmailSent } from "@/composables/auth/useVerifyEmailSent";
import { mapCommonError } from "@/api/error/errorMapper"
import { mapVerifyEmailSentError } from "./verifyEmailSentErrorMapper"

const router = useRouter()
const route = useRoute()
const userStore = useUserStore();
const authStore = useAuthStore();
const { successMessage, errorMessage, canResend, send, sending } = useVerifyEmailSent(route);

const { cooldownSec, isCooldown, startCooldown } =
  useCooldown();

onMounted(() => {
  userStore.fetchMe().catch(() => {});
});

async function onSubmit() {
  if (isCooldown.value || !canResend.value) return;

  try {
    await send(async () => {
      await authStore.resendEmailVerificationAction();
      successMessage.value = "인증 메일이 전송되었습니다. 메일함을 확인해주세요.";
    });
  } catch (err: any) {
    const apiError = err?.response?.data?.error

    const r = mapVerifyEmailSentError(apiError)
    if(r){
      if (r.kind === "cooldown") {
        startCooldown(r.cooldownSec)
        errorMessage.value = r.message
        return
      }

      if (r.kind === "logout") {
        await authStore.logoutAction()
        await router.push({ name: "Login" }).catch(() => {})
        return
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

async function goLogin() {
  await authStore.logoutAction()
  router.push({ name: "Login" }).catch(() => {})
}
</script>