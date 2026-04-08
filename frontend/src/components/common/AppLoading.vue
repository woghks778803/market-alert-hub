```vue
<template>
  <div v-if="show" class="app-loading" :class="{ overlay }">
    <div class="loading-content">
      <v-progress-circular indeterminate size="36" width="3" />
      <div v-if="text" class="loading-text">{{ text }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
  overlay?: boolean
  text?: string
}>()
</script>
```
