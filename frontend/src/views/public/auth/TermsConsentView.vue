<template>
  <AppCenterCard :center="false">
    <div class="auth-head">
      <div class="auth-head__title">서비스 이용을 위해<br />약관에 동의해주세요</div>
      <div class="auth-head__desc">안전한 서비스 이용을 위해 필요한 항목입니다</div>
    </div>

    <v-card
      class="terms-card"
      variant="outlined"
    >
      <div class="terms-row terms-row--all">
        <v-checkbox
          v-model="allChecked"
          density="compact"
          hide-details
          class="terms-check"
          aria-label="전체 동의"
          @update:model-value="toggleAll"
        />
        <div class="terms-row__text">
          <div class="terms-row__title">전체 동의</div>
          <div class="terms-row__desc">필수 및 선택 약관에 모두 동의합니다</div>
        </div>
      </div>

      <v-divider class="terms-divider" />

      <div class="terms-row">
        <v-checkbox
          v-model="agreeService"
          density="compact"
          hide-details
          class="terms-check"
          aria-label="서비스 이용약관 동의"
          @update:model-value="syncAllChecked"
        />
        <div class="terms-row__text">
          <div class="terms-row__title">
            <span class="terms-required">(필수)</span> 서비스 이용약관 동의
          </div>
        </div>
        <v-btn
          variant="text"
          class="terms-link"
          @click="openLegal('service')"
          >보기</v-btn
        >
      </div>

      <div class="terms-row">
        <v-checkbox
          v-model="agreePrivacy"
          density="compact"
          hide-details
          class="terms-check"
          aria-label="개인정보 처리방침 동의"
          @update:model-value="syncAllChecked"
        />
        <div class="terms-row__text">
          <div class="terms-row__title">
            <span class="terms-required">(필수)</span> 개인정보 처리방침 동의
          </div>
        </div>
        <v-btn
          variant="text"
          class="terms-link"
          @click="openLegal('privacy')"
          >보기</v-btn
        >
      </div>

      <div class="terms-row">
        <v-checkbox
          v-model="agreeMarketing"
          density="compact"
          hide-details
          class="terms-check"
          aria-label="광고성 정보 수신 동의"
          @update:model-value="syncAllChecked"
        />
        <div class="terms-row__text">
          <div class="terms-row__title">
            <span class="terms-optional">(선택)</span> 광고성 정보 수신 동의
          </div>
        </div>
        <v-btn
          variant="text"
          class="terms-link"
          @click="openLegal('marketing')"
          >보기</v-btn
        >
      </div>
    </v-card>

    <v-btn
      block
      size="large"
      class="auth-btn auth-btn--muted"
      color="primary"
      :disabled="!canProceed"
      @click="onNext"
    >
      다음
    </v-btn>

    <div class="auth-footer">
      <v-btn
        variant="text"
        class="auth-link auth-link--muted"
        @click="onCancel"
      >
        취소하고 로그인으로
      </v-btn>
    </div>
  </AppCenterCard>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import AppCenterCard from '@/components/common/AppCenterCard.vue'
import { useTermsConsent } from '@/composables/auth/useTermsConsent'
import { OAuthCode } from '@/services/auth.types'

type LegalKind = 'service' | 'privacy' | 'marketing'

const router = useRouter()
const route = useRoute()
const {
  agreeService,
  agreePrivacy,
  agreeMarketing,
  allChecked,
  canProceed,
  toggleAll,
  syncAllChecked,
} = useTermsConsent()

function openLegal(kind: LegalKind) {
  const nameMap: Record<LegalKind, string> = {
    service: 'TermsService',
    privacy: 'TermsPrivacy',
    marketing: 'TermsMarketing',
  }

  const targetName = nameMap[kind]

  router.push({ name: targetName }).catch(() => {
    router.push({ path: `/legal/${kind}` }).catch(() => {})
  })
}

async function onNext() {
  const source = typeof route.query.source === 'string' ? route.query.source : 'email'
  const next = typeof route.query.next === 'string' ? route.query.next : null

  if (next) {
    router.replace(next).catch(() => {})
    return
  }

  if (source === OAuthCode.KAKAO) {
    const params = new URLSearchParams({
      provider: source,
      agree_service: String(agreeService.value),
      agree_privacy: String(agreePrivacy.value),
      agree_marketing: String(agreeMarketing.value),
    })

    window.location.href = `${import.meta.env.VITE_API_BASE_URL}/auth/oauth/start?${params.toString()}`

    return
  } else {
    router.push({ name: 'SignupEmail' }).catch(() => {})
    return
  }
}

function onCancel() {
  router.push({ name: 'Login' }).catch(() => {})
}
</script>
