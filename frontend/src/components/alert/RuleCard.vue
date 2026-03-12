<template>

<v-card class="alert-rule-card">

  <div class="alert-rule-header">

    <div class="alert-rule-title-group">
      <span class="alert-rule-symbol">
        {{ rule.symbol }}
      </span>

      <span class="alert-rule-exchange">
        {{ rule.exchange }}
      </span>

      <span
        class="alert-rule-status"
        :class="rule.status.toLowerCase()"
      >
        {{ rule.status }}
      </span>
    </div>

    <div class="alert-rule-actions">

      <v-switch
        density="compact"
        hide-details
      />

      <v-btn icon variant="text">
        <v-icon>mdi-dots-vertical</v-icon>
      </v-btn>

    </div>

  </div>

  <div class="alert-rule-condition">
    {{ rule.condition }}
  </div>

  <div class="alert-rule-meta">
    쿨다운 {{ rule.cooldown }} · 채널:
    {{ rule.channels.join(", ") }}
  </div>

</v-card>

</template>

<script setup>

defineProps({
  rule: Object
})

</script>