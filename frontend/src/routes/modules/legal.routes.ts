import type { RouteRecordRaw } from 'vue-router'
import TermsDetailView from '@/views/public/legal/TermsDetailView.vue'

export const legalRoutes: RouteRecordRaw[] = [
  { path: '', redirect: { name: 'service' } },
  {
    path: 'service',
    name: 'TermsService',
    component: TermsDetailView,
    meta: { title: '서비스 이용약관', type: 'service', tab: 'more' },
  },
  {
    path: 'privacy',
    name: 'TermsPrivacy',
    component: TermsDetailView,
    meta: { title: '개인정보 처리방침', type: 'privacy', tab: 'more' },
  },
  {
    path: 'marketing',
    name: 'TermsMarketing',
    component: TermsDetailView,
    meta: { title: '광고성 정보 수신 동의', type: 'marketing', tab: 'more' },
  },
]
