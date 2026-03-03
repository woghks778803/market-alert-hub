<template>
  <CenterCardShell>
    <div class="auth-head">
      <div class="auth-head__title">{{ title }}</div>
      <div class="auth-head__desc">
        <slot name="description" />
      </div>
    </div>

    <div v-if="successMessage" class="auth-success">
      {{ successMessage }}
    </div>

    <div v-if="errorMessage" class="auth-error">
      {{ errorMessage }}
    </div>

    <div class="auth-field">
      <slot></slot>
    </div>

    <v-btn
      block
      color="primary"
      class="auth-btn"
      size="large"
      :loading="loading"
      :disabled="disabled"
      @click="$emit('submit')"
    >
      <slot name="button" />
    </v-btn>

    <div class="auth-footer">
      <slot name="footer" />
    </div>
  </CenterCardShell>
</template>

<script setup lang="ts">
import CenterCardShell from "@/components/CenterCardShell.vue"
defineProps<{
  title: string
  successMessage?: string | null
  errorMessage?: string | null
  loading?: boolean
  disabled?: boolean
}>()

defineEmits<{
  (e: "submit"): void
}>()
</script>