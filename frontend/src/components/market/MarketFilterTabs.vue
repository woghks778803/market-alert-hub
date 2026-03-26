<template>
  <div class="mk-tabs">

    <v-chip-group
      selected-class="mk-tab-active"
      multiple
      v-model="selected"
      @update:modelValue="onUpdate"
    >
      <v-chip
        v-for="tab in tabs"
        :key="tab.code"
        :value="tab.code"
      >
        {{ tab.name }}
      </v-chip>
    </v-chip-group>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue"
import type { ExchangeDto } from "@/services/market.types"

const props = defineProps<{
  exchangeTabs: ExchangeDto[],
}>()

const emit = defineEmits<{
  (e: "change", value: string[]): void
}>()

const selected = ref<string[]>(["all"])

const systemTabs = [
  { name: "전체", code: "all" },
  { name: "즐겨찾기", code: "watchlist" },
]

const tabs = computed(() => [...systemTabs, ...props.exchangeTabs])

function onUpdate(val: string[]) {
  // console.log("val", val)
  
  // 마지막 선택값
  const last = val[val.length - 1]
  let next: string[]

  if (last === "all") {
    next = ["all"]
  }else{
    next = val.filter(v => v !== "all")
  }

  if (next.length == 0){
    next = ["all"]
  }

  selected.value = next
  emit("change", next)

  // console.log("selected", selected.value)
}
</script>

<style scoped>
</style>