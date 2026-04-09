<template>
  <v-card rounded="xl" class="mb-4" elevation="1">
    <v-card-text class="d-flex align-center">
      <v-avatar size="56" class="mr-4" color="grey-lighten-3">
        <span class="text-subtitle-1 font-weight-bold">
          {{ me?.nickname?.charAt(0).toUpperCase() }}
        </span>
      </v-avatar>

      <div class="flex-grow-1">
        <div class="text-subtitle-1 font-weight-bold">
          {{ me?.nickname }}
        </div>

        <div class="text-body-2 text-medium-emphasis">
          {{ me?.email }}
        </div>

        <v-chip size="x-small" class="mt-1" color="grey" variant="tonal">
          {{ me?.providerDisplayName }} 가입
        </v-chip>
        
        <div class="text-caption text-disabled mt-2">
          가입일 {{ me?.createdAt ? formatDate(me.createdAt) : "-" }} ·
          최근 로그인 {{ me?.lastLoginAt ? formatDate(me.lastLoginAt) : "-" }}
        </div>
      </div>
    </v-card-text>
    
    <v-card-title>정보 수신 동의</v-card-title>
    <v-card-text>
      <div>
        <v-list>
          <v-list-item 
            title="마케팅 수신 동의"
            subtitle="이벤트 및 프로모션 등 광고성 정보"
          >
            <template #append>
              <v-switch
                v-if="me"
                :model-value="me.isMarketing"
                @update:model-value="userStore.setMarketing"
                inset
                hide-details
              />
            </template>
          </v-list-item>
        </v-list>
      </div>
    </v-card-text>

    <v-card-title>알림</v-card-title>
    <v-card-text>
      <div>
        <v-list>
          <v-list-item 
            title="야간 알림 설정"
            subtitle="23:00 ~ 08:00 알림을 허용"
          >
            <template #append>
              <v-switch
                v-if="me"
                :model-value="me.isQuietHours"
                @update:model-value="userStore.setQuietHours"
                inset
                hide-details
              />
            </template>
          </v-list-item>

        </v-list>
      </div>
    </v-card-text>

    <v-card-title>보안</v-card-title>

    <v-card-text>
      <!-- 보안 -->
      <div>
        <v-list>
          <v-list-item 
            v-if="me?.providerCode === 'email'"
            title="비밀번호 변경" 
            append-icon="mdi-chevron-right"
            @click="showPasswordDialog  = true" 
          />
          <v-list-item
            v-if="me?.providerCode !== 'email'"
            title="카카오 계정으로 가입된 사용자입니다"
            subtitle="비밀번호 변경은 지원되지 않습니다"
            disabled
          />
          <v-divider class="my-2" />

          <v-list-item
            title="회원탈퇴"
            class="text-error"
            @click="showConfirmDialog = true"
          />
        </v-list>
      </div>
    </v-card-text>
  </v-card>

<ConfirmDialog
  v-model="showConfirmDialog"
  title="회원 탈퇴"
  :message="`
  정말로 회원 탈퇴하시겠습니까?

  탈퇴 시 계정 정보는 삭제되며,
  30일 동안 동일 계정으로 재가입할 수 없습니다.

  이 작업은 되돌릴 수 없습니다.
  `"
  confirm-text="탈퇴"
  cancel-text="취소"
  danger
  :loading="loading"
  :is-ready="isReady"
  @confirm="handleDeactivate"
/>

<PasswordChangeDialog
  v-model="showPasswordDialog"
  :loading="loading"
  :is-ready="isReady"
  @submit="handleChangePassword"
/>

</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import PasswordChangeDialog from '@/components/common/PasswordChangeDialog.vue'
import type { SubmitPayload } from "@/components/common/PasswordChangeDialog.vue"
import { toast } from 'vue3-toastify'
import { ref, onMounted, nextTick } from "vue";
import { storeToRefs } from "pinia"
import { useRouter } from "vue-router"
import { useUserStore } from "@/stores/user.store"
import { formatDate } from "@/utils/format"
import { useAuthFlow } from "@/composables/auth/useAuthFlow"
import { useAsyncAction } from "@/composables/common/useAsyncAction";
import { mapCommonError } from "@/composables/error/error.mapper"
import { mapChangePasswordError } from "@/composables/error/changePasswordError.mapper"

const router = useRouter()
const userStore = useUserStore()
const { me } = storeToRefs(userStore)
const { run, loading, isReady } = useAsyncAction()
const { deactivate, changePassword } = useAuthFlow()

const showConfirmDialog = ref(false)
const showPasswordDialog = ref(false)

async function handleDeactivate() {
  try {
    await run(async () => {
      await deactivate() 
      router.replace({ name: "Login" })
    })
  } catch (err: any) {
    // 에러 처리
  }
}

async function handleChangePassword({ payload, onSuccess, onError }: SubmitPayload) {
  try {
    await run(async () => {
      await changePassword(payload)
      showPasswordDialog.value = false
      await nextTick()

      router.replace({ name: "Login" })
      setTimeout(() => {
        toast.success("비밀번호가 변경되었습니다. 다시 로그인해주세요.")
      }, 0)
    })
  } catch (err: any) {
    console.error("change password error:", err);
    const apiError = err?.response?.data?.error;

    const r = mapChangePasswordError(apiError)
    if(r){
      onError?.(r)
      return 
    }

    const commonMessage = mapCommonError(apiError)
    if (commonMessage) {
      onError?.(commonMessage)
      return
    }
  }
}

onMounted(async () => {
  await userStore.fetchMe()
});

</script>