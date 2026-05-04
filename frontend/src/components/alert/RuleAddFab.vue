<template>
  <v-btn
    class="alert-rule-fab"
    icon
    size="large"
    color="deep-purple"
    @click="goSetting"
  >
    <v-icon>mdi-plus</v-icon>
  </v-btn>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goSetting() {
  router.push({ name: 'RuleSetting' })
}
</script>
