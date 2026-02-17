<template>
  <v-layout class="fill-height">
    <v-app-bar density="comfortable" flat>
      <v-app-bar-title>{{ title }}</v-app-bar-title>

      <template #append>
        <v-btn icon="mdi-magnify" variant="text" :to="{ name: 'Market' }" />
        <!-- <v-btn icon="mdi-bell-outline" variant="text" :to="{ name: 'AlertLogs' }" /> -->
      </template>
    </v-app-bar>

    <v-main>
      <v-container class="py-4">
        <router-view />
      </v-container>
    </v-main>

    <v-bottom-navigation v-model="active" grow mandatory height="64">
      <v-btn value="home" :to="{ name: 'Home' }">
        <v-icon icon="mdi-home-outline" />
        <span>홈</span>
      </v-btn>

      <v-btn value="market" :to="{ name: 'Market' }">
        <v-icon icon="mdi-format-list-bulleted" />
        <span>마켓</span>
      </v-btn>

      <v-btn value="alerts" :to="{ name: 'Alerts' }">
        <v-icon icon="mdi-bell-outline" />
        <span>알림</span>
      </v-btn>

      <v-btn value="settings" :to="{ name: 'Settings' }">
        <v-icon icon="mdi-cog-outline" />
        <span>설정</span>
      </v-btn>
    </v-bottom-navigation>
  </v-layout>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue"
import { useRoute } from "vue-router"

const route = useRoute()
const active = ref<"home" | "market" | "alerts" | "settings">("home")

const mapNameToTab = (name: string | symbol | undefined) => {
  if (!name || typeof name !== "string") return "home"

  switch (name) {
    case "Home":
      return "home"

    case "Market":
    case "SymbolSelect":
      return "market"

    case "Alerts":
    case "AlertRules":
    case "AlertLogs":
    case "AlertChannels":
      return "alerts"

    case "Settings":
    case "Profile":
    case "Security":
      return "settings"

    default:
      return "home"
  }
}

watch(
  () => route.name,
  (name) => {
    active.value = mapNameToTab(name) as any
  },
  { immediate: true }
)

const title = computed(() => {
  switch (active.value) {
    case "home":
      return "홈"
    case "market":
      return "마켓"
    case "alerts":
      return "알림"
    case "settings":
      return "설정"
    default:
      return ""
  }
})
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
}
</style>
