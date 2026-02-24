import { computed, ref } from "vue"
import { isEmail, minLength } from "@/utils/validate";

function isStrongPassword(v: string): boolean {
    const s = v.trim();
    if (s.length < 8) return false;

    const hasDigit = /\d/.test(s);
    const hasLetter = /[A-Za-z]/.test(s);
    const hasSpecial = /[^A-Za-z0-9]/.test(s);

    return hasDigit && hasLetter && hasSpecial;
}

function isValidNickname(v: string): boolean {
    const s = v.trim();
    if (!s) return false;
    if (s.length < 2) return false;
    if (s.length > 20) return false;
    return true;
}

type FieldErrors = {
    email: string | null;
    nickname: string | null;
    password: string | null;
    passwordConfirm: string | null;
};

function emptyErrors(): FieldErrors {
    return { email: null, nickname: null, password: null, passwordConfirm: null };
}

export function useRegisterEmailForm() {
    const errorMessage = ref<string | null>(null);
    const submitting = ref(false);

    const email = ref("")
    const nickname = ref("")
    const password = ref("")
    const passwordConfirm = ref("")

    const showPassword = ref(false)
    const showPasswordConfirm = ref(false)

    const fieldErrors = ref<FieldErrors>(emptyErrors());

    function validate(): boolean {
        const e = email.value.trim();
        const n = nickname.value.trim();
        const p = password.value;
        const pc = passwordConfirm.value;

        const errs = emptyErrors();

        if (!e) errs.email = "이메일을 입력해주세요.";
        else if (!isEmail(e)) errs.email = "올바른 이메일 형식이 아닙니다.";

        if (!n) errs.nickname = "닉네임을 입력해주세요.";
        else if (!isValidNickname(n)) errs.nickname = "닉네임은 2~20자로 입력해주세요.";

        if (!p.trim()) errs.password = "비밀번호를 입력해주세요.";
        else if (!minLength(p, 8)) errs.password = "비밀번호는 8자 이상이어야 합니다.";
        else if (!isStrongPassword(p))
            errs.password = "비밀번호는 영문/숫자/특수문자를 모두 포함해야 합니다.";

        if (!pc.trim()) errs.passwordConfirm = "비밀번호 확인을 입력해주세요.";
        else if (p !== pc) errs.passwordConfirm = "비밀번호가 일치하지 않습니다.";

        fieldErrors.value = errs;

        return !errs.email && !errs.nickname && !errs.password && !errs.passwordConfirm;
    }

    function onInputChanged() {
        fieldErrors.value = emptyErrors();
        errorMessage.value = null;
    }
    function onBlurValidate() {
        validate();
    }

    const canSubmit = computed(() => {
        const e = email.value.trim();
        const n = nickname.value.trim();
        const p = password.value;
        const pc = passwordConfirm.value;

        if (!e) return false;
        if (!isEmail(e)) return false;

        if (!n) return false;
        if (!isValidNickname(n)) return false;

        if (!p.trim()) return false;
        if (!minLength(p, 8)) return false;
        if (!isStrongPassword(p)) return false;

        if (!pc.trim()) return false;
        if (p !== pc) return false;

        return submitting.value === false;
    });

    async function submit(onSuccess: () => Promise<void> | void) {
        if (!canSubmit.value) return
        fieldErrors.value = emptyErrors();
        errorMessage.value = null;

        if (!validate()) return;

        submitting.value = true;
        try {
            await onSuccess();
        } finally {
            submitting.value = false;
        }
    }

    return {
        email,
        nickname,
        password,
        passwordConfirm,
        showPassword,
        showPasswordConfirm,

        fieldErrors,
        validate,

        errorMessage,
        submitting,
        submit,
        canSubmit,
        onInputChanged,
        onBlurValidate,
    }
}
