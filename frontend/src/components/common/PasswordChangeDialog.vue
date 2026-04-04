<template>
  <v-dialog v-model="model" max-width="420">
    <v-card rounded="xl">
      <v-card-title class="text-subtitle-1 font-weight-bold">
        비밀번호 변경
      </v-card-title>

      <v-card-text>
        <v-text-field
          v-model="fields.currentPassword"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
          placeholder="비밀번호를 입력하세요"
          :type="showPasswordCurrent ? 'text' : 'password'"
          label="현재 비밀번호"
          variant="outlined"
          density="comfortable"
          class="mb-3"
          :append-inner-icon="showPasswordCurrent ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
          @click:append-inner="showPasswordCurrent = !showPasswordCurrent"
          :error="!!fieldErrors.currentPassword"
          :error-messages="fieldErrors.currentPassword ? [fieldErrors.currentPassword] : []"
        />

        <v-text-field
          v-model="fields.newPassword"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
          placeholder="비밀번호를 입력하세요"
          :type="showPassword ? 'text' : 'password'"
          label="새 비밀번호"
          variant="outlined"
          density="comfortable"
          class="mb-3"
          :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
          @click:append-inner="showPassword = !showPassword"
          :error="!!fieldErrors.newPassword"
          :error-messages="fieldErrors.newPassword ? [fieldErrors.newPassword] : []"
        />

        <v-text-field
          v-model="fields.confirmPassword"
          @update:model-value="onInputChanged"
          @blur="onBlurValidate"
          placeholder="비밀번호를 입력하세요"
          :type="showPasswordConfirm ? 'text' : 'password'"
          label="새 비밀번호 확인"
          variant="outlined"
          density="comfortable"
          :append-inner-icon="showPasswordConfirm ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
          @click:append-inner="showPasswordConfirm = !showPasswordConfirm"
          :error="!!fieldErrors.confirmPassword"
          :error-messages="fieldErrors.confirmPassword ? [fieldErrors.confirmPassword] : []"
        />

        <div v-if="errorMessage" class="text-error text-caption mt-2">
          {{ errorMessage }}
        </div>
      </v-card-text>

      <v-card-actions class="justify-end">
        <v-spacer />

        <v-btn variant="text" @click="onCancel">
          취소
        </v-btn>

        <v-btn color="primary" :loading="loading" :disabled="!canSubmit || !isReady" @click="onSubmit">
          변경
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { watch, computed } from "vue"
import { useChangePasswordForm } from "@/composables/auth/useChangePasswordForm"

const {
  fields,

  fieldErrors,
  errorMessage,
  showPasswordCurrent,
  showPassword,
  showPasswordConfirm,

  canSubmit,
  handleSubmit,

  reset,
  onInputChanged,
  onBlurValidate,
} = useChangePasswordForm()

const props = withDefaults(defineProps<{
  modelValue: boolean,
  loading: boolean,
  isReady: boolean
}>(), {
  loading: false
})

const emit = defineEmits<{
  (e: "update:modelValue", v: boolean): void
  (e: "submit", payload: SubmitPayload): void
}>()

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
})

function onCancel() {
  model.value = false
}

watch(
  () => props.modelValue,
  (v) => {
    if (!v) reset()
  }
)

async function onSubmit() {
  await handleSubmit(() => {
    emit("submit", {
      payload: {
        currentPassword: fields.value.currentPassword,
        newPassword: fields.value.newPassword
      },
      onSuccess: () => {
      },
      onError: (msg: string) => {
        errorMessage.value = msg
      }
    })
  })
}

export type SubmitPayload = {
  payload: {
    currentPassword: string
    newPassword: string
  }
  onSuccess: () => void
  onError: (msg: string) => void
}
</script>