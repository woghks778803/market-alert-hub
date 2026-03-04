<template>
  <CenterCardShell :center="true">
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
  </CenterCardShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import CenterCardShell from "@/components/CenterCardShell.vue"
import { mapOauthError } from "./oauthErrorMapper"

const router = useRouter()
const route = useRoute()

onMounted(() => {
    fetchError();
});

const errorMessage = ref("");

const fetchError = (() => {
  const getQueryString = (val: any) => Array.isArray(val) ? val[0] : (val ?? "");
  const code = getQueryString(route.query.code)
  const target = getQueryString(route.query.target)

  console.log({code, target})

  // const target = Array.isArray(route.query.target) 
  //   ? route.query.target[0] 
  //   : (route.query.target ?? "");

  const r = mapOauthError({code, target})
  if(r){
    errorMessage.value = r
    return
  }
})

function retry() {
  router.push({ name: "Login" }).catch(() => {})
}
</script>