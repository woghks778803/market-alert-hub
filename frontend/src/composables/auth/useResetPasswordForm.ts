import { computed, ref } from "vue"
import { isStrongPassword } from "@/utils/validate"

type FieldErrors = {
    password: string | null;
    passwordConfirm: string | null;
};

function emptyErrors(): FieldErrors {
    return { password: null, passwordConfirm: null };
}

export function useResetPasswordForm() {
    const password = ref("");
    const passwordConfirm = ref("");

    const showPassword = ref(false);
    const showPasswordConfirm = ref(false);

    const fieldErrors = ref<FieldErrors>(emptyErrors());
    const errorMessage = ref<string | null>(null);

    function validate(): boolean {
        const errs = emptyErrors();

        const p = password.value;
        const pc = passwordConfirm.value;

        if (!p.trim()) {
            errs.password = "비밀번호를 입력해주세요.";
        } else if (!isStrongPassword(p)) {
            errs.password = "비밀번호는 영문/숫자/특수문자를 포함한 8자 이상이어야 합니다.";
        }

        if (!pc.trim()) {
            errs.passwordConfirm = "비밀번호 확인을 입력해주세요.";
        } else if (pc !== p) {
            errs.passwordConfirm = "비밀번호가 일치하지 않습니다.";
        }

        fieldErrors.value = errs;

        return !errs.password && !errs.passwordConfirm;
    }

    function onInputChanged() {
        fieldErrors.value = emptyErrors();
    }

    function onBlurValidate() {
        validate();
    }

    const canSubmit = computed(() => {
        if (!password.value.trim()) return false;
        if (!passwordConfirm.value.trim()) return false;
        if (passwordConfirm.value !== password.value) return false;
        if (!isStrongPassword(password.value)) return false;
        return true
    });

    async function handleSubmit(onSuccess: () => Promise<void> | void) {
        if (!canSubmit.value) return
        fieldErrors.value = emptyErrors();
        errorMessage.value = null;

        if (!validate()) return;

        await onSuccess();
    }

    return {
        password,
        passwordConfirm,
        showPassword,
        showPasswordConfirm,

        fieldErrors,
        errorMessage,
        canSubmit,
        handleSubmit,

        validate,
        onInputChanged,
        onBlurValidate,
    };
}