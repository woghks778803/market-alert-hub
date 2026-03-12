<template>
  <CenterCardShell :center="true">
    <template v-if="viewMode === 'default'">
      <div class="verify-cb-icon verify-cb-icon--processing">
        <v-progress-circular indeterminate size="56" width="5" color="primary" />
      </div>
      <div class="verify-cb-sub">인증 확인 중...</div>
    </template>
    <template v-else>
      <div class="sle-iconWrap">
        <div class="sle-iconCircle">
          <v-icon size="26" color="warning">mdi-alert</v-icon>
        </div>
      </div>
  
      <div class="sle-title">소셜 로그인에 실패했습니다</div>
      <div class="sle-desc">
        로그인 과정에서 문제가 발생했습니다.<br />
        잠시 후 다시 시도해주세요.
      </div>
  
      <div v-if="errorMessage" class="sle-chip">
        {{ errorMessage }}
      </div>
  
      <v-btn block size="large" class="sle-primary" color="primary" variant="flat" @click="retry">
        다시 로그인 시도
      </v-btn>
  
      <div class="sle-help">문제가 계속 발생하나요?</div>
    </template>
  </CenterCardShell>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import CenterCardShell from "@/components/CenterCardShell.vue"
import { mapOauthError } from "./oauthErrorMapper"
import { useMode } from "@/composables/common/useMode"
import { useAsyncAction } from "@/composables/common/useAsyncAction";
import { useAuthStore } from "@/stores/auth.store";

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore();
const { mode, setMode } = useMode()
const { run, errorMessage } = useAsyncAction()
const viewMode = computed(() => mode.value)

onMounted(() => {
    fetchParam();
});

// const errorMessage = ref("");

const fetchParam = (async () => {
  const getQueryString = (val: any) => Array.isArray(val) ? val[0] : (val ?? "");
  const code = getQueryString(route.query.code)
  const target = getQueryString(route.query.target)
  
    // const target = Array.isArray(route.query.target) 
    //   ? route.query.target[0] 
    //   : (route.query.target ?? "");

  console.log({code, target})

  if (code == "ok") {
    setMode("default")
    try{
      await run(async () => {
        await authStore.reissueAction()
        await router.replace({ name: "VerifyEmail" })
      })
    } catch (err: any){
      authStore.clearToken()
      router.replace({ name: "OauthCallback", query: { code: "internal_error" } })
    }
    
  }else {
    setMode("fail")
    const r = mapOauthError({code, target})
    if(r){
      errorMessage.value = r
      return
    }
  }
})

function retry() {
  router.push({ name: "Login" }).catch(() => {})
}
</script>