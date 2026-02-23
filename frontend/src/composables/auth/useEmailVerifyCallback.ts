import { ref } from "vue"

export type EmailVerifyMode = "processing" | "success" | "fail"

export function useEmailVerifyCallback() {
    const mode = ref<EmailVerifyMode>("processing")
    const running = ref(false)

    function setMode(next: EmailVerifyMode) {
        mode.value = next
    }

    async function runVerify(run?: () => Promise<void> | void) {
        if (running.value) return
        running.value = true

        try {
            await run?.()
        } finally {
            running.value = false
        }
    }

    return {
        mode,
        running,
        setMode,
        runVerify,
    }
}
