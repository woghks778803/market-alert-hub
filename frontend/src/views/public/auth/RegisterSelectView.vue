<template>
  <AppCenterCard center>
    <div class="auth-title auth-title--lg">회원가입</div>
    <div class="auth-subtitle">가입 방법을 선택하세요</div>

    <v-btn
      class="auth-btn"
      block
      size="large"
      color="primary"
      variant="flat"
      prepend-icon="mdi-email-outline"
      @click="goTerms('email')"
    >
      이메일로 가입
    </v-btn>

    <div class="auth-divider auth-divider--tight">
      <v-divider />
      <span class="auth-divider__text">또는</span>
      <v-divider />
    </div>

    <v-btn
      class="auth-btn auth-btn--kakao"
      block
      size="large"
      variant="flat"
      :ripple="false"
      @click="goTerms('kakao')"
    >
      <v-icon class="mr-2" icon="mdi-message" />
      카카오로 가입
    </v-btn>

    <div class="auth-bottom">
      <span class="auth-bottom__text">이미 계정이 있나요?</span>
      <button class="auth-link" type="button" @click="goLogin">로그인</button>
    </div>
  </AppCenterCard>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router"
import AppCenterCard from "@/components/common/AppCenterCard.vue"

const router = useRouter()

function goTerms(source: string) {
  router.push({ name: "SignupTerms", query: { source } }).catch(() => {})
}

function goLogin() {
  router.push({ name: "Login" }).catch(() => {})
}
</script>
