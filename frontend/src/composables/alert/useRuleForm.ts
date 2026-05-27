import { computed, reactive, ref, type Ref } from 'vue'

import { toNumberOrNull } from '@/utils/numbers'
import { minLength, maxLength } from '@/utils/validate'
import { FormType, ThrottleTimeframe, AlertStatus } from '@/services/alert.types'
import type {
  AlertSaveQuery,
  AlertDto,
  AlertTypeDto,
  ThresholdFormValue,
  CrossFormValue,
  RangeFormValue,
  PercentFormValue,
  PatternFormValue,
} from '@/services/alert.types'

type RuleFormFields = {
  name: string
  exchangeInstrumentId: number | null
  alertTypeId: number | null
  isOnce: boolean
  throttleTimeframe: ThrottleTimeframe
  useValidity: boolean
  validFrom: string
  validTo: string
  status: AlertStatus
  timezone: string
}

type RuleFieldErrors = {
  name: string | null
  exchangeInstrumentId: string | null
  alertTypeId: string | null
  validFrom: string | null
  validTo: string | null
  params: Record<string, string> | null
}

export type UseRuleFormParams = {
  alertTypes: Ref<AlertTypeDto[]>
  initialFields?: Partial<RuleFormFields>
}

function emptyErrors(): RuleFieldErrors {
  return {
    name: null,
    exchangeInstrumentId: null,
    alertTypeId: null,
    validFrom: null,
    validTo: null,
    params: null,
  }
}

function hasAnyError(errors: RuleFieldErrors): boolean {
  return !!(
    errors.name ||
    errors.exchangeInstrumentId ||
    errors.alertTypeId ||
    errors.validFrom ||
    errors.validTo ||
    errors.params
  )
}

export function useRuleForm(params: UseRuleFormParams) {
  const { alertTypes, initialFields } = params

  const errorMessage = ref<string | null>(null)
  const isSimpleMarketOpen = ref(false)

  const form = reactive<RuleFormFields>({
    name: initialFields?.name ?? '',
    exchangeInstrumentId: initialFields?.exchangeInstrumentId ?? null,
    alertTypeId: initialFields?.alertTypeId ?? null,
    isOnce: initialFields?.isOnce ?? true,
    throttleTimeframe: initialFields?.throttleTimeframe ?? ThrottleTimeframe.MIN_5,
    useValidity: initialFields?.useValidity ?? false,
    validFrom: initialFields?.validFrom ?? '',
    validTo: initialFields?.validTo ?? '',
    status: initialFields?.status ?? AlertStatus.ACTIVE,
    timezone: initialFields?.timezone ?? 'UTC',
  })

  const thresholdForm = ref<ThresholdFormValue>({
    threshold: '',
  })

  const crossForm = ref<CrossFormValue>({
    threshold: '',
    confirmBars: 1,
  })

  const rangeForm = ref<RangeFormValue>({
    minValue: '',
    maxValue: '',
  })

  const percentForm = ref<PercentFormValue>({
    percent: '',
  })

  const patternForm = ref<PatternFormValue>({
    pattern: '',
    period: '',
  })

  const fieldErrors = ref<RuleFieldErrors>(emptyErrors())

  const selectedAlertType = computed(() => {
    return alertTypes.value.find((item) => item.id === form.alertTypeId) ?? null
  })

  const selectedSimpleMarketLabel = ref<string | null>(null)

  function buildParams() {
    const alertType = selectedAlertType.value
    if (!alertType) return {}

    switch (alertType.formType) {
      case FormType.THRESHOLD:
        return {
          threshold: toNumberOrNull(thresholdForm.value.threshold),
        }

      case FormType.CROSS:
        return {
          threshold: toNumberOrNull(crossForm.value.threshold),
          confirmBars: crossForm.value.confirmBars,
        }

      case FormType.RANGE:
        return {
          minValue: toNumberOrNull(rangeForm.value.minValue),
          maxValue: toNumberOrNull(rangeForm.value.maxValue),
        }

      case FormType.PERCENT:
        return {
          percent: toNumberOrNull(percentForm.value.percent),
        }

      case FormType.PATTERN:
        return {
          pattern: patternForm.value.pattern,
          period: toNumberOrNull(patternForm.value.period),
        }

      default:
        return {}
    }
  }

  function isParamsValid(): boolean {
    return validateParams() === null
  }

  const canSubmit = computed(() => {
    if (!form.name.trim() || !minLength(form.name, 4) || !maxLength(form.name, 40)) return false
    if (!form.exchangeInstrumentId) return false
    if (form.useValidity && (!form.validFrom || !form.validTo)) return false
    if (!selectedAlertType.value) return false
    if (!isParamsValid()) return false

    return true
  })

  function validateParams(): Record<string, string> | null {
    const alertType = selectedAlertType.value

    switch (alertType?.formType) {
      case FormType.THRESHOLD: {
        const errors: Record<string, string> = {}
        const value = toNumberOrNull(thresholdForm.value.threshold)
        if (value === null) {
          errors.threshold = '기준값을 입력해주세요.'
          return Object.keys(errors).length ? errors : null
        }

        if (value < 0) {
          errors.threshold = '0 이상 입력해주세요.'
        }

        return Object.keys(errors).length ? errors : null
      }

      case FormType.CROSS: {
        const errors: Record<string, string> = {}
        if (toNumberOrNull(crossForm.value.threshold) === null) {
          errors.threshold = '기준값을 입력해주세요.'
        }

        if (crossForm.value.confirmBars <= 0) {
          errors.confirmBars = '확인 캔들 수를 선택해주세요.'
        }
        return Object.keys(errors).length ? errors : null
      }

      case FormType.RANGE: {
        const errors: Record<string, string> = {}
        const minValue = toNumberOrNull(rangeForm.value.minValue)
        const maxValue = toNumberOrNull(rangeForm.value.maxValue)

        if (minValue === null) {
          errors.minValue = '최소값을 입력해주세요.'
        }

        if (maxValue === null) {
          errors.maxValue = '최대값을 입력해주세요.'
        }

        if (minValue !== null && maxValue !== null && minValue > maxValue) {
          errors.minValue = '최소값은 최대값보다 클 수 없습니다.'
        }
        return Object.keys(errors).length ? errors : null
      }

      case FormType.PERCENT: {
        const errors: Record<string, string> = {}
        if (toNumberOrNull(percentForm.value.percent) === null) {
          errors.percent = '변동률을 입력해주세요.'
        }
        return Object.keys(errors).length ? errors : null
      }

      case FormType.PATTERN: {
        const errors: Record<string, string> = {}
        if (!patternForm.value.pattern.trim()) {
          errors.pattern = '패턴을 선택해주세요.'
        }
        const period = toNumberOrNull(patternForm.value.period)

        if (period === null || period <= 0) {
          errors.period = '기간은 1 이상이어야 합니다.'
        }
        return Object.keys(errors).length ? errors : null
      }

      default: {
        const errors: Record<string, string> = {}
        return Object.keys(errors).length ? errors : null
      }
    }
  }

  function validate(): boolean {
    const errors = emptyErrors()

    if (!form.name.trim()) {
      errors.name = '알림 이름을 입력해주세요.'
    } else if (!minLength(form.name, 4) || !maxLength(form.name, 40)) {
      errors.name = '알림 이름은 4자이상 40자 이하로 입력해주세요.'
    }

    if (!form.exchangeInstrumentId) {
      errors.exchangeInstrumentId = '알림 대상을 선택해주세요.'
    }

    if (!form.alertTypeId) {
      errors.alertTypeId = '알림 타입을 선택해주세요.'
    }

    if (form.useValidity) {
      if (!form.validFrom) {
        errors.validFrom = '시작 일시를 입력해주세요.'
      }

      if (!form.validTo) {
        errors.validTo = '종료 일시를 입력해주세요.'
      }

      if (form.validFrom && form.validTo) {
        const fromTime = new Date(form.validFrom).getTime()
        const toTime = new Date(form.validTo).getTime()

        if (fromTime >= toTime) {
          errors.validTo = '종료 일시는 시작 일시보다 늦어야 합니다.'
        }
      }
    }

    if (!errors.alertTypeId) {
      errors.params = validateParams()
    }

    fieldErrors.value = errors
    return !hasAnyError(errors)
  }

  function resetAlertTypeForms() {
    thresholdForm.value.threshold = ''

    crossForm.value.threshold = ''
    crossForm.value.confirmBars = 1

    rangeForm.value.minValue = ''
    rangeForm.value.maxValue = ''

    percentForm.value.percent = ''

    patternForm.value.pattern = ''
    patternForm.value.period = ''
  }

  const buildAlertSavePayload = (): AlertSaveQuery => {
    if (form.alertTypeId === null) {
      throw new Error('alert_type_required')
    }

    return {
      name: form.name,
      exchangeInstrumentId: form.exchangeInstrumentId,
      alertTypeId: form.alertTypeId,

      isOnce: form.isOnce,
      status: form.status,

      throttleTimeframe: form.throttleTimeframe,
      timezone: form.timezone,

      useValidity: form.useValidity,
      validFrom: form.useValidity ? form.validFrom : null,
      validTo: form.useValidity ? form.validTo : null,

      params: buildParams(),
    }
  }

  function applyAlertToForm(alert: AlertDto) {
    form.name = alert.name
    form.exchangeInstrumentId = alert.exchangeInstrumentId
    form.alertTypeId = alert.alertTypeId
    form.isOnce = alert.isOnce
    form.status = alert.status
    form.timezone = alert.timezone

    form.throttleTimeframe = toThrottleTimeframe(alert.throttleSeconds)

    form.useValidity = alert.validFrom !== '' || alert.validTo !== ''
    form.validFrom = alert.validFrom ?? ''
    form.validTo = alert.validTo ?? ''

    selectedSimpleMarketLabel.value = `${alert.exchangeName} · ${alert.exchangeSymbol}`

    const alertType = alertTypes.value.find((item) => item.id === alert.alertTypeId)
    if (!alertType) return

    applyParamsToConditionForm(alert.params, alertType.formType)
  }

  function applyParamsToConditionForm(params: Record<string, unknown>, formType: FormType) {
    switch (formType) {
      case FormType.THRESHOLD:
        thresholdForm.value.threshold =
          params.threshold !== undefined && params.threshold !== null
            ? String(params.threshold)
            : ''
        return

      case FormType.CROSS:
        crossForm.value.threshold =
          params.threshold !== undefined && params.threshold !== null
            ? String(params.threshold)
            : ''

        crossForm.value.confirmBars =
          typeof params.confirmBars === 'number'
            ? params.confirmBars
            : Number(params.confirmBars ?? 1)

        return

      case FormType.RANGE:
        rangeForm.value.minValue =
          params.minValue !== undefined && params.minValue !== null ? String(params.minValue) : ''

        rangeForm.value.maxValue =
          params.maxValue !== undefined && params.maxValue !== null ? String(params.maxValue) : ''

        return

      case FormType.PERCENT:
        percentForm.value.percent =
          params.percent !== undefined && params.percent !== null ? String(params.percent) : ''

        return

      case FormType.PATTERN:
        patternForm.value.pattern = typeof params.pattern === 'string' ? params.pattern : ''

        patternForm.value.period =
          params.period !== undefined && params.period !== null ? String(params.period) : ''

        return

      default:
        return
    }
  }

  function toThrottleTimeframe(seconds: number): ThrottleTimeframe {
    if (seconds === 300) return ThrottleTimeframe.MIN_5
    if (seconds === 600) return ThrottleTimeframe.MIN_10
    if (seconds === 1800) return ThrottleTimeframe.MIN_30
    if (seconds === 3600) return ThrottleTimeframe.HOUR_1
    if (seconds === 10800) return ThrottleTimeframe.HOUR_3
    if (seconds === 21600) return ThrottleTimeframe.HOUR_6
    if (seconds === 43200) return ThrottleTimeframe.HOUR_12
    if (seconds === 86400) return ThrottleTimeframe.DAY_1

    return ThrottleTimeframe.MIN_5
  }

  function onInputChanged(): void {
    fieldErrors.value = emptyErrors()
    errorMessage.value = null
  }

  function onAlertTypeChanged(): void {
    resetAlertTypeForms()
    onInputChanged()

    fieldErrors.value.params = validateParams()
  }

  function onBlurValidate() {
    validate()
  }

  async function handleSubmit(onSuccess: () => Promise<void> | void): Promise<void> {
    if (!canSubmit.value) return

    fieldErrors.value = emptyErrors()
    errorMessage.value = null

    if (!validate()) return

    await onSuccess()
  }

  return {
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

    buildParams,
    buildAlertSavePayload,
    applyAlertToForm,

    validate,

    onAlertTypeChanged,
    onInputChanged,
    onBlurValidate,

    handleSubmit,
  }
}
