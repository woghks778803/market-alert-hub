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
    <div class="app-title">알림</div>

    <v-list
      class="app-card"
      density="comfortable"
    >
      <!-- 알림 사운드 -->
      <v-list-item title="알림 사운드">
        <template #append>
          <v-select
            :model-value="notificationSound"
            :items="soundItems"
            density="compact"
            variant="outlined"
            hide-details
            style="width: 120px"
            @update:model-value="onChangeNotificationSound"
          />
        </template>
      </v-list-item>

      <!-- <v-divider /> -->
      <!-- 진동 -->
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

      <!-- <v-divider /> -->

    </v-list>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAppSettings, ThemeMode, SoundMode } from '@/composables/common/useAppSettings'

const {
  ThemeLabel,
  NotificationSoundLabel,
  getSavedTheme,
  getSavedKeepScreenOnEnabled,
  getSavedNotificationSound,
  applyTheme,
  applyKeepScreenOn,
  applyNotificationSound,
} = useAppSettings()

const theme = ref(getSavedTheme())
const keepScreenOn = ref(getSavedKeepScreenOnEnabled())
const notificationSound = ref(getSavedNotificationSound())

const themeItems = Object.values(ThemeMode).map((value) => ({
  title: ThemeLabel[value],
  value,
}))

const soundItems = Object.values(SoundMode).map((value) => ({
  title: NotificationSoundLabel[value],
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

function onChangeNotificationSound(val: SoundMode) {
  if (val == null) return
  notificationSound.value = val
  applyNotificationSound(val)
}
</script>
