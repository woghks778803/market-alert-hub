<template>
  <CenterCardShell>
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
        :loading="submitting"
        :disabled="!canSubmit"
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
  </CenterCardShell>
</template>

<script setup lang="ts">
import CenterCardShell from "@/components/CenterCardShell.vue"
import { useRoute, useRouter } from "vue-router";
import { authApi } from "@/api/auth.api";
import { setAccessToken } from "@/api/http";
import { useLoginForm } from "@/composables/auth/useLoginForm";
import { isTokenExpired, isEmailVerifiedFromToken } from "@/utils/jwt"

const router = useRouter();
const route = useRoute();

const { email, password, showPassword, submitting, errorMessage, fieldErrors, canSubmit, validate, submit } = useLoginForm();

function onInputChanged() {
  errorMessage.value = null;
}

function onBlurValidate() {
  validate();
}

function getNextPath(): string | null {
  const next = route.query.next;
  return typeof next === "string" && next.trim() ? next : null;
}

async function onSubmit() {
  errorMessage.value = null;
  console.log("LoginView onSubmit", { email: email.value, password: password.value ? "****" : "" });

  await submit(async () => {
    try {
      const env = await authApi.login({
        email: email.value,
        password: password.value,
      });

      const token = env?.data?.access_token;
      if (!token) {
        errorMessage.value = "로그인 응답이 올바르지 않습니다.";
        return;
      }
      
      setAccessToken(token);

      if (isTokenExpired(token)) {
        errorMessage.value = "세션이 만료되었습니다. 다시 로그인해주세요.";
        return;
      }
      
      const next = getNextPath();
      if (!isEmailVerifiedFromToken(token)) {
        await router.push({
          name: "VerifyEmailSent",
          query: { email: email.value, ...(next ? { next } : {}) },
        }).catch(() => {});
        return;
      }

      if (next) {
        await router.push(next).catch(() => {});
      } else {
        await router.push({ name: "Home" }).catch(() => {});
      }
    } catch (err: any) {
      console.error("Login error:", err);
      errorMessage.value = "이메일 또는 비밀번호가 올바르지 않습니다.";
    }
  });
}

function goSignup() {
  router.push({ name: "Signup" }).catch(() => {})
}

function goForgotPassword() {
  router.push({ name: "ForgotPassword" }).catch(() => {})
}

function onKakaoLogin() {
  console.log("kakao login")
}
</script>

