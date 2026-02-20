<template>
  <CenterCardShell center>
    <div class="verify-title">인증 메일을 보냈어요</div>

    <div class="verify-desc">
      <div class="verify-email">{{ email }}</div>
      <div>인증 링크를 전송했습니다</div>
      <div>메일함에서 링크를 눌러 가입을 완료하세요</div>
      <div class="verify-hint">메일이 안 보이면 스팸함을 확인해주세요</div>
    </div>

    <v-btn
      class="verify-btn"
      block
      size="large"
      variant="outlined"
      color="primary"
      :loading="sending"
      :disabled="!canResend"
      @click="onResend"
    >
      인증메일 다시 보내기
    </v-btn>

    <button class="auth-link verify-login" type="button" @click="goLogin">
      다른 계정으로 로그인
    </button>
  </CenterCardShell>
</template>
<script setup lang="ts">
import CenterCardShell from "@/components/CenterCardShell.vue"
import { onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth.store"
import { clearAccessToken } from "@/api/http"
import { useVerifyEmailSent } from "@/composables/auth/useVerifyEmailSent"

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const {
  sending,
  canResend,
  resend,
  email,
  loadMe,
} = useVerifyEmailSent(route)

onMounted(() => {
  loadMe()
})

async function onResend() {
  await resend(async () => {
    console.log("resend verify email:", email.value)
    // TODO: 실제 resend API 붙이기
  })
}

async function goLogin() {
  await authStore.logout()
  router.push({ name: "Login" }).catch(() => {})
}
</script>