<template>
  <AppHeader />

  <v-main>
    <v-container class="py-4">
      <router-view />
    </v-container>
  </v-main>

  <AppFooter />

  <div class="app-bottom-spacer" />

  <v-bottom-navigation
    :model-value="activeTab"
    grow
    mandatory
    height="64"
  >
    <!-- <v-btn value="home" @click="handleTabClick">
      <v-icon icon="mdi-home-outline" />
      <span>홈</span>
    </v-btn> -->

    <v-btn
      value="market"
      @click="handleTabClick"
    >
      <v-icon icon="mdi-format-list-bulleted" />
      <span>마켓</span>
    </v-btn>

    <v-btn
      value="alert"
      @click="handleTabClick"
    >
      <v-icon icon="mdi-bell-outline" />
      <span>알림</span>
    </v-btn>

    <v-btn
      value="news"
      @click="handleTabClick"
    >
      <v-icon icon="mdi-rss" />
      <span>피드</span>
      <!-- <v-icon icon="mdi-newspaper-variant-outline" /> -->
      <!-- <span>뉴스</span> -->
    </v-btn>

    <v-btn
      value="more"
      @click="handleTabClick"
    >
      <v-icon icon="mdi-dots-grid" />
      <span>더보기</span>
    </v-btn>
  </v-bottom-navigation>
</template>

<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeTab = computed(() => {
  const matched = [...route.matched].reverse().find((r) => r.meta?.tab)
  return (matched?.meta?.tab as string) || 'home'
})

const handleTabClick = (e: MouseEvent) => {
  const btn = e.currentTarget as HTMLElement
  const tabValue = btn.getAttribute('value')

  if (!tabValue) return

  const routeNames: Record<string, string> = {
    // home: 'Home',
    market: 'Markets',
    alert: 'Rules',
    news: 'Newses',
    more: 'More',
  }

  const targetName = routeNames[tabValue]
  if (targetName) {
    // 동일 라우터로 이동시 컴포넌트 재사용(Component Reuse)
    // console.log("Navigating to:", targetName);
    router.push({ name: targetName }).catch(() => {})
  }
}
</script>
