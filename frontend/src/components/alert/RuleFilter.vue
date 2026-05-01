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

        <v-select
            :model-value="sort"
            :items="sortItems"
            label="정렬"
            variant="outlined"
            density="comfortable"
            hide-details
            @update:model-value="onChangeSort"
        />
    </div>
</template>

<script setup lang="ts">
import {
  AlertSort,
  AlertSortLabel,
  AlertStatusFilter,
  AlertStatusFilterLabel,
} from "@/services/alert.types"

defineProps<{
  status: AlertStatusFilter
  sort: AlertSort
}>()

const emit = defineEmits<{
  (e: "changeStatus", value: AlertStatusFilter): void
  (e: "changeSort", value: AlertSort): void
}>()

const statusItems = Object.values(AlertStatusFilter).map((value) => ({
  title: AlertStatusFilterLabel[value],
  value,
}))

const sortItems = Object.values(AlertSort).map((value) => ({
  title: AlertSortLabel[value],
  value,
}))

const onChangeStatus = (value: AlertStatusFilter) => {
  emit("changeStatus", value)
}

const onChangeSort = (value: AlertSort) => {
  emit("changeSort", value)
}
</script>