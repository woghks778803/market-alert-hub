<template>
  <div class="faq-container flex-grow-1 d-flex flex-column">
    <v-container class="pa-4 bg-white">
      <v-text-field
        :model-value="FAQListQuery.search"
        @update:modelValue="supportStore.setSearch"
        prepend-inner-icon="mdi-magnify"
        label="궁금한 점을 검색해보세요"
        variant="solo"
        flat
        hide-details
        rounded="lg"
        class="border"
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

          <v-expansion-panel-text class="bg-grey-lighten-5 pt-4">
            <div
              class="faq-content-wrapper text-body-2"
              v-html="item.answer"
            />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue"
import { storeToRefs } from "pinia"
import { useSupportStore } from "@/stores/support.store"

const supportStore = useSupportStore()
const { faqs, FAQListQuery } = storeToRefs(supportStore)

onMounted(() => {
  supportStore.fetchFAQs()
})

onUnmounted(() => {
  supportStore.resetSupport()
})
</script>