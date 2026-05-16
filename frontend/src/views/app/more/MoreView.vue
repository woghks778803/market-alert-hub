<template>
  <v-card
    rounded="lg"
    variant="flat"
    class="mb-4"
  >
    <v-card-title>계정</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item
          title="내정보"
          subtitle="프로필 / 로그인 수단"
          append-icon="mdi-chevron-right"
          :to="{ name: 'Profile' }"
        />
      </v-list>
    </v-card-text>
  </v-card>

  <v-card
    rounded="lg"
    variant="flat"
    class="mb-4"
  >
    <v-card-title>설정</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item
          title="앱 설정"
          subtitle="화면 테마 / 화면 꺼짐 / 진동"
          append-icon="mdi-chevron-right"
          :to="{ name: 'AppSetting' }"
        />
      </v-list>
    </v-card-text>
  </v-card>

  <v-card
    rounded="lg"
    variant="flat"
    class="mb-4"
  >
    <v-card-title>고객 지원</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item
          title="공지사항"
          subtitle="새로운 소식 및 이용 안내"
          append-icon="mdi-chevron-right"
          :to="{ name: 'Notice' }"
        />
      </v-list>
      <v-list lines="one">
        <v-list-item
          title="자주하는 질문"
          subtitle="서비스 이용 팁과 해결 방법"
          append-icon="mdi-chevron-right"
          :to="{ name: 'FAQ' }"
        />
      </v-list>
      <v-list lines="one">
        <v-list-item
          title="1:1 문의"
          subtitle="카카오톡으로 빠른 답변"
          append-icon="mdi-chevron-right"
          :to="{ name: 'Alerts' }"
        />
      </v-list>
    </v-card-text>
  </v-card>

  <v-card
    rounded="lg"
    variant="flat"
    class="mb-4"
  >
    <v-card-title>약관 및 정책</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item
          title="이용약관"
          subtitle="서비스 이용 규칙 및 약관"
          append-icon="mdi-chevron-right"
          :to="{ name: 'TermsService' }"
        />
      </v-list>
      <v-list lines="one">
        <v-list-item
          title="개인정보 처리방침"
          subtitle="개인정보 수집 및 이용 안내"
          append-icon="mdi-chevron-right"
          :to="{ name: 'TermsPrivacy' }"
        />
      </v-list>
      <v-list lines="one">
        <v-list-item
          title="광고성 정보 수신 동의"
          subtitle="광고성 정보 수신 및 이용 안내"
          append-icon="mdi-chevron-right"
          :to="{ name: 'TermsMarketing' }"
        />
      </v-list>
    </v-card-text>
  </v-card>

  <v-card
    rounded="lg"
    variant="flat"
  >
    <v-card-title>기타</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item
          title="버전"
          subtitle="0.0.0"
        />
      </v-list>
      <v-btn
        class="mt-3"
        block
        variant="tonal"
        color="error"
        @click="goLogin"
      >
        로그아웃
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthFlow } from '@/composables/auth/useAuthFlow'

const router = useRouter()
const { logout } = useAuthFlow()

async function goLogin() {
  await logout()
  router.replace({ name: 'Login' })
}
</script>
