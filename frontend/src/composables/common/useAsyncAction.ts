import { computed, ref } from "vue"

export function useAsyncAction() {
    const loading = ref(false)
    const errorMessage = ref<string | null>(null)
    const successMessage = ref<string | null>(null)

    const isReady = computed(() => !loading.value)

    function resetMessages() {
        errorMessage.value = null
        successMessage.value = null
    }

    async function run<T>(fn: () => Promise<T>) {
        if (loading.value) return null
        resetMessages()
        loading.value = true
        try {
            await fn()
        } finally {
            loading.value = false
        }
    }

    return {
        loading,
        isReady,
        errorMessage,
        successMessage,
        resetMessages,
        run,
    }
}