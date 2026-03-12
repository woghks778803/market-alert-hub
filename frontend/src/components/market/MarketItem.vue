<template>

  <v-card class="mk-card">

    <v-card-text>

      <!-- row 1 -->
      <div class="mk-row-top">

        <div>

          <div class="mk-symbol">
            {{ item.symbol }}
          </div>

          <div class="mk-exchange">
            {{ item.exchange }} · {{ item.pair }}
          </div>

          <div class="mk-name">
            {{ item.name }}
          </div>

        </div>

        <v-icon
          :icon="item.favorite ? 'mdi-star' : 'mdi-star-outline'"
          :color="item.favorite ? 'amber' : 'grey'"
          size="25"
        />

      </div>

      <!-- row 2 -->
      <div class="mk-row-bottom">

        <div class="mk-price">
          {{ item.price }}
        </div>

        <div class="mk-change-block">

          <div
            class="mk-change"
            :class="item.change.includes('-') ? 'mk-change-down' : 'mk-change-up'"
          >
            {{ item.change }}
          </div>

          <div class="mk-volume">
            {{ item.volume }}
          </div>

        </div>

      </div>

    </v-card-text>

  </v-card>

</template>

<script setup lang="ts">
defineProps({
  item: Object
})
</script>