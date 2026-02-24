import { computed, ref } from "vue";
import { isEmail } from "@/utils/validate";
import { useCooldown } from "@/composables/common/useCooldown";

type FieldErrors = { email: string | null };

function emptyErrors(): FieldErrors {
    return { email: null };
}

export function useForgotPasswordForm() {
    const email = ref("");
    const sending = ref(false);

    const fieldErrors = ref<FieldErrors>(emptyErrors());
    const errorMessage = ref<string | null>(null);
    const successMessage = ref<string | null>(null);

    const { cooldownSec, isCooldown, startCooldown } = useCooldown();
    const canSend = computed(() => {
        const e = email.value.trim();
        if (!e) return false;
        if (!isEmail(e)) return false;
        return !sending.value && !isCooldown.value;
    });

    function validate(): boolean {
        const e = email.value.trim();
        const errs = emptyErrors();

        if (!e) errs.email = "이메일을 입력해주세요.";
        else if (!isEmail(e)) errs.email = "올바른 이메일 형식이 아닙니다.";

        fieldErrors.value = errs;
        return !errs.email;
    }

    function onInputChanged() {
        errorMessage.value = null;
        successMessage.value = null;
    }

    function onBlurValidate() {
        validate();
    }

    async function send(onSuccess: () => Promise<void> | void) {
        if (!canSend.value) return
        fieldErrors.value = emptyErrors();
        errorMessage.value = null;
        successMessage.value = null;

        if (!validate()) return;

        sending.value = true;
        try {
            await onSuccess();
        } finally {
            sending.value = false;
        }
    }

    return {
        errorMessage,
        successMessage,

        sending,
        canSend,
        send,

        cooldownSec,
        isCooldown,
        startCooldown,

        fieldErrors,
        email,
        validate,
        onInputChanged,
        onBlurValidate,
    };
}