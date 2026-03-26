<template>

<div class="mk-tabs">

    <v-chip-group
      selected-class="mk-tab-active"
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
const selected = ref<string>("1m")

const tabs = [
  { label: "1m", value: "1m" },
  { label: "5m", value: "5m" },
  { label: "15m", value: "15m" },
  { label: "1h", value: "1h" },
  { label: "4h", value: "4h" },
  { label: "1d", value: "1d" },
]

function onUpdate(val: string[]) {
  console.log("val", val)
  console.log("selected", selected.value)
}
</script>