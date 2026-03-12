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
        :key="tab.value"
        :value="tab.value"
      >
        {{ tab.label }}
      </v-chip>
    </v-chip-group>

  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
const selected = ref<string[]>(["all"])

const systemTabs = [
  { label: "전체", value: "all" },
  { label: "즐겨찾기", value: "favorite" },
]

const exchangeTabs = [
  { label: "UPBIT", value: "upbit" },
  { label: "BITHUMB", value: "bithumb" },
  { label: "BINANCE", value: "binance" },
]

const tabs = [...systemTabs, ...exchangeTabs]

function onUpdate(val: string[]) {
  console.log("val", val)

  // 마지막 선택값
  const last = val[val.length - 1]

  if (last === "all") {
    selected.value = ["all"]
    return
  }

  // 거래소 선택하면 all 제거
  selected.value = val.filter(v => v !== "all")

  console.log("selected", selected.value)

}
</script>

<style scoped>
</style>