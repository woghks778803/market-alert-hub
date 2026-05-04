<template>
  <div class="app-container">
    <div class="app-title">디스플레이</div>

    <v-list
      class="app-card"
      density="comfortable"
    >
      <!-- 화면 테마 -->
      <v-list-item title="화면 테마">
        <template #append>
          <v-select
            :model-value="theme"
            :items="themeItems"
            density="compact"
            variant="outlined"
            hide-details
            style="width: 120px"
            @update:model-value="onChangeTheme"
          />
        </template>
      </v-list-item>
    </v-list>
  </div>

  <div class="app-container">
    <div class="app-title">디바이스</div>

    <v-list
      class="app-card"
      density="comfortable"
    >
      <!-- 화면 꺼짐 방지 -->
      <v-list-item title="화면 꺼짐 방지">
        <template #append>
          <v-switch
            :model-value="keepScreenOn"
            inset
            hide-details
            @update:model-value="onChangeKeepScreenOn"
          />
        </template>
      </v-list-item>

      <v-divider />

      <!-- 진동 -->
      <v-list-item title="진동">
        <template #append>
          <v-switch
            :model-value="vibration"
            inset
            hide-details
            @update:model-value="onChangeVibration"
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
import { ref } from 'vue'
import { useAppSettings, ThemeMode } from '@/composables/common/useAppSettings'

const {
  ThemeLabel,
  getSavedTheme,
  getSavedKeepScreenOnEnabled,
  getSavedVibrateEnabled,
  applyTheme,
  applyKeepScreenOn,
  applyVibrate,
} = useAppSettings()

const theme = ref(getSavedTheme())
const keepScreenOn = ref(getSavedKeepScreenOnEnabled())
const vibration = ref(getSavedVibrateEnabled())
const push = ref(false)

const themeItems = Object.values(ThemeMode).map((value) => ({
  title: ThemeLabel[value],
  value,
}))

function onChangeTheme(val: ThemeMode) {
  if (val == null) return
  theme.value = val
  applyTheme(val)
}

function onChangeKeepScreenOn(val: boolean | null) {
  if (val == null) return
  keepScreenOn.value = val
  applyKeepScreenOn(val)
}

function onChangeVibration(val: boolean | null) {
  if (val == null) return
  vibration.value = val
  applyVibrate(val)
}
</script>
