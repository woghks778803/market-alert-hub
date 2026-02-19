import { computed, ref } from "vue"
import { isEmail } from "@/utils/validate";

type FieldErrors = {
    email: string | null;
    password: string | null;
};

function emptyErrors(): FieldErrors {
    return {
        email: null,
        password: null,
    };
}

export function useLoginForm() {
    const email = ref("")
    const password = ref("")
    const showPassword = ref(false)
    const submitting = ref(false)

    const errorMessage = ref<string | null>(null)
    const fieldErrors = ref<FieldErrors>(emptyErrors()); // 필드 에러용

    function clearErrors() {
        fieldErrors.value = emptyErrors();
    }

    function validate(): boolean {
        const e = email.value.trim();
        const p = password.value.trim();

        const errs = emptyErrors();

        if (!e) {
            errs.email = "이메일을 입력해주세요.";
        } else if (!isEmail(e)) {
            errs.email = "올바른 이메일 형식이 아닙니다.";
        }

        if (!p) {
            errs.password = "비밀번호를 입력해주세요.";
        }

        fieldErrors.value = errs;

        return !errs.email && !errs.password;
    }

    const canSubmit = computed(() => {
        const e = email.value.trim();
        const p = password.value.trim();

        if (!e) return false
        if (!isEmail(e)) return false
        if (!p) return false
        return true
    })

    async function submit(onSuccess?: () => Promise<void> | void) {
        clearErrors();
        errorMessage.value = null;

        if (!validate()) return;

        submitting.value = true
        try {
            // TODO: API는 나중에. 지금은 UI 플로우만.
            await onSuccess?.()
        } finally {
            submitting.value = false
        }
    }

    return {
        email,
        password,
        showPassword,
        submitting,

        errorMessage,
        fieldErrors,

        canSubmit,
        validate,
        submit,
    }
}
