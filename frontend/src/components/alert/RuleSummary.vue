<template>

<div class="alert-rule-summary">

  <div class="alert-rule-summary-left">
    <span class="alert-rule-title">전체 알림</span>

    <v-switch
      v-model="enabled"
      density="compact"
      hide-details
    />
  </div>

  <div class="alert-rule-summary-right">
    활성 6 · 일시정지 3
  </div>

</div>

</template>

<script setup>
import { ref } from "vue"

const enabled = ref(true)
</script>