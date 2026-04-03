<template>
  <div class="notice-detail-wrapper bg-white fill-height">
    <v-container v-if="notice" class="pa-0">
      <div class="pa-6 pb-4 border-b border-grey-lighten-4">
        <div class="d-flex align-center mb-3">
          <v-chip
            size="x-small"
            :color="NoticeCategoryLabel[notice.category].bg"
            :class="[
              'mr-2 font-weight-bold px-3',
              NoticeCategoryLabel[notice.category].text
            ]"
            variant="flat"
            rounded="lg"
          >
            {{ NoticeCategoryLabel[notice.category].title }}
          </v-chip>
          <span class="text-caption text-grey-lighten-1">{{ formatDateTime(notice.updatedAt) }} · 조회 {{ notice.viewCount }}</span>
        </div>
        <h1 class="text-h5 font-weight-black text-grey-darken-4 leading-tight">
          {{ notice.title }}
        </h1>
      </div>

      <div class="pa-6 notice-content text-body-1 text-grey-darken-3">
        <v-sheet
          v-if="notice.summary"
          color="deep-purple-lighten-5"
          rounded="lg"
          class="pa-4 mb-6 border-s-lg border-deep-purple-accent-2"
        >
          <p class="text-body-2 text-deep-purple-darken-2 font-weight-medium">
            {{ notice.summary }}
          </p>
        </v-sheet>

        <div class="whitespace-pre-wrap line-height-relaxed">
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
            <template v-slot:prepend>
              <span class="text-caption text-grey mr-4">이전 글</span>
            </template>
            <v-list-item-title class="text-body-2">{{ notice.prevNotice.title }}</v-list-item-title>
            <template v-slot:append>
              <v-icon size="small" color="grey-lighten-1">mdi-chevron-right</v-icon>
            </template>
          </v-list-item>

          <v-divider v-if="notice.prevNotice && notice.nextNotice" inset></v-divider>

          <v-list-item 
            v-if="notice.nextNotice" 
            link 
            class="px-2"
            @click="goToNotice(notice.nextNotice.id)"
          >
            <template v-slot:prepend>
              <span class="text-caption text-grey mr-4">다음 글</span>
            </template>
            <v-list-item-title class="text-body-2">{{ notice.nextNotice.title }}</v-list-item-title>
            <template v-slot:append>
              <v-icon size="small" color="grey-lighten-1">mdi-chevron-right</v-icon>
            </template>
          </v-list-item>
        </v-list>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { watch, onMounted } from "vue"
import { storeToRefs } from "pinia"
import { useRoute, useRouter } from "vue-router"
import { useSupportStore } from "@/stores/support.store"
import { NoticeCategoryLabel } from "@/services/support.types"
import { formatDateTime } from "@/utils/format"

const route = useRoute()
const router = useRouter()
const supportStore = useSupportStore()
const { notice } = storeToRefs(supportStore)

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