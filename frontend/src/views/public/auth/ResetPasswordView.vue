<template>
  <CenterCardShell center>
    <template v-if="viewMode === 'default'">
      <div class="auth-head">
        <div class="auth-head__title">비밀번호 설정</div>
        <div class="auth-head__desc">
          안전한 계정을 위해 기존에 사용하지 않은<br />
          새로운 비밀번호를 입력해주세요.
        </div>
      </div>

      <v-alert
        v-if="errorMessage"
        class="mb-4"
        type="error"
        variant="tonal"
        density="compact"
      >
        {{ errorMessage }}
      </v-alert>

      <v-form ref="formRef" @submit.prevent="onSubmit">
        <v-card class="auth-card__inner" variant="outlined">
          <v-card-text>
            <div class="auth-label">새 비밀번호</div>
            <v-text-field
              v-model="password"
              class="mb-4"
              placeholder="비밀번호를 입력하세요"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              variant="outlined"
              hide-details="auto"
              :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
              @click:append-inner="showPassword = !showPassword"
              :error="!!fieldErrors.password"
              :error-messages="fieldErrors.password ? [fieldErrors.password] : []"
              @update:model-value="onInputChanged"
              @blur="onBlurValidate"
            />
            <!-- <div class="auth-hint">영문, 숫자, 특수문자 포함 8자 이상</div> -->

            <div class="auth-label mt-4">비밀번호 확인</div>
            <v-text-field
              v-model="passwordConfirm"
              placeholder="비밀번호를 다시 입력하세요"
              :type="showPasswordConfirm ? 'text' : 'password'"
              autocomplete="new-password"
              variant="outlined"
              hide-details="auto"
              :append-inner-icon="showPasswordConfirm ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
              @click:append-inner="showPasswordConfirm = !showPasswordConfirm"
              :error="!!fieldErrors.passwordConfirm"
              :error-messages="fieldErrors.passwordConfirm ? [fieldErrors.passwordConfirm] : []"
              @update:model-value="onInputChanged"
              @blur="onBlurValidate"
            />
          </v-card-text>
        </v-card>

        <v-btn
          class="auth-btn mt-4"
          block
          size="large"
          color="primary"
          variant="flat"
          :loading="submitting"
          :disabled="!canSubmit"
          type="submit"
        >
          비밀번호 변경
        </v-btn>
      </v-form>

      <div class="auth-footer">
        <button class="auth-link auth-link--muted" type="button" @click="goLogin">
          로그인 화면으로 돌아가기
        </button>
      </div>
    </template>

    <!-- 성공 -->
    <template v-else-if="viewMode === 'success'">
      <div class="verify-cb-icon verify-cb-icon--success">
        <v-icon icon="mdi-check" size="30" />
      </div>

      <div class="verify-cb-msg">
        <div class="verify-cb-msg__title">비밀번호가 변경되었습니다</div>
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

      <button class="auth-link verify-cb-link" type="button" @click="goPasswordForgot">
        비밀번호 찾기
      </button>
    </template>
    
  </CenterCardShell>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue"
import CenterCardShell from "@/components/CenterCardShell.vue"
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth.store";
import { useResetPasswordForm } from "@/composables/auth/useResetPasswordForm";
import { useMode } from "@/composables/common/useMode"

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const { mode, setMode } = useMode();

const {
  password,
  passwordConfirm,
  showPassword,
  showPasswordConfirm,
  
  fieldErrors,
  errorMessage,
  
  submitting,
  canSubmit,
  submit,

  onInputChanged,
  onBlurValidate,
} = useResetPasswordForm();

const viewMode = computed(() => mode.value)

function readToken(): string {
  const q = route.query?.token
  return typeof q === "string" ? q : ""
}

onMounted(() => {
  setMode("default")
});

async function onSubmit() {
  try {
    const token = readToken()
    if (!token) {
      setMode("fail")
    }

    await submit(async () => {
      await authStore.resetPasswordAction({
        token: token,
        new_password: password.value,
      });
    });

    setMode("success")
  } catch (err: any) {
    errorMessage.value = "비밀번호 변경에 실패했습니다. 다시 시도해주세요."
  }
}

function goLogin() {
  router.push({ name: "Login" }).catch(() => {});
}

function goPasswordForgot() {
  router.push({ name: "ForgotPassword" }).catch(() => {});
}
</script>

