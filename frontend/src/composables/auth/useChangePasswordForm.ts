import { ref, computed } from "vue"
import { isStrongPassword, minLength } from "@/utils/validate"

type Fields = {
    currentPassword: string
    newPassword: string
    confirmPassword: string
}

type FieldErrors = {
    currentPassword: string | null
    newPassword: string | null
    confirmPassword: string | null
}

const emptyErrors = (): FieldErrors => ({
    currentPassword: null,
    newPassword: null,
    confirmPassword: null,
})

export function useChangePasswordForm() {
    const fields = ref<Fields>({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
    })

    const fieldErrors = ref<FieldErrors>(emptyErrors())
    const errorMessage = ref<string | null>(null)
    const showPasswordCurrent = ref(false)
    const showPassword = ref(false)
    const showPasswordConfirm = ref(false)

    function validate(): boolean {
        const errs = emptyErrors()

        const cp = fields.value.currentPassword.trim()
        const np = fields.value.newPassword.trim()
        const npc = fields.value.confirmPassword.trim()

        if (!cp) {
            errs.currentPassword = "현재 비밀번호를 입력해주세요."
        }

        if (!np)
            errs.newPassword = "새 비밀번호를 입력해주세요."
        else if (!minLength(np, 8))
            errs.newPassword = "비밀번호는 8자 이상이어야 합니다."
        else if (!isStrongPassword(np))
            errs.newPassword = "비밀번호는 영문/숫자/특수문자를 모두 포함해야 합니다.";

        if (!npc)
            errs.confirmPassword = "비밀번호 확인을 입력해주세요."
        else if (np !== npc)
            errs.confirmPassword = "비밀번호가 일치하지 않습니다."

        fieldErrors.value = errs

        return !errs.currentPassword && !errs.newPassword && !errs.confirmPassword
    }

    function reset() {
        fields.value.currentPassword = ""
        fields.value.newPassword = ""
        fields.value.confirmPassword = ""
        showPasswordCurrent.value = false
        showPassword.value = false
        showPasswordConfirm.value = false

        fieldErrors.value = emptyErrors()
        errorMessage.value = null
    }

    function onInputChanged() {
        fieldErrors.value = emptyErrors()
        errorMessage.value = null
    }

    function onBlurValidate() {
        validate();
    }

    const canSubmit = computed(() => {
        const { currentPassword, newPassword, confirmPassword } = fields.value
        if (!currentPassword) return false
        if (!newPassword) return false
        if (!minLength(newPassword, 8)) return false
        if (!isStrongPassword(newPassword)) return false
        if (!confirmPassword) return false
        if (newPassword !== confirmPassword) return false
        return true
    })

    async function handleSubmit(fn: () => Promise<void> | void) {
        if (!canSubmit.value) return

        fieldErrors.value = emptyErrors()
        errorMessage.value = null

        if (!validate()) return

        await fn()
    }

    return {
        fields,

        fieldErrors,
        errorMessage,
        showPasswordCurrent,
        showPassword,
        showPasswordConfirm,

        validate,
        handleSubmit,

        onInputChanged,
        onBlurValidate,
        reset,

        canSubmit,
    }
}