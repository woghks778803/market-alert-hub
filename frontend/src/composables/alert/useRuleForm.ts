import { computed, reactive, ref, type Ref } from 'vue'

import { toNumberOrNull } from '@/utils/numbers'
import {
    FormType,
    ThrottleTimeframe,
    AlertScope,
    AlertStatus
} from '@/services/alert.types'
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
    scope: AlertScope
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
        scope: initialFields?.scope ?? AlertScope.SINGLE,
        timezone: initialFields?.timezone ?? 'UTC',
    })

    const thresholdForm = reactive<ThresholdFormValue>({
        threshold: '',
    })

    const crossForm = reactive<CrossFormValue>({
        threshold: '',
        confirmBars: 1,
    })

    const rangeForm = reactive<RangeFormValue>({
        minValue: '',
        maxValue: '',
    })

    const percentForm = reactive<PercentFormValue>({
        percent: '',
    })

    const patternForm = reactive<PatternFormValue>({
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
                    threshold: toNumberOrNull(thresholdForm.threshold),
                }

            case FormType.CROSS:
                return {
                    threshold: toNumberOrNull(crossForm.threshold),
                    confirmBars: crossForm.confirmBars,
                }

            case FormType.RANGE:
                return {
                    minValue: toNumberOrNull(rangeForm.minValue),
                    maxValue: toNumberOrNull(rangeForm.maxValue),
                }

            case FormType.PERCENT:
                return {
                    percent: toNumberOrNull(percentForm.percent),
                }

            case FormType.PATTERN:
                return {
                    pattern: patternForm.pattern,
                    period: toNumberOrNull(patternForm.period),
                }

            default:
                return {}
        }
    }

    function isParamsValid(): boolean {
        return validateParams() === null
    }

    const canSubmit = computed(() => {
        if (!form.name.trim()) return false
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
                const value = toNumberOrNull(thresholdForm.threshold)
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
                if (toNumberOrNull(crossForm.threshold) === null) {
                    errors.threshold = '기준값을 입력해주세요.'
                }

                if (crossForm.confirmBars <= 0) {
                    errors.confirmBars = '확인 캔들 수를 선택해주세요.'
                }
                return Object.keys(errors).length ? errors : null
            }

            case FormType.RANGE: {
                const errors: Record<string, string> = {}
                const minValue = toNumberOrNull(rangeForm.minValue)
                const maxValue = toNumberOrNull(rangeForm.maxValue)

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
                console.log("percentForm", percentForm)
                const errors: Record<string, string> = {}
                if (toNumberOrNull(percentForm.percent) === null) {
                    errors.percent = '변동률을 입력해주세요.'
                }
                return Object.keys(errors).length ? errors : null
            }

            case FormType.PATTERN: {
                const errors: Record<string, string> = {}
                if (!patternForm.pattern.trim()) {
                    errors.pattern = '패턴을 선택해주세요.'
                }
                const period = toNumberOrNull(patternForm.period)

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
        thresholdForm.threshold = ''

        crossForm.threshold = ''
        crossForm.confirmBars = 1

        rangeForm.minValue = ''
        rangeForm.maxValue = ''

        percentForm.percent = ''

        patternForm.pattern = ''
        patternForm.period = ''
    }

    const buildAlertSavePayload = (): AlertSaveQuery => {
        if (form.alertTypeId === null) {
            throw new Error("alert_type_required")
        }

        return {
            name: form.name,
            exchangeInstrumentId: form.exchangeInstrumentId,
            alertTypeId: form.alertTypeId,

            isOnce: form.isOnce,
            status: form.status,
            scope: form.scope,

            throttleTimeframe: form.throttleTimeframe,
            timezone: form.timezone,

            useValidity: form.useValidity,
            validFrom: form.useValidity ? form.validFrom : null,
            validTo: form.useValidity ? form.validTo : null,

            timeframe: null,
            period: null,

            params: buildParams(),
        }
    }

    function applyAlertToForm(alert: AlertDto) {
        form.name = alert.name
        form.exchangeInstrumentId = alert.exchangeInstrumentId
        form.alertTypeId = alert.alertTypeId
        form.isOnce = alert.isOnce
        form.status = alert.status
        form.scope = alert.scope
        form.timezone = alert.timezone

        form.throttleTimeframe = toThrottleTimeframe(alert.throttleSeconds)

        form.useValidity = alert.validFrom !== null || alert.validTo !== null
        form.validFrom = alert.validFrom ?? ''
        form.validTo = alert.validTo ?? ''

        selectedSimpleMarketLabel.value = `${alert.exchangeName} · ${alert.exchangeSymbol}`

        const alertType = alertTypes.value.find((item) => item.id === alert.alertTypeId)
        if (!alertType) return

        applyParamsToConditionForm(alert.params, alertType.formType)
    }

    function applyParamsToConditionForm(
        params: Record<string, unknown>,
        formType: FormType,
    ) {
        switch (formType) {
            case FormType.THRESHOLD:
                thresholdForm.threshold =
                    params.threshold !== undefined && params.threshold !== null
                        ? String(params.threshold)
                        : ""
                return

            case FormType.CROSS:
                crossForm.threshold =
                    params.threshold !== undefined && params.threshold !== null
                        ? String(params.threshold)
                        : ""

                crossForm.confirmBars =
                    typeof params.confirmBars === "number"
                        ? params.confirmBars
                        : Number(params.confirmBars ?? 1)

                return

            case FormType.RANGE:
                rangeForm.minValue =
                    params.minValue !== undefined && params.minValue !== null
                        ? String(params.minValue)
                        : ""

                rangeForm.maxValue =
                    params.maxValue !== undefined && params.maxValue !== null
                        ? String(params.maxValue)
                        : ""

                return

            case FormType.PERCENT:
                percentForm.percent =
                    params.percent !== undefined && params.percent !== null
                        ? String(params.percent)
                        : ""

                return

            case FormType.PATTERN:
                patternForm.pattern =
                    typeof params.pattern === "string"
                        ? params.pattern
                        : ""

                patternForm.period =
                    params.period !== undefined && params.period !== null
                        ? String(params.period)
                        : ""

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
        console.log("handleSubmit", form, thresholdForm)
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