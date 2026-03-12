<template>

  <v-card
    rounded="lg"
    variant="flat"
    class="sd-summary-card"
  >

    <v-card-text>

      <div class="sd-top">

        <div>

        <div class="sd-name">
          {{ symbol.name }}
          <v-chip size="x-small">{{ symbol.exchange }}</v-chip>
        </div>

        <div class="sd-base">
          KRW
        </div>

        </div>

      <v-icon color="amber" size="25" :color="symbol.favorite ? 'amber' : 'grey'">
      mdi-star
      </v-icon>

      </div>

      <div class="sd-price">
        {{ symbol.price }}
      </div>

      <div
        class="sd-change"
        :class="symbol.change.includes('-') ? 'down' : 'up'"
      >
        {{ symbol.change }} (24h)
      </div>

      <div class="sd-stats">

      <div>
      <div class="label">고가</div>
      <div>{{ symbol.high }}</div>
      </div>

      <div>
      <div class="label">저가</div>
      <div>{{ symbol.low }}</div>
      </div>

      <div>
      <div class="label">거래대금</div>
      <div>{{ symbol.volume }}</div>
      </div>

    </div>

    </v-card-text>

  </v-card>

</template>

<script setup lang="ts">
defineProps({
  symbol: Object
})
</script>