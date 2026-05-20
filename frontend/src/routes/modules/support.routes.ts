import type { RouteRecordRaw } from 'vue-router'
import SupportView from '@/views/public/support/SupportView.vue'
import FAQView from '@/views/public/support/FAQView.vue'
import NoticeView from '@/views/public/support/NoticeView.vue'
import NoticeDetailView from '@/views/public/support/NoticeDetailView.vue'

export const supportRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'Support',
    component: SupportView,
    meta: { title: '고객 지원', tab: 'more' },
  },
  {
    path: 'notice',
    name: 'Notice',
    component: NoticeView,
    meta: { title: '공지사항', allows: [], tab: 'more' },
  },
  {
    path: 'notice/:id',
    name: 'NoticeDetail',
    component: NoticeDetailView,
    meta: { title: '공지사항', allows: [], tab: 'more' },
  },

  {
    path: 'faq',
    name: 'FAQ',
    component: FAQView,
    meta: { title: 'FAQ', allows: [], tab: 'more' },
  },
]
