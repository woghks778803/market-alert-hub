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
import { useLoginForm } from "@/composables/auth/useLoginForm";
import { isTokenExpired, isEmailVerifiedFromToken } from "@/utils/jwt"
import { useAuthStore } from "@/stores/auth.store";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const {
  email,
  password,
  showPassword,

  fieldErrors,
  errorMessage,

  submitting,
  canSubmit,
  submit,

  validate,
  onInputChanged,
  onBlurValidate,
} = useLoginForm();



function getNextPath(): string | null {
  const next = route.query.next;
  return typeof next === "string" && next.trim() ? next : null;
}

async function onSubmit() {
  try {
    await submit(async () => {
      const token = await authStore.loginAction({
        email: email.value,
        password: password.value,
      });

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

      if (next) await router.push(next).catch(() => {});
      else await router.push({ name: "Home" }).catch(() => {});
    });
  } catch (err: any) {
    console.error("Login error:", err);
    const e = err?.response?.data?.error;

    if (!e) {
      errorMessage.value = "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
      return
    }
    if (e.code === "forbidden" && e?.target === "role") {
      errorMessage.value = "권한이 없습니다.";
      return;
    }
    if (e.code === "forbidden" && e?.target === "status") {
      errorMessage.value = "계정이 정지되었습니다. 자세한 내용은 고객센터에 문의해주세요.";
      return;
    }
    if (e.code === "unauthorized" && e?.target === "email") {
      errorMessage.value = "이메일 정보에 문제가 있습니다. 고객센터에 문의해주세요.";
      return;
    }

    errorMessage.value = "로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.";
  }
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

