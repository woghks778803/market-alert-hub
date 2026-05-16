<template>
  <footer 
    v-if="!hideFooter"
    class="app-footer"
  >
    <div class="app-footer__inner">
      <div class="app-footer__brand">AlertPing</div>

      <p class="app-footer__summary">
        AlertPing은 가상자산 시세, 뉴스 및 사용자가 설정한 조건을 기반으로
        정보성 알림을 제공하는 서비스입니다.
      </p>

      <p class="app-footer__disclaimer">
        제공되는 정보는 투자 권유나 수익 보장을 의미하지 않으며, 최종 투자 판단과 그 결과는 이용자 본인에게 있습니다.
      </p>

      <div class="app-footer__links">
        <RouterLink :to="{ name: 'TermsService' }">
          이용약관
        </RouterLink>

        <RouterLink :to="{ name: 'TermsPrivacy' }">
          개인정보처리방침
        </RouterLink>

        <RouterLink :to="{ name: 'TermsMarketing' }">
          광고성 정보 수신 동의
        </RouterLink>
      </div>

      <div class="app-footer__business">
        <span>대표자: 정재환</span>
        <span>문의: alertping.cloud@outlook.com</span>
      </div>

      <div class="app-footer__copyright">
        © 2026 AlertPing. All rights reserved.
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { usePageMeta } from '@/composables/layout/usePageMeta'
const { hideFooter } = usePageMeta()
</script>