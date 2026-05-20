<template>
  <div class="auth-page">
    <v-container
      class="auth-container"
      fluid
    >
      <v-card
        class="auth-card"
        elevation="0"
      >
        <v-card-text
          class="auth-card__body"
          :class="{ 'auth-card__body--center': center }"
        >
          <slot />
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  center?: boolean
}>()
</script>
