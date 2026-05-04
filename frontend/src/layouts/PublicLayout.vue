<template>
  <AppHeader />

  <v-main>
    <v-container
      class="py-8"
      style="max-width: 420px"
    >
      <router-view />
    </v-container>
  </v-main>
</template>

<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
</script>
