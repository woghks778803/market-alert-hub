<template>
  <AppCenterCard center>
    <div class="nf-code">404</div>

    <div class="nf-title">페이지를 찾을 수 없어요</div>
    <div class="nf-desc">
      요청하신 페이지가 삭제되었거나,<br />
      주소가 잘못되었을 수 있어요.
    </div>

    <v-btn
      class="nf-btn"
      block
      size="large"
      color="primary"
      variant="flat"
      @click="goHome"
    >
      <v-icon
        icon="mdi-home-outline"
        class="mr-2"
      />
      홈으로 돌아가기
    </v-btn>

    <button
      class="nf-link"
      type="button"
      @click="goBack"
    >
      <v-icon
        icon="mdi-arrow-left"
        class="mr-1"
        size="18"
      />
      이전 화면으로
    </button>

    <div class="nf-foot">문제가 계속 발생하면 다시 시도해주세요.</div>
  </AppCenterCard>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import AppCenterCard from '@/components/common/AppCenterCard.vue'

const router = useRouter()

function goHome() {
  // 로그인 필요 여부는 beforeEach가 처리
  router.push({ name: 'Home' }).catch(() => {})
}

function goBack() {
  // 히스토리 없을 때를 대비해 홈으로 폴백
  if (window.history.state?.back) router.back()
  else goHome()
}
</script>
