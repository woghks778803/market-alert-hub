<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import type { MarketDto } from '@/services/market.types'
import { formatPrice, formatChange, formatVolume } from '@/utils/format'
import { getDecimalPlaces } from '@/utils/number'

const props = defineProps<{
  item: MarketDto
}>()

const emit = defineEmits<{
  select: [market: MarketDto]
}>()

const flash = ref(false)
let flashTimer: ReturnType<typeof setTimeout> | null = null

function triggerFlash() {
  flash.value = true

  if (flashTimer) {
    clearTimeout(flashTimer)
  }

  flashTimer = setTimeout(() => {
    flash.value = false
  }, 500)
}

watch(
  () => [
    props.item.closePrice,
    props.item.changeRate,
    props.item.volume,
    props.item.normalizedVolume,
    props.item.normalizedPrice,
  ],
  (newVal, oldVal) => {
    if (oldVal === undefined) return
    if (newVal === oldVal) return
    triggerFlash()
  },
)

onBeforeUnmount(() => {
  if (flashTimer) {
    clearTimeout(flashTimer)
  }
})
</script>

<template>
  <v-card
    class="mk-card market-entity-market-card"
    :class="{ flash }"
    @click="emit('select', item)"
  >
    <div class="mk-row-top">
      <div>
        <div class="market-entity-symbol-row">
          <strong class="mk-symbol">
            {{ item.baseSymbol }}/{{ item.quoteSymbol }}
          </strong>

          <v-chip
            size="x-small"
            variant="tonal"
          >
            <slot
              name="chip"
              :market="item"
            />
          </v-chip>
        </div>

        <div class="mk-name">
          {{ item.name }}
        </div>
      </div>

      <div class="mk-change-block">
        <div class="mk-price">
          {{ formatPrice(
            item.closePrice,
            getDecimalPlaces(item.closePrice),
          ) }}
          {{ item.quoteSymbol }}
        </div>

        <div
          :class="
            item.changeRate && item.changeRate < 0
              ? 'mk-change-down'
              : 'mk-change-up'
          "
        >
          {{ formatChange(item.changeRate) }}%
        </div>
      </div>
    </div>

    <div class="mk-row-bottom">
      <span class="mk-volume">
        거래대금(원) {{ formatVolume(item.normalizedVolume) }}
      </span>

      <v-icon
        icon="mdi-chevron-right"
        size="20"
        color="medium-emphasis"
      />
    </div>
  </v-card>
</template>