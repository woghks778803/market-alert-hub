<template>
  <v-app-bar v-if="!hideHeader" density="comfortable" flat class="border-b">
    <v-btn
      v-if="showBack"
      icon="mdi-arrow-left"
      variant="text"
      @click="goBack"
    />
    <v-app-bar-title class="text-subtitle-1 font-weight-bold">
      {{ title }}
    </v-app-bar-title>

    <!-- <template #append>
      <slot name="append">
        <v-btn icon="mdi-bell-outline" variant="text" to="/alerts" />
      </slot>
    </template> -->
  </v-app-bar>
</template>

<script setup lang="ts">
import { usePageMeta } from '@/composables/layout/usePageMeta';
const { title, showBack, hideHeader, goBack } = usePageMeta();
</script>