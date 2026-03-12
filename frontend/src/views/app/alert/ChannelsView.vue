<template>
  <div class="alert-channel-container">
    <ChannelCard
      v-for="channel in channels"
      :key="channel.id"
      :title="channel.title"
      :description="channel.description"
      :code="channel.code"
      :icon="channel.icon"
      v-model:enabled="channel.enabled"
      :connected="channel.connected"
    />

    <ChannelAddFab />

  </div>
</template>

<script setup>
import { ref } from "vue"
import ChannelCard from "@/components/alert/ChannelCard.vue"
import ChannelAddFab from "@/components/alert/ChannelAddFab.vue"
const channels = ref([
  {
    id: 1,
    title: "Telegram",
    code: "TELEGRAM",
    description: "chat_id: 1234****",
    icon: "mdi-telegram",
    connected: true,
    enabled: true
  },
  {
    id: 2,
    title: "FCM",
    code: "FCM",
    description: "이 기기",
    icon: "mdi-bell",
    connected: true,
    enabled: true
  },
  {
    id: 3,
    title: "Email",
    code: "EMAIL",
    description: "email: te****@gmail.com",
    icon: "mdi-email",
    connected: true,
    enabled: false
  },
  {
    id: 4,
    title: "Telegram (Bot 2)",
    code: "TELEGRAM",
    description: "연결 필요",
    icon: "mdi-telegram",
    connected: false,
    enabled: false
  },
  {
    id: 5,
    title: "Discord",
    code: "DISCORD",
    description: "연결 필요",
    icon: "mdi-discord",
    connected: false,
    enabled: false
  },
  {
    id: 1,
    title: "Telegram",
    code: "TELEGRAM",
    description: "chat_id: 1234****",
    icon: "mdi-telegram",
    connected: true,
    enabled: true
  },
  {
    id: 2,
    title: "FCM",
    code: "FCM",
    description: "이 기기",
    icon: "mdi-bell",
    connected: true,
    enabled: true
  },
  {
    id: 3,
    title: "Email",
    code: "EMAIL",
    description: "email: te****@gmail.com",
    icon: "mdi-email",
    connected: true,
    enabled: false
  },
  {
    id: 4,
    title: "Telegram (Bot 2)",
    code: "TELEGRAM",
    description: "연결 필요",
    icon: "mdi-telegram",
    connected: false,
    enabled: false
  },
  {
    id: 5,
    title: "Discord",
    code: "DISCORD",
    description: "연결 필요",
    icon: "mdi-discord",
    connected: false,
    enabled: false
  }
])
</script>