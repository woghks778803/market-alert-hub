<template>
  <v-card
    class="alert-channel-card"
    :class="{ 'alert-channel-disabled': !connected }"
    elevation="1"
  >
    <div class="alert-channel-icon">
      <TelegramIcon v-if="code === 'TELEGRAM'" />

      <DiscordIcon v-else-if="code === 'DISCORD'" />

      <v-icon v-else-if="code === 'EMAIL'" icon="mdi-email-outline" />

      <v-icon v-else icon="mdi-bell-outline" />
    </div>

    <div class="alert-channel-body">
      <div class="alert-channel-title">
        {{ title }}
        <span
          class="alert-channel-badge"
          :class="connected ? 'connected' : 'disconnected'"
        >
          {{ connected ? '연결됨' : '미연결' }}
        </span>
      </div>

      <div class="alert-channel-desc">
        {{ description }}
      </div>
    </div>

    <div class="alert-channel-actions">
      <v-switch
        v-model="enabled"
        :disabled="!connected"
        hide-details
        density="compact"
      />
      <v-btn icon variant="text">
        <v-icon size="18">mdi-dots-vertical</v-icon>
      </v-btn>
    </div>
  </v-card>
</template>

<script setup>
import TelegramIcon from "@/components/icons/TelegramIcon.vue"
import DiscordIcon from "@/components/icons/DiscordIcon.vue"

defineProps({
  title: String,
  code: String,
  description: String,
  icon: String,
})

const connected = defineModel("connected")
const enabled = defineModel("enabled")

</script>