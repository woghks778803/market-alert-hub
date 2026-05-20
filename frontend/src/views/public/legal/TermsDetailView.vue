<template>
  <v-container>
    <v-sheet
      class="pa-6 pa-md-12 mx-auto markdown-body"
      width="100%"
      max-width="900"
    >
      <vue-markdown :source="currentContent" />
    </v-sheet>
  </v-container>

  <ScrollTopButton
    :bottom-offset="100"
    :show-after="300"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import VueMarkdown from 'vue-markdown-render'
import 'github-markdown-css/github-markdown-light.css'

import serviceMd from '@/assets/legal/service.md?raw'
import privacyMd from '@/assets/legal/privacy.md?raw'
import marketingMd from '@/assets/legal/marketing.md?raw'

import ScrollTopButton from '@/components/common/ScrollTopButton.vue'
import { LegalLabel, type LegalType } from '@/services/user.types'

const route = useRoute()

const currentContent = computed(() => {
  const contents: Record<LegalType, string> = {
    [LegalLabel.SERVICE]: serviceMd,
    [LegalLabel.PRIVACY]: privacyMd,
    [LegalLabel.MARKETING]: marketingMd,
  }

  const type = route.meta.type as LegalType
  return contents[type]
})
</script>
