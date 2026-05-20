<template>
  <AppHeader />

  <v-main>
    <v-container
      class="py-8"
    >
      <router-view />
    </v-container>
  </v-main>

  <AppFooter />
</template>

<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
</script>
