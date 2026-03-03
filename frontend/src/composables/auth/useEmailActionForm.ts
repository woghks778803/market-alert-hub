import { computed } from "vue";
import { isEmail } from "@/utils/validate";
import { useCooldown } from "@/composables/common/useCooldown";
import { useAuthForm } from "@/composables/auth/useAuthForm"

type Fields = { email: string }
type Errors = { email: string }

const emptyErrors = (): Errors => ({ email: "" })
const hasAnyError = (e: Errors) => !!e.email

export function useEmailActionForm() {

    const { cooldownSec, isCooldown, startCooldown } = useCooldown();
    const form = useAuthForm<Fields, Errors>({
        initialFields: { email: "" },
        emptyErrors,
        validate: (f) => {
            const e = emptyErrors()
            const email = f.email.trim()
            if (!email) e.email = "이메일을 입력해주세요."
            else if (!isEmail(email)) e.email = "올바른 이메일 형식이 아닙니다."
            return e
        },
        hasAnyError,
        cooldown: { cooldownSec, isCooldown },
        canSend: ({ fields, sending, isCooldown }) => {
            const email = fields.email.trim()
            if (!email) return false
            if (sending) return false
            if (isCooldown) return false
            return true
        },
    })

    const isReady = computed(() => form.canSend.value)

    return {
        ...form,
        cooldownSec,
        isCooldown,
        startCooldown,
        isReady,
    }
}