<template>
  <AppCenterCard>
    <div class="auth-logo-wrap">
      <img :src="Logo" class="auth-logo" />
    </div>
    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      class="mb-4"
      density="compact"
    >
      {{ errorMessage }}
    </v-alert>
    <v-form @submit.prevent="onSubmit">
      <div class="auth-field">
        <div class="auth-label">이메일</div>
        <v-text-field
          v-model="email"
          placeholder="example@email.com"
          variant="outlined"
          density="comfortable"
          hide-details="auto"
          autocomplete="email"
          inputmode="email"
          :error="!!fieldErrors.email"
          :error-messages="fieldErrors.email ? [fieldErrors.email] : []"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
        />
      </div>

      <div class="auth-field">
        <div class="auth-label">비밀번호</div>
        <v-text-field
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          placeholder="비밀번호를 입력하세요"
          variant="outlined"
          density="comfortable"
          hide-details="auto"
          :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
          @click:append-inner="showPassword = !showPassword"
          autocomplete="current-password"
          :error="!!fieldErrors.password"
          :error-messages="fieldErrors.password ? [fieldErrors.password] : []"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
        />
      </div>

      <v-btn
        class="auth-btn"
        type="submit"
        color="primary"
        variant="flat"
        block
        size="large"
        :loading="loading"
        :disabled="!isReady || !canSubmit"
      >
        로그인
      </v-btn>

    </v-form>

    <div class="auth-divider">
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
      @click="onKakaoLogin"
    >
      <v-icon class="mr-2" icon="mdi-message" />
      카카오로 로그인
    </v-btn>

    <div class="auth-links">
      <button class="auth-link" type="button" @click="goSignup">회원가입</button>
    </div>

    <div class="auth-footer">
      <button class="auth-link auth-link--muted" type="button" @click="goForgotPassword">
        비밀번호를 잊으셨나요?
      </button>
    </div>
  </AppCenterCard>
</template>

<script setup lang="ts">
import Logo from '@/assets/logo/alertping-logo.svg'
import AppCenterCard from "@/components/common/AppCenterCard.vue"
import { useRoute, useRouter } from "vue-router";
import { useLoginForm } from "@/composables/auth/useLoginForm";
import { useAsyncAction } from "@/composables/common/useAsyncAction";
import { isEmailVerifiedFromToken } from "@/utils/jwt"
import { useAuthStore } from "@/stores/auth.store";
import { mapCommonError } from "@/composables/error/error.mapper"
import { mapLoginError } from "@/composables/error/loginError.mapper"
import { OAuthCode } from "@/services/auth.types"

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const {
  email,
  password,
  showPassword,

  fieldErrors,
  errorMessage,

  canSubmit,
  handleSubmit,

  onInputChanged,
  onBlurValidate,
} = useLoginForm();
const { run, loading, isReady } = useAsyncAction()


function getNextPath(): string | null {
  const next = route.query.next;
  return typeof next === "string" && next.trim() ? next : null;
}

async function onSubmit() {
  try {
    await handleSubmit(async () => {
      await run(async () => {
        const token = await authStore.login({
          email: email.value,
          password: password.value,
        });

        const next = getNextPath();
        if (!isEmailVerifiedFromToken(token)) {
          await router.push({
            name: "VerifyEmailSent",
            query: { email: email.value, ...(next ? { next } : {}) },
          }).catch(() => {});
          return;
        }

        if (next) await router.push(next).catch(() => {});
        else await router.push({ name: "Home" }).catch(() => {});
      });
    });
  } catch (err: any) {
    console.error("Login error:", err);
    const apiError = err?.response?.data?.error;

    const r = mapLoginError(apiError)
    if(r){
      errorMessage.value = r
      return 
    }

    const commonMessage = mapCommonError(apiError)
    if (commonMessage) {
      errorMessage.value = commonMessage
      return
    }
  }
}

function goSignup() {
  router.push({ name: "Signup" }).catch(() => {})
}

function goForgotPassword() {
  router.push({ name: "ForgotPassword" }).catch(() => {})
}

function onKakaoLogin() {
  const params = new URLSearchParams({
    provider: OAuthCode.KAKAO,
  })

  window.location.href =
    `${import.meta.env.VITE_API_BASE_URL}/auth/oauth/start?${params.toString()}`
  
  return
}
</script>

