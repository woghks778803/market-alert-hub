<template>
  <AppCenterCard :center="true">
    <template v-if="viewMode === 'default'">
      <div class="verify-cb-icon verify-cb-icon--processing">
        <v-progress-circular
          indeterminate
          size="56"
          width="5"
          color="primary"
        />
      </div>
      <div class="verify-cb-sub">인증 확인 중...</div>
    </template>
    <template v-else>
      <div class="sle-iconWrap">
        <div class="sle-iconCircle">
          <v-icon
            size="26"
            color="warning"
            >mdi-alert</v-icon
          >
        </div>
      </div>

      <div class="sle-title">소셜 로그인에 실패했습니다</div>
      <div class="sle-desc">
        로그인 과정에서 문제가 발생했습니다.<br />
        잠시 후 다시 시도해주세요.
      </div>

      <div
        v-if="errorMessage"
        class="sle-chip"
      >
        {{ errorMessage }}
      </div>

      <v-btn
        block
        size="large"
        class="sle-primary"
        color="primary"
        variant="flat"
        @click="retry"
      >
        다시 로그인 시도
      </v-btn>

      <div class="sle-help">문제가 계속 발생하나요?</div>
    </template>
  </AppCenterCard>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter, type LocationQueryValue } from 'vue-router'
import AppCenterCard from '@/components/common/AppCenterCard.vue'
import { getOauthError } from '@/composables/error/authError.message'
import { useMode } from '@/composables/common/useMode'

const router = useRouter()
const route = useRoute()
const { mode, setMode } = useMode()
const viewMode = computed(() => mode.value)
const errorMessage = ref<string | null>(null)

onMounted(() => {
  fetchParam()
})

const fetchParam = async () => {
  const getQueryString = (val: LocationQueryValue | LocationQueryValue[] | undefined): string => (Array.isArray(val) ? (val[0] ?? '') : (val ?? ''))
  const code = getQueryString(route.query.code)
  const target = getQueryString(route.query.target)

  setMode('fail')
  const result = getOauthError({ code, target })
  errorMessage.value = result
}

function retry() {
  router.push({ name: 'Login' }).catch(() => {})
}
</script>
