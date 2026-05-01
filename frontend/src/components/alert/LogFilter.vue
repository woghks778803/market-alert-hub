<template>
    <div class="alert-filter">
        <v-select
            :model-value="status"
            :items="statusItems"
            label="상태"
            variant="outlined"
            density="comfortable"
            hide-details
            @update:model-value="onChangeStatus"
        />
    </div>
</template>

<script setup lang="ts">
import {
  AlertEventStatusFilter,
  AlertEventStatusFilterLabel,
} from "@/services/alert.types"

defineProps<{
  status: AlertEventStatusFilter
}>()

const emit = defineEmits<{
  (e: "changeStatus", value: AlertEventStatusFilter): void
}>()

const statusItems = Object.values(AlertEventStatusFilter).map((value) => ({
  title: AlertEventStatusFilterLabel[value],
  value,
}))

const onChangeStatus = (value: AlertEventStatusFilter) => {
  emit("changeStatus", value)
}
</script>