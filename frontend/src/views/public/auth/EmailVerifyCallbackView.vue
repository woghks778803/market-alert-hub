<template>
  <CenterCardShell center>

    <div class="verify-cb-title">이메일 인증</div>

    <!-- 처리중 -->
    <template v-if="viewMode === 'default'">
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

      <button class="auth-link verify-cb-link" type="button" @click="goLogin">
        다시 로그인하기
      </button>
    </template>
  </CenterCardShell>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import CenterCardShell from "@/components/CenterCardShell.vue"
import { useMode } from "@/composables/common/useMode"
import { useAuthStore } from "@/stores/auth.store";

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore();

const { mode, setMode } = useMode()

const viewMode = computed(() => mode.value)

async function goLogin() {
  await authStore.logoutAction()
  router.replace({ name: "Login" })
}

onMounted(async () => {
  const code = String(route.query.code ?? "")
  const target = String(route.query.target ?? "")
  setMode("default")

  if (code === "success") {
    setMode("success")
    return
  }

  // 실패 케이스
  if (
    code === "not_found" ||
    code === "validation_error" ||
    code === "expired" ||
    code === "invalid_status" ||
    code === "user_not_found" ||
    code === "internal_error"
  ) {
    setMode("fail")
    return
  }
  // try {
  //   const token = readToken()
  //   if (!token) {
  //     throw new Error("invalid_verify_token")
  //   }
  //   await authStore.verifyEmailAction({ token })

  //   setMode("success")
  // } catch (err: any) {
  //   setMode("fail")
  // } finally {
  //   await authStore.logoutAction()
  // }

  // runVerify(async () => {
  //   const token = readToken()
  //   if (!token) {
  //     throw new Error("invalid_verify_token")
  //   }
  //   await verifyEmail({ token })
  // }).then(async (res) => {
  //   setMode("success")
  // })
  // .catch(async (e) => {
  //   console.error("EmailVerifyCallbackView error", e)
  //   setMode("fail")
  // }).finally(async () => {
  //   await logout()
  // })
})
</script>
