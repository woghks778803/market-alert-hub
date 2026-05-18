<template>
  <AppCenterCard>
    <div class="auth-logo-wrap">
      <img
        :src="Logo"
        class="auth-logo"
      />
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
          autocomplete="current-password"
          :error="!!fieldErrors.password"
          :error-messages="fieldErrors.password ? [fieldErrors.password] : []"
          @click:append-inner="showPassword = !showPassword"
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
        :loading="emailAction.loading.value"
        :disabled="
          !kakaoAction.isReady.value || 
          !emailAction.isReady.value || 
          !canSubmit
        "
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
      :loading="kakaoAction.loading.value"
      :disabled="
        !kakaoAction.isReady.value || 
        !emailAction.isReady.value
      "
      @click="onKakaoLogin"
    >
      <v-icon
        class="mr-2"
        icon="mdi-message"
      />
      카카오로 로그인
    </v-btn>

    <div class="auth-links">
      <button
        class="auth-link"
        type="button"
        @click="goSignup"
      >
        회원가입
      </button>
      ·
      <button
        class="auth-link"
        type="button"
        @click="goSupport"
      >
        고객지원
      </button>
    </div>

    <div class="auth-footer">
      <button
        class="auth-link auth-link--muted"
        type="button"
        @click="goForgotPassword"
      >
        비밀번호를 잊으셨나요?
      </button>
    </div>
  </AppCenterCard>
</template>

<script setup lang="ts">
import Logo from '@/assets/logo/alertping-logo.svg'
import AppCenterCard from '@/components/common/AppCenterCard.vue'
import { useRoute, useRouter } from 'vue-router'
import { useLoginForm } from '@/composables/auth/useLoginForm'
import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { useAppSettings } from '@/composables/common/useAppSettings'
import { getLoginError } from '@/composables/error/authError.message'
import { useAuthStore } from '@/stores/auth.store'
import { OAuthCode } from '@/services/auth.types'

let kakaoloadTime: ReturnType<typeof setTimeout> | null = null
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
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
} = useLoginForm()
const emailAction = useAsyncAction()
const kakaoAction = useAsyncAction()
const { applyLogin } = useAppSettings()

function getNextPath(): string | null {
  const next = route.query.next
  return typeof next === 'string' && next.trim() ? next : null
}

async function onSubmit() {
  try {
    await handleSubmit(async () => {
      await emailAction.run(async () => {
        const authStatus = await authStore.login({
          email: email.value,
          password: password.value,
        })

        applyLogin()

        const next = getNextPath()
        if (!authStatus?.emailVerified) {
          await router
            .push({
              name: 'VerifyEmailSent',
              query: { email: email.value, ...(next ? { next } : {}) },
            })
            .catch(() => {})
          return
        }

        if (next) await router.push(next).catch(() => {})
        else await router.push({ name: 'Home' }).catch(() => {})
      })
    })
  } catch (err) {
    const result = getLoginError(err)
    if(result){
      errorMessage.value = result
      return
    }
  }
}

function goSignup() {
  router.push({ name: 'Signup' }).catch(() => {})
}

function goSupport() {
  router.push({ name: 'Support' }).catch(() => {})
}

function goForgotPassword() {
  router.push({ name: 'ForgotPassword' }).catch(() => {})
}

function onKakaoLogin() {
  if (!kakaoAction.isReady.value || !emailAction.isReady.value) return

  kakaoAction.loading.value = true

  if (kakaoloadTime)
      clearTimeout(kakaoloadTime)

  kakaoloadTime = window.setTimeout(() => {
    kakaoAction.loading.value = false
    kakaoloadTime = null
  }, 3000)
  
  const params = new URLSearchParams({
    provider: OAuthCode.KAKAO,
  })

  window.location.href = `${import.meta.env.VITE_API_BASE_URL}/auth/oauth/start?${params.toString()}`

  return
}
</script>
