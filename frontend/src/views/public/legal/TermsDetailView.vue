<template>
  <v-container>
    <v-sheet class="pa-6 pa-md-12 mx-auto markdown-body" max-width="900">
      <vue-markdown :source="currentContent" />
    </v-sheet>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import VueMarkdown from 'vue-markdown-render'
import 'github-markdown-css/github-markdown-light.css'

import serviceMd from '@/assets/legal/service.md?raw'
import privacyMd from '@/assets/legal/privacy.md?raw'
import marketingMd from '@/assets/legal/marketing.md?raw'
const route = useRoute()

const currentContent = computed(() => {
  const contents = {
    service: serviceMd,
    privacy: privacyMd,
    marketing: marketingMd
  }
  return contents[route.meta.type] || ''
})
</script>