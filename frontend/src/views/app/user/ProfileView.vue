<template>
  <AppLoading
    :show="userAction.loading.value"
    overlay
  />

  <v-card
    rounded="xl"
    class="mb-4"
    elevation="1"
  >
    <v-card-text class="d-flex align-center">
      <v-avatar
        size="56"
        class="mr-4"
        color="grey-lighten-3"
      >
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

        <v-chip
          size="x-small"
          class="mt-1"
          color="grey"
          variant="tonal"
        >
          {{ me?.providerDisplayName }} 가입
        </v-chip>

        <div class="text-caption text-disabled mt-2">
          가입일 {{ me?.createdAt ? formatDate(me.createdAt) : '-' }} · 최근 로그인
          {{ me?.lastLoginAt ? formatDate(me.lastLoginAt) : '-' }}
        </div>
      </div>
    </v-card-text>

    <v-card-title>정보 수신 동의</v-card-title>
    <v-card-text>
      <div>
        <v-list>
          <v-list-item
            title="광고성 수신 동의"
            subtitle="이벤트 및 프로모션 등 광고성 정보"
          >
            <template #append>
              <v-switch
                v-if="me"
                :model-value="me.isMarketing"
                inset
                hide-details
                @update:model-value="userStore.setMarketing"
              />
            </template>
          </v-list-item>
        </v-list>
      </div>
    </v-card-text>

    <!-- <v-card-title>알림</v-card-title>
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
                inset
                hide-details
                @update:model-value="userStore.setQuietHours"
              />
            </template>
          </v-list-item>
        </v-list>
      </div>
    </v-card-text> -->

    <v-card-title>보안</v-card-title>

    <v-card-text>
      <!-- 보안 -->
      <div>
        <v-list>
          <v-list-item
            v-if="me?.providerCode === 'email'"
            title="비밀번호 변경"
            append-icon="mdi-chevron-right"
            @click="showPasswordDialog = true"
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
    :loading="userAction.loading.value"
    :is-ready="userAction.isReady.value"
    @confirm="handleDeactivate"
  />

  <PasswordChangeDialog
    v-model="showPasswordDialog"
    :loading="userAction.loading.value"
    :is-ready="userAction.isReady.value"
    @submit="handleChangePassword"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { storeToRefs } from 'pinia'

import AppLoading from '@/components/common/AppLoading.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

import PasswordChangeDialog from '@/components/user/PasswordChangeDialog.vue'

import type { SubmitPayload } from '@/composables/auth/useChangePasswordForm'
import { useAuthFlow } from '@/composables/auth/useAuthFlow'
import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { getChangePasswordError } from '@/composables/error/authError.message'

import { useUserStore } from '@/stores/user.store'
import { formatDate } from '@/utils/format'

const router = useRouter()
const userStore = useUserStore()
const { me } = storeToRefs(userStore)

const { deactivate, changePassword } = useAuthFlow()
const userAction = useAsyncAction()

const showConfirmDialog = ref(false)
const showPasswordDialog = ref(false)

onMounted(async () => {
  await userAction.run(async () => {
    await userStore.fetchMe()
  })
})

const handleDeactivate = async () => {
  await userAction.run(async () => {
    await deactivate()
    await nextTick()

    router.replace({ name: 'Login' })
    setTimeout(() => {
      toast.success(
        '회원 탈퇴 신청이 완료되었습니다. 계정은 30일 후 최종 삭제됩니다.',
        {
          toastId: 'account-deactivated',
        },
      )
    }, 0)
  })
}

const handleChangePassword = async ({ payload, onSuccess, onError }: SubmitPayload) => {
  try {
    await userAction.run(async () => {
      await changePassword(payload)
      showPasswordDialog.value = false
      await nextTick()

      router.replace({ name: 'Login' })
      setTimeout(() => {
        toast.success('비밀번호가 변경되었습니다. 다시 로그인해주세요.', {
          toastId: 'change-password-success',
        })
      }, 0)

      onSuccess()
    })
  } catch (err) {
    const result = getChangePasswordError(err)
    onError?.(result)
  }
}
</script>
