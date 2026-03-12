<template>

<v-slide-group
  show-arrows
  class="sd-timeframe"
>

<v-slide-group-item
  v-for="t in frames"
  :key="t"
  class="sd-timeframe-item"
>

<v-chip class="sd-timeframe-chip">
{{ t }}
</v-chip>

</v-slide-group-item>

</v-slide-group>

</template>

<script setup lang="ts">

const frames = [
"1m",
"5m",
"15m",
"1h",
"4h",
"1d"
]

</script>