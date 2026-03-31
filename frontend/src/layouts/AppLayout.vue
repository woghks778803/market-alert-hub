<template>
  <v-app-bar density="comfortable" flat>
    <v-btn
      v-if="showBack"
      icon="mdi-arrow-left"
      variant="text"
      @click="goBack"
    />
    <v-app-bar-title>{{ title }}</v-app-bar-title>

    <template #append>
      <v-btn icon="mdi-bell-outline" variant="text" :to="{ name: 'Alerts' }" />
    </template>
  </v-app-bar>

  <v-main>
    <v-container class="py-4">
      <router-view />
    </v-container>
  </v-main>

  <v-bottom-navigation 
    :model-value="activeTab" 
    grow mandatory height="64">
    <v-btn value="home" @click="handleTabClick">
      <v-icon icon="mdi-home-outline" />
      <span>홈</span>
    </v-btn>

    <v-btn value="market" @click="handleTabClick">
      <v-icon icon="mdi-format-list-bulleted" />
      <span>마켓</span>
    </v-btn>

    <v-btn value="alert" @click="handleTabClick">
      <v-icon icon="mdi-bell-outline" />
      <span>알림</span>
    </v-btn>

    <v-btn value="setting" @click="handleTabClick">
      <v-icon icon="mdi-cog-outline" />
      <span>설정</span>
    </v-btn>
  </v-bottom-navigation>
</template>

<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"

const route = useRoute()
const router = useRouter()
const showBack = computed(() => route.meta.showBack === true)
const activeTab = computed(() => {
  const matched = [...route.matched].reverse().find(r => r.meta?.tab);
  return (matched?.meta?.tab as string) || 'home';
});

const handleTabClick = (e: any) => {
  const btn = (e.currentTarget as HTMLElement);
  const tabValue = btn.getAttribute('value');

  if (!tabValue) return;

  const routeNames: Record<string, string> = {
    home: 'Home',
    market: 'Markets',
    alert: 'Rules',
    setting: 'Settings'
  };

  const targetName = routeNames[tabValue];
  if (targetName) {
    // 동일 라우터로 이동시 컴포넌트 재사용(Component Reuse)
    // console.log("Navigating to:", targetName);
    router.push({ name: targetName }).catch(() => {});
  }
};

const title = computed(() => {
  const t = route.meta.title
  return typeof t === "function" ? t(route) : t ?? ""
})

const goBack = () => {
  if (window.history.state?.back) {
    router.back()
    return
  }
  
  const fallback = route.meta.fallback
  if (fallback) {
    router.push(fallback)
  } else {
    router.push({ name: 'Home' })
  }
}

</script>

