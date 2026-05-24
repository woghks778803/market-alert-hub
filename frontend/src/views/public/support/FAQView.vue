<template>
  <AppLoading
    :show="supportAction.loading.value"
    overlay
  />

  <div class="faq-container flex-grow-1 d-flex flex-column">
    <v-container class="pa-4 bg-surface">
      <v-text-field
        :model-value="FAQListQuery.search"
        prepend-inner-icon="mdi-magnify"
        label="궁금한 점을 검색해보세요"
        variant="solo"
        density="comfortable"
        rounded="lg"
        hide-details
        clearable
        flat
        @update:model-value="supportStore.setSearch"
      />
    </v-container>

    <v-container class="pa-0 mt-2 flex-grow-1 d-flex flex-column">
      <v-expansion-panels
        variant="accordion"
        elevation="0"
      >
        <v-expansion-panel
          v-for="item in faqs"
          :key="item.id"
          class="border-b"
        >
          <v-expansion-panel-title class="text-subtitle-1 font-weight-bold py-4">
            <span class="text-primary mr-2">Q.</span>
            {{ item.question }}
          </v-expansion-panel-title>

          <v-expansion-panel-text class="pt-4">
            <div
              class="html-content text-body-2"
              v-html="item.answer"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-container>
  </div>

  <ScrollTopButton
    :bottom-offset="100"
    :show-after="300"
  />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'

import AppLoading from '@/components/common/AppLoading.vue'
import ScrollTopButton from '@/components/common/ScrollTopButton.vue'

import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { useSupportStore } from '@/stores/support.store'

const supportStore = useSupportStore()
const { faqs, FAQListQuery } = storeToRefs(supportStore)
const supportAction = useAsyncAction()

onMounted(() => {
  supportAction.run(async () => {
    await supportStore.fetchFAQs()
  })
})

onUnmounted(() => {
  supportStore.resetSupport()
})
</script>
