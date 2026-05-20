<template>
  <v-dialog
    v-model="model"
    max-width="400"
    persistent
  >
    <v-card rounded="xl">
      <!-- 제목 -->
      <v-card-title class="text-h6 font-weight-bold">
        {{ title }}
      </v-card-title>

      <!-- 내용 -->
      <v-card-text
        class="text-body-2 text-medium-emphasis"
        style="white-space: pre-line; line-height: 1.6"
      >
        {{ message }}
      </v-card-text>

      <!-- 버튼 -->
      <v-card-actions class="justify-end">
        <v-btn
          variant="text"
          @click="onCancel"
        >
          {{ cancelText }}
        </v-btn>

        <v-btn
          :color="danger ? 'error' : 'primary'"
          :loading="loading"
          @click="onConfirm"
        >
          {{ confirmText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    isReady: boolean
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    danger?: boolean
    loading?: boolean
  }>(),
  {
    title: '확인',
    message: '',
    confirmText: '확인',
    cancelText: '취소',
    danger: false,
    loading: false,
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'confirm'): void
}>()

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

function onCancel() {
  model.value = false
}

const onConfirm = () => {
  emit('confirm')
}
</script>
