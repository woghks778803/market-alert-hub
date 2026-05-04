<template>
  <AppLoading
    :show="ruleAction.loading.value"
    overlay
  />

  <v-container
    class="rs-form-view pa-0"
    fluid
  >
    <div class="rs-form-page">
      <div class="rs-form-body">
        <section class="rs-section">
          <div class="rs-section-title">기본 정보</div>

          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            class="mb-4"
            density="compact"
          >
            {{ errorMessage }}
          </v-alert>

          <v-card
            class="rs-section-card"
            rounded="xl"
            elevation="0"
          >
            <v-card-text class="pa-4">
              <div class="rs-field-block">
                <div class="rs-field-label">알림 이름</div>
                <v-text-field
                  v-model="form.name"
                  variant="solo-filled"
                  flat
                  rounded="lg"
                  density="comfortable"
                  hide-details="auto"
                  placeholder="예: 비트코인 알림"
                  :error="!!fieldErrors.name"
                  :error-messages="fieldErrors.name ? [fieldErrors.name] : []"
                  @update:model-value="onInputChanged"
                  @blur="onBlurValidate"
                />
              </div>

              <div class="rs-field-block rs-search-block">
                <div class="rs-field-label">알림 대상</div>

                <v-text-field
                  :model-value="selectedSimpleMarketLabel"
                  readonly
                  label="선택된 알림 대상"
                  :error="!!fieldErrors.exchangeInstrumentId"
                  :error-messages="
                    fieldErrors.exchangeInstrumentId ? [fieldErrors.exchangeInstrumentId] : []
                  "
                />

                <v-text-field
                  v-model="simpleMarketListQuery.search"
                  placeholder="거래소 및 심볼 검색"
                  @update:model-value="onSimpleMarketSearchChanged"
                  @blur="onBlurValidate"
                />

                <div
                  v-if="isSimpleMarketOpen && simpleMarkets.length > 0"
                  class="rs-simple-market-dropdown"
                >
                  <div
                    v-for="item in simpleMarkets"
                    :key="item.exchangeInstrumentId"
                    class="rs-simple-market-item"
                    @click="onSimpleMarketSelected(item)"
                  >
                    {{ item.label }}
                  </div>
                </div>
              </div>

              <div class="rs-field-block">
                <div class="rs-field-label">알림 타입</div>
                <v-autocomplete
                  v-model="form.alertTypeId"
                  :items="alertTypes"
                  item-title="name"
                  item-value="id"
                  variant="solo-filled"
                  flat
                  rounded="lg"
                  density="comfortable"
                  hide-details="auto"
                  placeholder="알림 타입 선택"
                  no-data-text="선택 가능한 항목이 없습니다."
                  :error="!!fieldErrors.alertTypeId"
                  :error-messages="fieldErrors.alertTypeId ? [fieldErrors.alertTypeId] : []"
                  @update:model-value="onAlertTypeChanged"
                  @blur="onBlurValidate"
                />
              </div>
            </v-card-text>
          </v-card>
        </section>

        <section class="rs-section">
          <div class="rs-section-title">알림 조건</div>

          <v-card
            class="rs-section-card"
            rounded="xl"
            elevation="0"
          >
            <v-card-text class="pa-4">
              <ThresholdForm
                v-if="selectedAlertType?.formType === FormType.THRESHOLD"
                v-model="thresholdForm"
                :schema="selectedAlertType.paramSchema"
                :error="fieldErrors.params"
                @input="onInputChanged"
                @blur="onBlurValidate"
              />

              <CrossForm
                v-else-if="selectedAlertType?.formType === FormType.CROSS"
                v-model="crossForm"
                :schema="selectedAlertType.paramSchema"
                :error="fieldErrors.params"
                @input="onInputChanged"
                @blur="onBlurValidate"
              />

              <RangeForm
                v-else-if="selectedAlertType?.formType === FormType.RANGE"
                v-model="rangeForm"
                :schema="selectedAlertType.paramSchema"
                :error="fieldErrors.params"
                @input="onInputChanged"
                @blur="onBlurValidate"
              />

              <PercentForm
                v-else-if="selectedAlertType?.formType === FormType.PERCENT"
                v-model="percentForm"
                :schema="selectedAlertType.paramSchema"
                :error="fieldErrors.params"
                @input="onInputChanged"
                @blur="onBlurValidate"
              />

              <PatternForm
                v-else-if="selectedAlertType?.formType === FormType.PATTERN"
                v-model="patternForm"
                :schema="selectedAlertType.paramSchema"
                :error="fieldErrors.params"
                @input="onInputChanged"
                @blur="onBlurValidate"
              />

              <div
                v-else
                class="rs-empty-guide"
              >
                알림 타입을 선택하면 조건 입력 폼이 표시됩니다.
              </div>
            </v-card-text>
          </v-card>
        </section>

        <section class="rs-section">
          <div class="rs-section-title">발동 정책</div>

          <v-card
            class="rs-section-card"
            rounded="xl"
            elevation="0"
          >
            <v-card-text class="pa-4">
              <div class="rs-field-block">
                <v-checkbox
                  v-model="form.isOnce"
                  hide-details
                  density="comfortable"
                >
                  <template #label>
                    <div class="rs-checkbox-label-wrap">
                      <div class="rs-checkbox-title">1회 알림</div>
                      <div class="rs-checkbox-caption">조건 충족 시 한 번만 알림을 보냅니다</div>
                    </div>
                  </template>
                </v-checkbox>
              </div>

              <div class="rs-field-block">
                <div class="rs-field-label">재알림 간격</div>
                <v-select
                  v-model="form.throttleTimeframe"
                  :items="THROTTLE_TIMEFRAME_ITEMS"
                  variant="solo-filled"
                  flat
                  rounded="lg"
                  density="comfortable"
                  hide-details="auto"
                  :disabled="form.isOnce"
                />
              </div>
            </v-card-text>
          </v-card>
        </section>

        <section class="rs-section">
          <div class="rs-section-title">유효 기간</div>

          <v-card
            class="rs-section-card"
            rounded="xl"
            elevation="0"
          >
            <v-card-text class="pa-4">
              <div class="rs-field-block">
                <v-checkbox
                  v-model="form.useValidity"
                  hide-details
                  density="comfortable"
                >
                  <template #label>
                    <div class="rs-checkbox-label-wrap">
                      <div class="rs-checkbox-title">유효 기간 제한</div>
                      <div class="rs-checkbox-caption">특정 기간 동안만 알림이 동작합니다</div>
                    </div>
                  </template>
                </v-checkbox>
              </div>

              <div class="rs-field-block">
                <div class="rs-field-row">
                  <div class="rs-field-col">
                    <div class="rs-field-label">시작 일시</div>
                    <v-text-field
                      v-model="form.validFrom"
                      type="datetime-local"
                      variant="solo-filled"
                      flat
                      rounded="lg"
                      density="comfortable"
                      hide-details="auto"
                      :error="!!fieldErrors.validFrom"
                      :error-messages="fieldErrors.validFrom ? [fieldErrors.validFrom] : []"
                      :disabled="!form.useValidity"
                      @update:model-value="onInputChanged"
                      @blur="onBlurValidate"
                    />
                  </div>

                  <div class="rs-field-col">
                    <div class="rs-field-label">종료 일시</div>
                    <v-text-field
                      v-model="form.validTo"
                      type="datetime-local"
                      variant="solo-filled"
                      flat
                      rounded="lg"
                      density="comfortable"
                      hide-details="auto"
                      :error="!!fieldErrors.validTo"
                      :error-messages="fieldErrors.validTo ? [fieldErrors.validTo] : []"
                      :disabled="!form.useValidity"
                      @update:model-value="onInputChanged"
                      @blur="onBlurValidate"
                    />
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </section>
      </div>

      <footer class="rs-form-footer">
        <v-btn
          v-if="isEditMode"
          class="rs-submit-btn"
          color="primary"
          block
          size="x-large"
          rounded="xl"
          :disabled="!canSubmit || !ruleAction.isReady"
          @click="onUpdate"
        >
          {{ submitLabel }}
        </v-btn>

        <v-btn
          v-else
          class="rs-submit-btn"
          color="primary"
          block
          size="x-large"
          rounded="xl"
          :disabled="!canSubmit || !ruleAction.isReady"
          @click="onCreate"
        >
          {{ submitLabel }}
        </v-btn>
      </footer>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { onMounted, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { toast } from 'vue3-toastify'
import { storeToRefs } from 'pinia'

import AppLoading from '@/components/common/AppLoading.vue'
import ThresholdForm from '@/components/alert/forms/ThresholdForm.vue'
import CrossForm from '@/components/alert/forms/CrossForm.vue'
import RangeForm from '@/components/alert/forms/RangeForm.vue'
import PercentForm from '@/components/alert/forms/PercentForm.vue'
import PatternForm from '@/components/alert/forms/PatternForm.vue'

import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { useRuleForm } from '@/composables/alert/useRuleForm'
import { getChangeAlertError, getCreateAlertError } from '@/composables/error/alertError.message'

import { FormType, THROTTLE_TIMEFRAME_ITEMS } from '@/services/alert.types'
import type { SimpleMarketDto } from '@/services/market.types'
import { useAlertStore } from '@/stores/alert.store'
import { useMarketStore } from '@/stores/market.store'

const router = useRouter()
const route = useRoute()
const alertId = computed(() => {
  const value = route.params.alertId
  return typeof value === 'string' ? Number(value) : null
})
const isEditMode = computed(() => alertId.value !== null)

const marketStore = useMarketStore()
const alertStore = useAlertStore()
const { simpleMarkets, simpleMarketListQuery } = storeToRefs(marketStore)
const { alertTypes } = storeToRefs(alertStore)
const ruleAction = useAsyncAction()

const {
  form,
  thresholdForm,
  crossForm,
  rangeForm,
  percentForm,
  patternForm,

  fieldErrors,
  errorMessage,

  selectedAlertType,
  selectedSimpleMarketLabel,
  isSimpleMarketOpen,
  canSubmit,

  buildAlertSavePayload,
  applyAlertToForm,

  onAlertTypeChanged,
  onInputChanged,
  onBlurValidate,

  handleSubmit,
} = useRuleForm({ alertTypes })

onMounted(() => {
  ruleAction.run(async () => {
    await marketStore.fetchSimpleMarkets()
    await alertStore.fetchAlertTypes()

    if (isEditMode.value && alertId.value) {
      const alert = await alertStore.fetchAlert(alertId.value)
      applyAlertToForm(alert)
    }
  })
})

const submitLabel = computed(() => {
  if (!ruleAction.isReady) {
    return isEditMode.value ? '수정 중...' : '등록 중...'
  }

  return isEditMode.value ? '알림 수정' : '알림 생성'
})

async function onUpdate() {
  const id = alertId.value
  if (id === null) return

  try {
    await handleSubmit(async () => {
      await ruleAction.run(async () => {
        await alertStore.changeAlert(id, buildAlertSavePayload())
      })

      await nextTick()

      router.replace({ name: 'Rules' })

      setTimeout(() => {
        toast.success('알림이 수정되었습니다.', {
          toastId: 'alert-update-success',
        })
      }, 0)
    })
  } catch (err) {
    const result = getChangeAlertError(err)
    if(result){
      toast.error(result, {
        toastId: 'alert-update-failed',
      })
      return
    }
  }
}

async function onCreate() {
  try {
    await handleSubmit(async () => {
      await ruleAction.run(async () => {
        await alertStore.createAlert(buildAlertSavePayload())
      })

      await nextTick()

      router.replace({ name: 'Rules' })
      setTimeout(() => {
        toast.success('알림이 등록되었습니다.', {
          toastId: 'alert-create-success',
        })
      }, 0)
    })
  } catch (err) {
    const result = getCreateAlertError(err)
    if(result){
      toast.error(result, {
        toastId: 'alert-create-failed',
      })
      return
    }
  }
}

function onSimpleMarketSelected(item: SimpleMarketDto) {
  form.exchangeInstrumentId = item.exchangeInstrumentId
  selectedSimpleMarketLabel.value = item.label
  simpleMarketListQuery.value.search = ''
  simpleMarkets.value = []
  isSimpleMarketOpen.value = false
  onInputChanged()
}

function onSimpleMarketSearchChanged(value: string) {
  simpleMarketListQuery.value.search = value
  isSimpleMarketOpen.value = true
  marketStore.setSimpleMarketSearch(value)
}
</script>
