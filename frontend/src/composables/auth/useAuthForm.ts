import { computed, ref } from "vue"

type Validator<TFields, TErrors> = (fields: TFields) => TErrors
type HasAnyError<TErrors> = (errors: TErrors) => boolean

type UseAuthFormOptions<TFields, TErrors> = {
    /** 초기 폼 값 */
    initialFields: TFields
    /** 빈 에러 객체 생성기 */
    emptyErrors: () => TErrors

    /** fields -> errors */
    validate: Validator<TFields, TErrors>
    /** errors에 에러가 하나라도 있는지 */
    hasAnyError: HasAnyError<TErrors>

    /** 전송 가능 여부 (기본: 에러 없고, sending 아님) */
    canSend?: (ctx: {
        fields: TFields
        errors: TErrors
        // 쿨다운 옵션
        isCooldown?: boolean
    }) => boolean

    /** 쿨다운(있으면 반영) */
    cooldown?: {
        isCooldown: { value: boolean }
        cooldownSec: { value: number }
    }
}

export function useAuthForm<TFields extends Record<string, any>, TErrors>(
    opts: UseAuthFormOptions<TFields, TErrors>
) {
    const fields = ref<TFields>({ ...opts.initialFields })
    const fieldErrors = ref<TErrors>(opts.emptyErrors())

    const errorMessage = ref<string | null>(null)
    const successMessage = ref<string | null>(null)

    function runValidate(): boolean {
        const errors = opts.validate(fields.value)
        fieldErrors.value = errors
        return !opts.hasAnyError(errors)
    }

    function resetMessages() {
        errorMessage.value = null
        successMessage.value = null
    }

    function onInputChanged() {
        resetMessages()
    }

    function onBlurValidate() {
        runValidate()
    }

    const canSend = computed(() => {
        const isCooldown = opts.cooldown?.isCooldown.value ?? false
        if (opts.canSend) {
            return opts.canSend({
                fields: fields.value,
                errors: fieldErrors.value,
                isCooldown,
            })
        }
        return !isCooldown && !opts.hasAnyError(fieldErrors.value)
    })

    /**
     * onSuccess: 실제 API 호출/비즈니스 로직. 실패 시 throw하면 됨.
     */
    async function handleSubmit(onSuccess: () => Promise<void> | void) {
        if (!canSend.value) return

        // 항상 최신 상태로 검증
        fieldErrors.value = opts.emptyErrors()
        resetMessages()

        if (!runValidate()) return

        await onSuccess()
    }

    return {
        // state
        fields,
        fieldErrors,
        errorMessage,
        successMessage,
        canSend,

        // actions
        runValidate,
        onInputChanged,
        onBlurValidate,
        handleSubmit,
        resetMessages,
    }
}