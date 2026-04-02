import { ref } from "vue"

export function useVerifyEmailSent() {
    const successMessage = ref<string | null>(null)
    const errorMessage = ref<string | null>(null)

    function resetMessages() {
        errorMessage.value = null
        successMessage.value = null
    }

    return {
        successMessage,
        errorMessage,
        resetMessages
    }
}