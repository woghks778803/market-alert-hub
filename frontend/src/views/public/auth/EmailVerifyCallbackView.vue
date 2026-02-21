<template>
  <CenterCardShell center>
    <!-- (개발용) 상태 토글: 필요 없으면 삭제 -->
    <div class="verify-dev-toggle">
      <v-btn-toggle v-model="devMode" density="compact" variant="outlined" divided>
        <v-btn value="processing">처리중</v-btn>
        <v-btn value="success">성공</v-btn>
        <v-btn value="fail">실패</v-btn>
      </v-btn-toggle>
    </div>

    <div class="verify-cb-title">이메일 인증</div>

    <!-- 처리중 -->
    <template v-if="viewMode === 'processing'">
      <div class="verify-cb-icon verify-cb-icon--processing">
        <v-progress-circular indeterminate size="56" width="5" color="primary" />
      </div>
      <div class="verify-cb-sub">인증 확인 중...</div>
    </template>

    <!-- 성공 -->
    <template v-else-if="viewMode === 'success'">
      <div class="verify-cb-icon verify-cb-icon--success">
        <v-icon icon="mdi-check" size="30" />
      </div>

      <div class="verify-cb-msg">
        <div class="verify-cb-msg__title">가입이 완료되었습니다</div>
        <div class="verify-cb-msg__desc">이제 로그인할 수 있어요</div>
      </div>

      <v-btn
        class="verify-cb-btn"
        block
        size="large"
        color="primary"
        variant="flat"
        @click="goLogin"
      >
        로그인하기
      </v-btn>
    </template>

    <!-- 실패 -->
    <template v-else>
      <div class="verify-cb-icon verify-cb-icon--fail">
        <v-icon icon="mdi-close" size="30" />
      </div>

      <div class="verify-cb-msg">
        <div class="verify-cb-msg__title">
          인증 링크가 만료되었거나<br />
          유효하지 않습니다
        </div>
        <div class="verify-cb-msg__desc">인증메일을 다시 받아주세요</div>
      </div>

      <v-btn
        class="verify-cb-btn"
        block
        size="large"
        color="primary"
        variant="flat"
        @click="goResend"
      >
        인증메일 다시 보내기
      </v-btn>

      <button class="auth-link verify-cb-link" type="button" @click="goLogin">
        로그인으로
      </button>
    </template>
  </CenterCardShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import CenterCardShell from "@/components/CenterCardShell.vue"
import { type EmailVerifyMode, useEmailVerifyCallback } from "@/composables/auth/useEmailVerifyCallback"

const router = useRouter()
const { mode, runVerify } = useEmailVerifyCallback()

// 개발용 토글(실서비스에서는 제거 가능)
const devMode = ref<EmailVerifyMode>("processing")

// 현재는 devMode 우선으로 보이게(퍼블리싱 확인용)
const viewMode = computed<EmailVerifyMode>(() => devMode.value || mode.value)

onMounted(async () => {
  // TODO: API 붙이기 전까지는 더미 처리
  await runVerify(async () => {
    await new Promise((r) => setTimeout(r, 900))
    return "success"
  })
})

function goLogin() {
  router.push({ name: "Login" }).catch(() => {})
}

function goResend() {
  router.push({ name: "VerifyEmailSent" }).catch(() => {})
}
</script>
