<template>
  <div class="app-container">
    <div class="app-title">디스플레이</div>

    <v-list class="app-card" density="comfortable">
      <!-- 화면 테마 -->
      <v-list-item title="화면 테마">
        <template #append>
          <v-select
            v-model="theme"
            :items="themeItems"
            density="compact"
            variant="outlined"
            hide-details
            style="width: 120px"
          />
        </template>
      </v-list-item>

    </v-list>
  </div>

  <div class="app-container">
    <div class="app-title">디바이스</div>

    <v-list class="app-card" density="comfortable">
      <!-- 화면 꺼짐 방지 -->
      <v-list-item title="화면 꺼짐 방지">
        <template #append>
          <v-switch
            v-model="keepScreenOn"
            inset
            hide-details
          />
        </template>
      </v-list-item>

      <v-divider />

      <!-- 진동 -->
      <v-list-item title="진동">
        <template #append>
          <v-switch
            v-model="vibration"
            inset
            hide-details
          />
        </template>
      </v-list-item>

      <!-- 푸쉬 알림 -->
      <v-list-item title="푸쉬 알림">
        <template #append>
          <v-switch
            v-model="push"
            inset
            hide-details
          />
        </template>
      </v-list-item>
    </v-list>
  </div>

</template>

<script setup lang="ts">
import { ref } from "vue"

const theme = ref("system")
const keepScreenOn = ref(false)
const vibration = ref(true)
const push = ref(true)

const themeItems = [
  { title: "시스템", value: "system" },
  { title: "라이트", value: "light" },
  { title: "다크", value: "dark" },
]
</script>

<style scoped>
.app-title {
  font-weight: 800;
  font-size: 18px;
  margin-bottom: 12px;
}
</style>