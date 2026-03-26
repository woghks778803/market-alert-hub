<template>
  <v-text-field
    placeholder="심볼/마켓 검색"
    prepend-inner-icon="mdi-magnify"
    variant="solo"
    density="comfortable"
    hide-details
    class="mk-search"
    :v-model="search"
    @update:modelValue="onInput"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  search: string
}>()

const emit = defineEmits<{
  (e: "search", value: string): void
}>()

function onInput(v: string) {
  emit("search", v)
}
</script>
