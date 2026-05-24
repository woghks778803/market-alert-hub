<template>
  <AppLoading
    :show="supportAction.loading.value"
    overlay
  />

  <div class="notice-wrapper bg-[#F5F5F7] fill-height">
    <!-- 탭 -->
    <div class="bg-surface px-4 py-3">
      <v-tabs
        v-model="activeTab"
        color="transparent"
        slider-color="transparent"
        class="notice-tabs"
        height="40"
      >
        <v-tab
          v-for="(value, key) in NoticeCategoryLabel"
          :key="key"
          :value="key"
          :class="[
            'notice-tab-item mr-2 text-caption font-weight-bold',
            activeTab === key ? 'notice-active-tab' : 'notice-inactive-tab',
          ]"
          variant="flat"
          rounded="pill"
        >
          {{ value.title }}
        </v-tab>
      </v-tabs>
    </div>

    <!-- 리스트 -->
    <v-container class="pa-4">
      <v-row dense>
        <v-col
          v-for="notice in notices"
          :key="notice.id"
          cols="12"
          class="mb-3"
        >
          <v-card
            flat
            rounded="xl"
            class="notice-card pa-5 pb-4"
            @click="goDetail(notice.id)"
          >
            <div class="d-flex justify-space-between align-center mb-3">
              <v-chip
                size="x-small"
                :class="[
                  'notice-chip font-weight-bold px-3',
                  NoticeCategoryLabel[notice.category].bg,
                ]"
                variant="flat"
                rounded="lg"
              >
                {{ NoticeCategoryLabel[notice.category].title }}
              </v-chip>

              <v-icon
                size="small"
                color="#CCCCCC"
              >
                mdi-chevron-right
              </v-icon>
            </div>

            <div class="text-subtitle-1 font-weight-black text-[#1A1A1A] mb-1 leading-tight">
              {{ notice.title }}
            </div>

            <div class="text-caption font-weight-medium text-[#BDBDBD]">
              {{ formatDateTime(notice.createdAt) }}
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>

  <ScrollTopButton
    :bottom-offset="100"
    :show-after="300"
  />
</template>

<script setup lang="ts">
import { watch, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'

import AppLoading from '@/components/common/AppLoading.vue'
import ScrollTopButton from '@/components/common/ScrollTopButton.vue'

import { useAsyncAction } from '@/composables/common/useAsyncAction'

import { NoticeCategoryLabel } from '@/services/support.types'
import { useSupportStore } from '@/stores/support.store'
import { formatDateTime } from '@/utils/format'

const router = useRouter()

const supportStore = useSupportStore()
const { notices, activeTab } = storeToRefs(supportStore)
const supportAction = useAsyncAction()

onMounted(() => {
  supportAction.run(async () => {
    await supportStore.fetchNotices()
  })
})

watch(activeTab, (v) => {
  supportStore.setNoticeCategory(v)
})

function goDetail(id: number) {
  router.push({
    name: 'NoticeDetail',
    params: { id },
  })
}
</script>
