<template>
  <v-card rounded="lg" variant="flat" class="mb-4">
    <v-card-title>계정</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item
          title="내정보"
          subtitle="프로필 / 로그인 수단"
          append-icon="mdi-chevron-right"
          :to="{ name: 'Profile' }"
        />
      </v-list>
    </v-card-text>
  </v-card>

  <v-card rounded="lg" variant="flat" class="mb-4">
    <v-card-title>알림</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item
          title="채널 관리"
          subtitle="텔레그램 / FCM"
          append-icon="mdi-chevron-right"
          :to="{ name: 'Alerts' }"
        />
      </v-list>
    </v-card-text>
  </v-card>

  <v-card rounded="lg" variant="flat">
    <v-card-title>기타</v-card-title>
    <v-card-text class="pt-0">
      <v-list lines="one">
        <v-list-item title="버전" subtitle="0.0.0" />
      </v-list>

      <v-btn class="mt-3" block variant="tonal" color="error" @click="goLogin">
        로그아웃
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth.store"

const router = useRouter()
const authStore = useAuthStore()

async function goLogin() {
  await authStore.logoutAction() 
  router.replace({ name: "Login" })
}
</script>
