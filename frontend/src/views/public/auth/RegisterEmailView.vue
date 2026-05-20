<template>
  <AppCenterCard>
    <div class="auth-head">
      <div class="auth-head__title">이메일로 가입</div>
      <div class="auth-head__desc">정보를 입력하면 인증 이메일을 보내드립니다</div>
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
          autocomplete="email"
          inputmode="email"
          hide-details="auto"
          :error="!!fieldErrors.email"
          :error-messages="fieldErrors.email ? [fieldErrors.email] : []"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
        />
      </div>

      <div class="auth-field">
        <div class="auth-label">닉네임</div>
        <v-text-field
          v-model="nickname"
          placeholder="닉네임을 입력하세요"
          variant="outlined"
          density="comfortable"
          autocomplete="nickname"
          hide-details="auto"
          :error="!!fieldErrors.nickname"
          :error-messages="fieldErrors.nickname ? [fieldErrors.nickname] : []"
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
          autocomplete="new-password"
          :error="!!fieldErrors.password"
          :error-messages="fieldErrors.password ? [fieldErrors.password] : []"
          @click:append-inner="showPassword = !showPassword"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
        />
      </div>

      <div class="auth-field">
        <div class="auth-label">비밀번호 확인</div>
        <v-text-field
          v-model="passwordConfirm"
          :type="showPasswordConfirm ? 'text' : 'password'"
          placeholder="비밀번호를 다시 입력하세요"
          variant="outlined"
          density="comfortable"
          hide-details="auto"
          :append-inner-icon="showPasswordConfirm ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
          autocomplete="new-password"
          :error="!!fieldErrors.passwordConfirm"
          :error-messages="fieldErrors.passwordConfirm ? [fieldErrors.passwordConfirm] : []"
          @click:append-inner="showPasswordConfirm = !showPasswordConfirm"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
        />
      </div>

      <v-btn
        class="auth-btn auth-btn--muted"
        type="submit"
        block
        size="large"
        variant="flat"
        color="primary"
        :disabled="!canSubmit || !canProceed || !isReady"
        :loading="loading"
      >
        인증메일 보내기
      </v-btn>
    </v-form>

    <div class="auth-bottom auth-bottom--center">
      <span class="auth-bottom__text">이미 계정이 있나요?</span>
      <button
        class="auth-link"
        type="button"
        @click="goLogin"
      >
        로그인
      </button>
    </div>
  </AppCenterCard>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppCenterCard from '@/components/common/AppCenterCard.vue'
import { useRegisterEmailForm } from '@/composables/auth/useRegisterEmailForm'
import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { useTermsConsent } from '@/composables/auth/useTermsConsent'
import { useAuthStore } from '@/stores/auth.store'
import { getRegisterError } from '@/composables/error/authError.message'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const { canProceed, consentPayload, resetTermsConsent } = useTermsConsent()
const { run, loading, isReady } = useAsyncAction()
const {
  email,
  nickname,
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
} = useRegisterEmailForm()

onMounted(() => {
  if (!canProceed.value) {
    router
      .replace({
        name: 'SignupTerms',
        query: {
          source: 'email',
          next: route.fullPath,
        },
      })
      .catch(() => {})
  }
})

async function onSubmit() {
  if (!canProceed.value) {
    errorMessage.value = '약관 동의가 필요합니다.'
    await router
      .push({ name: 'SignupTerms', query: { source: 'email', next: '/auth/signup/email' } })
      .catch(() => {})
    return
  }

  try {
    await handleSubmit(async () => {
      await run(async () => {
        const payload = {
          email: email.value,
          nickname: nickname.value,
          password: password.value,
          ...consentPayload.value,
        }
        await authStore.register(payload)
      })

      resetTermsConsent()
      await router
        .push({
          name: 'VerifyEmailSent',
          query: { email: email.value },
        })
        .catch(() => {})
    })
  } catch (err) {
    const result = getRegisterError(err)
    if(result){
      errorMessage.value = result
      return
    }
  }
}

function goLogin() {
  resetTermsConsent()
  router.push({ name: 'Login' }).catch(() => {})
}
</script>
