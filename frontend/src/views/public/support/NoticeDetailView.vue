<template>
  <AppLoading
    :show="supportAction.loading.value"
    overlay
  />

  <div class="notice-detail-wrapper bg-surface fill-height">
    <v-container
      v-if="notice"
      class="pa-0"
    >
      <div class="pa-6 pb-4 border-b border-default">
        <div class="d-flex align-center mb-3">
          <v-chip
            size="x-small"
            :class="['notice-chip font-weight-bold px-3', NoticeCategoryLabel[notice.category].bg]"
            variant="flat"
            rounded="lg"
          >
            {{ NoticeCategoryLabel[notice.category].title }}
          </v-chip>
          <span class="text-caption"
            >{{ formatDateTime(notice.updatedAt) }} · 조회 {{ notice.viewCount }}</span
          >
        </div>
        <h1 class="text-h5 font-weight-black text-primary leading-tight">
          {{ notice.title }}
        </h1>
      </div>

      <div class="pa-6 notice-content text-body-1">
        <v-sheet
          v-if="notice.summary"
          class="notice-summary pa-4 mb-6"
          rounded="lg"
        >
          <p class="notice-summary-text text-body-2 font-weight-medium">
            {{ notice.summary }}
          </p>
        </v-sheet>

        <div class="notice-body whitespace-pre-wrap line-height-relaxed">
          <div v-html="notice.content"></div>
        </div>
      </div>

      <v-divider class="mx-6"></v-divider>
      <div class="pa-4">
        <v-list class="bg-transparent">
          <v-list-item
            v-if="notice.prevNotice"
            link
            class="px-2"
            @click="goToNotice(notice.prevNotice.id)"
          >
            <template #prepend>
              <span class="text-caption text-grey mr-4">이전 글</span>
            </template>
            <v-list-item-title class="text-body-2">{{ notice.prevNotice.title }}</v-list-item-title>
            <template #append>
              <v-icon
                size="small"
                color="grey-lighten-1"
                >mdi-chevron-right</v-icon
              >
            </template>
          </v-list-item>

          <v-divider
            v-if="notice.prevNotice && notice.nextNotice"
            inset
          ></v-divider>

          <v-list-item
            v-if="notice.nextNotice"
            link
            class="px-2"
            @click="goToNotice(notice.nextNotice.id)"
          >
            <template #prepend>
              <span class="text-caption text-grey mr-4">다음 글</span>
            </template>
            <v-list-item-title class="text-body-2">{{ notice.nextNotice.title }}</v-list-item-title>
            <template #append>
              <v-icon
                size="small"
                color="grey-lighten-1"
                >mdi-chevron-right</v-icon
              >
            </template>
          </v-list-item>
        </v-list>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'

import AppLoading from '@/components/common/AppLoading.vue'
import { useAsyncAction } from '@/composables/common/useAsyncAction'

import { NoticeCategoryLabel } from '@/services/support.types'
import { useSupportStore } from '@/stores/support.store'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const supportStore = useSupportStore()
const { notice } = storeToRefs(supportStore)
const supportAction = useAsyncAction()

onMounted(async () => {
  const id = Number(route.params.id)
  await supportStore.fetchNotice(id)
})

watch(
  () => route.params.id,
  async (id) => {
    await supportStore.fetchNotice(Number(id))
  },
  { immediate: true }
)

function goToNotice(id: number) {
  router.replace({
    name: 'NoticeDetail',
    params: { id },
  })
}
</script>
