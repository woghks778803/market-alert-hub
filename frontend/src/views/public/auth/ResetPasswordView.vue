<template>
  <AppCenterCard center>
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
          :loading="loading"
          :disabled="!canSubmit || !isReady"
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
    
  </AppCenterCard>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue"
import AppCenterCard from "@/components/common/AppCenterCard.vue"
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth.store";
import { useResetPasswordForm } from "@/composables/auth/useResetPasswordForm";
import { useAsyncAction } from "@/composables/common/useAsyncAction";
import { useMode } from "@/composables/common/useMode"
import { mapCommonError } from "@/composables/error/error.mapper"
import { mapResetPasswordError } from "@/composables/error/resetPasswordError.mapper"

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
  
  canSubmit,
  handleSubmit,

  onInputChanged,
  onBlurValidate,
} = useResetPasswordForm();
const { run, loading, isReady } = useAsyncAction()

const viewMode = computed(() => mode.value)

function readToken(): string {
  const q = route.query?.token
  return typeof q === "string" ? q : ""
}

onMounted(async () => {
  setMode("default")
  try {
    const token = readToken()
    if (!token) {
      throw new Error("invalid_verify_token")
    }
    await authStore.verifyPasswordReset({ token })

    console.log("verify success")
  } catch (err: any) {
    setMode("fail")
  }
});

async function onSubmit() {
  try {
    const token = readToken()
    if (!token) {
      throw new Error("invalid_verify_token")
    }

    await handleSubmit(async () => {
      await run(async () => {
        await authStore.resetPassword({
          token: token,
          newPassword: password.value,
        });
      });
    })

    setMode("success")
  } catch (err: any) {
    if (err?.message === "invalid_verify_token") {
      setMode("fail")
      return
    }

    const apiError = err?.response?.data?.error

    const r = mapResetPasswordError(apiError)
    if(r){
      if (r.kind === "fail_mode") {
        setMode("fail")
        return
      }

      errorMessage.value = r.message
      return
    }
    
    const commonMessage = mapCommonError(apiError)
    if (commonMessage) {
      errorMessage.value = commonMessage
      return
    }
  }
}

function goLogin() {
  router.push({ name: "Login" }).catch(() => {});
}

function goPasswordForgot() {
  router.push({ name: "ForgotPassword" }).catch(() => {});
}
</script>

